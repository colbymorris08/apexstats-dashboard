"""
Preflight — lift-anchored tip primitives.

This module implements the vocabulary that professional pitch-tipping reports
actually use (see ``docs/apex_tipping_examples.pdf`` and
``docs/thorpe_pitch_tip_milb.pdf``). Every note in those documents is anchored
at SET or AT LIFT, never during arm action, which matches the product
constraint:

    window opens : coming set -> set -> leg kick
    window closes: the instant the bare hand leaves the glove (hand break)

The leg kick sits inside that window and is the reference event the scouts use
("at lift"), so it is detected explicitly here and most primitives are measured
in a few frames centred on it rather than averaged over the whole window. An
average over the window blurs exactly the contrast the scout is describing.

Normalisation
-------------
Raw normalised-image units are not comparable across pitchers or camera zoom:
a taller pitcher, a tighter crop, or a different park all change them. Every
distance primitive here is divided by that pitch's own torso length (shoulder
midpoint to hip midpoint, taken as a median over the window), so the unit is
"torso lengths" and is comparable across arms. Angles are in degrees and need
no scaling.

Boundary detection reuses ``window.actionable_window`` so this module inherits
any improvement made to the set/hand-break logic instead of forking it.

Set position and coming set
---------------------------
The original fifteen primitives all measure where the GLOVE sits at an anchor.
The scouting documents are wider than that: they also describe how a pitcher
sets ("various notes centred around his set position"), his posture ("more
upright on the SL", annotated STRAIGHTER POSTURE), and how much of his arm the
runner can see (annotated MORE FOREARM VISIBLE TO COACH). Those cues fall at or
before the set, which is earlier in the actionable window than the lift and
therefore further ahead of a swing decision.

Two things about them differ from the lift-anchored group:

* The coming-set cues are TRAJECTORIES. A sway has no value at an anchor; it
  has a shape. They are summarised from a smoothed pelvis path over
  ``window.preset_segment``, by excursion and by directness rather than by
  integrated path length — per-frame landmark jitter is 0.10 torso lengths, so
  an integrated path accumulates several torso lengths of pure noise over a
  45-frame segment.
* They are only defined for a delivery that has a set. ``delivery_type`` is
  emitted alongside them so the stratification in ``spot_diff`` can see it.

``PRIMITIVE_STATUS`` records which of the new primitives survived validation and
which did not, with the measured numbers. Read it before wiring anything into
discovery.
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from preflight.window import actionable_window, preset_segment

# Frames either side of peak lift that get medianed into an "at lift" value.
LIFT_HALF_WIN = 3
# Plausible CF-view pitcher torso length (shoulder mid to hip mid) in
# normalised image units. Below the floor the pose has collapsed; above the
# ceiling the tracked subject is a broadcast close-up rather than the pitcher,
# and its "leg lift" is really a hitter's stride.
MIN_TORSO = 0.05
MAX_TORSO = 0.24
# Knee must rise at least this fraction of a torso length to count as a leg
# kick; a rise beyond the ceiling is not a leg kick at all but a tracking swap
# onto another body.
MIN_KNEE_RISE = 0.12
MAX_KNEE_RISE = 1.10
# Peak lift must be at least this many frames after the set, otherwise there is
# no pre-lift stretch to measure drift over.
MIN_SET_TO_LIFT = 5

# --- set-position and coming-set cues ----------------------------------------
# Smoothing width for trajectory features. Measured landmark jitter over the set
# interval, where the pitcher is still by construction, is 0.098-0.106 torso
# lengths per frame at the hips (see landmark_noise_probe.py). Integrating a
# path frame-by-frame at that jitter accumulates several torso lengths of pure
# noise across a 45-frame segment, which is how the original glove path-length
# feature reached physically impossible values. So every trajectory feature here
# is computed on a smoothed path and expressed as an EXCURSION from an anchor
# rather than as an accumulated path length.
TRAJ_SMOOTH = 7
# A trajectory feature needs this fraction of its frames actually tracked.
# Below it the result is NaN: a landmark that dropped out and came back looks
# like a large excursion, and reporting that as sway would be inventing motion.
MIN_TRAJ_COVERAGE = 0.5
MIN_TRAJ_FRAMES = 10
# Subject continuity across the pre-set segment. The apparent torso length of a
# pitcher standing on the rubber cannot legitimately swing by much before he
# sets: measured inside the actionable window, the foreshortening term spans
# 0.84-1.16 of the window median (5th-95th percentile), so ±16% covers the whole
# range real posture change produces from CF. A coefficient of variation above
# 0.25 is therefore outside what posture can do and indicates the tracker
# changed subject, or the broadcast changed zoom, part-way through the segment.
# Sway is NaN on those pitches rather than reporting the subject change as
# motion. Measured on Thorpe this rejects roughly a quarter of segments.
MAX_PRESET_TORSO_CV = 0.25
# A pitcher coming set does not leave the rubber. A smoothed pelvis excursion
# beyond a full torso length is him walking or a tracking swap onto another
# body, not a sway.
MAX_SWAY_AMPLITUDE = 1.0
# Feet stay on or beside the rubber at the set. An ankle separation beyond this
# is a stride, which means the anchor is not the set.
MAX_STANCE_WIDTH = 1.5
# Ankle and knee landmarks are the least reliable of the trunk group (mean
# visibility 0.69-0.74 against 0.999 at the hips), so the two features that
# depend on them are gated on the model actually claiming to see them.
MIN_LEG_VISIBILITY = 0.3
# An angle between two landmarks is only as good as the length of the segment
# joining them. The CF camera looks down the pitcher's forward axis, so segments
# that point toward the lens (the shoulder line of a side-on pitcher, a forearm
# angled at the camera) project to almost nothing, and the arctangent of two
# noise terms is a uniformly distributed angle rather than a posture. With
# single-anchor landmark noise measured at 0.05-0.07 torso lengths, holding the
# angular error near 10 degrees needs a projected segment of at least
# 0.05 / tan(10 deg) = 0.28 torso lengths. Shorter than that the angle is NaN.
MIN_ANGLE_SEGMENT = 0.28

PRIMITIVES = [
    "glove_height_at_lift",
    "glove_height_at_set",
    "glove_rise_set_to_lift",
    "glove_drift_pre_lift",  # max smoothed excursion from the set anchor
    "glove_drift_dx",
    "glove_drift_dy",
    "drift_lift_sync",
    "glove_angle_at_lift",
    "glove_rise_above_elbow_at_lift",
    "glove_off_body_at_lift",
    "glove_off_body_at_set",
    "glove_flare_at_lift",
    "posture_lean_at_lift",
    "posture_upright_at_lift",
    "hand_gap_at_lift",
    "hand_vis_at_lift",
    # --- set position: how and where he sets -------------------------------
    "stance_width_at_set",
    "knee_flex_at_set",
    "posture_lean_at_set",
    "shoulder_tilt_at_set",
    "torso_foreshorten_at_set",
    "glove_angle_at_set",
    "forearm_exposure_at_set",
    "forearm_exposure_at_lift",
    # --- set -> lift change --------------------------------------------------
    "lean_change_set_to_lift",
    "foreshorten_change_set_to_lift",
    # --- coming set: trajectory over the pre-set segment ---------------------
    "sway_amplitude",
    "sway_dx",
    "sway_dy",
    "sway_directness",
    "come_set_peak_speed",
]

# Primitives measured on the pre-set segment rather than inside the actionable
# window. They are NaN on any pitch whose clip does not carry enough pre-set
# footage, which is a data limit and not a zero.
PRESET_PRIMITIVES = [
    "sway_amplitude",
    "sway_dx",
    "sway_dy",
    "sway_directness",
    "come_set_peak_speed",
]

# --- retention status --------------------------------------------------------
# Every primitive below is computed and banked, because doing so is free once
# the track is loaded and a NaN is more informative than a missing column. What
# this table controls is which of them are fit to enter DISCOVERY. Adding a
# feature to the discovery set spends FDR budget, and a feature that is noisy or
# only defined on a third of pitches spends that budget for no power.
#
# Statuses, from test_primitives.noise_reliability on 381 Thorpe tracks with
# additive landmark noise at the measured 0.10 torso/frame jitter:
#
#   validated          recoverable signal above the 0.05-torso visibility floor
#                      AND defined on at least 60% of usable pitches.
#   under_covered      signal is fine, coverage is not, and the shortfall is a
#                      property of the clips rather than of the feature.
#   excluded_permanently
#                      will not be wired into discovery, and not because of a
#                      number that might improve. See the sway family below.
#   resolution_limited the quantity does not survive the CF viewing geometry.
#
# Only "validated" entries should be wired into spot_diff.CUES. That wiring is
# deliberately NOT done here: these features have never been tested against real
# pitch types, and adding them to discovery is a separate, later decision.
#
# The table originally covered only the newly added primitives. The cue audit
# (cv/preflight/cue_audit.py) put the ORIGINAL lift-anchored fifteen through the
# identical measurement, because a cue that shipped earlier has no claim to a
# lower bar, and their entries are below. Two statuses were added to say what the
# numbers actually showed:
#
#   underpowered       signal is real and the measurement is sound, but the
#                      standard error of a 50-pitch group mean does not clear the
#                      cue's own visibility threshold. This is a statement about
#                      sample size, not about validity: the cue needs a larger n
#                      before a group difference in it can be believed.
#   retracted          the measurement does not measure its name. See
#                      provenance.RETRACTED_CUES for the reason and the numbers.
#
# One correction the audit forced on its own method: comparing a PER-PITCH noise
# standard deviation directly against a visibility threshold is not a valid test,
# because the threshold applies to a DIFFERENCE OF GROUP MEANS, whose error falls
# as 1/sqrt(n). Applied literally that comparison disqualifies 14 of these 15
# cues; applied correctly it disqualifies none of them on noise alone. The two
# tests actually used here are (a) noise/signal against the 1.9 bar that retired
# PitchCom, and (b) the group-mean standard error against the threshold.
PRIMITIVE_STATUS = {
    # --- original lift-anchored fifteen, re-measured by the cue audit --------
    # Format: noise/signal, coverage, group-mean SE at n=50 vs the threshold.
    "glove_height_at_lift": "validated",  # 0.50, 1.00, 0.037 < 0.05
    "glove_height_at_set": "validated",  # 0.50, 0.99, 0.030 < 0.05
    "glove_rise_set_to_lift": "validated",  # 0.63, 0.99, 0.044 < 0.05
    "glove_off_body_at_lift": "validated",  # 0.61, 1.00, 0.011 < 0.05
    "glove_off_body_at_set": "validated",  # 0.58, 0.99, 0.009 < 0.05
    "glove_flare_at_lift": "validated",  # 0.53, 1.00, 0.016 < 0.05
    "glove_drift_dx": "validated",  # 0.65, 0.99, 0.048 < 0.05
    "drift_lift_sync": "validated",  # 0.74, 0.99, 0.044 < 0.25
    "posture_lean_at_lift": "validated",  # 0.47, 0.89, 0.89 < 4.0 deg
    "posture_upright_at_lift": "validated",  # 0.74, 1.00, 0.013 < 0.05
    "hand_gap_at_lift": "validated",  # 0.40, 1.00, 0.018 < 0.04
    "hand_vis_at_lift": "validated",  # 0.49, 1.00, 0.009 < 0.08
    # Signal is sound; the group-mean error does not clear 0.05 torso at n=50.
    # A max-excursion and a signed displacement both inherit the drift family's
    # large per-pitch noise (0.48 and 0.39 torso), so they need roughly n=92 and
    # n=60 per pitch type rather than 50.
    "glove_drift_pre_lift": "underpowered",  # 0.69, 0.99, 0.068 > 0.05
    "glove_drift_dy": "underpowered",  # 0.61, 0.99, 0.055 > 0.05
    "glove_angle_at_lift": "retracted",  # arctangent saturates; see provenance
    "glove_rise_above_elbow_at_lift": "validated",  # 0.50, 1.00, 0.019 < 0.05
    # signal 0.184 torso, coverage 0.86
    "stance_width_at_set": "validated",
    # signal 0.259 torso, coverage 0.96
    "knee_flex_at_set": "validated",
    # signal 15.4 deg against 3.7 deg induced noise, coverage 0.90
    "posture_lean_at_set": "validated",
    # signal 0.083 torso, coverage 0.98. Clears the floor but only just; it is
    # the weakest of the validated set and the closest to being noise.
    "torso_foreshorten_at_set": "validated",
    # signal 0.180 torso, coverage 0.98
    "forearm_exposure_at_set": "validated",
    # signal 0.184 torso, coverage 1.00
    "forearm_exposure_at_lift": "validated",
    # signal 10.0 deg against 8.4 deg induced noise, coverage 0.85
    "lean_change_set_to_lift": "validated",
    # signal 0.179 torso, coverage 0.98
    "foreshorten_change_set_to_lift": "validated",
    # The sway family. Signal is genuinely there (0.12-0.25 torso, all well
    # above the floor) but only 27-32% of stretch pitches carry a measurable
    # approach. Of 381 tracks: 92 have fewer than PRESET_MIN_FRAMES of footage
    # before the set because the Savant clip starts too late, 40 more show the
    # apparent torso changing by over 25% across the approach (subject or zoom
    # change in the broadcast lead-in), 19 imply the pelvis travelling over a
    # torso length.
    #
    # "The fix is longer clips" was the original note here, and it is wrong.
    # Savant serves one pre-rendered 6.0s mp4 per playId — exactly 180 frames
    # with zero variance across all 381 clips, no trim parameter, and a re-fetch
    # returns byte-identical files (docs/clip_lead_in.md). The missing lead-in
    # does not exist in any asset that can be requested. Coverage is capped by
    # where the set happens to fall inside a fixed render: 31.8% of pitches carry
    # the full PRESET_LOOKBACK of 45 frames, and that is the ceiling.
    #
    # Hence excluded_permanently rather than under_covered, on three independent
    # grounds, none of which more data can move:
    #
    #   1. No documentary basis. Tip 12 (sway coming set) is recorded in
    #      docs/tip_taxonomy.md as "not in the documents" — a target named by the
    #      user, not a cue any scout wrote down. That matters most, because
    #      entering discovery spends FDR budget for the WHOLE family: five
    #      undocumented cues at 30% coverage would raise the bar for the twenty
    #      documented ones and buy nothing.
    #   2. Coverage cannot be raised honestly. The only lever is shortening
    #      PRESET_LOOKBACK, which is tuning a minimum to manufacture coverage,
    #      and a 15-frame excursion is not the sway a scout describes anyway.
    #   3. sway_directness is majority jitter: noise/signal 1.13, so more than
    #      half of what it reports is landmark noise. The family's best member is
    #      0.43.
    #
    # They stay computed and banked, because a NaN column is free and a future
    # second-base or higher-frame-rate source would change item 2. Nothing about
    # the CF broadcast will.
    "sway_amplitude": "excluded_permanently",
    "sway_dx": "excluded_permanently",
    "sway_dy": "excluded_permanently",
    "sway_directness": "excluded_permanently",
    "come_set_peak_speed": "excluded_permanently",
    # Both of these are angles on a segment that points at the CF camera, so it
    # projects to almost nothing and the arctangent of two noise terms wins.
    # MIN_ANGLE_SEGMENT turns the unresolvable cases into NaN, which is why
    # coverage is 0.56 and 0.44 rather than 1.00 — without the gate they were
    # 100% populated and 100% noise (raw standard deviations of 80 and 81
    # degrees). Even among survivors the induced noise is 13.2 and 27.5 degrees.
    # These are the clearest examples in the set of a cue scouts read easily
    # from the side that center field cannot deliver.
    "shoulder_tilt_at_set": "resolution_limited",
    "glove_angle_at_set": "retracted",  # same saturation as the lift version
}

VALIDATED_NEW_PRIMITIVES = [k for k, v in PRIMITIVE_STATUS.items() if v == "validated"]
META = [
    "play_id",
    "lift_frame",
    "set_frame",
    "break_frame",
    "knee_rise_peak",
    "lift_style",
    "torso_scale",
    "window_method",
    # Read straight off the window rather than inferred from the base state.
    # spot_diff._groups refuses a frame carrying more than one delivery, and the
    # set-position and coming-set primitives are only defined for a delivery
    # that HAS a set, so the stratum label has to travel with them.
    "delivery_type",
]


def _col(df: pd.DataFrame, name: str) -> np.ndarray:
    if name not in df.columns:
        return np.full(len(df), np.nan)
    s = pd.to_numeric(df[name], errors="coerce")
    s = s.interpolate(limit=3, limit_direction="both")
    return s.rolling(3, center=True, min_periods=1).median().to_numpy(dtype=float)


def _mid(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.nanmean(np.vstack([a, b]), axis=0)


def _med(arr: np.ndarray, lo: int, hi: int) -> float:
    """Median of ``arr[lo:hi]``, NaN when nothing usable is in range."""
    lo, hi = max(0, lo), min(len(arr), hi)
    if hi <= lo:
        return float("nan")
    chunk = arr[lo:hi]
    if not np.isfinite(chunk).any():
        return float("nan")
    return float(np.nanmedian(chunk))


def _smooth_path(x: np.ndarray, y: np.ndarray, lo: int, hi: int) -> tuple[np.ndarray, np.ndarray] | None:
    """
    Smoothed (x, y) path over ``[lo, hi)``, or None when too little of it was
    actually tracked to describe a movement.

    The coverage guard is the point of this helper. A landmark that drops out
    mid-segment and reappears elsewhere produces a large apparent excursion; the
    caller must not read that as sway.
    """
    lo, hi = max(0, lo), min(len(x), hi)
    if hi - lo < MIN_TRAJ_FRAMES:
        return None
    sx, sy = x[lo:hi], y[lo:hi]
    tracked = np.isfinite(sx) & np.isfinite(sy)
    if tracked.mean() < MIN_TRAJ_COVERAGE:
        return None
    px = pd.Series(sx).rolling(TRAJ_SMOOTH, center=True, min_periods=3).median().to_numpy(dtype=float)
    py = pd.Series(sy).rolling(TRAJ_SMOOTH, center=True, min_periods=3).median().to_numpy(dtype=float)
    if np.isfinite(px).sum() < MIN_TRAJ_FRAMES // 2:
        return None
    return px, py


def _angle_off_vertical(dx: float, dy: float) -> float:
    """
    Degrees a hip->shoulder vector leans off image vertical. 0 = upright.

    ``dy`` is required to be positive, i.e. the shoulders above the hips in
    image coordinates. When it is not, the pose is inverted — the tracker has
    the trunk upside down — and the arctangent of that is not a lean angle but a
    number near ±180 that would enter a group mean as a huge posture difference.
    Those pitches return NaN.
    """
    if not (np.isfinite(dx) and np.isfinite(dy)) or dy <= 0:
        return float("nan")
    return math.degrees(math.atan2(dx, dy))


def _elevation(dx: float, dy: float, min_segment: float = 0.0) -> float:
    """
    Degrees a segment sits above image horizontal, folded to [-90, 90].

    ``min_segment`` rejects segments too short to carry an angle; it is in the
    same units as ``dx`` and ``dy``, so callers pass torso-normalised values.

    Taking the absolute value of the horizontal component makes the result
    invariant to which way the pitcher faces. Without that fold the same
    physical posture reads as +100 for a lefty and -80 for a righty, and the
    group mean of a mixed sample is meaningless — which is what the raw
    arctangent produced: a standard deviation of 80 degrees on a cue whose real
    range is a few degrees. The fold costs the open-versus-closed side, keeping
    only the magnitude of the tilt.
    """
    if not (np.isfinite(dx) and np.isfinite(dy)):
        return float("nan")
    if math.hypot(dx, dy) < min_segment:
        return float("nan")
    return math.degrees(math.atan2(dy, abs(dx)))


def _point_to_line(px, py, ax, ay, bx, by) -> float:
    """Perpendicular distance from the glove to the torso midline."""
    vx, vy = bx - ax, by - ay
    norm = math.hypot(vx, vy)
    if not np.isfinite(norm) or norm < 1e-9:
        return float("nan")
    return abs(vx * (ay - py) - vy * (ax - px)) / norm


def _find_lift(
    knee_rise_l: np.ndarray,
    knee_rise_r: np.ndarray,
    start: int,
    end: int,
) -> tuple[int | None, float, np.ndarray]:
    """
    Peak leg lift inside the actionable window.

    The lead knee is whichever knee rises further relative to the hips; taking
    the max per frame and then the argmax avoids having to know handedness.
    """
    if end - start < 4:
        return None, float("nan"), knee_rise_l

    def top(arr: np.ndarray) -> float:
        seg = arr[start:end]
        return float(np.nanmax(seg)) if np.isfinite(seg).any() else -np.inf

    lead = knee_rise_l if top(knee_rise_l) >= top(knee_rise_r) else knee_rise_r
    seg = lead[start:end]
    if not np.isfinite(seg).any():
        return None, float("nan"), lead
    idx = int(np.nanargmax(seg)) + start

    # Baseline used to be the median of the few frames right after the set. That
    # silently failed whenever the knee was not yet tracked at the set: the
    # baseline came out NaN, so the peak came out NaN, and a perfectly visible
    # leg lift was discarded. This accounted for most rejected pitches. Taking a
    # low percentile of the whole pre-lift stretch is robust to those dropouts
    # and still represents "knee at rest".
    pre = lead[start : idx + 1]
    pre = pre[np.isfinite(pre)]
    if pre.size == 0:
        return None, float("nan"), lead
    baseline = float(np.percentile(pre, 20))
    return idx, float(lead[idx] - baseline), lead


def pitch_primitives(df: pd.DataFrame, play_id: str) -> dict[str, Any] | None:
    """Compute the lift-anchored primitives for one pitch, or None if unusable."""
    lsho_x, lsho_y = _col(df, "lsho_x"), _col(df, "lsho_y")
    rsho_x, rsho_y = _col(df, "rsho_x"), _col(df, "rsho_y")
    lhip_x, lhip_y = _col(df, "lhip_x"), _col(df, "lhip_y")
    rhip_x, rhip_y = _col(df, "rhip_x"), _col(df, "rhip_y")
    lwri_x, lwri_y = _col(df, "lwri_x"), _col(df, "lwri_y")
    rwri_x, rwri_y = _col(df, "rwri_x"), _col(df, "rwri_y")
    lelb_x, lelb_y = _col(df, "lelb_x"), _col(df, "lelb_y")
    relb_x, relb_y = _col(df, "relb_x"), _col(df, "relb_y")
    lkne_y, rkne_y = _col(df, "lkne_y"), _col(df, "rkne_y")
    lank_x, lank_y = _col(df, "lank_x"), _col(df, "lank_y")
    rank_x, rank_y = _col(df, "rank_x"), _col(df, "rank_y")

    sho_x, sho_y = _mid(lsho_x, rsho_x), _mid(lsho_y, rsho_y)
    hip_x, hip_y = _mid(lhip_x, rhip_x), _mid(lhip_y, rhip_y)

    # Both hands are inside the glove for the whole actionable window (hand
    # break is the window's closing edge), so the wrist midpoint is a steadier
    # glove estimate than picking one wrist and risking a left/right swap.
    glove_x, glove_y = _mid(lwri_x, rwri_x), _mid(lwri_y, rwri_y)
    hand_gap = np.hypot(lwri_x - rwri_x, lwri_y - rwri_y)

    # Boundaries come from the shared window module, fed the column names it
    # expects, so the definition of set / hand break stays in one place.
    # The whole landmark frame goes through, not just the glove proxy: the window
    # module locates the delivery from the faster individual wrist (the midpoint
    # cancels that motion once the hands separate) and closes just after peak leg
    # lift, which it finds from the knee and hip landmarks.
    wdf = df.copy()
    wdf["glove_x"] = glove_x
    wdf["glove_y"] = glove_y
    wdf["wrist_dist"] = hand_gap
    win = actionable_window(wdf)
    if not win.valid:
        return None
    start = int(win.start)
    end = int(win.end)
    set_frame = int(win.set_frame if win.set_frame is not None else start)

    torso = np.hypot(sho_x - hip_x, sho_y - hip_y)
    scale = _med(torso, start, end)
    if not np.isfinite(scale) or not (MIN_TORSO <= scale <= MAX_TORSO):
        return None

    knee_rise_l = (hip_y - lkne_y) / scale
    knee_rise_r = (hip_y - rkne_y) / scale
    if win.lift_frame is not None:
        # The window already located the top of the kick and closed just after
        # it, so re-searching here could only disagree with the boundary the
        # features are drawn from.
        lift = int(win.lift_frame)
        lead = np.nanmax(np.vstack([knee_rise_l, knee_rise_r]), axis=0)
        knee_peak = _med(lead, lift - LIFT_HALF_WIN, lift + LIFT_HALF_WIN + 1)
        lead_rise = lead
    else:
        lift, knee_peak, lead_rise = _find_lift(knee_rise_l, knee_rise_r, set_frame, end)
    if lift is None or not np.isfinite(knee_peak) or knee_peak > MAX_KNEE_RISE:
        # Either no knee signal at all, or a "rise" too large to be a leg kick,
        # which means the tracker swapped onto another body. Refuse the pitch: a
        # mis-anchored "at lift" value is worse than a missing one.
        return None

    # A knee rise below the threshold is not a detection failure. Slide-steps
    # and quick pitches from the stretch genuinely have almost no knee lift, and
    # every one of these in the sample came from the stretch. Discarding them
    # would throw away real pitches and bias the sample toward full windups, so
    # they are kept and labelled: the peak-knee frame is still the right anchor,
    # it just is not much of a lift.
    lift_style = "leg_lift" if knee_peak >= MIN_KNEE_RISE else "minimal_lift"
    if lift - set_frame < MIN_SET_TO_LIFT:
        return None

    lo, hi = lift - LIFT_HALF_WIN, lift + LIFT_HALF_WIN + 1
    s_lo, s_hi = set_frame, set_frame + 2 * LIFT_HALF_WIN + 1

    def at(arr, lo_=lo, hi_=hi):
        return _med(arr, lo_, hi_)

    # 1. Glove height, signed so that larger = higher glove, in torso lengths.
    glove_height_lift = (at(hip_y) - at(glove_y)) / scale
    glove_height_set = (_med(hip_y, s_lo, s_hi) - _med(glove_y, s_lo, s_hi)) / scale

    # 2. Drift from the set anchor up to peak lift: path length, net direction,
    #    and whether the drift tracks the knee coming up.
    ax, ay = _med(glove_x, s_lo, s_hi), _med(glove_y, s_lo, s_hi)
    # Path length integrated frame-by-frame is dominated by landmark jitter: it
    # summed to double-digit torso lengths, which is physically impossible for a
    # glove before lift. Smoothing first and taking the largest excursion from
    # the set anchor measures "how far the glove wandered" without accumulating
    # per-frame noise.
    seg_x = pd.Series(glove_x[set_frame : lift + 1]).rolling(5, center=True, min_periods=2).median()
    seg_y = pd.Series(glove_y[set_frame : lift + 1]).rolling(5, center=True, min_periods=2).median()
    if len(seg_x) >= 2:
        excursion = np.hypot(seg_x - ax, seg_y - ay)
        drift_path = float(np.nanmax(excursion)) / scale if np.isfinite(excursion).any() else float("nan")
    else:
        drift_path = float("nan")
    drift_dx = (at(glove_x) - ax) / scale
    drift_dy = (ay - at(glove_y)) / scale  # positive = drifted upward

    disp = np.hypot(glove_x[set_frame : lift + 1] - ax, glove_y[set_frame : lift + 1] - ay)
    knee_seg = lead_rise[set_frame : lift + 1]
    ok = np.isfinite(disp) & np.isfinite(knee_seg)
    if ok.sum() >= 5 and np.nanstd(disp[ok]) > 1e-6 and np.nanstd(knee_seg[ok]) > 1e-6:
        drift_sync = float(np.corrcoef(disp[ok], knee_seg[ok])[0, 1])
    else:
        drift_sync = float("nan")

    # 3. Glove angle: both forearms converge on the glove during the window, so
    #    the mean forearm vector describes how the glove is presented (angled up
    #    vs flat). Degrees above horizontal.
    #
    #    Folded for handedness and gated on a resolvable segment, for the
    #    reasons in _elevation and MIN_ANGLE_SEGMENT. This replaced a raw atan2
    #    that was measured, over 416 pitches on three arms, to put 44.2% of its
    #    values beyond ±90 degrees — mirroring a lefty into a righty flips the
    #    raw angle by 180, so the sample was two clusters and the group mean sat
    #    between them. Induced landmark noise on the raw version was 42.7
    #    degrees against 7.2 on this one; the cost is that 63% of pitches now
    #    return NaN because the forearm points down the camera axis and its
    #    angle was never measurable. Window placement is unchanged by this:
    #    window.py imports nothing from this module, verified pitch-by-pitch in
    #    angle_fix_probe.py.
    elb_x, elb_y = _mid(lelb_x, relb_x), _mid(lelb_y, relb_y)
    fx = (at(glove_x) - at(elb_x)) / scale
    fy = (at(elb_y) - at(glove_y)) / scale
    glove_angle = _elevation(fx, fy, MIN_ANGLE_SEGMENT)

    # 3b. The part of the forearm's presentation that CF can actually resolve.
    #
    #    glove_angle above is retracted, and this is what replaces it. The angle
    #    form cannot work from this camera, for a reason that is geometric rather
    #    than fixable (cv/preflight/glove_angle_resolve.py, 326 pitches):
    #      * the forearm's HORIZONTAL extent has a median of 0.066 torso lengths
    #        against a 0.100 landmark-jitter floor. It is below the noise on 68%
    #        of pitches and below twice the noise on 97%. The forearm points down
    #        the camera axis, so |dx| is never measured, only guessed;
    #      * with |dx| -> 0 the arctangent saturates, so 96% of the angle's
    #        variance is explained by the SIGN of the vertical component alone.
    #        Median |angle| is 80.4 deg and only 3.4% of pitches land within 45
    #        deg of horizontal. It was one bit of information carrying a degrees
    #        label and an 8-degree threshold it could never be compared against.
    #
    #    The vertical component on its own is a genuine measurement: how far the
    #    glove sits above the elbow, as a torso-normalised distance, which takes
    #    the same 0.05-torso visibility threshold as every other distance here.
    #    Taken as a median over the lift window rather than at the single lift
    #    frame — the estimator the other lift-anchored cues already use — induced
    #    noise is 0.132 torso against a recovered signal of 0.263, a noise/signal
    #    of 0.50 where the PitchCom retraction bar is 1.9. Coverage returns to
    #    100% because no angle gate is needed.
    #
    #    Honest limits: this keeps the MAGNITUDE of the forearm's tilt and loses
    #    its direction, so "wrist angled up" and "wrist cocked in" are not
    #    distinguishable. It is the vertical component, not the glove angle, and
    #    is named for what it is.
    fy_med = (
        _med(np.asarray(elb_y, dtype=float), lo, hi)
        - _med(np.asarray(glove_y, dtype=float), lo, hi)
    ) / scale
    glove_rise_above_elbow = float(fy_med) if np.isfinite(fy_med) else float("nan")

    # 4. Distance off the body: perpendicular offset from the torso midline.
    off_lift = _point_to_line(at(glove_x), at(glove_y), at(sho_x), at(sho_y), at(hip_x), at(hip_y)) / scale
    off_set = _point_to_line(
        _med(glove_x, s_lo, s_hi),
        _med(glove_y, s_lo, s_hi),
        _med(sho_x, s_lo, s_hi),
        _med(sho_y, s_lo, s_hi),
        _med(hip_x, s_lo, s_hi),
        _med(hip_y, s_lo, s_hi),
    ) / scale

    # 5. Posture: torso lean off vertical, and torso extension at lift relative
    #    to the pitch's own median (a proxy for standing more upright).
    #    The lean now returns NaN on an inverted trunk instead of a number near
    #    ±180. Measured over 416 pitches: 42 of them (10.1%) had the shoulders
    #    tracked below the hips, and the old atan2 reported those as leans, which
    #    is why the published 5th percentile was -171.5 degrees. Removing them
    #    takes the standard deviation from 55.0 to 16.1 degrees and the induced
    #    landmark noise from 31.0 to 4.3, at a cost of 10% coverage.
    tx, ty = at(sho_x) - at(hip_x), at(hip_y) - at(sho_y)
    lean = _angle_off_vertical(tx, ty)
    upright = at(torso) / scale

    # 6. Flare: signed horizontal offset of the glove from the torso midline.
    flare = (at(glove_x) - at(hip_x)) / scale

    # 7. Grip burial proxies. hand_gap is how far the wrists have parted while
    #    still pre-break; hand_vis is how confidently the pose model sees the
    #    finger landmarks, which drops when the hand is buried in the glove.
    #    Both are proxies — true grip burial needs the parts detector.
    vis = np.nanmean(
        np.vstack([_col(df, c) for c in ("lidx_v", "ridx_v", "lpnk_v", "rpnk_v")]), axis=0
    )

    # 8. Set position: how and where he sets. All medianed over the same
    #    2*LIFT_HALF_WIN+1 frames at the set that the existing set-anchored
    #    primitives use, so a set-anchored value here is directly comparable to
    #    glove_height_at_set.
    def at_set(arr):
        return _med(arr, s_lo, s_hi)

    ank_vis = at_set(np.nanmean(np.vstack([_col(df, "lank_v"), _col(df, "rank_v")]), axis=0))
    kne_vis = at_set(np.nanmean(np.vstack([_col(df, "lkne_v"), _col(df, "rkne_v")]), axis=0))

    # Stance width: how wide he sets up, ankle to ankle.
    stance_width = float(
        np.hypot(at_set(lank_x) - at_set(rank_x), at_set(lank_y) - at_set(rank_y))
    ) / scale
    if not (np.isfinite(ank_vis) and ank_vis >= MIN_LEG_VISIBILITY) or stance_width > MAX_STANCE_WIDTH:
        stance_width = float("nan")

    # Knee flex: how deep he sits into the set. Higher = knees more bent, since
    # a flexed knee sits higher relative to the hips than a straight one.
    kne_y_set = float(np.nanmean([at_set(lkne_y), at_set(rkne_y)]))
    knee_flex = (at_set(hip_y) - kne_y_set) / scale
    if not (np.isfinite(kne_vis) and kne_vis >= MIN_LEG_VISIBILITY):
        knee_flex = float("nan")

    # Posture at the set, matching posture_lean_at_lift so the pair can be
    # differenced. Note this is the LATERAL lean component: the CF camera looks
    # down the pitcher's forward axis, so forward lean projects almost entirely
    # onto the camera axis and barely moves this angle. Forward lean is carried
    # by the foreshortening term below instead.
    lean_set = _angle_off_vertical(at_set(sho_x) - at_set(hip_x), at_set(hip_y) - at_set(sho_y))

    # Shoulder tilt: the shoulder line off image horizontal, which is how the
    # open/closed side reads from behind.
    stx = (at_set(lsho_x) - at_set(rsho_x)) / scale
    sty = (at_set(lsho_y) - at_set(rsho_y)) / scale
    shoulder_tilt = _elevation(stx, sty, MIN_ANGLE_SEGMENT)

    # Forward lean proxy. Apparent torso length shortens as the trunk tips
    # toward or away from the camera, so torso-at-set over the pitch's own
    # window-median torso is a dimensionless "how much is he leaning out of the
    # frontal plane" number. This is a proxy, not a lean angle, and it cannot
    # tell forward from backward.
    foreshorten_set = at_set(torso) / scale

    # Glove/forearm presentation at the set, mirroring glove_angle_at_lift.
    # Covers "wrist angled up" / "top of glove up".
    fsx = (at_set(glove_x) - at_set(elb_x)) / scale
    fsy = (at_set(elb_y) - at_set(glove_y)) / scale
    glove_angle_set = _elevation(fsx, fsy, MIN_ANGLE_SEGMENT)

    # Forearm exposure: apparent elbow-to-wrist length. A forearm rotated toward
    # the camera foreshortens; one turned across the view reads at full length.
    # This is the geometric read on "more forearm visible to coach".
    def forearm(getter):
        left = float(np.hypot(getter(lelb_x) - getter(lwri_x), getter(lelb_y) - getter(lwri_y)))
        right = float(np.hypot(getter(relb_x) - getter(rwri_x), getter(relb_y) - getter(rwri_y)))
        vals = [v for v in (left, right) if np.isfinite(v)]
        return (max(vals) / scale) if vals else float("nan")

    forearm_set = forearm(at_set)
    forearm_lift = forearm(at)

    # 9. Set -> lift change. The scouts read posture as a contrast ("more
    #    upright on the SL"), and a within-pitch difference cancels the part of
    #    the pose that is just this pitcher's build or where he stands.
    lean_change = lean - lean_set
    foreshorten_change = upright - foreshorten_set

    # 10. Coming set: the sway. This is a trajectory, not a value at an anchor,
    #     so it is measured over the whole pre-set segment and summarised by the
    #     SHAPE of the smoothed pelvis path:
    #
    #       amplitude  how far the pelvis ever got from where it ended up set
    #       dx, dy     which way it went, net
    #       directness net displacement / amplitude, in [0, 1]. A single smooth
    #                  settle into the set scores near 1; a rock out and back
    #                  scores near 0. This is the part that actually needs the
    #                  path — no single-frame measurement can distinguish those
    #                  two, and they are different cues to a runner.
    #       peak_speed fastest the smoothed path ever moved
    #
    #     The pelvis (hip midpoint) is the carrier because it is the steadiest
    #     landmark group available: hip visibility is 0.999 across the sample
    #     against 0.54 at the wrists.
    sway_amp = sway_dx = sway_dy = sway_direct = come_set_speed = float("nan")
    pre = preset_segment(df, win)
    # Subject continuity first. The pre-set segment reaches back toward the
    # broadcast lead-in, where the tracked body can change or the zoom can
    # shift; either shows up as a large pelvis excursion that is not sway.
    pre_seg = torso[pre[0] : pre[1]] if pre is not None else np.array([])
    pre_med = float(np.nanmedian(pre_seg)) if np.isfinite(pre_seg).any() else float("nan")
    pre_cv = (
        float(np.nanstd(pre_seg) / pre_med)
        if np.isfinite(pre_med) and pre_med > 1e-9
        else float("nan")
    )
    if pre is not None and (not np.isfinite(pre_cv) or pre_cv > MAX_PRESET_TORSO_CV):
        pre = None
    if pre is not None:
        path = _smooth_path(hip_x, hip_y, pre[0], pre[1])
        if path is not None:
            px, py = path
            # Anchor on the END of the segment: the set is where the movement
            # resolves, so excursion is "how far from set did he come".
            tail = slice(max(0, len(px) - (2 * LIFT_HALF_WIN + 1)), len(px))
            ax_s = float(np.nanmedian(px[tail]))
            ay_s = float(np.nanmedian(py[tail]))
            if np.isfinite(ax_s) and np.isfinite(ay_s):
                exc = np.hypot(px - ax_s, py - ay_s)
                if np.isfinite(exc).any():
                    sway_amp = float(np.nanmax(exc)) / scale
                    head = slice(0, min(len(px), 2 * LIFT_HALF_WIN + 1))
                    hx = float(np.nanmedian(px[head]))
                    hy = float(np.nanmedian(py[head]))
                    if np.isfinite(hx) and np.isfinite(hy):
                        sway_dx = (ax_s - hx) / scale
                        sway_dy = (hy - ay_s) / scale  # positive = pelvis rose
                        net = float(np.hypot(ax_s - hx, ay_s - hy)) / scale
                        sway_direct = net / sway_amp if sway_amp > 1e-9 else float("nan")
            step = np.hypot(np.diff(px), np.diff(py))
            if np.isfinite(step).any():
                come_set_speed = float(np.nanmax(step)) / scale
    # The pelvis cannot travel a torso length before the set. When it appears to,
    # every descriptor of that path is describing something other than a sway, so
    # the whole group goes rather than just the amplitude.
    if np.isfinite(sway_amp) and sway_amp > MAX_SWAY_AMPLITUDE:
        sway_amp = sway_dx = sway_dy = sway_direct = come_set_speed = float("nan")

    return {
        "play_id": play_id,
        "lift_frame": lift,
        "set_frame": set_frame,
        "break_frame": end,
        "knee_rise_peak": round(knee_peak, 5),
        "lift_style": lift_style,
        "torso_scale": round(scale, 5),
        "window_method": win.method,
        "delivery_type": win.delivery_type,
        "glove_height_at_lift": glove_height_lift,
        "glove_height_at_set": glove_height_set,
        "glove_rise_set_to_lift": glove_height_lift - glove_height_set,
        "glove_drift_pre_lift": drift_path,
        "glove_drift_dx": drift_dx,
        "glove_drift_dy": drift_dy,
        "drift_lift_sync": drift_sync,
        "glove_angle_at_lift": glove_angle,
        "glove_rise_above_elbow_at_lift": glove_rise_above_elbow,
        "glove_off_body_at_lift": off_lift,
        "glove_off_body_at_set": off_set,
        "glove_flare_at_lift": flare,
        "posture_lean_at_lift": lean,
        "posture_upright_at_lift": upright,
        "hand_gap_at_lift": at(hand_gap) / scale,
        "hand_vis_at_lift": at(vis),
        "stance_width_at_set": stance_width,
        "knee_flex_at_set": knee_flex,
        "posture_lean_at_set": lean_set,
        "shoulder_tilt_at_set": shoulder_tilt,
        "torso_foreshorten_at_set": foreshorten_set,
        "glove_angle_at_set": glove_angle_set,
        "forearm_exposure_at_set": forearm_set,
        "forearm_exposure_at_lift": forearm_lift,
        "lean_change_set_to_lift": lean_change,
        "foreshorten_change_set_to_lift": foreshorten_change,
        "sway_amplitude": sway_amp,
        "sway_dx": sway_dx,
        "sway_dy": sway_dy,
        "sway_directness": sway_direct,
        "come_set_peak_speed": come_set_speed,
    }


# Where per-frame landmark tracks live, newest schema first.
#
# ``lift_tracks`` was a separate second pass: the original ``tracks`` directory
# held only the 16 derived window scalars, so landmarks had to be written
# alongside it. The pipeline's tracker now emits ONE unified table under
# ``tracks`` carrying both — 72/73 columns, the 16 window scalars plus 18
# landmarks in x/y/visibility — which makes the second pass redundant and means
# ``lift_tracks`` is no longer written for new arms.
#
# This lookup existed only as ``run_dir / "lift_tracks"``, and that single hard
# coded path is what disconnected the two halves of this system. Arms tracked by
# the current pipeline had full landmark data sitting in ``tracks`` and no
# ``lift_tracks`` directory, so ``build_run`` refused to run, no primitives.csv
# was written, and ``spot_diff.load_pitcher`` silently fell back to window
# features alone. After the cue audit removed six of the eight legacy window
# cues, that left exactly TWO cues available on a 300-pitch, 7-game arm — while
# the same code reported 20 cues on the one arm that still had a stale
# ``lift_tracks`` directory. Nothing errored; the cue set just quietly shrank by
# 90% depending on which directory an arm happened to have.
TRACK_DIRS = ("tracks", "lift_tracks")


def resolve_track_dir(run_dir: Path) -> tuple[Path, list[Path]]:
    """The landmark-bearing track directory for this arm, and its CSVs.

    A directory only qualifies if its tables actually carry landmarks. The
    legacy ``tracks`` layout has the same directory name but no landmark
    columns, so matching on name alone would hand back 16-column tables and
    produce a primitives file full of NaN rather than an honest failure.
    """
    for name in TRACK_DIRS:
        d = run_dir / name
        csvs = sorted(d.glob("*.csv"))
        if not csvs:
            continue
        try:
            head = pd.read_csv(csvs[0], nrows=0).columns
        except Exception:
            continue
        if {"lwri_x", "rwri_x", "lhip_y", "lsho_y"} <= set(head):
            return d, csvs
    return run_dir / TRACK_DIRS[0], []


# Track filenames carry the play_id plus, depending on which pass wrote them, a
# suffix. ``lift_tracks`` used a bare "<play_id>.csv"; the pipeline's unified
# ``tracks`` uses "<play_id>_tracks.csv".
TRACK_SUFFIXES = ("_tracks", "_lift", "_track")


def play_id_of(path: Path) -> str:
    """The play_id a track file belongs to, with any writer suffix removed.

    This was ``path.stem``, which is correct only for the bare-filename layout.
    Against the pipeline's "<play_id>_tracks.csv" it produced play_ids ending in
    "_tracks" that matched nothing in features.csv — 0 of 358 on Webb — so the
    outer merge in spot_diff.load_pitcher orphaned every primitive row into a
    parallel set of rows with no pitch_type and no delivery label. The run still
    reported "cues available: 20", because the columns existed; they were simply
    never populated on any row that also had a pitch type to contrast.
    """
    stem = path.stem
    for suffix in TRACK_SUFFIXES:
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def build_run(run_dir: Path) -> Path:
    track_dir, tracks = resolve_track_dir(run_dir)
    if not tracks:
        raise SystemExit(
            f"No landmark-bearing tracks under {run_dir}/{{{','.join(TRACK_DIRS)}}}; "
            "run the tracker first"
        )

    rows: list[dict[str, Any]] = []
    skipped: dict[str, int] = {}
    for path in tracks:
        try:
            df = pd.read_csv(path)
        except Exception:
            skipped["unreadable"] = skipped.get("unreadable", 0) + 1
            continue
        got = pitch_primitives(df, play_id_of(path))
        if got is None:
            skipped["no_window_or_lift"] = skipped.get("no_window_or_lift", 0) + 1
            continue
        rows.append(got)

    prim = pd.DataFrame(rows)
    feats_path = run_dir / "features.csv"
    if feats_path.is_file() and not prim.empty:
        feats = pd.read_csv(feats_path)
        keep = [
            c
            for c in ("play_id", "pitch_type", "balls", "strikes", "runner_bucket", "batter_tag", "delivery")
            if c in feats.columns
        ]
        prim = prim.merge(feats[keep], on="play_id", how="left")

    out = run_dir / "primitives.csv"
    prim.to_csv(out, index=False)
    print(
        f"{run_dir.name}: {len(tracks)} tracks -> {len(prim)} usable pitches; skipped {skipped}",
        flush=True,
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, nargs="+")
    args = ap.parse_args()
    for d in args.run_dir:
        build_run(Path(d))


if __name__ == "__main__":
    main()
