"""
Tests for the per-pitcher ranked leads.

Two properties are load-bearing and both are negative:

* **Ranking cannot promote.** Leads are evaluated on holdout so their rows can
  carry a fires-versus-random line, which means the code path that produces them
  now computes exactly the numbers the tiers gate on. That is precisely when a
  second route to promotion appears by accident, so it is closed in code.
* **Discovery is blind.** Nothing in the leads path may read the scout
  documentation, or the later check for matches against documented tips proves
  nothing.
"""
from __future__ import annotations

import json
from pathlib import Path

from preflight import build_board, leads, tiering


def test_leads_module_emits_only_the_low_tier():
    assert leads.TIER == "LOW"
    assert leads.TIER not in (tiering.TIER_HIGH, tiering.TIER_MEDIUM)


def test_the_leads_source_never_mentions_the_promotable_tiers():
    """A lead must not be able to acquire HIGH or MEDIUM anywhere in this path."""
    src = Path(leads.__file__).read_text()
    assert "TIER_HIGH" not in src
    assert "TIER_MEDIUM" not in src


def test_the_leads_path_does_not_read_scout_documentation():
    """Checked against the code, not the prose.

    The module docstring names the scout files in order to explain that it does not
    read them, so scanning the raw text would flag its own documentation. What
    matters is the executable body.
    """
    import ast

    tree = ast.parse(Path(leads.__file__).read_text())
    tree.body = [n for n in tree.body
                 if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
    body = ast.unparse(tree)
    for forbidden in ("prespecified_tips", "documented_tips", "apex_tipping"):
        assert forbidden not in body, f"blind guarantee broken: reads {forbidden}"


def test_published_leads_json_declares_itself_blind_and_low():
    out = Path(leads.__file__).resolve().parents[2] / "runs" / "leads.json"
    if not out.exists():
        return
    doc = json.loads(out.read_text())
    assert doc["consulted_scout_documentation"] is False
    assert doc["tier"] == "LOW"
    for arm in doc["arms"]:
        for row in arm["leads"]:
            assert row["tier"] == "LOW"


def test_a_row_worse_than_guessing_is_marked_and_carries_the_inverse():
    row = {
        "rank": 1, "cue": "c", "contrast": "A vs B", "delivery_stratum": "stretch",
        "separation_floor_multiples": 17.5, "separation_raw": -0.88, "unit": "torso lengths",
        "direction": "on B he lifts higher", "fires_vs_random": "right 29.0% (vs 42.7% baseline mix)",
        "youden_j": -0.23, "lr_pos": 0.55, "n_fire": 31, "n_a": 15, "n_b": 8,
        "gate_plain": "did not survive multiple-comparison correction",
        "below_base_rate": True, "inverse_reading": "read the other way",
    }
    html = build_board.top5_row(row)
    assert "Complementary / Inverse Indicator" in html
    assert "read the other way" in html


def test_a_normal_row_carries_no_warning():
    row = {
        "rank": 2, "cue": "c", "contrast": "A vs B", "delivery_stratum": "stretch",
        "separation_floor_multiples": 3.0, "separation_raw": 0.1, "unit": "torso lengths",
        "direction": "on A he sets higher", "fires_vs_random": "right 62.0% (vs 53.3% baseline mix)",
        "youden_j": 0.19, "lr_pos": 1.43, "n_fire": 50, "n_a": 35, "n_b": 8,
        "gate_plain": "did not survive multiple-comparison correction",
        "below_base_rate": False,
    }
    assert "Complementary / Inverse Indicator" not in build_board.top5_row(row)


def test_the_board_refuses_leads_that_broke_the_blind_guarantee():
    """The build must fail loudly rather than publish a compromised comparison."""
    src = Path(build_board.__file__).read_text()
    assert "blind guarantee broken" in src
    assert "leads must be LOW only" in src


def test_an_arm_with_too_few_visible_cues_is_not_padded():
    doc_path = Path(leads.__file__).resolve().parents[2] / "runs" / "leads.json"
    if not doc_path.exists():
        return
    for arm in json.loads(doc_path.read_text())["arms"]:
        assert len(arm["leads"]) <= leads.TOP_N
        if len(arm["leads"]) < leads.TOP_N:
            # Showing fewer is fine; showing fewer without saying why is not.
            assert arm["short_reason"]
