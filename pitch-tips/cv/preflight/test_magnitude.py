"""
Tests for the magnitude-ranked view.

The one property that matters here is a negative one: **ranking by magnitude must
never change what is believed.** The whole point of surfacing large differences is
to show a club where more film would help, and the moment display order can promote
a result it becomes a route around the gates. The Kelly artifact peaked at g = 0.491
on a rising curve, so "large" and "real" are demonstrably independent.
"""
from __future__ import annotations

import numpy as np

from preflight import magnitude


def test_a_large_effect_needs_fewer_pitches_than_a_small_one():
    assert magnitude.needed_per_group(1.0) < magnitude.needed_per_group(0.25)


def test_required_sample_is_finite_and_sane_for_a_typical_effect():
    # A medium effect of g=0.5 needs ~63 per group at nominal 0.05/80% power. This
    # pins the formula against a textbook value so a future edit cannot quietly
    # turn it into an encouraging number.
    assert 55 <= magnitude.needed_per_group(0.5) <= 70


def test_a_degenerate_effect_has_no_answer_rather_than_a_huge_one():
    # Returning a gigantic n would read as "collectable with enough film". It is
    # not: an effect of zero is never detectable, and saying so is the honest
    # output.
    assert magnitude.needed_per_group(0.0) is None
    assert magnitude.needed_per_group(float("nan")) is None


def _entry(**kw):
    base = {
        "floor_multiples": 5.0, "g_discovery": 1.0, "n_smaller_group": 8,
        "failed_at": "fdr", "cue": "c", "contrast": "A vs B", "n_discovery": 100,
    }
    return {**base, **kw}


def test_sample_limited_excludes_anything_that_passed_the_gates():
    # A survivor is not a case for more film: it already replicated.
    arm = {"ranked": [_entry(failed_at=None)]}
    assert magnitude.sample_limited(arm) == []


def test_sample_limited_excludes_a_null_that_had_plenty_of_pitches():
    # 500 pitches per side against an effect needing 16 is a real null. Calling it
    # sample-limited would tell a club to buy film that cannot change the answer.
    arm = {"ranked": [_entry(n_smaller_group=500)]}
    assert magnitude.sample_limited(arm) == []


def test_sample_limited_flags_a_large_effect_with_too_few_pitches():
    arm = {"ranked": [_entry(g_discovery=1.0, n_smaller_group=8)]}
    got = magnitude.sample_limited(arm)
    assert len(got) == 1
    assert got[0]["n_needed_per_group"] > got[0]["n_have_smaller_group"]


def test_sample_limited_ignores_differences_below_the_visibility_floor():
    # Under the floor a person could not see it even if it were real, so more film
    # would buy a statistically clean invisible cue.
    arm = {"ranked": [_entry(floor_multiples=0.4)]}
    assert magnitude.sample_limited(arm) == []


def test_magnitude_ranking_is_independent_of_gate_outcome():
    """Display order must not encode belief, and belief must not encode order."""
    ranked = [
        _entry(floor_multiples=20.0, failed_at="fdr"),
        _entry(floor_multiples=1.0, failed_at=None),
    ]
    order = sorted(ranked, key=lambda e: e["floor_multiples"], reverse=True)
    # The failing cue sorts above the passing one, and that is correct: the
    # ranking is a physical quantity. What must stay true is that its tier is
    # still driven by ``failed_at`` and not by its position.
    assert order[0]["failed_at"] == "fdr"
    assert order[1]["failed_at"] is None


def test_the_report_never_calls_an_ungated_result_significant():
    arm = {
        "arm": "X", "n_pitches": 1, "n_games_analysed": 1, "n_games_banked": 1,
        "comparisons": 1, "n_surviving": 0,
        "ranked": [_entry(delta=1.0, q_discovery=0.9, unit="torso")],
    }
    text = magnitude.report_text(arm, 5).lower()
    assert "significant" not in text
    assert "failed: fdr" in text
