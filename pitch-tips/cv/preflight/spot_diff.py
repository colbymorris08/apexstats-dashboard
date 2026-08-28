"""
Preflight — unified "spot the difference" tip detection.

A scout does not evaluate one cue at a time. Watching the same arm throw a
fastball and a slider, they take in glove height, glove flare, how far the
glove sits off the body, posture, PitchCom taps, hand visibility — all of it at
once — and call out whatever looks different. This stage does the same thing:
it takes EVERY cue available for a pitcher and tests EVERY cue against EVERY
meaningful pitch-type contrast.

Doing that honestly is the hard part. Fifteen-plus cues across a dozen
contrasts is 100+ simultaneous tests, and at any fixed threshold a handful will
look significant purely by chance. That failure mode is exactly how a board
ends up advertising 32 tips when 6 are real. Three defenses, all mandatory:

1. Holdout on GAMES. Cues are split by game, never by pitch, because pitches
   within a game share camera, park, lighting, and the pitcher's day — a
   pitch-level split leaks all of that across the boundary and makes noise
   replicate. A chance difference will not survive a fresh game; a real tip
   will. This is the primary defense.
2. Benjamini-Hochberg FDR across the full family of discovery tests, so the
   expected proportion of false discoveries among reported tips is a stated
   number rather than an unknown one.
3. A practical-significance floor. A difference can be real and still useless:
   a baserunner at second cannot see two hundredths of a torso length. Cues
   must clear a visibility floor in their own units as well as a standardized
   effect-size floor.

Only cues computed inside the actionable window (coming set / set / leg kick
through hand break) are eligible — that constraint is enforced upstream in
``window.py``, which both feature builders go through, so anything from the
delivery never reaches this module regardless of how significant it looks.

Delivery type is a hard stratification boundary
-----------------------------------------------
Stretch and windup are different deliveries, not different looks. Between them
essentially every geometric cue moves — glove height, flare, how long the set
lasts, how much the hands travel — because the pitcher is doing a mechanically
different thing. Pitchers also throw different mixes from the two: more
breaking balls with runners aboard is the norm, not the exception. Pool the two
and a fastball-versus-slider test is partly a windup-versus-stretch test, so the
stretch's mechanical signature gets reported as a tip. That is a phantom-tip
generator, not an edge case, so it is closed structurally: contrasts are built
inside one delivery stratum at a time and ``_groups`` refuses a frame carrying
more than one delivery type. Nothing in this module can run a cross-delivery
comparison by accident.

The cost is real and is reported rather than hidden: splitting an arm's pitches
in two roughly halves both sides of every contrast, and for most arms one
stratum will fall under the testable minimum. Those strata are reported as
UNDERPOWERED. An untestable stratum is not evidence that a pitcher is clean
there; it is evidence we have not looked.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from preflight import snapshot

# Expected proportion of reported differences that are false discoveries.
# 0.10 is the usual screening choice: at six surviving tips it means we expect
# well under one of them to be noise, which is a statement an analyst can check.
FDR_Q = 0.10
# Holdout is a directional confirmation of an already-chosen hypothesis, so it
# is one-sided at the conventional alpha.
HOLDOUT_ALPHA = 0.05
# Standardized effect floor (Hedges' g). Below ~0.35 the two pitch types'
# distributions overlap so heavily that no observer watching pitch by pitch
# could sort them, whatever the p-value says.
MIN_G_DISCOVERY = 0.35
MIN_G_HOLDOUT = 0.20
# Pitches per pitch type per split needed before a contrast is worth testing.
MIN_PER_GROUP = 8
# Fraction of pitches aimed at the discovery split; the rest are held out.
DISCOVERY_FRACTION = 0.6

# Per-pitch delivery label, preferred source first.
#
# ``delivery_type`` comes out of window.actionable_window, which labels a pitch
# "stretch" when it finds a sustained quiet glove before hand break and "windup"
# when it does not.
#
# CORRECTED: this is NOT a delivery label, and it was wrong to describe it as one.
# It is a set-DETECTION flag, and "windup" means the detector failed. Two pieces of
# evidence:
#
#   1. Mechanically, ``_find_set_before`` returns None when the pre-break segment
#      is too short, has no finite speed values, or contains no sustained quiet
#      run. It never tests whether the pitcher used a windup. A genuine windup also
#      contains a still point before it starts, so a real windup is usually
#      labelled "stretch".
#   2. Empirically, the "windup" share is invariant to base state, which is
#      impossible if it tracked delivery. Kelly: 0.200 with the bases empty,
#      0.202 with a runner on second. Webb: 0.222 and 0.249. No pitcher uses a
#      windup a fifth of the time with a runner on second.
#
# Stratifying on it is still worth doing, because the two labels do carry different
# window geometry — set-anchored versus a fixed 45-frame lookback — and comparing
# across them would compare features measured over different spans. So the gate
# did real protective work and no prior result is invalidated by this. But it is a
# window-geometry stratification, not a delivery stratification, and NO
# windup-versus-stretch claim can rest on it.
#
# ``delivery`` is the older label, inferred from the base state on the
# assumption that runners mean the stretch. That assumption is wrong often
# enough to matter — plenty of arms work exclusively from the stretch with the
# bases empty, and some use a windup with a runner on third — so it is only a
# fallback, and which source was used is recorded in the result.
DELIVERY_COLS = ("delivery_type", "delivery")
# Delivery strata that represent an actual delivery. Anything else (blank,
# "unknown", a track whose window could not classify it) is held out of testing
# and counted separately rather than being dropped quietly or folded into one
# of the real strata.
KNOWN_DELIVERIES = ("stretch", "windup")


@dataclass(frozen=True)
class Cue:
    """One observable cue, with what it takes for a human to actually see it."""

    label: str  # plain scouting name
    unit: str
    # Smallest change a runner/hitter could pick up live, in the cue's own unit.
    #
    # This is only meaningful for cues carried in a physical unit. Torso-
    # normalised distances get 0.05 torso lengths, which is about 1.5 inches of
    # glove on a six-foot pitcher — roughly the floor of what is callable from
    # second base on a broadcast-quality look. Angles get a few degrees, and tap
    # counts get most of a tap, since you cannot see a fraction of one.
    #
    # ``None`` means the cue lives in normalised image units, which depend on
    # camera zoom and park and therefore have no fixed real-world size. Putting
    # a hand-picked raw floor on those would be a threshold invented to taste,
    # so their practical-significance test is carried entirely by the
    # standardized effect floor (how far apart the two pitch types sit relative
    # to this pitcher's own pitch-to-pitch spread), which is scale-free.
    visible_delta: float | None
    # How readable the cue is from the field at all, 0-1. Glove position is
    # plainly visible; facial motion needs a face-on angle and is close to
    # unusable from second base; landmark-confidence proxies are indirect.
    visibility: float
    # Direction words: (what a HIGH value looks like, what a LOW value looks like)
    high: str
    low: str


# The cues DISCOVERY is allowed to test. This is deliberately narrower than the
# set the pipeline can compute: primitives.py banks every primitive because a NaN
# column is free and informative, but entering this dict spends FDR budget, and
# BH-FDR at q=0.10 is a family-wide bar. A marginal cue does not just fail on its
# own — it raises the threshold every other cue has to clear. So a cue is admitted
# only if it clears three gates:
#
#   1. PRIMITIVE_STATUS is "validated" — recoverable signal above the visibility
#      floor and adequate coverage. test_only_validated_primitives_reach_discovery
#      enforces this, and it is what keeps a retracted or underpowered cue from
#      being wired back in by hand.
#   2. Its measured noise clears its own visibility threshold, as the standard
#      error of a group mean rather than as a per-pitch spread. Numbers per cue
#      are in PRIMITIVE_STATUS; the method is in cv/preflight/cue_audit.py.
#   3. The scouting documents actually describe it. Cues invented because they
#      were computable are excluded, listed at the bottom with the reason.
#
# Removed by the cue audit (was 26 cues, now 20):
#   glove_angle_at_lift, glove_angle_at_set  retracted, arctangent saturates from
#                                            CF; superseded by the vertical
#                                            component. See provenance.
#   cheek_motion_mean/std                    retracted, pose-nose fallback.
#   pitchcom_tap_count/rate/mean_isi         retracted, not an event detector.
#   glove_drift_pre_lift, glove_drift_dy     underpowered: real signal, but the
#                                            group-mean error (0.068, 0.055
#                                            torso) does not clear the 0.05
#                                            visibility threshold at n=50.
#   glove_vs_belt_mean, glove_flare_mean     superseded duplicates: the same
#                                            physical quantities, un-normalised
#                                            and in zoom-dependent image units,
#                                            of glove_height_at_lift and
#                                            glove_flare_at_lift.
#   glove_vs_belt_std, glove_flare_std       no documentary basis (no scouting
#                                            note describes glove steadiness) and
#                                            the weakest measurements in the set:
#                                            noise/signal 1.29 and 0.86, so most
#                                            or half of what they report is
#                                            tracker jitter.
#
# Computable, validated, and deliberately NOT wired, because nothing in the
# documents asks for them — the sway family is also excluded, on coverage:
#   torso_foreshorten_at_set, foreshorten_change_set_to_lift
#       torso foreshortening is a projection artefact, not a cue a scout reads.
#       Tip 11 (lean/weight) is marked in docs/tip_taxonomy.md as "not in the
#       documents", so a foreshortening proxy for it is doubly speculative.
#   lean_change_set_to_lift
#       a derived change on the same undocumented tip 11.
#   sway_amplitude, sway_dx, sway_dy, sway_directness, come_set_peak_speed
#       tip 12 is likewise "not in the documents", AND coverage re-measured on
#       tonight's tracks is 27.0-27.6%, lower than the 32% recorded earlier. The
#       longer pre-set clips have not landed for these arms yet. Re-check before
#       wiring; do not wire on the expectation.
#   shoulder_tilt_at_set
#       resolution_limited: 50% coverage and 13.6 degrees of induced noise.
CUES: dict[str, Cue] = {
    # -- lift-anchored primitives (torso-normalised, scout vocabulary) --------
    "glove_height_at_lift": Cue("glove height at leg lift", "torso lengths", 0.05, 1.00, "carries the glove higher", "carries the glove lower"),
    "glove_height_at_set": Cue("glove height at set", "torso lengths", 0.05, 1.00, "sets up with the glove higher", "sets up with the glove lower"),
    "glove_rise_set_to_lift": Cue("glove rise from set to lift", "torso lengths", 0.05, 0.85, "lifts the glove more on the way up", "keeps the glove flatter on the way up"),
    "glove_off_body_at_lift": Cue("glove distance off the body at lift", "torso lengths", 0.05, 0.95, "holds the glove further off the chest", "tucks the glove tighter to the chest"),
    "glove_off_body_at_set": Cue("glove distance off the body at set", "torso lengths", 0.05, 0.95, "sets with the glove further off the chest", "sets with the glove tucked tighter"),
    "glove_flare_at_lift": Cue("glove flare at lift", "torso lengths", 0.05, 0.90, "flares the glove wider off the midline", "keeps the glove in tighter to the midline"),
    "glove_drift_dx": Cue("sideways glove drift into lift", "torso lengths", 0.05, 0.70, "drifts the glove toward the arm side", "drifts the glove toward the glove side"),
    "drift_lift_sync": Cue("glove moving in time with the leg kick", "correlation", 0.25, 0.55, "moves the glove in sync with the knee", "moves the glove independently of the knee"),
    # Replaces the retracted glove_angle_at_lift. This is the vertical component
    # of the forearm only — the part CF can resolve — so it carries the standard
    # 0.05-torso distance threshold instead of the angle's unusable 8 degrees.
    # It keeps the MAGNITUDE of the tilt and loses its direction, so it cannot
    # separate "angled up" from "cocked in"; that needs the second-base look.
    "glove_rise_above_elbow_at_lift": Cue("how far the glove sits above the elbow at lift", "torso lengths", 0.05, 0.75, "presents the glove higher above the elbow", "presents the glove level with the elbow"),
    "posture_lean_at_lift": Cue("posture lean at lift", "degrees", 4.0, 0.70, "leans back further at lift", "stays more over the rubber"),
    "posture_upright_at_lift": Cue("how tall he stands at lift", "torso lengths", 0.05, 0.60, "stands taller at lift", "stays more collapsed at lift"),
    "hand_gap_at_lift": Cue("how deep the hand is in the glove at lift", "torso lengths", 0.04, 0.85, "carries the hand further out of the glove", "buries the hand deeper in the glove"),
    "hand_vis_at_lift": Cue("how much of the throwing hand shows at lift", "visibility 0-1", 0.08, 0.85, "shows more of the hand/grip", "keeps the grip hidden in the glove"),
    # -- set position and posture -------------------------------------------
    # Tip 8 ("various notes centered around his set position") and tip 10
    # ("more upright on the SL", "STRAIGHTER POSTURE") in docs/tip_taxonomy.md.
    # These sit EARLIER in the delivery than the lift, so a read on them reaches
    # a hitter with more time than a lift-anchored one.
    "stance_width_at_set": Cue("how wide he sets his feet", "torso lengths", 0.05, 0.80, "sets with a wider base", "sets with the feet closer together"),
    "knee_flex_at_set": Cue("how deep he sits in the set", "torso lengths", 0.05, 0.75, "sits deeper in the set", "stands straighter in the set"),
    "posture_lean_at_set": Cue("how upright he stands at the set", "degrees", 4.0, 0.75, "stands straighter at the set", "leans over more at the set"),
    # Tip 21, "MORE FOREARM VISIBLE TO COACH". The document's own phrasing names
    # a base coach, i.e. a side angle, so treat a CF read on this as weaker than
    # the glove family even though the measurement itself validates.
    "forearm_exposure_at_set": Cue("how much forearm shows at the set", "torso lengths", 0.05, 0.60, "shows more forearm at the set", "keeps the forearm covered at the set"),
    "forearm_exposure_at_lift": Cue("how much forearm shows at lift", "torso lengths", 0.05, 0.60, "shows more forearm at lift", "keeps the forearm covered at lift"),
    # -- window features (whole actionable window, normalised image units) ----
    # Only the micro-motion pair survives the audit. It is the one legacy window
    # measurement with a documentary basis — tip 7, "2 SQUEEZES + MORE FLAIR" —
    # and the one with no torso-normalised replacement, since none of the
    # primitives measure fidget. It stays in zoom-dependent image units, so its
    # practical-significance test is carried entirely by the standardized effect
    # floor, as the visible_delta docstring describes.
    "wrist_speed_mean": Cue("glove/hand micro-motion at set", "image units/frame", None, 0.70, "fidgets more in the set", "sits quieter in the set"),
    "wrist_speed_p90": Cue("late glove twitch before separation", "image units/frame", None, 0.65, "shows a sharper late twitch", "shows a flatter late twitch"),
}

PITCH_NAMES = {
    "FF": "four-seam", "FA": "fastball", "SI": "sinker", "FT": "two-seam",
    "FC": "cutter", "SL": "slider", "ST": "sweeper", "SV": "slurve",
    "CU": "curveball", "KC": "knuckle-curve", "CH": "changeup", "FS": "splitter",
    "FO": "forkball", "EP": "eephus", "KN": "knuckleball",
}


def pitch_name(code: str) -> str:
    return PITCH_NAMES.get(code, code)


@dataclass
class Difference:
    feature: str
    cue: str
    delivery: str  # stratum this contrast was measured inside
    contrast: str
    pitch_a: str
    pitch_b: str
    direction: str  # "a_higher" | "b_higher"
    n_discovery: int
    n_holdout: int
    mean_a: float
    mean_b: float
    delta: float  # mean_a - mean_b on the holdout, cue's own units
    unit: str
    g_discovery: float
    g_holdout: float
    p_discovery: float
    q_discovery: float
    p_holdout: float
    visibility: float
    utility: float
    scouting_note: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def hedges_g(a: np.ndarray, b: np.ndarray) -> float:
    """Standardized mean difference, small-sample corrected."""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan")
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    pooled = ((na - 1) * va + (nb - 1) * vb) / (na + nb - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    d = (np.mean(a) - np.mean(b)) / np.sqrt(pooled)
    correction = 1.0 - 3.0 / (4.0 * (na + nb) - 9.0)
    return float(d * correction)


def benjamini_hochberg(pvals: list[float], q: float) -> tuple[list[float], float | None]:
    """
    BH-adjusted p-values (q-values) and the largest p still called significant.

    Controls the expected share of false discoveries among the rejections at
    ``q``, which is the honest thing to report when the whole point of the
    stage is to run every test at once.
    """
    m = len(pvals)
    if m == 0:
        return [], None
    order = np.argsort(pvals)
    ranked = np.asarray(pvals, dtype=float)[order]
    adj = ranked * m / (np.arange(1, m + 1))
    adj = np.minimum.accumulate(adj[::-1])[::-1]  # enforce monotonicity
    adj = np.clip(adj, 0.0, 1.0)
    out = np.empty(m)
    out[order] = adj
    passing = ranked[adj <= q]
    return out.tolist(), (float(passing[-1]) if passing.size else None)


def split_by_game(df: pd.DataFrame, fraction: float = DISCOVERY_FRACTION) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Partition pitches into discovery/holdout at the GAME boundary.

    Pitches inside one game share camera angle, park, lighting and the
    pitcher's condition that day. Splitting on pitches would let all of that
    cross the boundary, and a difference driven by a camera angle would
    "replicate" out of sample. Splitting on games makes replication mean what
    we need it to mean.

    Games are assigned largest-first to whichever side is furthest below its
    target share, which keeps the split near ``fraction`` without randomness.
    """
    if "game_pk" not in df.columns:
        raise ValueError("cannot split without game_pk")
    sizes = df["game_pk"].value_counts()
    total = int(sizes.sum())
    disc: list[Any] = []
    hold: list[Any] = []
    n_disc = n_hold = 0
    for game, n in sizes.items():
        want_disc = (n_disc + n_hold + n) * fraction
        if n_disc < want_disc:
            disc.append(game)
            n_disc += int(n)
        else:
            hold.append(game)
            n_hold += int(n)
    if not hold and len(sizes) > 1:  # never let the holdout vanish
        hold.append(disc.pop())
    return df[df["game_pk"].isin(disc)], df[df["game_pk"].isin(hold)]


def _contrasts(df: pd.DataFrame, types: list[str]) -> list[tuple[str, str, str]]:
    """Every meaningful pitch-type contrast: each pair, then each type vs rest."""
    out = [(a, b, "pair") for a, b in combinations(types, 2)]
    if len(types) > 2:
        out += [(t, "REST", "one_vs_rest") for t in types]
    return out


def delivery_source(df: pd.DataFrame) -> str | None:
    """Which delivery label this table carries, preferring the track-read one."""
    for col in DELIVERY_COLS:
        if col in df.columns and df[col].astype(str).str.lower().isin(KNOWN_DELIVERIES).any():
            return col
    return None


def _delivery_series(df: pd.DataFrame) -> pd.Series:
    col = delivery_source(df)
    if col is None:
        return pd.Series(["unlabelled"] * len(df), index=df.index)
    s = df[col].astype(str).str.lower().str.strip()
    return s.where(s.isin(KNOWN_DELIVERIES), "unlabelled")


def _assert_single_delivery(df: pd.DataFrame) -> None:
    """
    Refuse to compare pitches thrown from different deliveries.

    This is the structural half of the stratification rule. Every path that
    reaches a t-test goes through ``_groups``, so a caller that forgets to
    stratify gets an exception here instead of a plausible-looking phantom tip.
    """
    if df.empty:
        return
    kinds = set(_delivery_series(df).unique())
    if len(kinds) > 1:
        raise ValueError(
            "cross-delivery comparison attempted on a frame containing "
            f"{sorted(kinds)}; contrasts must be built inside one delivery stratum"
        )


def _groups(df: pd.DataFrame, col: str, a: str, b: str) -> tuple[np.ndarray, np.ndarray]:
    _assert_single_delivery(df)
    va = pd.to_numeric(df.loc[df["pitch_type"] == a, col], errors="coerce").dropna().to_numpy()
    if b == "REST":
        vb = pd.to_numeric(df.loc[df["pitch_type"] != a, col], errors="coerce").dropna().to_numpy()
    else:
        vb = pd.to_numeric(df.loc[df["pitch_type"] == b, col], errors="coerce").dropna().to_numpy()
    return va, vb


def _utility(cue: Cue, g_holdout: float, p_holdout: float) -> float:
    """
    Rank by scouting usefulness, not by p-value.

    A cue is useful when a person can see it (visibility), when the gap is big
    enough to call in real time (effect size), and when it showed up again in
    games the model never saw (replication). p-value alone would put an
    invisible facial-motion cue above a plainly visible glove-height cue.
    """
    size = min(abs(g_holdout) / 1.0, 1.0)
    replication = min(max(0.0, (HOLDOUT_ALPHA - p_holdout) / HOLDOUT_ALPHA), 1.0)
    return round(0.45 * cue.visibility + 0.35 * size + 0.20 * replication, 4)


def _side(code: str) -> str:
    """How to name one side of a contrast in a sentence a scout would say."""
    return "everything else he throws" if code == "REST" else f"the {pitch_name(code)}"


def _note(cue: Cue, higher: str, lower: str, delta: float) -> str:
    """One sentence a scout can act on: which cue, which pitch, which way."""
    return (
        f"{cue.label}: on {_side(higher)} he {cue.high}; on {_side(lower)} he "
        f"{cue.low}. About {abs(delta):.3g} {cue.unit} of separation."
    )


def load_pitcher(run_dir: Path, features_name: str = "features.csv") -> pd.DataFrame:
    """
    Assemble every cue available for one arm into a single pitch-level table.

    Window features and lift-anchored primitives are produced by separate
    passes over different tracks; both are keyed on play_id, so a pitch carries
    whichever cues exist for it. game_pk lives only on the feature table and is
    joined onto the primitives so the split can happen at the game boundary.
    """
    feats_path = run_dir / features_name
    prim_path = run_dir / "primitives.csv"
    frames: list[pd.DataFrame] = []
    if feats_path.is_file():
        frames.append(pd.read_csv(feats_path, dtype={"play_id": str}))
    if prim_path.is_file():
        prim = pd.read_csv(prim_path, dtype={"play_id": str})
        prim = prim.drop(columns=[c for c in ("pitch_type", "balls", "strikes", "runner_bucket", "batter_tag", "delivery") if c in prim.columns])
        # A join that matches nothing must be an error, not a quiet degradation.
        #
        # These two tables are keyed on play_id and merged with how="outer", so a
        # key mismatch does not raise — it doubles the row count and produces two
        # disjoint halves, one with pitch types and no primitives, one with
        # primitives and no pitch type. Discovery then reports the full cue list
        # as "available" (the columns are all present) while every contrast that
        # needs a primitive silently finds an empty group. That is exactly what
        # happened when the tracker changed its filenames: 0 of 358 play_ids
        # matched on Webb, and the run completed normally reporting 20 cues and
        # 36 comparisons instead of the ~200 it should have performed.
        if frames and not prim.empty:
            overlap = len(set(frames[0]["play_id"]) & set(prim["play_id"]))
            if overlap < 0.5 * min(len(frames[0]), len(prim)):
                raise SystemExit(
                    f"{run_dir.name}: primitives.csv and {features_name} share only "
                    f"{overlap} play_ids ({len(prim)} primitives, {len(frames[0])} "
                    "features). The join key is broken — rebuild primitives.csv "
                    "rather than running discovery on a half-empty frame."
                )
        frames.append(prim)
    if not frames:
        return pd.DataFrame()
    df = frames[0]
    for extra in frames[1:]:
        df = df.merge(extra, on="play_id", how="outer", suffixes=("", "_dup"))
    return df


def _stratum_report(stratum: str, df: pd.DataFrame, disc: pd.DataFrame, hold: pd.DataFrame, types: list[str]) -> dict[str, Any]:
    """
    What this delivery stratum could support, before any test was run.

    Recorded whether or not the stratum is testable, because "we could not look
    here" and "we looked and found nothing" are different findings and must not
    be allowed to read the same in a summary.
    """
    return {
        "delivery": stratum,
        "n_pitches": int(len(df)),
        "n_games": int(df["game_pk"].nunique()) if "game_pk" in df.columns else 0,
        "n_discovery": int(len(disc)),
        "n_holdout": int(len(hold)),
        "pitch_counts": {str(k): int(v) for k, v in df["pitch_type"].value_counts().items()},
        "pitch_types_tested": types,
        "testable": len(types) >= 2,
        "status": "testable" if len(types) >= 2 else "underpowered",
    }


def analyse(df: pd.DataFrame, name: str) -> dict[str, Any]:
    """
    Run the full cue x contrast family for one pitcher, honestly.

    Discovery runs separately inside each delivery stratum; the FDR correction
    is applied once across every test from every stratum, because the family
    that matters for false discoveries is everything we looked at for this arm.
    """
    result: dict[str, Any] = {
        "pitcher": name,
        "fdr_q": FDR_Q,
        "n_pitches": int(len(df)),
        "comparisons": 0,
        "differences": [],
        "skipped": {},
        "stratified_by": "delivery_type",
    }
    if df.empty or "pitch_type" not in df.columns:
        result["skipped"]["no_features"] = 1
        return result

    df = df[df["pitch_type"].astype(str).str.len() > 0].copy()
    df["_delivery"] = _delivery_series(df)
    src = delivery_source(df)
    result["delivery_label_source"] = src or "none"
    result["delivery_mix"] = {str(k): int(v) for k, v in df["_delivery"].value_counts().items()}
    result["n_games"] = int(df["game_pk"].nunique())

    unlabelled = int((df["_delivery"] == "unlabelled").sum())
    if unlabelled:
        # Not dropped quietly and not folded into a real stratum: a pitch whose
        # delivery we cannot name cannot be safely compared to either side.
        result["unlabelled_delivery_pitches"] = unlabelled
        result["skipped"]["unlabelled_delivery"] = unlabelled
    if src is None:
        result["skipped"]["no_delivery_label"] = 1
        result["strata"] = []
        return result

    cue_cols = [c for c in CUES if c in df.columns and pd.to_numeric(df[c], errors="coerce").notna().sum() >= 2 * MIN_PER_GROUP]
    result["cues_available"] = cue_cols

    candidates: list[dict[str, Any]] = []
    pvals: list[float] = []
    strata_reports: list[dict[str, Any]] = []
    holds: dict[str, pd.DataFrame] = {}
    n_disc_total = n_hold_total = 0

    for stratum in KNOWN_DELIVERIES:
        sdf = df[df["_delivery"] == stratum]
        if sdf.empty:
            strata_reports.append(
                {"delivery": stratum, "n_pitches": 0, "n_games": 0, "n_discovery": 0,
                 "n_holdout": 0, "pitch_counts": {}, "pitch_types_tested": [],
                 "testable": False, "status": "absent"}
            )
            continue
        if sdf["game_pk"].nunique() < 2:
            # One game cannot be split into discovery and holdout, so there is
            # nothing to replicate against here.
            strata_reports.append(
                {"delivery": stratum, "n_pitches": int(len(sdf)), "n_games": int(sdf["game_pk"].nunique()),
                 "n_discovery": 0, "n_holdout": 0,
                 "pitch_counts": {str(k): int(v) for k, v in sdf["pitch_type"].value_counts().items()},
                 "pitch_types_tested": [], "testable": False, "status": "underpowered"}
            )
            continue
        sdisc, shold = split_by_game(sdf)
        holds[stratum] = shold
        n_disc_total += len(sdisc)
        n_hold_total += len(shold)
        # A pitch type only enters if both splits can support it; otherwise there
        # is nothing to replicate against and testing it just inflates the family.
        types = sorted(
            t
            for t in sdf["pitch_type"].unique()
            if (sdisc["pitch_type"] == t).sum() >= MIN_PER_GROUP and (shold["pitch_type"] == t).sum() >= MIN_PER_GROUP
        )
        strata_reports.append(_stratum_report(stratum, sdf, sdisc, shold, types))
        if len(types) < 2:
            result["skipped"]["insufficient_pitch_types"] = result["skipped"].get("insufficient_pitch_types", 0) + 1
            continue
        for a, b, kind in _contrasts(sdf, types):
            for col in cue_cols:
                da, db = _groups(sdisc, col, a, b)
                if len(da) < MIN_PER_GROUP or len(db) < MIN_PER_GROUP:
                    result["skipped"]["thin_group"] = result["skipped"].get("thin_group", 0) + 1
                    continue
                if np.allclose(np.var(da), 0) and np.allclose(np.var(db), 0):
                    continue
                t = stats.ttest_ind(da, db, equal_var=False)
                p = float(t.pvalue)
                if not np.isfinite(p):
                    continue
                g = hedges_g(da, db)
                candidates.append(
                    {"col": col, "a": a, "b": b, "kind": kind, "p": p, "g": g, "delivery": stratum,
                     "mean_a": float(np.mean(da)), "mean_b": float(np.mean(db)), "n": len(da) + len(db),
                     # Per-group sizes, not just the total. A contrast of 14 against
                     # 98 and one of 56 against 56 both report n=112, but only the
                     # first is limited by how little of one pitch type exists, and
                     # that distinction is what says whether more film would help.
                     "n_a": int(len(da)), "n_b": int(len(db)),
                     "sd_a": float(np.std(da, ddof=1)), "sd_b": float(np.std(db, ddof=1))}
                )
                pvals.append(p)

    result["strata"] = strata_reports
    result["n_discovery"] = n_disc_total
    result["n_holdout"] = n_hold_total
    result["pitch_types_tested"] = sorted({t for s in strata_reports for t in s["pitch_types_tested"]})
    result["testable_strata"] = [s["delivery"] for s in strata_reports if s["testable"]]
    result["underpowered_strata"] = [s["delivery"] for s in strata_reports if s["status"] == "underpowered"]

    result["comparisons"] = len(candidates)
    # Raw differences before any correction. Reported because the attrition table
    # alone jumps from "how many we looked at" to "how many survived", which hides
    # how much apparent signal exists at the uncorrected stage — and that figure is
    # what makes the size of the multiple-comparison problem legible. It is a
    # reporting field only: nothing downstream reads it, and no gate uses it.
    result["n_nominal_discovery"] = int(sum(1 for c in candidates if c["p"] < 0.05))
    result["n_nominal_expected_by_chance"] = round(0.05 * len(candidates), 1)
    if not candidates:
        return result

    qvals, _ = benjamini_hochberg(pvals, FDR_Q)
    # Where candidates die matters as much as how many survive: an arm that
    # loses everything at the FDR step has no signal, while one that loses
    # everything at the replication step had signal that was game-specific.
    attrition = dict.fromkeys(
        ["fdr", "effect_size", "visibility", "thin_holdout", "direction_flip",
         "holdout_effect", "holdout_visibility", "replication"], 0
    )
    diffs: list[Difference] = []
    # Candidates that cleared the discovery hurdles but failed out of sample.
    # These are the "high variance spots" the tiered board shows as LOW: a real
    # measured difference on the discovery starts that did not hold up. Recorded
    # rather than discarded so the board can show a club what to check for itself,
    # clearly labelled as a lead rather than a finding.
    leads: list[dict[str, Any]] = []
    # Every comparison that was performed, with its physical separation and the
    # gate it died at. The lists above answer "what survived"; this answers "how
    # big was the difference", which is a different question. Reporting only
    # survivors makes a trivially small separation and a large one that ran out of
    # sample look identical — both simply absent — so it hides the one case where
    # more film would help. Nothing downstream gates on this: it sets display
    # order, never confidence. A large effect on a small sample is precisely what a
    # small sample produces, so magnitude must never promote a result.
    distribution: list[dict[str, Any]] = []
    for cand, q in zip(candidates, qvals):
        cue = CUES[cand["col"]]
        raw_delta = cand["mean_a"] - cand["mean_b"]
        # Raw deltas are not comparable across cues: the units are torso lengths,
        # frames, and unit-free ratios all at once. A cross-cue ranking needs a
        # common denominator, and each cue's own visibility floor is the physically
        # meaningful one — 1.0 means "just barely visible to a person", 3.0 means
        # "three times the size a person needs to see it".
        floors = abs(raw_delta) / cue.visible_delta if cue.visible_delta else None
        entry = {
            "col": cand["col"], "cue": cue.label, "delivery": cand["delivery"],
            "contrast": f"{cand['a']} vs {'the rest' if cand['b'] == 'REST' else cand['b']}",
            "pitch_a": cand["a"], "pitch_b": cand["b"],
            "delta": round(raw_delta, 5), "unit": cue.unit,
            "visible_delta": cue.visible_delta,
            "floor_multiples": round(floors, 2) if floors is not None else None,
            "g_discovery": round(cand["g"], 3),
            "p_discovery": float(f"{cand['p']:.3g}"),
            "q_discovery": float(f"{q:.3g}"),
            "n_discovery": cand["n"],
            "n_a": cand["n_a"], "n_b": cand["n_b"],
            "n_smaller_group": min(cand["n_a"], cand["n_b"]),
            "sd_a": round(cand["sd_a"], 5), "sd_b": round(cand["sd_b"], 5),
            "delta_holdout": None, "g_holdout": None, "n_holdout": None,
            "failed_at": None,
        }
        distribution.append(entry)
        # Three discovery hurdles: FDR-controlled significance, a standardized
        # effect a person could sort on, and a raw gap big enough to see.
        if q > FDR_Q:
            attrition["fdr"] += 1
            entry["failed_at"] = "fdr"
            continue
        if not np.isfinite(cand["g"]) or abs(cand["g"]) < MIN_G_DISCOVERY:
            attrition["effect_size"] += 1
            entry["failed_at"] = "effect_size"
            continue
        if cue.visible_delta is not None and abs(raw_delta) < cue.visible_delta:
            attrition["visibility"] += 1
            entry["failed_at"] = "visibility"
            continue

        ha, hb = _groups(holds[cand["delivery"]], cand["col"], cand["a"], cand["b"])
        if len(ha) < MIN_PER_GROUP or len(hb) < MIN_PER_GROUP:
            attrition["thin_holdout"] += 1
            entry["failed_at"] = "thin_holdout"
            leads.append({"col": cand["col"], "cue": cue.label, "delivery": cand["delivery"],
                          "contrast": f"{cand['a']} vs {'the rest' if cand['b'] == 'REST' else cand['b']}",
                          "pitch_a": cand["a"], "pitch_b": cand["b"],
                          "g_discovery": round(cand["g"], 3), "q_discovery": float(f"{q:.3g}"),
                          "n_discovery": cand["n"], "unit": cue.unit,
                          "failed_at": "thin_holdout"})
            continue
        g_hold = hedges_g(ha, hb)
        if not np.isfinite(g_hold) or np.sign(g_hold) != np.sign(cand["g"]):
            attrition["direction_flip"] += 1
            entry["failed_at"] = "direction_flip"
            leads.append({"col": cand["col"], "cue": cue.label, "delivery": cand["delivery"],
                          "contrast": f"{cand['a']} vs {'the rest' if cand['b'] == 'REST' else cand['b']}",
                          "pitch_a": cand["a"], "pitch_b": cand["b"],
                          "g_discovery": round(cand["g"], 3), "q_discovery": float(f"{q:.3g}"),
                          "n_discovery": cand["n"], "unit": cue.unit,
                          "failed_at": "direction_flip"})
            continue  # flipped direction out of sample: it was noise
        alt = "greater" if cand["g"] > 0 else "less"
        p_hold = float(stats.ttest_ind(ha, hb, equal_var=False, alternative=alt).pvalue)
        hold_delta = float(np.mean(ha) - np.mean(hb))
        entry["delta_holdout"] = round(hold_delta, 5)
        entry["g_holdout"] = round(g_hold, 3)
        entry["n_holdout"] = len(ha) + len(hb)
        if p_hold > HOLDOUT_ALPHA:
            attrition["replication"] += 1
            entry["failed_at"] = "replication"
            leads.append({"col": cand["col"], "cue": cue.label, "delivery": cand["delivery"],
                          "contrast": f"{cand['a']} vs {'the rest' if cand['b'] == 'REST' else cand['b']}",
                          "pitch_a": cand["a"], "pitch_b": cand["b"],
                          "g_discovery": round(cand["g"], 3), "q_discovery": float(f"{q:.3g}"),
                          "n_discovery": cand["n"], "unit": cue.unit,
                          "failed_at": "replication"})
            continue
        if abs(g_hold) < MIN_G_HOLDOUT:
            attrition["holdout_effect"] += 1
            entry["failed_at"] = "holdout_effect"
            leads.append({"col": cand["col"], "cue": cue.label, "delivery": cand["delivery"],
                          "contrast": f"{cand['a']} vs {'the rest' if cand['b'] == 'REST' else cand['b']}",
                          "pitch_a": cand["a"], "pitch_b": cand["b"],
                          "g_discovery": round(cand["g"], 3), "q_discovery": float(f"{q:.3g}"),
                          "n_discovery": cand["n"], "unit": cue.unit,
                          "failed_at": "holdout_effect"})
            continue
        if cue.visible_delta is not None and abs(hold_delta) < cue.visible_delta:
            attrition["holdout_visibility"] += 1
            entry["failed_at"] = "holdout_visibility"
            leads.append({"col": cand["col"], "cue": cue.label, "delivery": cand["delivery"],
                          "contrast": f"{cand['a']} vs {'the rest' if cand['b'] == 'REST' else cand['b']}",
                          "pitch_a": cand["a"], "pitch_b": cand["b"],
                          "g_discovery": round(cand["g"], 3), "q_discovery": float(f"{q:.3g}"),
                          "n_discovery": cand["n"], "unit": cue.unit,
                          "failed_at": "holdout_visibility"})
            continue

        higher, lower = (cand["a"], cand["b"]) if hold_delta > 0 else (cand["b"], cand["a"])
        diffs.append(
            Difference(
                feature=cand["col"],
                cue=cue.label,
                delivery=cand["delivery"],
                contrast=f"{cand['a']} vs {'the rest' if cand['b'] == 'REST' else cand['b']}",
                pitch_a=cand["a"],
                pitch_b=cand["b"],
                direction="a_higher" if hold_delta > 0 else "b_higher",
                n_discovery=cand["n"],
                n_holdout=len(ha) + len(hb),
                mean_a=round(float(np.mean(ha)), 5),
                mean_b=round(float(np.mean(hb)), 5),
                delta=round(hold_delta, 5),
                unit=cue.unit,
                g_discovery=round(cand["g"], 3),
                g_holdout=round(g_hold, 3),
                p_discovery=float(f"{cand['p']:.3g}"),
                q_discovery=float(f"{q:.3g}"),
                p_holdout=float(f"{p_hold:.3g}"),
                visibility=cue.visibility,
                utility=_utility(cue, g_hold, p_hold),
                scouting_note=_note(cue, higher, lower, hold_delta),
            )
        )

    diffs.sort(key=lambda d: d.utility, reverse=True)
    result["differences"] = [d.as_dict() for d in diffs]
    result["leads"] = leads
    result["distribution"] = distribution
    result["n_leads"] = len(leads)
    result["n_surviving"] = len(diffs)
    result["attrition"] = attrition
    return result


def report_text(res: dict[str, Any]) -> str:
    lines = [
        f"\n=== {res['pitcher']} ===",
        f"pitches {res['n_pitches']} | games {res.get('n_games', 0)} "
        f"(discovery {res.get('n_discovery', 0)} / holdout {res.get('n_holdout', 0)})",
        f"delivery label from: {res.get('delivery_label_source', 'none')} | mix {res.get('delivery_mix', {})}",
        f"pitch types tested: {', '.join(res.get('pitch_types_tested', [])) or 'none'}",
        f"cues available: {len(res.get('cues_available', []))}",
        f"comparisons performed: {res['comparisons']}",
        f"differences surviving holdout + BH-FDR(q={res['fdr_q']}): {res.get('n_surviving', 0)}",
    ]
    if res.get("sample"):
        lines.insert(1, snapshot.describe(res["sample"]))
        rdy = (res["sample"].get("readiness") or {}).get("ready")
        if rdy is False:
            lines.insert(2, "  WARNING: arm not ready — this result cannot publish")
    for s in res.get("strata", []):
        lines.append(
            f"  [{s['delivery']}] n={s['n_pitches']} games={s['n_games']} "
            f"(disc {s['n_discovery']} / hold {s['n_holdout']}) "
            f"types tested: {', '.join(s['pitch_types_tested']) or 'none'} -> {s['status'].upper()}"
        )
    if res.get("unlabelled_delivery_pitches"):
        lines.append(
            f"  [unlabelled delivery] n={res['unlabelled_delivery_pitches']} — held out of all "
            f"contrasts; not pooled into either stratum"
        )
    if res.get("attrition"):
        lines.append(f"candidates lost at: {res['attrition']}")
    if res.get("skipped"):
        lines.append(f"skipped: {res['skipped']}")
    for i, d in enumerate(res.get("differences", []), 1):
        lines.append(
            f"  {i}. [{d['delivery']} · {d['contrast']}] {d['scouting_note']}\n"
            f"     effect g={d['g_holdout']} (discovery {d['g_discovery']}), "
            f"holdout p={d['p_holdout']}, discovery q={d['q_discovery']}, "
            f"n_holdout={d['n_holdout']}, utility={d['utility']}"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, nargs="+")
    ap.add_argument("--features", default="features.csv", help="feature table filename inside each run dir")
    ap.add_argument("--out", default=None, help="write a combined JSON summary here")
    ap.add_argument("--json-name", default="spot_diff.json", help="per-run output filename")
    ap.add_argument(
        "--allow-unready",
        action="store_true",
        help="compute against an arm still being tracked; the result is fingerprinted "
        "as unready and will not publish",
    )
    args = ap.parse_args()

    all_res = []
    for d in args.run_dir:
        run_dir = Path(d)
        name = run_dir.name.replace("_poc", "").replace("_", " ").title()
        # Before reading anything: refuse a directory that is still being written.
        snapshot.assert_quiescent(run_dir, allow_unready=args.allow_unready)
        df = load_pitcher(run_dir, args.features)
        res = analyse(df, name)
        # Bind the result to the sample it was computed from, so that publication
        # can refuse it later if the sample has moved on.
        res["sample"] = snapshot.fingerprint(run_dir, args.features, df)
        (run_dir / args.json_name).write_text(json.dumps(res, indent=2))
        all_res.append(res)
        print(report_text(res), flush=True)

    total_tests = sum(r["comparisons"] for r in all_res)
    total_tips = sum(r.get("n_surviving", 0) for r in all_res)
    print(
        f"\nTOTAL: {total_tests} comparisons across {len(all_res)} arms -> {total_tips} "
        f"surviving differences, false-discovery rate controlled at q={FDR_Q} "
        f"(expect <= {FDR_Q * max(total_tips, 0):.1f} of them to be false)."
    )
    if args.out:
        Path(args.out).write_text(json.dumps({"arms": all_res, "fdr_q": FDR_Q, "total_comparisons": total_tests, "total_surviving": total_tips}, indent=2))


if __name__ == "__main__":
    main()
