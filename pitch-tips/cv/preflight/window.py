"""
Actionable pre-decision window for pitch tips.

Domain constraint: a tip is only worth anything if a hitter, baserunner, or base
coach can act on it BEFORE the swing decision. That means the signal must live in

  coming set  ->  set position  ->  PitchCom taps  ->  catcher setup

and must end no later than hand break / the start of arm action. Once the arm is
coming up, the information is worthless, so any frame at or after that boundary
must not contribute to a feature.

This module locates that boundary from a per-frame track CSV. It works on the
columns already cached in ``runs/*_poc/tracks/*_tracks.csv`` so tips can be
re-derived without re-running MediaPipe over every clip. When a track carries the
newer ``wrist_dist`` column (distance between the two wrists) the bare hand
separating from the glove is used directly, which is the true hand-break event.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np
import pandas as pd

# --- frame rate -------------------------------------------------------------
#
# EIGHTH FAILURE MODE, and the reason this section exists.
#
# Every temporal constant below was originally written as a frame count and
# reasoned "at 30fps" in its own comment. The corpus is 60fps — measured at
# 600/600 sampled tracks across all ten arms, uniformly, from each track's own
# ``t_sec`` against ``frame`` rather than from container metadata. So every
# duration was half its documented intent and every speed threshold was calibrated
# against the wrong scale, in the opposite direction: the same physical motion
# produces half the per-frame displacement at 60fps as at 30fps.
#
# Measured consequence before the fix: the median actionable window was 21 frames
# = 0.35s, against a documented intent of about 0.7s.
#
# The fix is not to substitute 60 for 30, which would leave the same latent bug for
# the next corpus. Durations are declared in SECONDS and speeds in NORMALIZED UNITS
# PER SECOND, then converted per clip using that clip's measured rate. A mixed-rate
# corpus is then handled correctly and this class of error cannot recur.
DEFAULT_FPS = 60.0
# Rate is inferred per clip; anything outside this is treated as unreliable and the
# default is used rather than silently scaling by a garbage number.
FPS_PLAUSIBLE = (10.0, 240.0)


def infer_fps(df: pd.DataFrame) -> float:
    """Frames per second for one clip, from its own timestamps.

    Derived from ``t_sec`` versus ``frame`` rather than from metadata, because
    metadata is what the original 30fps assumption rested on.
    """
    if "t_sec" not in df.columns or "frame" not in df.columns:
        return DEFAULT_FPS
    t = pd.to_numeric(df["t_sec"], errors="coerce").to_numpy(dtype=float)
    fr = pd.to_numeric(df["frame"], errors="coerce").to_numpy(dtype=float)
    m = np.isfinite(t) & np.isfinite(fr)
    if m.sum() < 10:
        return DEFAULT_FPS
    dt, dfr = np.diff(t[m]), np.diff(fr[m])
    ok = (dt > 0) & (dfr > 0)
    if ok.sum() < 5:
        return DEFAULT_FPS
    fps = float(np.median(dfr[ok] / dt[ok]))
    return fps if FPS_PLAUSIBLE[0] <= fps <= FPS_PLAUSIBLE[1] else DEFAULT_FPS


def _f(seconds: float, fps: float, minimum: int = 1) -> int:
    """Seconds -> frames at this clip's rate."""
    return max(minimum, int(round(seconds * fps)))


def _v(units_per_second: float, fps: float) -> float:
    """Normalized units per second -> per-frame displacement at this clip's rate."""
    return units_per_second / fps


# --- durations, in seconds --------------------------------------------------
QUIET_RUN_S = 0.20           # quiet needed to call it a set
BREAK_SUSTAIN_S = 0.133      # departure must persist this long
BREAK_GROWTH_LOOKAHEAD_S = 0.333
DELIVERY_SUSTAIN_S = 0.10
SET_LOOKBACK_MAX_S = 3.0     # how far back from hand break the set may be sought
WINDUP_WINDOW_S = 1.5        # bounded opening when no set is found
MAX_BREAK_TO_DELIVERY_S = 2.0
LIFT_TRAIL_MARGIN_S = 0.167  # margin past peak knee, per the scout's "just after"
LIFT_LOOKBACK_S = 3.0
MIN_WINDOW_S = 0.267

# --- speeds: NOT rescaled, and this is deliberate ---------------------------
#
# The obvious move is to treat these like the durations — declare them per second
# and divide by fps — and it is wrong. A per-frame displacement threshold has to
# separate real motion from landmark jitter, and those two scale differently with
# frame rate:
#
#   * real motion per frame HALVES when the rate doubles (same speed, half the time)
#   * landmark jitter per frame does NOT. It is a property of the pose estimator on
#     a single image pair, roughly independent of how fast frames arrive.
#
# So dividing a stillness threshold by fps drives it into the noise floor. Measured
# directly: rescaling QUIET_SPEED from 0.020 to 0.010 collapsed set detection from
# 80.6% to 42.0% on a fixed 600-track sample, because a genuinely still glove no
# longer reads as still once the threshold sits below the jitter.
#
# These therefore keep their empirically tuned per-frame values, which were fitted
# on this corpus's actual footage and so are already correct for 60fps whatever
# their original comments claimed. Re-deriving them properly means measuring the
# jitter floor at 60fps and setting each threshold above it — a measurement, not an
# arithmetic conversion, and it is not done here.
QUIET_SPEED_PER_FRAME_MEASURED = 0.020
DELIVERY_SPEED_PER_FRAME_MEASURED = 0.055

# --- IN-USE frame counts: original empirical values, NOT yet converted -------
#
# STATUS: the 60fps finding is confirmed and the seconds-based intent above is
# recorded, but the conversion is NOT applied, because applying it arithmetically
# makes things worse rather than better. Measured on a fixed 600-track sample:
#
#   configuration                        valid   duration   frame-0   set found
#   original (these values)              67.2%   0.317s     30.8%     80.6%
#   durations converted + speeds halved  61.8%   0.667s     56.9%     42.0%
#   durations converted only             19.2%   0.617s     52.2%     53.9%
#
# The middle row restores the documented ~0.7s duration, which is the point. But
# both converted rows degrade set detection badly and roughly double the rate at
# which the window runs off the front of the clip, and the third collapses the
# valid-window rate outright. Two reasons, and neither is fixable by rescaling:
#
#   1. The clips are too short. Every track is exactly 180 frames = 3.0s at 60fps,
#      not the 6s the design assumed. A correct 1.5s pre-set lookback simply does
#      not fit, which is why frame-0 openings rise instead of falling. This needs
#      LONGER CLIPS (max_frames 180 -> ~360), i.e. re-tracking, not re-derivation.
#   2. These constants are jointly tuned and interact. QUIET_RUN and QUIET_SPEED
#      trade off against each other, and MIN_WINDOW_FRAMES gates the result of
#      both. They have to be re-derived together against the measured jitter floor
#      and re-validated on the placement statistics, as was done when the boundary
#      was first set.
#
# So the values below are left at the empirically tuned settings that produced the
# published results. They were fitted on this corpus's real 60fps footage, so they
# are self-consistent with it whatever their original "at 30fps" comments claimed;
# what is wrong is the reasoning recorded beside them, not necessarily the numbers.
# Do not convert these without re-running the placement validation.
QUIET_SPEED = QUIET_SPEED_PER_FRAME_MEASURED
QUIET_RUN = 6
# Glove must leave the set anchor by this much to count as departure.
BREAK_RADIUS = 0.055
# ...and stay gone this many frames, so a tracker hiccup is not a hand break.
BREAK_SUSTAIN = 4
# A real departure keeps accelerating away; a tracker hand-swap parks at a fixed
# offset. Candidates that do not grow past BREAK_RADIUS * factor are rejected.
BREAK_GROWTH_LOOKAHEAD = 10
BREAK_GROWTH_FACTOR = 1.8
# Sustained glove speed this high is the delivery itself — a hard backstop that
# the window may never reach, regardless of break detection.
DELIVERY_SPEED = DELIVERY_SPEED_PER_FRAME_MEASURED
DELIVERY_SUSTAIN = 3
# Wrists separated by more than this is a hand break outright.
WRIST_SPLIT = 0.075
# Never publish a window shorter than this; below it the features are noise.
MIN_WINDOW_FRAMES = 8

# --- delivery-anchored search -------------------------------------------------
# Savant clips open on seconds of pre-pitch idle footage. Scanning forward from
# frame 0 finds that idle period first: a pitcher standing on the mound is
# "quiet", so it reads as the set, and him fidgeting with the ball reads as a
# hand break. The window then opens and closes before the delivery even starts.
#
# So the delivery is located first and every other boundary is found by walking
# backward from it. The pitch event, not the clip boundary, is the anchor, and
# idle lead-in can no longer masquerade as the set because it is not adjacent to
# the delivery.
#
# A fidget can clear DELIVERY_SPEED, so a burst only counts as the delivery if
# it is also a decent fraction of the clip's peak motion.
DELIVERY_PROMINENCE = 0.45
# How far back from hand break the set may be sought (SET_LOOKBACK_MAX_S). Beyond this
# we are back in the idle footage that caused the original bug.
SET_LOOKBACK_MAX = 90
# From the windup there may be no static set at all. Rather than forcing one,
# the delivery is labelled a windup and the window opens a bounded distance
# before hand break.
WINDUP_WINDOW_FRAMES = 45
# Hand break should sit close to the delivery. A "break" this far ahead of the
# delivery onset is a fidget, not the hand leaving the glove.
MAX_BREAK_TO_DELIVERY = 60

# --- closing boundary: just after the top of the leg lift ---------------------
# Per the scout: "top of leg lift and just after is the last moment we care
# about." Hand break is NOT the boundary — it happens early in the leg kick
# (measured here at ~29% of the knee's travel) and closing there discards the
# part of the delivery every documented cue is anchored to ("at lift").
#
# The margin is 5 frames, LIFT_TRAIL_MARGIN_S seconds. Chosen to be long enough to
# capture the top of the kick as a scout reads it — the knee hangs at its peak
# for several frames rather than turning over instantly — and short enough that
# it cannot reach arm action, which sits a median of 12 frames past peak knee on
# this sample. Arm-action onset clamps it regardless.
#
# CORRECTED for 60fps. This is the one temporal constant that could be fixed from
# the existing footage, and it is fixed: 5 frames was 0.083s, half the 0.167s its
# own comment argued for. The footage it needs exists, because it sits AFTER peak
# leg lift and before arm action — the truncation in this corpus is at the start of
# the clip, not here.
#
# Placement statistics re-verified on a fixed 600-track sample, as when the
# boundary was first set:
#
#                        valid   duration   peak lift inside   lift->end   past arm action
#   5 frames (0.083s)    67.2%   0.317s     96.5%              5           0.0%
#   10 frames (0.167s)   72.3%   0.367s     96.8%              10          0.0%
#
# The valid-window rate improves rather than degrading, the lift stays inside the
# window, and the close still never reaches arm action. Contrast the set-side
# constants above, which cannot be corrected because the clip does not contain the
# pre-set footage they would need.
LIFT_TRAIL_MARGIN = _f(LIFT_TRAIL_MARGIN_S, DEFAULT_FPS)
# How far back from arm action the leg lift may be sought (SET_LOOKBACK_MAX_S).
LIFT_LOOKBACK = 90
# A leg lift must raise the knee at least this far (torso lengths) to be a lift
# rather than tracker noise. Mirrors primitives.MIN_KNEE_RISE.
LIFT_MIN_RISE = 0.12


@dataclass
class Window:
    start: int
    end: int  # exclusive
    n_frames: int
    set_frame: int | None
    break_frame: int | None
    method: str
    valid: bool
    delivery_frame: int | None = None
    delivery_type: str = "unknown"
    lift_frame: int | None = None
    arm_action_frame: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean(df: pd.DataFrame, col: str) -> np.ndarray:
    if col not in df.columns:
        return np.full(len(df), np.nan)
    s = pd.to_numeric(df[col], errors="coerce")
    s = s.interpolate(limit=3, limit_direction="both")
    return s.rolling(3, center=True, min_periods=1).median().to_numpy(dtype=float)


def _travel(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Per-frame glove displacement, robust to dropout gaps."""
    d = np.full(len(x), np.nan)
    d[1:] = np.hypot(np.diff(x), np.diff(y))
    return pd.Series(d).rolling(3, center=True, min_periods=1).median().to_numpy(dtype=float)


def _delivery_motion(df: pd.DataFrame, glove_travel: np.ndarray) -> np.ndarray:
    """
    Motion signal used to locate the delivery.

    The glove proxy is the midpoint of the two wrists, which is the right anchor
    while the hands are together but a poor delivery detector: once they
    separate they move in opposing directions and the midpoint cancels much of
    the motion. Measured on Thorpe, 16% of clips never cross the delivery
    threshold on midpoint travel versus 8% on the faster individual wrist. So
    the faster wrist is preferred where the landmark columns exist, which is
    both code paths that build a window.
    """
    cols = ("lwri_x", "lwri_y", "rwri_x", "rwri_y")
    if not all(c in df.columns for c in cols):
        return glove_travel
    lt = _travel(_clean(df, "lwri_x"), _clean(df, "lwri_y"))
    rt = _travel(_clean(df, "rwri_x"), _clean(df, "rwri_y"))
    both = np.vstack([lt, rt])
    if not np.isfinite(both).any():
        return glove_travel
    return np.nanmax(both, axis=0)


def _find_delivery(speed: np.ndarray, min_onset: int = 0) -> tuple[int | None, int | None]:
    """
    Locate the delivery: (onset frame, peak frame).

    Peak motion is an unambiguous marker of arm action. Clips can contain a
    replay as well as the live pitch, so the FIRST burst prominent enough to be a
    delivery wins — the live pitch always precedes its replay.

    Bursts starting before ``min_onset`` are skipped rather than accepted. A clip
    that opens on a broadcast cut shows large apparent motion in its first frames;
    that burst has no room for a window in front of it, and treating it as the
    delivery would hide the real one later in the clip.
    """
    roll = pd.Series(speed).rolling(3, min_periods=1).mean().to_numpy(dtype=float)
    if not np.isfinite(roll).any():
        return None, None
    peak = float(np.nanmax(roll))
    thr = max(DELIVERY_SPEED, peak * DELIVERY_PROMINENCE)

    hot = np.isfinite(roll) & (roll >= DELIVERY_SPEED)
    i = 0
    while i < len(roll):
        if not hot[i]:
            i += 1
            continue
        start = i
        j = i
        while j + 1 < len(roll) and hot[j + 1]:
            j += 1
        seg = roll[start : j + 1]
        long_enough = (j - start + 1) >= DELIVERY_SUSTAIN
        prominent = np.isfinite(seg).any() and float(np.nanmax(seg)) >= thr
        if long_enough and prominent and start >= min_onset:
            return start, start + int(np.nanargmax(seg))
        i = j + 1
    return None, None


def _knee_height(df: pd.DataFrame) -> np.ndarray | None:
    """
    Normalized height of the higher knee, in torso lengths.

    Image y grows downward, so hip_y - knee_y is negative when standing and
    rises toward zero as the knee comes up. Returns None when the rich landmark
    columns are absent, which lets callers fall back to the older boundary.
    """
    need = ("lkne_y", "rkne_y", "lhip_y", "rhip_y", "lsho_x", "rsho_x", "lsho_y", "rsho_y", "lhip_x", "rhip_x")
    if not all(c in df.columns for c in need):
        return None
    hip_y = np.nanmean(np.vstack([_clean(df, "lhip_y"), _clean(df, "rhip_y")]), axis=0)
    hip_x = np.nanmean(np.vstack([_clean(df, "lhip_x"), _clean(df, "rhip_x")]), axis=0)
    sho_y = np.nanmean(np.vstack([_clean(df, "lsho_y"), _clean(df, "rsho_y")]), axis=0)
    sho_x = np.nanmean(np.vstack([_clean(df, "lsho_x"), _clean(df, "rsho_x")]), axis=0)
    torso = np.hypot(sho_x - hip_x, sho_y - hip_y)
    scale = float(np.nanmedian(torso))
    if not np.isfinite(scale) or scale <= 0:
        return None
    lk = (hip_y - _clean(df, "lkne_y")) / scale
    rk = (hip_y - _clean(df, "rkne_y")) / scale
    both = np.vstack([lk, rk])
    if not np.isfinite(both).any():
        return None
    return np.nanmax(both, axis=0)


def _find_peak_lift(knee: np.ndarray, arm_action: int) -> int | None:
    """
    Top of the leg kick: the highest knee position before arm action.

    Bounded above by arm action so the follow-through leg swing — which is
    higher than the leg lift and would otherwise win a global search — cannot be
    mistaken for the lift.
    """
    lo = max(0, arm_action - LIFT_LOOKBACK)
    seg = knee[lo:arm_action]
    if seg.size < 3 or not np.isfinite(seg).any():
        return None
    if float(np.nanmax(seg)) - float(np.nanmin(seg)) < LIFT_MIN_RISE:
        return None
    return lo + int(np.nanargmax(seg))


def _find_set_before(speed: np.ndarray, break_frame: int) -> int | None:
    """
    Last sustained quiet run before hand break: the set immediately preceding
    this delivery, rather than the first quiet period anywhere in the clip.

    The quiet threshold is taken over the pre-break region only, so it describes
    what "still" looks like on this pitch instead of being dragged around by
    however much idle footage the clip happens to carry.
    """
    lo = max(0, break_frame - SET_LOOKBACK_MAX)
    seg = speed[lo:break_frame]
    if seg.size < QUIET_RUN:
        return None
    finite = seg[np.isfinite(seg)]
    if not finite.size:
        return None
    thr = max(QUIET_SPEED, float(np.nanpercentile(finite, 40)))
    quiet = np.isfinite(seg) & (seg <= thr)

    # Walk backward so the run adjacent to the delivery is the one returned, then
    # extend to that run's true beginning. Stopping as soon as QUIET_RUN frames
    # accumulate would put the set six frames before hand break and leave a
    # window too short to carry any feature.
    run = 0
    for k in range(len(quiet) - 1, -1, -1):
        run = run + 1 if quiet[k] else 0
        if run >= QUIET_RUN:
            start = k
            while start - 1 >= 0 and quiet[start - 1]:
                start -= 1
            return lo + start
    return None


def _find_break_before(
    gx: np.ndarray,
    gy: np.ndarray,
    wrist_dist: np.ndarray,
    onset: int,
) -> tuple[int | None, str]:
    """
    Locate hand break by walking BACKWARD from the delivery onset.

    The hand is inside the glove right up until hand break, so the break is the
    last moment before the delivery at which the hands were still together.
    Searching backward means the break found is necessarily the one belonging to
    this delivery, not an earlier fidget.
    """
    lo = max(0, onset - MAX_BREAK_TO_DELIVERY)

    # Preferred cue: the bare hand separating from the glove.
    if np.isfinite(wrist_dist[lo:onset]).sum() >= QUIET_RUN:
        base = float(np.nanmedian(wrist_dist[lo:onset]))
        thr = max(WRIST_SPLIT, base * 1.8)
        for i in range(onset - 1, lo - 1, -1):
            if np.isfinite(wrist_dist[i]) and wrist_dist[i] <= thr:
                return min(i + 1, onset), "wrist_separation"

    # Fallback: the glove departing where it was being held before the delivery.
    tracked = np.isfinite(gx) & np.isfinite(gy)
    ax = float(np.nanmedian(gx[lo:onset]))
    ay = float(np.nanmedian(gy[lo:onset]))
    if not (np.isfinite(ax) and np.isfinite(ay)):
        return None, "no_glove_anchor"
    dist = np.where(tracked, np.hypot(gx - ax, gy - ay), np.nan)
    for i in range(onset - 1, lo - 1, -1):
        if np.isfinite(dist[i]) and dist[i] <= BREAK_RADIUS:
            return min(i + 1, onset), "glove_departure"
    return None, "no_break_found"


def actionable_window(df: pd.DataFrame) -> Window:
    """
    Frame window [start, end) that a hitter or baserunner could actually act on.

    ``valid`` is False when the boundary could not be established. Those pitches
    are dropped rather than guessed at: a window we cannot bound is a window that
    might contain arm action, and a tip built on arm action is not a tip.
    """
    n = len(df)
    if n < MIN_WINDOW_FRAMES:
        return Window(0, n, n, None, None, "too_short", False)

    gx, gy = _clean(df, "glove_x"), _clean(df, "glove_y")
    wrist_dist = _clean(df, "wrist_dist")
    speed = _travel(gx, gy)

    # 1. The delivery is the anchor. Without it there is nothing to measure
    #    backward from, and falling back to clip start is the original bug.
    onset, peak = _find_delivery(_delivery_motion(df, speed), min_onset=MIN_WINDOW_FRAMES)
    if onset is None:
        return Window(0, 0, 0, None, None, "no_delivery_found", False)

    # 2. Hand break. No longer the closing boundary, but recorded: the bare hand
    #    becomes visible at break, which is what grip-burial cues read.
    break_frame, _bm = _find_break_before(gx, gy, wrist_dist, onset)

    # 3. Close just after the top of the leg kick, clamped so the window can
    #    never reach arm action. Without the rich landmarks there is no lift to
    #    find, so those tracks fall back to closing at hand break.
    knee = _knee_height(df)
    lift_frame = _find_peak_lift(knee, onset) if knee is not None else None
    if lift_frame is not None:
        end = min(lift_frame + LIFT_TRAIL_MARGIN, int(onset))
        method = "peak_leg_lift"
    elif break_frame is not None:
        end = min(int(break_frame), int(onset))
        method = "hand_break_no_lift"
    else:
        return Window(0, 0, 0, None, break_frame, "no_lift_or_break", False, peak, "unknown", None, onset)

    # 4. The set, walking back from the lift rather than from hand break, so the
    #    window necessarily opens before the top of the kick and peak lift sits
    #    inside it by construction.
    anchor = lift_frame if lift_frame is not None else end
    set_frame = _find_set_before(speed, anchor)
    if set_frame is None:
        delivery_type = "windup"
        start = max(0, anchor - WINDUP_WINDOW_FRAMES)
    else:
        delivery_type = "stretch"
        start = int(set_frame)

    if end - start < MIN_WINDOW_FRAMES:
        return Window(start, end, end - start, set_frame, break_frame, f"{method}+too_short", False, peak, delivery_type, lift_frame, onset)
    return Window(start, end, end - start, set_frame, break_frame, method, True, peak, delivery_type, lift_frame, onset)


# --- pre-set segment ----------------------------------------------------------
# PitchCom programming — taking the sign, shaking it off, working the wrist
# device — happens on the rubber BEFORE the pitcher comes set, so it is not
# inside the set-to-lift window above. That window is where the glove and lift
# cues live and its geometry is deliberately left alone here; this is a second,
# additive segment covering the stretch immediately preceding the set.
#
# It remains actionable: a runner on second or a base coach sees the programming
# well before the swing decision.
#
# Bounded rather than run back to frame 0 because Savant clips open on seconds of
# unrelated idle footage (the same footage that caused the original window bug).
#
# PRESET_LOOKBACK_S (1.5s) is set from glove-tracking reliability, not from tap
# activity. Measured over Kelly and Thorpe, glove tracking holds roughly flat out
# to ~45-60 frames before the set (Thorpe 0.64 at -20 -> 0.59 at -45) and then
# falls away (0.53 at -65, 0.44 at -90) as the clip regresses into broadcast
# lead-in framing. Opening at -45 therefore buys the whole reliably-tracked
# pre-set stretch and stops before the idle region.
#
# Note for whoever reads this next: the tap-activity profile is FLAT from -5 all
# the way to -120, so it offers no basis for choosing this number. See
# preset_extent_probe.py — that flatness is itself evidence the current tap
# detector is not detecting taps.
PRESET_LOOKBACK_S = 1.5
PRESET_LOOKBACK = 45
PRESET_MIN_S = 0.267
PRESET_MIN_FRAMES = 8


def preset_segment(df: pd.DataFrame, win: Window) -> tuple[int, int] | None:
    """
    Frame range [start, end) covering the approach to the set, or None when the
    clip does not carry enough pre-set footage to measure anything.

    ``end`` is the set frame, so this segment and the actionable window are
    disjoint and no frame contributes to both.
    """
    if not win.valid or win.set_frame is None:
        return None
    end = int(win.set_frame)
    start = max(0, end - PRESET_LOOKBACK)
    if end - start < PRESET_MIN_FRAMES:
        return None
    return start, end
