"""
The blind sweep must be structurally unable to consult the documented tips.

The Dreyer experiment only means anything if the blind discovery path cannot see the
answer key. Intention is not a guarantee — if the sweep is run after the answer is
known, the separation has to be enforced by the code path. These tests are that
enforcement, and they will fail loudly if a future edit imports the registry into
the discovery path.

Also tested: published leads cannot become a promotion route. Evaluating a failed
candidate on the holdout is necessary for the board's "versus random" column, and
it must never make that candidate eligible for a gated tier.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REGISTRY = HERE.parents[1] / "docs" / "prespecified_tips.json"

# Modules that make up the blind discovery and ranking path. None of them may read
# the documented-tip registry, directly or transitively through our own package.
BLIND_PATH = [
    "spot_diff.py",
    "temporal.py",
    "temporal_discover.py",
    "magnitude.py",
    "leads.py",
    "jcalib.py",
    "tiering.py",
]

FORBIDDEN = ("prespec", "prespecified_tips", "documented_tips")


def _imports_and_strings(path: Path) -> tuple[set[str], list[str]]:
    tree = ast.parse(path.read_text())
    mods: set[str] = set()
    strings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module)
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.append(node.value)
    return mods, strings


@pytest.mark.parametrize("name", BLIND_PATH)
def test_blind_path_never_imports_the_answer_key(name):
    path = HERE / name
    if not path.exists():
        pytest.skip(f"{name} not present")
    mods, _ = _imports_and_strings(path)
    offenders = [m for m in mods if any(f in m for f in FORBIDDEN)]
    assert not offenders, (
        f"{name} imports {offenders}: the blind sweep must not be able to consult "
        "the documented tips, or the Dreyer answer-key experiment is worthless"
    )


@pytest.mark.parametrize("name", BLIND_PATH)
def test_blind_path_never_opens_the_registry_by_path(name):
    """An import is the obvious route; a hardcoded filename is the sneaky one."""
    path = HERE / name
    if not path.exists():
        pytest.skip(f"{name} not present")
    _, strings = _imports_and_strings(path)
    offenders = [s for s in strings
                 if "prespecified_tips" in s or "documented_tips" in s]
    assert not offenders, f"{name} references the registry by name: {offenders}"


def test_the_registry_exists_and_is_prespecified():
    reg = json.loads(REGISTRY.read_text())
    assert reg["written_before_results"] is True
    # Every registered test must fix its direction in advance. A test without a
    # predicted direction is not prespecified: it could be scored either way after
    # the fact, which is the whole thing prespecification exists to prevent.
    for t in reg["tests"]:
        assert t["predicted_direction"] in {"a_higher", "a_lower"}, t["id"]
        assert t["cue"], t["id"]
        assert t["pitch_a"], t["id"]


def test_registered_cues_are_not_retracted():
    """A scout naming a cue does not override what the instrument measures."""
    from preflight import tiering
    reg = json.loads(REGISTRY.read_text())
    for t in reg["tests"]:
        assert tiering.retraction_reason(t["cue"]) is None, (
            f"{t['id']} registers retracted cue {t['cue']}"
        )


def test_published_leads_are_hard_locked_to_the_low_tier():
    from preflight import leads, tiering
    assert leads.TIER == "low"
    assert leads.TIER not in (tiering.TIER_HIGH, tiering.TIER_MEDIUM)


def test_leads_module_cannot_assign_a_gated_tier():
    """No literal in the leads module may name a gated tier."""
    from preflight import tiering
    _, strings = _imports_and_strings(HERE / "leads.py")
    gated = {tiering.TIER_HIGH, tiering.TIER_MEDIUM}
    # Prose may discuss the tiers; what must not exist is a bare literal equal to
    # one, which is what an assignment would look like.
    assert not [s for s in strings if s in gated], (
        "leads.py contains a bare gated-tier literal: evaluating a failed candidate "
        "must never be able to promote it"
    )


def test_prespecified_results_carry_a_distinct_family_label():
    """So the two families can never be silently pooled in a count."""
    src = (HERE / "prespec.py").read_text()
    assert '"family": "prespecified_documented"' in src
    src_leads = (HERE / "leads.py").read_text()
    assert '"family": "blind_sweep"' in src_leads
