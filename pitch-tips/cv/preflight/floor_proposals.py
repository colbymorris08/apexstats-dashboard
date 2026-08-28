"""
Proposed publish floors from Müller/Fadde-style outcomes (BB% / OBP / SLG / K) — NOT AVG.

Literature (correlational, not an RCT tip-accuracy trial):
  - Müller & Fadde, JASP 2016 (Single-A): pitch-type anticipation ↔ BB% (r≈.35–.37), OBP (r≈.37)
  - Müller & Fadde, JMLD 2018 (pros N=105): pitch-type anticipation ↔ OBP (r≈.23), BB:K (r≈.25),
    SLG via type+location (r≈.21), fewer Ks (r≈−.28)

Break-even accuracy (same algebra as before, metric-specific):

  Higher-is-better (OBP, BB%, SLG):
    p* = (M0 − Mw) / (Mc − Mw)

  Lower-is-better (K%):
    p* = (M0 − Mw) / (Mc − Mw)   # same form once you plug rates

These are CLUB HEURISTICS calibrated to literature direction (discipline / damage),
not measured tip→outcome RCTs. Pick a package; we will wire it into COUNT_GATES + site copy.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FloorPackage:
    id: str
    label: str
    rationale: str
    site_language: str
    early: float
    hitter: float
    neutral: float
    pitcher: float
    two_strike: float
    tier_operational: float
    tier_elite: float
    example_breakevens: dict[str, float]


# --- Scenario math (illustrative MLB-ish baselines) ---
# OBP: M0=.320, Mc=.350, Mw=.290 → p* = (.320-.290)/(.350-.290) = 0.50
# BB%: M0=.085, Mc=.110, Mw=.060 → p* = 0.50
# K%:  M0=.220, Mc=.170, Mw=.300 → p* = (.220-.300)/(.170-.300) ≈ 0.615
# K% two-strike: M0=.380, Mc=.300, Mw=.520 → p* ≈ 0.636
# SLG: M0=.400, Mc=.450, Mw=.340 → p* ≈ 0.545

FLOOR_PACKAGES: dict[str, FloorPackage] = {
    "A_discipline_balanced": FloorPackage(
        id="A_discipline_balanced",
        label="A — Discipline-balanced (OBP/BB ~50% + light safety)",
        rationale=(
            "Anchors on OBP/BB break-even ≈50% from small anticipation correlations with walks/OBP. "
            "Adds a thin safety margin early; raises floors as wrong sits get more expensive."
        ),
        site_language=(
            "Publish when tip confidence clears an OBP/BB-style break-even (~50%) with a count "
            "safety margin — early counts near 52%, two-strike near 68%. Gains targeted: walks, "
            "OBP, fewer chase-driven outs — not batting average."
        ),
        early=0.52,
        hitter=0.55,
        neutral=0.58,
        pitcher=0.62,
        two_strike=0.68,
        tier_operational=0.52,
        tier_elite=0.68,
        example_breakevens={"OBP_example": 0.50, "BB_example": 0.50, "K_example": 0.615},
    ),
    "B_k_protection": FloorPackage(
        id="B_k_protection",
        label="B — K-protection (K% EV ~62% core)",
        rationale=(
            "Anchors on K% EV (~61.5% in the illustrative 22%/17%/30% scenario) because Müller/Fadde "
            "link anticipation most clearly to fewer strikeouts / better swing decisions. "
            "Two-strike sits require ~68%+."
        ),
        site_language=(
            "Publish when confidence clears a strikeout-protection break-even (~62% illustrative). "
            "Early counts ~55%; two-strike ~72%. Primary product claim: fewer incorrect swings / Ks, "
            "with OBP/BB as secondary."
        ),
        early=0.55,
        hitter=0.58,
        neutral=0.62,
        pitcher=0.66,
        two_strike=0.72,
        tier_operational=0.55,
        tier_elite=0.72,
        example_breakevens={"OBP_example": 0.50, "BB_example": 0.50, "K_example": 0.615},
    ),
    "C_strict_club": FloorPackage(
        id="C_strict_club",
        label="C — Strict club gate (noisy CF / sell-to-ops)",
        rationale=(
            "Same discipline metrics, but assumes tip error is costly in-game and CF PoC is noisy — "
            "so absolute floors sit well above break-even. Closest to a 'only show what we'd put in the box' bar."
        ),
        site_language=(
            "Operational tips require ≥60% early and ≥75% with two strikes, always beating arsenal "
            "base rate. Framed for club ops: anticipation supports BB%/OBP/SLG and K reduction; "
            "we do not sell AVG lift."
        ),
        early=0.60,
        hitter=0.62,
        neutral=0.65,
        pitcher=0.70,
        two_strike=0.75,
        tier_operational=0.60,
        tier_elite=0.75,
        example_breakevens={"OBP_example": 0.50, "BB_example": 0.50, "K_example": 0.615},
    ),
    "D_slg_damage": FloorPackage(
        id="D_slg_damage",
        label="D — Damage / SLG-aware (SLG EV ~55%)",
        rationale=(
            "Uses SLG-style break-even (~54.5% in .400/.450/.340 example) plus K protection late. "
            "Fits 'type+location anticipation ↔ SLG' (r≈.21) while still counting wrong tips as "
            "damage events with two strikes."
        ),
        site_language=(
            "Floors track an SLG/damage break-even (~55%) early, rising to ~70% with two strikes. "
            "Product language: better pitch-type anticipation associates with OBP/SLG and fewer Ks."
        ),
        early=0.55,
        hitter=0.57,
        neutral=0.60,
        pitcher=0.65,
        two_strike=0.70,
        tier_operational=0.55,
        tier_elite=0.70,
        example_breakevens={"SLG_example": 0.545, "K_example": 0.615, "OBP_example": 0.50},
    ),
}


def package_table() -> str:
    lines = ["id | early | hitter | neutral | pitcher | two_strike | ops tier | elite tier"]
    for p in FLOOR_PACKAGES.values():
        lines.append(
            f"{p.id} | {p.early:.0%} | {p.hitter:.0%} | {p.neutral:.0%} | "
            f"{p.pitcher:.0%} | {p.two_strike:.0%} | {p.tier_operational:.0%} | {p.tier_elite:.0%}"
        )
    return "\n".join(lines)
