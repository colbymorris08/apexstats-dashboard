"""
Count-contextual + tip confidence thresholds for Preflight.

Locked package: C — Strict club (75% tip floor). Floor chart A–D kept for diligence;
C is the strictest absolute tip gate.
"""
from __future__ import annotations

from dataclasses import dataclass

# Product tip gate — tip cards only publish at/above this
TIP_CONFIDENCE_FLOOR = 0.75


@dataclass(frozen=True)
class CountGate:
    name: str
    abs_floor: float
    base_rate_margin: float
    note: str


# Package C — Strict club (from floor_proposals). Tip display uses TIP_CONFIDENCE_FLOOR=75%.
COUNT_GATES: dict[str, CountGate] = {
    "early": CountGate(
        "early",
        abs_floor=0.60,
        base_rate_margin=0.08,
        note="0-0 / 1-0 / 0-1 — package C early floor",
    ),
    "hitter": CountGate(
        "hitter",
        abs_floor=0.62,
        base_rate_margin=0.08,
        note="2-0 / 3-0 / 3-1",
    ),
    "neutral": CountGate(
        "neutral",
        abs_floor=0.65,
        base_rate_margin=0.10,
        note="1-1 / 2-1 / 3-2",
    ),
    "pitcher": CountGate(
        "pitcher",
        abs_floor=0.70,
        base_rate_margin=0.10,
        note="0-2 / 1-2",
    ),
    "two_strike": CountGate(
        "two_strike",
        abs_floor=0.75,
        base_rate_margin=0.12,
        note="x-2 — package C / tip floor alignment",
    ),
}

TIER_ELITE = 0.75
TIER_OPERATIONAL = 0.60
TIER_DEVELOPING = 0.50


def count_bucket(balls: int, strikes: int) -> str:
    b, s = int(balls), int(strikes)
    if s >= 2:
        return "two_strike"
    if (b, s) in {(0, 0), (1, 0), (0, 1)}:
        return "early"
    if (b, s) in {(2, 0), (3, 0), (3, 1)}:
        return "hitter"
    if (b, s) in {(0, 2), (1, 2)}:
        return "pitcher"
    return "neutral"


def required_accuracy(base_rate: float, balls: int, strikes: int) -> float:
    gate = COUNT_GATES[count_bucket(balls, strikes)]
    return max(gate.abs_floor, float(base_rate) + gate.base_rate_margin, TIP_CONFIDENCE_FLOOR)


def passes_gate(accuracy: float, base_rate: float, balls: int, strikes: int) -> bool:
    return float(accuracy) >= required_accuracy(base_rate, balls, strikes)


def clears_tip_floor(accuracy: float, floor: float = TIP_CONFIDENCE_FLOOR) -> bool:
    return float(accuracy) >= float(floor)


def confidence_tier(accuracy: float) -> str:
    a = float(accuracy)
    if a >= TIER_ELITE:
        return "elite"
    if a >= TIER_OPERATIONAL:
        return "operational"
    if a >= TIER_DEVELOPING:
        return "developing"
    return "watch"


def binary_ev_breakeven(v_correct: float, v_wrong: float, v_baseline: float) -> float:
    denom = v_correct - v_wrong
    if abs(denom) < 1e-9:
        return 1.0
    return (v_baseline - v_wrong) / denom
