"""
Confidence tiers for disclosure, defined so the label can be trusted.

The product moves from a single publish/withhold gate to tiered disclosure: a club
sees HIGH, MEDIUM and LOW findings with the confidence attached and triages for
itself. That is how advance scouting actually works, and it is defensible — but the
entire value sits in the label being honest, so the tier definition is the whole
design.

Why precision alone cannot define a tier
----------------------------------------
A raw precision number is close to meaningless without the base rate beside it,
and tiering on precision alone would be actively misleading. Three measured
examples from this project:

* Kelly, ``knee_rise_duration_frac``: precision 0.529 against a 0.500 base rate.
  A coin flip. A naive ">= 0.50 is MEDIUM" rule labels it MEDIUM.
* E. Rodríguez, ``stance_width_at_set``: precision 0.143 against a 0.142 base
  rate, because curveballs are 14% of his pitches. Near zero lift — yet 0.62 precision
  on that same 14% pitch would be an enormous edge, and evaluating predictive lift
  isolates true advance scouting value.
* E. Rodríguez, ``glove_speed_cv`` FF vs SI: precision **0.920**, isolating a sharp
  mechanical variation, evaluated alongside an 0.889 baseline to quantify exact predictive lift.

So a tier requires precision **and** lift over that pitch's own base rate.

Definitions
-----------
``base_rate``  Prevalence of the predicted pitch type among the validation pitches
               the contrast covers. This is what "always guess" would achieve on
               the same pitches, so it is the right thing to beat.
``precision``  Share of the pitches where the rule fires that really are that type.
``lift``       ``precision - base_rate``. Percentage points of improvement over
               guessing.

Thresholds, and why these
-------------------------
``MIN_LIFT = 0.10``  A tip has to be worth changing an approach over. Ten
    percentage points is the smallest improvement that survives being described
    out loud to a hitter — below that, the guidance is "he might be very slightly
    more likely to throw this", which is not actionable and invites overfitting to
    the label. It is also comfortably above the 0.03 lift that the three real
    near-misses above produced, so it separates the cases we know to be worthless
    from the cases we would want to see.
``LIFT_ALPHA = 0.05``  Lift also has to be more than sampling noise. A one-sided
    binomial test asks whether the hits among the fires could have come from the
    base rate alone. This is what stops a rule that fires four times and happens
    to be right from carrying a confidence label.
``MIN_FIRES = 8``  A rule that fires three times is not a tip at any precision.
    Eight is the group minimum the rest of the system already uses
    (``spot_diff.MIN_PER_GROUP``), reused rather than invented.

Hard exclusions
---------------
Retracted cues never appear at any tier. They fail on *what they measure*, not on
strength of evidence: a wrong measurement is not a low-confidence finding, and
demoting one into a tier would launder it back onto the board. LOW must mean "a
real difference we measured that did not validate", not a drawer for known-broken
measurements.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy import stats

from preflight.provenance import RETRACTED_CUES
from preflight.spot_diff import MIN_PER_GROUP

HIGH_PRECISION = 0.75
MEDIUM_PRECISION = 0.50
MIN_LIFT = 0.10
LIFT_ALPHA = 0.05
MIN_FIRES = MIN_PER_GROUP

# Retraction is by family, not only by exact name. Every ``pitchcom_``,
# ``cheek_motion_`` and ``catcher_`` cue was retracted for a reason that applies to
# the whole instrument — the PitchCom detector measures glove-centroid variance,
# the cheek features are head jitter behind a 1.04% face-detection rate, and the
# catcher features track the pitcher. So a *newly added* cue in one of these
# families inherits the defect and must not be able to reach the board just
# because nobody remembered to list it.
RETRACTED_FAMILIES = ("pitchcom_", "cheek_motion_", "catcher_")


def retraction_reason(feature: str) -> str | None:
    if feature in RETRACTED_CUES:
        return RETRACTED_CUES[feature]
    for fam in RETRACTED_FAMILIES:
        if feature.startswith(fam):
            return f"cue is in the retracted {fam.rstrip('_')} family"
    return None


# --------------------------------------------------------------------- stability
#
# The convergence check — effect size as starts accumulate — is the diagnostic that
# caught the partial-sample artifact, and it cannot be computed on a capped arm.
# Kelly is the calibration standard for how much a 3+3 result is worth:
#
#     3 games g=0.125 | 8 g=0.131 | 11 g=0.429 | 18 g=0.491 (peak) | 25 g=0.205
#
# Read that curve from the left. Through 8 games it is flat and small; by 11 it is
# climbing hard and looks like a strengthening real cue; it does not turn over until
# past 18. Anyone who had stopped at 11 would have promoted an artifact with a
# *rising* curve as evidence in its favour. So the sample needed to check stability
# is not "more than three" — it is enough games to see past the peak, which for the
# one artifact we have measured was about twenty.
#
# Consequence, stated plainly: HIGH requires a computable convergence curve, so at
# present only Kelly can produce one. Every capped arm tops out at MEDIUM with the
# caveat attached. This is deliberately strict. The alternative is labelling a
# three-start coincidence "actionable" on a sample that we have direct evidence is
# too small to tell the difference, which is the one mistake this project cannot
# afford to put in front of a club.
MIN_GAMES_FOR_CONVERGENCE = 20

STABILITY_CHECKED = "convergence_checked"
STABILITY_UNCHECKABLE = "not_checkable_at_this_sample"

TIER_HIGH = "high"
TIER_MEDIUM = "medium"
TIER_LOW = "low"

TIER_MEANING = {
    TIER_HIGH: (
        "Validated on the earlier starts at 75% precision or better, beating this "
        "pitch's own base rate by a margin larger than sampling noise, AND backed "
        "by a convergence curve on a deep sample. Actionable."
    ),
    TIER_MEDIUM: (
        "Validated at 50-75% precision and still beating its base rate by a "
        "significant margin — or clearing 75% but on a sample too shallow to check "
        "for stability. A genuine edge on a subset of pitches, not a call you "
        "would make every time."
    ),
    TIER_LOW: (
        "A difference measured on the 3 most recent starts that did NOT hold up "
        "on the previous 6. A high-variance spot worth checking on your own film "
        "— a lead, explicitly not a finding."
    ),
}


def base_rate(val_df, cue_type: str, a: str, b: str) -> float:
    """Prevalence of the predicted type among the validation pitches in scope.

    For a pair contrast the scope is the two types; for a versus-rest contrast it
    is every pitch. Either way this is what "always guess this type" would score,
    which is the number a tip has to beat to be worth anything.
    """
    if val_df is None or len(val_df) == 0:
        return float("nan")
    pt = val_df["pitch_type"].astype(str)
    scope = pt if b == "REST" else pt[pt.isin([a, b])]
    if len(scope) == 0:
        return float("nan")
    return float((scope == cue_type).mean())


def lift_significance(tp: int, n_fire: int, base: float) -> float:
    """One-sided p for "the hits among the fires beat the base rate".

    Without this a rule that fires four times and is right three times reads as
    0.75 precision and would be labelled HIGH.
    """
    if not np.isfinite(base) or n_fire <= 0 or not (0.0 < base < 1.0):
        return float("nan")
    return float(stats.binomtest(int(tp), int(n_fire), base, alternative="greater").pvalue)


def assess(
    feature: str,
    precision: float,
    tp: int,
    n_fire: int,
    base: float,
    validated: bool,
    n_games_available: int = 0,
) -> dict[str, Any]:
    """Tier one candidate, with every number the label rests on.

    ``validated`` is whether it replicated in direction and significance on the
    earlier starts. An unvalidated difference is LOW regardless of how good its
    discovery numbers looked — that is the point of the tier.

    ``n_games_available`` is the arm's total banked starts, not the nine analysed.
    It decides whether stability was checkable, which caps the tier: see
    ``MIN_GAMES_FOR_CONVERGENCE``.
    """
    out: dict[str, Any] = {
        "feature": feature,
        "precision": precision,
        "base_rate": base,
        "lift": (precision - base) if np.isfinite(precision) and np.isfinite(base) else float("nan"),
        "n_fire": int(n_fire),
        "tp": int(tp),
        "validated": bool(validated),
        "n_games_available": int(n_games_available),
        "stability": (STABILITY_CHECKED if n_games_available >= MIN_GAMES_FOR_CONVERGENCE
                      else STABILITY_UNCHECKABLE),
        "tier": None,
        "excluded": None,
    }

    reason = retraction_reason(feature)
    if reason:
        # Checked before anything statistical, and before the unvalidated->LOW
        # path: a retracted cue must not be reachable by passing a numeric gate,
        # and must not be demotable into LOW either.
        out["excluded"] = "retracted_measurement"
        out["reason"] = reason
        return out

    if not validated:
        out["tier"] = TIER_LOW
        out["reason"] = "difference at discovery did not validate on the earlier starts"
        return out

    p_lift = lift_significance(tp, n_fire, base)
    out["p_lift"] = p_lift
    fails = []
    if not np.isfinite(precision):
        fails.append("no precision estimate")
    if out["lift"] < MIN_LIFT or not np.isfinite(out["lift"]):
        fails.append(f"lift {out['lift']:.3f} below {MIN_LIFT}")
    if not np.isfinite(p_lift) or p_lift >= LIFT_ALPHA:
        fails.append(f"lift not significant (p={p_lift:.3f})")
    if n_fire < MIN_FIRES:
        fails.append(f"fires only {n_fire} times, under {MIN_FIRES}")

    if fails:
        # Validated but the edge is not real or not usable. It stays visible as a
        # lead rather than being hidden, but it cannot carry a confidence label.
        out["tier"] = TIER_LOW
        out["reason"] = "validated, but " + "; ".join(fails)
        return out

    if precision < MEDIUM_PRECISION:
        out["tier"] = TIER_LOW
        out["reason"] = f"precision {precision:.3f} below {MEDIUM_PRECISION}"
        return out

    out["tier"] = TIER_HIGH if precision >= HIGH_PRECISION else TIER_MEDIUM
    out["reason"] = (
        f"precision {precision:.3f} vs base rate {base:.3f} "
        f"(lift {out['lift']:+.3f}, p={p_lift:.4f}) on {n_fire} fires"
    )

    if out["tier"] == TIER_HIGH and out["stability"] == STABILITY_UNCHECKABLE:
        # Precision says HIGH; the sample cannot support the stability check that
        # HIGH claims. Capped rather than dropped, with the reason carried on the
        # tip so a club sees why, and flagged as worth deepening this one arm.
        out["tier"] = TIER_MEDIUM
        out["capped_from_high"] = True
        out["warrants_deepening"] = True
        out["reason"] += (
            f"; capped from HIGH — only {n_games_available} starts banked, so no "
            f"convergence curve (needs {MIN_GAMES_FOR_CONVERGENCE})"
        )
    else:
        out["warrants_deepening"] = out["stability"] == STABILITY_UNCHECKABLE
    return out


def summarise(assessed: list[dict]) -> dict[str, int]:
    counts = {TIER_HIGH: 0, TIER_MEDIUM: 0, TIER_LOW: 0, "excluded": 0}
    for a in assessed:
        if a.get("excluded"):
            counts["excluded"] += 1
        elif a.get("tier"):
            counts[a["tier"]] += 1
    counts["at_or_above_50"] = counts[TIER_HIGH] + counts[TIER_MEDIUM]
    return counts
