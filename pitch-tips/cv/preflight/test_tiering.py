"""
Tests for the confidence tiers.

The tier label is the entire product now, so these tests are written around the
cases the project has actually been burned by rather than around abstract limits.
Every "naive rule" case below is a real measured result whose raw precision would
have earned a confidence label under a precision-only rule.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from preflight import tiering


DEEP = 25   # Kelly: enough starts to compute a convergence curve
CAPPED = 9  # a capped arm: nine starts, no curve possible


def tier(precision, tp, n_fire, base, validated=True, games=DEEP):
    return tiering.assess("glove_speed_cv", precision, tp, n_fire, base, validated,
                          n_games_available=games)


# --------------------------------------------------------------- the real cases
# Each is measured, and each would be labelled by a precision-only rule.

def test_rodriguez_glove_speed_cv_is_not_high_despite_88_percent_precision():
    """precision 0.884 on an 0.810 base rate. Accuracy 0.583 vs 0.810 majority.

    A precision-only rule calls this HIGH. It is worse than always guessing FF.
    """
    t = tier(0.884, 38, 43, 0.810)
    assert t["tier"] == tiering.TIER_LOW
    assert t["lift"] == pytest.approx(0.074, abs=1e-3)


def test_rodriguez_knee_rise_is_not_high_because_its_lift_is_not_significant():
    """precision 0.775 on an 0.662 base rate over 40 fires.

    Lift of +0.113 clears the absolute floor, so this one is caught only by the
    binomial test: 40 fires is not enough to establish an 11-point edge.
    """
    t = tier(0.775, 31, 40, 0.662)
    assert t["tier"] == tiering.TIER_LOW
    assert t["lift"] >= tiering.MIN_LIFT
    assert t["p_lift"] > tiering.LIFT_ALPHA


def test_kellys_coin_flip_is_not_medium():
    """precision 0.529 on a 0.500 base rate. The canonical naive-rule failure."""
    assert tier(0.529, 27, 51, 0.500)["tier"] == tiering.TIER_LOW


def test_a_rare_pitch_at_its_own_base_rate_has_no_lift():
    """E. Rodríguez stance_width: 0.143 precision, 0.142 base rate."""
    t = tier(0.143, 10, 70, 0.142)
    assert t["lift"] < 0.01
    assert t["tier"] == tiering.TIER_LOW


# ------------------------------------------------------- stability / convergence

def test_high_precision_on_a_capped_arm_is_capped_to_medium():
    """The sample cannot support the stability check that HIGH claims.

    Kelly's artifact was still climbing at 11 games and did not turn over until
    past 18, so a nine-start arm cannot distinguish a real cue from that curve.
    """
    t = tier(0.86, 43, 50, 0.40, games=CAPPED)
    assert t["tier"] == tiering.TIER_MEDIUM
    assert t["capped_from_high"] is True
    assert t["stability"] == tiering.STABILITY_UNCHECKABLE
    assert "capped from HIGH" in t["reason"]


def test_high_stands_on_an_arm_deep_enough_to_check():
    t = tier(0.86, 43, 50, 0.40, games=DEEP)
    assert t["tier"] == tiering.TIER_HIGH
    assert t["stability"] == tiering.STABILITY_CHECKED
    assert not t.get("capped_from_high")


def test_twelve_games_is_still_not_enough_to_check_stability():
    """Webb has twelve. At eleven Kelly's artifact read g=0.429 and rising."""
    assert tier(0.86, 43, 50, 0.40, games=12)["capped_from_high"] is True


def test_a_capped_result_is_flagged_for_targeted_deepening():
    """The agreed follow-up policy: deepen the one arm that would settle it."""
    assert tier(0.68, 68, 100, 0.40, games=CAPPED)["warrants_deepening"] is True
    assert tier(0.68, 68, 100, 0.40, games=DEEP)["warrants_deepening"] is False


def test_the_stability_cap_cannot_promote_anything():
    """A cue failing lift stays LOW regardless of how deep the arm is."""
    assert tier(0.884, 38, 43, 0.810, games=DEEP)["tier"] == tiering.TIER_LOW


def test_the_same_rare_pitch_hit_well_does_earn_a_tier():
    """The counterexample that makes the base-rate rule fair rather than merely strict.

    0.62 precision on a pitch thrown 14% of the time is an enormous edge, and must
    be tiered even though its raw precision is lower than the 0.884 case above.
    """
    t = tier(0.62, 62, 100, 0.142)
    assert t["tier"] == tiering.TIER_MEDIUM
    assert t["lift"] > tiering.MIN_LIFT


# ------------------------------------------------------------------- structural

def test_a_rule_that_fires_three_times_is_not_a_tip_at_any_precision():
    t = tier(1.0, 3, 3, 0.30)
    assert t["tier"] == tiering.TIER_LOW
    assert "fires only 3" in t["reason"]


def test_high_needs_precision_and_lift_together():
    t = tier(0.86, 43, 50, 0.40, games=DEEP)
    assert t["tier"] == tiering.TIER_HIGH


def test_medium_sits_between_the_precision_bounds():
    t = tier(0.68, 68, 100, 0.40)
    assert t["tier"] == tiering.TIER_MEDIUM


def test_an_unvalidated_difference_is_low_however_good_it_looked():
    t = tier(0.95, 95, 100, 0.20, validated=False)
    assert t["tier"] == tiering.TIER_LOW
    assert "did not validate" in t["reason"]


def test_a_retracted_cue_cannot_reach_any_tier():
    """A wrong measurement is not a low-confidence finding.

    Demoting one into LOW would launder it back onto the board, so the retraction
    check runs before anything statistical and returns no tier at all.
    """
    for cue in ("pitchcom_tap_count", "cheek_motion_mean", "glove_angle_at_lift",
                "catcher_glove_x_mean", "glove_angle_at_set"):
        t = tiering.assess(cue, 0.99, 99, 100, 0.10, validated=True)
        assert t["tier"] is None
        assert t["excluded"] == "retracted_measurement"


def test_a_newly_added_cue_in_a_retracted_family_is_also_blocked():
    """The families were retracted for reasons that apply to the whole instrument.

    A cue added later inherits the defect, so matching only the listed names would
    leave the board one forgotten registry entry away from republishing PitchCom.
    """
    for cue in ("pitchcom_burst_len", "catcher_shin_angle", "cheek_motion_p90"):
        assert tiering.assess(cue, 0.99, 99, 100, 0.1, True)["excluded"] == "retracted_measurement"


def test_a_retracted_cue_is_also_excluded_when_unvalidated():
    t = tiering.assess("catcher_glove_speed_p90", 0.9, 9, 10, 0.1, validated=False)
    assert t["tier"] is None, "retraction must beat the unvalidated->LOW path"


def test_summarise_counts_the_number_the_user_asked_for():
    rows = [tier(0.86, 43, 50, 0.40, games=DEEP), tier(0.68, 68, 100, 0.40),
            tier(0.529, 27, 51, 0.5), tiering.assess("pitchcom_tap_rate", 0.9, 9, 10, 0.1, True)]
    c = tiering.summarise(rows)
    assert (c["high"], c["medium"], c["low"], c["excluded"]) == (1, 1, 1, 1)
    assert c["at_or_above_50"] == 2


# ------------------------------------------------------------------- base rates

def _df(types):
    return pd.DataFrame({"pitch_type": types})


def test_base_rate_of_a_pair_contrast_ignores_other_pitches():
    df = _df(["FF"] * 8 + ["SI"] * 2 + ["CH"] * 90)
    assert tiering.base_rate(df, "FF", "FF", "SI") == pytest.approx(0.8)


def test_base_rate_of_a_versus_rest_contrast_uses_every_pitch():
    df = _df(["FF"] * 10 + ["SI"] * 90)
    assert tiering.base_rate(df, "FF", "FF", "REST") == pytest.approx(0.10)


def test_base_rate_is_nan_on_an_empty_scope_rather_than_zero():
    assert np.isnan(tiering.base_rate(_df([]), "FF", "FF", "SI"))
    assert np.isnan(tiering.base_rate(_df(["CH"] * 5), "FF", "FF", "SI"))


def test_a_nan_base_rate_cannot_produce_a_tier():
    """A missing base rate must fail closed, not default to beating zero."""
    assert tier(0.99, 99, 100, float("nan"))["tier"] == tiering.TIER_LOW


def test_lift_significance_scales_with_fire_count():
    """Same 20-point lift, more fires -> more evidence. Sanity on the direction."""
    few = tiering.lift_significance(6, 10, 0.40)
    many = tiering.lift_significance(60, 100, 0.40)
    assert many < few
