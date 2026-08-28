"""
Preflight situational context tags for tip mining and dossier filters.

Buckets requested for testing:
  - runners: first only · any with runner on second · third only · (also empty / other)
  - batter: LHH vs RHH
  - delivery: set/stretch vs windup
"""
from __future__ import annotations

from typing import Any

# Site / dossier filter IDs (must stay in sync with data/demo.json meta.contexts)
CONTEXT_DEFS: list[dict[str, str]] = [
    {"id": "none", "label": "Bases empty"},
    {"id": "1b", "label": "First only"},
    {"id": "second_any", "label": "Any w/ runner on 2nd"},
    {"id": "3b", "label": "Third only"},
    {"id": "2b", "label": "Runner on 2nd only"},
    {"id": "12", "label": "1st & 2nd"},
    {"id": "13", "label": "1st & 3rd"},
    {"id": "23", "label": "2nd & 3rd"},
    {"id": "loaded", "label": "Bases loaded"},
    {"id": "stretch", "label": "Set / stretch"},
    {"id": "windup", "label": "Windup"},
    {"id": "lhh", "label": "vs LHH"},
    {"id": "rhh", "label": "vs RHH"},
]


def runner_state(on1: bool, on2: bool, on3: bool) -> str:
    """Exact base-state id."""
    key = (bool(on1), bool(on2), bool(on3))
    return {
        (False, False, False): "none",
        (True, False, False): "1b",
        (False, True, False): "2b",
        (False, False, True): "3b",
        (True, True, False): "12",
        (True, False, True): "13",
        (False, True, True): "23",
        (True, True, True): "loaded",
    }[key]


def runner_test_bucket(on1: bool, on2: bool, on3: bool) -> str:
    """
    Coarse buckets used for tip mining / EV tests:
      first only | any with R2 | third only | empty | other (e.g. 1st+3rd)
    """
    if on2:
        return "second_any"
    if on1 and not on3:
        return "1b"
    if on3 and not on1:
        return "3b"
    if not on1 and not on2 and not on3:
        return "none"
    return "other"  # e.g. 1st & 3rd


def delivery_from_runners(on1: bool, on2: bool, on3: bool) -> str:
    """
    MLB heuristic for PoC: any baserunner → set/stretch; empty → windup.
    Club film can override with labeled delivery later.
    """
    return "stretch" if (on1 or on2 or on3) else "windup"


def batter_side_tag(code: str | None) -> str | None:
    if not code:
        return None
    c = str(code).upper()
    if c.startswith("L"):
        return "lhh"
    if c.startswith("R"):
        return "rhh"
    return None


def context_tags(
    *,
    on1: bool,
    on2: bool,
    on3: bool,
    bat_side: str | None,
    delivery: str | None = None,
) -> list[str]:
    """All filter tags that apply to one pitch."""
    tags: list[str] = []
    exact = runner_state(on1, on2, on3)
    tags.append(exact)
    coarse = runner_test_bucket(on1, on2, on3)
    if coarse not in tags and coarse != "other":
        tags.append(coarse)
    deliv = delivery or delivery_from_runners(on1, on2, on3)
    tags.append(deliv)
    side = batter_side_tag(bat_side)
    if side:
        tags.append(side)
    # de-dupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def context_phrase(tags: list[str]) -> str:
    """Short English prefix for lookFor copy."""
    parts: list[str] = []
    if "lhh" in tags:
        parts.append("vs lefties")
    elif "rhh" in tags:
        parts.append("vs righties")
    runner_labels = {
        "none": "bases empty",
        "1b": "first only",
        "second_any": "any time a runner is on second",
        "3b": "third only",
        "2b": "runner on second only",
        "12": "1st & 2nd",
        "13": "1st & 3rd",
        "23": "2nd & 3rd",
        "loaded": "bases loaded",
    }
    for rid, label in runner_labels.items():
        if rid in tags:
            parts.append(label)
            break
    if "stretch" in tags:
        parts.append("from the set")
    elif "windup" in tags:
        parts.append("from the windup")
    if not parts:
        return ""
    return "In " + ", ".join(parts) + ": "


def apply_runner_movements(bases: dict[str, Any], runners: list[dict]) -> dict[str, Any]:
    """Update 1B/2B/3B occupancy after a play using live-feed runner movements."""
    stay = dict(bases)
    for r in runners or []:
        mv = r.get("movement") or {}
        start = mv.get("start")
        end = mv.get("end")
        rid = ((r.get("details") or {}).get("runner") or {}).get("id")
        if start in ("1B", "2B", "3B"):
            stay[start] = None
        if mv.get("isOut"):
            continue
        if end in ("1B", "2B", "3B"):
            stay[end] = rid
    return stay


# Strata we always try to mine tips for (when n clears min)
TIP_STRATA: list[tuple[str, str | None]] = [
    ("all", None),  # pooled
    ("runner", "none"),
    ("runner", "1b"),
    ("runner", "second_any"),
    ("runner", "3b"),
    ("batter", "lhh"),
    ("batter", "rhh"),
    ("delivery", "stretch"),
    ("delivery", "windup"),
]
