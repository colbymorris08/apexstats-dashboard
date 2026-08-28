#!/usr/bin/env python3
"""
Pre-pitch glove target: where the catcher sets his mitt, measured against home
plate.

Why this is the only one of the three requested catcher cue families implemented
here
-----------------------------------------------------------------------------
Catcher stance (squat depth, stance width, weight distribution, body angle) and
catcher mitt ANGLE all need articulated landmarks on the catcher. Those are not
available at a usable rate. Measured over 391-436 sampled frames from 8 clips:

  detector locates a catcher REGION per clip     4/4 and 3/3 clips, 80-123
                                                 agreeing gear boxes each
  pose identifies the catcher in that region     3.3% of frames
  ... with the ``full`` pose model               3.96%
  ... with the ``heavy`` pose model              1.76%

The dominant rejection is ``no_pose_in_crop`` (50-67%): the crop is on the
catcher and the pose model returns nothing in it. A bigger model does not fix it,
so this is a capability limit on a ~50x45 px subject occluded by the umpire, not
a threshold to loosen. Any cue requiring those landmarks would be computed on
3-4% of frames, and the frames it succeeded on would be a visibility-selected
subsample — the same selection hazard that discredited the tap detector. So those
two families are NOT implemented, and the reason is a measurement, not an
oversight. See docs/catcher_localisation.md.

The glove TARGET survives because it needs a position, not a skeleton. A box is
enough, and the detector supplies two of them: ``catcher_mitt`` for the mitt and
``plate`` for the reference.

What the measurement geometry is, and why it is genuinely better than the
pitcher's glove
-------------------------------------------------------------------------------
All in units of the home-plate box width measured in the SAME frame, which is
what makes this robust to the zoom differences between parks:

  plate box width                            0.0637 of frame width (~81 px)
  mitt centre-x jitter, frame to frame       0.05 plate widths
  mitt lateral offset, spread within a pitch 0.12-0.34 plate widths (interdecile)
  mitt lateral offset, difference BETWEEN    ~0.23 plate widths
    pitches (per-pitch medians)

So the per-pitch mean has a standard error of roughly 0.04 plate widths against a
between-pitch signal of ~0.23 — call it six to one. Contrast the pitcher's glove
angle, which was retracted precisely because its horizontal extent (0.066 torso)
sat BELOW its own jitter floor (0.100), leaving 96% of the variance as the sign of
the vertical component. The structural reason is the one that motivated looking at
the catcher at all: the pitcher's glove points down the camera axis and the
catcher's mitt faces the camera.

Coverage, however, does NOT replicate across arms, and this is the reason the cues
here are not wired into discovery. Mitt detection rate inside the actionable span
versus outside it, per-clip medians:

  Bryan Woo, 4 clips      in window 0.645   out 0.230   plate in window 1.00
  Zac Gallen, 3 clips     in window 0.223   out 0.368   plate in window 0.00

On Gallen the cue yields nothing at all: no frame carries both a mitt and a plate
inside the window, on any of the three clips. Whole-clip rates put the cause in the
detector rather than the window — at conf 0.25 plate fires on 22.5% of Gallen
frames against 45.4% of Woo frames — which is what a detector trained on 28
fully-labeled frames does when it meets a new park and framing.

So the precision figures above are precision WHEN AVAILABLE, and availability is
currently unknown per arm and demonstrably zero on at least one. That matters more
than it sounds: coverage that varies by park varies by opponent, so a cue used
without measuring its own coverage per arm would carry a confound capable of
manufacturing an effect. Per-arm coverage has to be reported alongside any result
this module ever produces.

Names
-----
``cmitt_*``, deliberately new. The ``catcher_*`` family is in
``provenance.RETRACTED_CUES`` and stays there; those names described the
pitcher's body and are not being reused or un-retracted.

Honest limits, stated up front
------------------------------
* ``catcher_mitt`` and ``plate`` come from ``parts_gear.pt``, trained on 28
  fully-labeled frames, with ``catcher_mitt`` validated on 5 instances in 5
  images. The rates and spreads above were therefore measured directly on real
  frames rather than taken from the model's reported mAP, which carries no
  information at that sample size. More labelled mitt frames is the single
  highest-value thing that could be done for this cue.
* Lateral offset here is in CAMERA frame, toward-third versus toward-first. It
  is not inside/outside until it is combined with the batter's handedness, which
  lives in the pitch record and not in the track. The cue is named for what it
  measures.
* Nothing in this module has been validated against pitch type. The discovery and
  holdout protocol has not been run: the arms marked ``complete`` have had their
  clips purged by the janitor and the arms that still have clips are mid-tracking,
  so no eligible arm currently has pixels. See docs/catcher_localisation.md.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np

# Detector confidence floors.
#
# The mitt floor is set from the measured confidence distribution and the
# coverage it buys, not from any downstream outcome: at 0.50 the mitt appears on
# 3.2% of sampled frames and in only 3 of 8 clips, which cannot support a
# per-pitch statistic; at 0.25 it appears on 20.2% of sampled frames overall and
# 64.5% of in-window frames, in 5 of 8 clips. 0.15 and 0.05 buy more frames at
# the cost of boxes that were not inspected. 0.25 is the loosest level at which
# the rendered boxes were checked to be on the mitt.
MITT_CONF = 0.25
PLATE_CONF = 0.25

# Plausibility guard on the mitt box: a catcher's mitt set for a pitch sits above
# the plate and within a couple of plate widths of it laterally. A box outside
# that is on something else — the hitter's shin guard, the umpire's gear, a
# fielder — and is dropped rather than averaged in.
#
# The bounds are deliberately much wider than any real target (a target is under
# one plate width off centre) so that the guard removes wrong objects without
# clipping the signal. How often it fires is reported, because a guard that fires
# often is telling you the detector is unreliable rather than saving you.
MAX_LATERAL_PLATE_WIDTHS = 2.0
MIN_HEIGHT_PLATE_WIDTHS = -0.5
MAX_HEIGHT_PLATE_WIDTHS = 4.0

# Minimum in-window frames carrying both a mitt and a plate before a per-pitch
# value is emitted.
#
# Derived from the noise floor rather than picked: the within-pitch interdecile
# spread of lateral offset is 0.12-0.34 plate widths, so the standard error of a
# per-pitch median over n frames is about (0.34 / 2.56) / sqrt(n). At n = 5 that
# is 0.059 plate widths, roughly a quarter of the ~0.23 between-pitch signal,
# which is the point at which the measurement can resolve the thing it is for.
# Below it the per-pitch value is dominated by which frames happened to detect.
MIN_MITT_FRAMES = 5

# Visibility threshold for the cue, in the same units as its own noise floor.
# A per-pitch value whose standard error exceeds this cannot support a claim
# about a group difference smaller than it.
LATERAL_VISIBILITY_PLATE_WIDTHS = 0.06


@dataclass
class MittTarget:
    """
    Per-pitch pre-pitch glove target, or an explicit refusal.

    Every field is None when the target could not be measured, and ``reason``
    says which stage refused. There is no fallback to a nearby frame, to the
    out-of-window mitt, or to the previous pitch.
    """

    # Median lateral offset of the mitt from the plate centre, in plate widths,
    # positive toward increasing image x. Camera frame, not inside/outside.
    lateral: float | None
    # Median height of the mitt above the plate centre, in plate widths.
    height: float | None
    # Interdecile spread of the lateral offset across the measured frames: how
    # much the target drifts once it is set.
    lateral_drift: float | None
    # Difference between the last third and the first third of the measured
    # frames. Signed, so a target that is walked in one direction is separable
    # from one that jitters. Threshold-free by construction.
    lateral_late_minus_early: float | None
    # Standard error of ``lateral``, so a reader can compare it against
    # LATERAL_VISIBILITY_PLATE_WIDTHS without recomputing anything.
    lateral_se: float | None
    n_frames: int
    n_window_frames: int
    n_dropped_implausible: int
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _nan_target(reason: str, n_window: int = 0, n_dropped: int = 0) -> MittTarget:
    return MittTarget(None, None, None, None, None, 0, n_window, n_dropped, reason)


def mitt_target(frames: list[dict], lo: int, hi: int) -> MittTarget:
    """
    Per-pitch glove target from per-frame detector output.

    ``frames`` is a list of {"frame": int, "mitt": {...} | None, "plate": {...}
    | None} where the box dicts carry normalised ``cx``, ``cy``, ``bw`` and
    ``conf``. ``lo`` and ``hi`` bound the actionable span, half-open.

    Both boxes must come from the SAME frame. Pairing a mitt with a plate
    measured elsewhere in the clip would reintroduce camera motion into a
    quantity whose whole purpose is to be free of it.
    """
    inw = [f for f in frames if lo <= f["frame"] < hi]
    if not inw:
        return _nan_target("no_window_frames")

    lat: list[float] = []
    hgt: list[float] = []
    dropped = 0
    for f in inw:
        m, p = f.get("mitt"), f.get("plate")
        if not m or not p:
            continue
        if m["conf"] < MITT_CONF or p["conf"] < PLATE_CONF:
            continue
        pw = p.get("bw") or 0.0
        if pw <= 1e-9:
            continue
        dx = (m["cx"] - p["cx"]) / pw
        # Image y grows downward, so plate minus mitt is height above the plate.
        dy = (p["cy"] - m["cy"]) / pw
        if abs(dx) > MAX_LATERAL_PLATE_WIDTHS or not (MIN_HEIGHT_PLATE_WIDTHS <= dy <= MAX_HEIGHT_PLATE_WIDTHS):
            dropped += 1
            continue
        lat.append(float(dx))
        hgt.append(float(dy))

    if len(lat) < MIN_MITT_FRAMES:
        return _nan_target("too_few_mitt_frames", len(inw), dropped)

    a = np.asarray(lat, dtype=float)
    inter = float(np.percentile(a, 90) - np.percentile(a, 10))
    third = max(1, len(a) // 3)
    early = float(np.median(a[:third]))
    late = float(np.median(a[-third:]))
    # Standard error of the median, via the interdecile range. Using the
    # interdecile rather than the standard deviation keeps a single badly-placed
    # box from inflating it, and 2.56 is the interdecile-to-sigma factor for a
    # normal.
    se = (inter / 2.56) / float(np.sqrt(len(a))) if inter > 0 else 0.0

    return MittTarget(
        lateral=round(float(np.median(a)), 5),
        height=round(float(np.median(hgt)), 5),
        lateral_drift=round(inter, 5),
        lateral_late_minus_early=round(late - early, 5),
        lateral_se=round(se, 5),
        n_frames=len(a),
        n_window_frames=len(inw),
        n_dropped_implausible=dropped,
        reason="measured",
    )


def clears_visibility(t: MittTarget) -> bool:
    """
    Whether this pitch's target is precise enough to contribute to a claim.

    Separate from ``mitt_target`` on purpose: the measurement records its own
    error and the gate is applied where the claim is made, so a reader can see
    both the value and the reason it was or was not used.
    """
    return (
        t.reason == "measured"
        and t.lateral_se is not None
        and t.lateral_se <= LATERAL_VISIBILITY_PLATE_WIDTHS
    )


# Cue names this module can produce, for wiring into discovery later. Kept
# separate from spot_diff.CUES until the localisation and the protocol run have
# both been signed off — a name in CUES is a name that can reach the board.
CMITT_CUES = (
    "cmitt_target_lateral_plate_widths",
    "cmitt_target_height_plate_widths",
    "cmitt_target_lateral_drift_plate_widths",
    "cmitt_target_lateral_late_minus_early",
)

CMITT_STATUS: dict[str, str] = {
    # measured: the quantity is what its name says and its noise floor is known.
    # unvalidated: no discovery or holdout has been run on it, because no arm in
    # the league pipeline is marked complete.
    "cmitt_target_lateral_plate_widths": "measured_unvalidated",
    "cmitt_target_height_plate_widths": "measured_unvalidated",
    "cmitt_target_lateral_drift_plate_widths": "measured_unvalidated",
    "cmitt_target_lateral_late_minus_early": "measured_unvalidated",
}

__all__ = [
    "CMITT_CUES",
    "CMITT_STATUS",
    "LATERAL_VISIBILITY_PLATE_WIDTHS",
    "MIN_MITT_FRAMES",
    "MITT_CONF",
    "MittTarget",
    "clears_visibility",
    "mitt_target",
]
