"""
Discrete PitchCom tap detection from wrist landmarks.

Rebuild of the retracted ``pitchcom_tap_*`` family. The detector it replaces read
local maxima in GLOVE-CENTROID displacement, which is the wrong object at the
wrong scale: a PitchCom press is a thumb movement of roughly a centimetre on a
forearm device and moves the glove as a whole not at all.

This version differs on four points, each of which was a named defect before:

  1. SIGNAL. Wrist landmarks (``lwri_*`` / ``rwri_*``) from the 72-column tracks,
     not the glove centroid. This is the finest granularity the persisted tracks
     carry — MediaPipe pose gives no finger landmarks here — which bounds what
     any detector on this data can see. See ``noise_floor`` below.
  2. SCALE. Threshold in torso lengths, derived from the physical size of the
     movement and checked against the landmark's own measured noise floor, rather
     than a percentile of the segment under test. A percentile threshold finds
     "peaks" in any segment however still, which is why the old one fired
     uniformly through broadcast idle footage.
  3. DROPOUT. Frames where the landmark was not tracked, or whose visibility is
     below ``MIN_VIS``, are excluded rather than bridged. Bridging is what made a
     multi-frame tracking gap read as one frame of enormous speed; that
     accounted for 17-43% of the old detections.
  4. SHAPE. A tap must be an out-and-back excursion: the wrist departs a local
     baseline, peaks, and RETURNS toward that baseline within a short span. A
     bare local maximum in speed — the old criterion — is satisfied by any
     wobble, including monotonic drift and tracking jitter.

VERDICT: THIS DETECTOR FAILS ITS OWN VALIDATION GATE AND IS NOT WIRED INTO THE
FEATURE PIPELINE. It is kept because the measurement that killed it is the useful
artefact, and because the next person to propose a tap feature should have to
clear the same bar.

Measured on Drew Thorpe's 72-column tracks:

  * NOISE FLOOR — FAIL, and decisively. The wrist landmark's own frame-to-frame
    jitter, measured while the pitcher is holding still in the set, is 0.116
    torso lengths per frame. The largest plausible tap excursion is 0.060. The
    measurement noise is ~1.9x LARGER than the signal. No threshold separates
    the two, because the problem is not where the threshold sits.
  * ACTIVITY PROFILE — FAIL. Detection rate before the set (0.0080/frame) is
    actually LOWER than in broadcast idle footage 75-120 frames earlier
    (0.0097/frame), a contrast of 0.83x against a required 1.5x. Detections do
    not localise to sign-taking.
  * PHASE SHUFFLE — passes, at 78x, and this is the instructive part: passing it
    is necessary but NOT sufficient. The detector responds strongly to temporal
    structure, but the structure it finds is the smoothness of the wrist
    trajectory as the arm moves, which shuffling destroys. Responding to real
    motion is not the same as responding to taps.

Conclusion: a thumb press on a forearm device is an ARTICULATION cue, and
articulation cues do not survive Savant CF broadcast resolution — the same
boundary already documented for grip and finger curl. The persisted tracks carry
no finger landmarks, so the wrist is the finest granularity available, and the
wrist does not move enough. Fixing this needs different footage, not different
code.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# --- physical calibration -----------------------------------------------------
# A PitchCom press is a thumb/finger action. Published device dimensions and
# normal use put the thumb excursion at roughly 1-2 cm. The wrist itself barely
# moves during a press; being deliberately generous to the detector, allow that
# working the device rocks the wrist/forearm by up to ~3 cm.
TAP_TRAVEL_CM_MIN = 1.0
TAP_TRAVEL_CM_MAX = 3.0
# Shoulder-to-hip on an adult male pitcher, the normalising length used by every
# other feature in the system.
TORSO_CM = 50.0
# So a tap should displace the wrist by this much, in torso lengths.
TAP_AMPLITUDE_MIN = TAP_TRAVEL_CM_MIN / TORSO_CM  # 0.020
TAP_AMPLITUDE_MAX = TAP_TRAVEL_CM_MAX / TORSO_CM  # 0.060

# --- shape --------------------------------------------------------------------
# A press and release is fast. At 30 fps the whole excursion should complete
# within about half a second; anything slower is postural drift, not a tap.
TAP_MAX_DURATION = 8
# The wrist must come back at least this fraction of the way to baseline for the
# excursion to be an out-and-back rather than a step change.
TAP_RETURN_FRACTION = 0.5
# Local baseline is the median over this many frames around the candidate.
BASELINE_HALFWIDTH = 9
# Minimum separation between accepted taps, so one excursion is not counted
# twice off adjacent frames.
TAP_REFRACTORY = 4

# --- tracking quality ---------------------------------------------------------
# MediaPipe visibility below this is not a measurement.
MIN_VIS = 0.5
# A candidate must sit in a run of consecutively tracked frames at least this
# long, so no detection can straddle a dropout.
MIN_CLEAN_RUN = 5


def torso_scale(df: pd.DataFrame) -> float:
    """Median shoulder-to-hip distance, the normalising length. NaN if absent."""
    need = ("lsho_x", "rsho_x", "lsho_y", "rsho_y", "lhip_x", "rhip_x", "lhip_y", "rhip_y")
    if not all(c in df.columns for c in need):
        return float("nan")

    def mid(a: str, b: str) -> np.ndarray:
        return np.nanmean(
            np.vstack(
                [
                    pd.to_numeric(df[a], errors="coerce").to_numpy(dtype=float),
                    pd.to_numeric(df[b], errors="coerce").to_numpy(dtype=float),
                ]
            ),
            axis=0,
        )

    with np.errstate(invalid="ignore"):
        t = np.hypot(mid("lsho_x", "rsho_x") - mid("lhip_x", "rhip_x"),
                     mid("lsho_y", "rsho_y") - mid("lhip_y", "rhip_y"))
    v = float(np.nanmedian(t))
    return v if np.isfinite(v) and v > 0 else float("nan")


def wrist_series(df: pd.DataFrame, side: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Torso-normalised wrist position and a per-frame tracked mask.

    Untracked and low-visibility frames are returned as NaN rather than
    interpolated. Interpolating here is exactly the defect that turned tracking
    gaps into detections.
    """
    n = len(df)
    cx, cy, cv = f"{side}wri_x", f"{side}wri_y", f"{side}wri_v"
    if cx not in df.columns or cy not in df.columns:
        nan = np.full(n, np.nan)
        return nan, nan, np.zeros(n, dtype=bool)
    x = pd.to_numeric(df[cx], errors="coerce").to_numpy(dtype=float)
    y = pd.to_numeric(df[cy], errors="coerce").to_numpy(dtype=float)
    vis = (
        pd.to_numeric(df[cv], errors="coerce").to_numpy(dtype=float)
        if cv in df.columns
        else np.ones(n)
    )
    scale = torso_scale(df)
    if not np.isfinite(scale):
        nan = np.full(n, np.nan)
        return nan, nan, np.zeros(n, dtype=bool)
    tracked = np.isfinite(x) & np.isfinite(y) & (np.nan_to_num(vis, nan=0.0) >= MIN_VIS)
    x = np.where(tracked, x / scale, np.nan)
    y = np.where(tracked, y / scale, np.nan)
    return x, y, tracked


def _clean_runs(tracked: np.ndarray) -> np.ndarray:
    """
    Mask of frames eligible to carry a detection.

    A frame qualifies only if it sits inside a tracked run of at least
    MIN_CLEAN_RUN frames AND is not within MIN_CLEAN_RUN frames of either end of
    that run. The margin matters: the first frame after a dropout is where the
    landmark reappears displaced, and without the margin that re-acquisition is
    measured against a baseline drawn entirely from the post-gap frames, so it
    looks exactly like a clean out-and-back excursion.
    """
    ok = np.zeros(len(tracked), dtype=bool)
    i = 0
    while i < len(tracked):
        if not tracked[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(tracked) and tracked[j + 1]:
            j += 1
        if (j - i + 1) >= MIN_CLEAN_RUN:
            lo, hi = i + MIN_CLEAN_RUN, j - MIN_CLEAN_RUN + 1
            if hi > lo:
                ok[lo:hi] = True
        i = j + 1
    return ok


def noise_floor(df: pd.DataFrame, lo: int, hi: int) -> float:
    """
    Measured jitter of the wrist landmark over a span where the pitcher is
    holding still, in torso lengths.

    This is the number that decides whether tap detection is physically possible
    on this footage at all: if the landmark's own frame-to-frame noise is
    comparable to TAP_AMPLITUDE_MAX, a real tap is not separable from jitter and
    no threshold choice can fix it.
    """
    vals = []
    for side in ("l", "r"):
        x, y, tracked = wrist_series(df, side)
        ok = _clean_runs(tracked)[lo:hi]
        xs, ys = x[lo:hi], y[lo:hi]
        if ok.sum() < MIN_CLEAN_RUN:
            continue
        d = np.hypot(np.diff(xs), np.diff(ys))
        m = ok[1:] & ok[:-1] & np.isfinite(d)
        if m.sum():
            vals.append(float(np.nanmedian(d[m])))
    return float(np.nanmedian(vals)) if vals else float("nan")


def detect_taps(df: pd.DataFrame, lo: int, hi: int) -> list[int]:
    """
    Frame indices of discrete out-and-back wrist excursions in [lo, hi).

    Returns absolute frame indices. Both wrists are searched and detections
    merged, since which hand works the device varies by pitcher and handedness.
    """
    hits: list[int] = []
    for side in ("l", "r"):
        x, y, tracked = wrist_series(df, side)
        ok = _clean_runs(tracked)
        for i in range(max(lo, 1), min(hi, len(df) - 1)):
            if not ok[i]:
                continue
            b0, b1 = max(0, i - BASELINE_HALFWIDTH), min(len(df), i + BASELINE_HALFWIDTH + 1)
            bx = np.nanmedian(np.where(ok[b0:b1], x[b0:b1], np.nan))
            by = np.nanmedian(np.where(ok[b0:b1], y[b0:b1], np.nan))
            if not (np.isfinite(bx) and np.isfinite(by)):
                continue
            amp = float(np.hypot(x[i] - bx, y[i] - by))
            # In-band amplitude: big enough to be a press, small enough not to be
            # the arm moving. An upper bound matters — without it the delivery
            # itself is the largest "tap" in every clip.
            if not (TAP_AMPLITUDE_MIN <= amp <= TAP_AMPLITUDE_MAX):
                continue
            # Local peak of the excursion.
            if np.isfinite(x[i - 1]) and float(np.hypot(x[i - 1] - bx, y[i - 1] - by)) > amp:
                continue
            if np.isfinite(x[i + 1]) and float(np.hypot(x[i + 1] - bx, y[i + 1] - by)) > amp:
                continue
            # Out-and-back: must return toward baseline within TAP_MAX_DURATION.
            returned = False
            for k in range(i + 1, min(i + TAP_MAX_DURATION + 1, len(df))):
                if not ok[k]:
                    break
                if float(np.hypot(x[k] - bx, y[k] - by)) <= amp * (1.0 - TAP_RETURN_FRACTION):
                    returned = True
                    break
            if returned:
                hits.append(i)

    hits.sort()
    out: list[int] = []
    for i in hits:
        if not out or (i - out[-1]) >= TAP_REFRACTORY:
            out.append(i)
    return out


def tap_features(df: pd.DataFrame, lo: int, hi: int) -> dict[str, float]:
    """Tap summary over [lo, hi), or NaN when the span is not measurable."""
    taps = detect_taps(df, lo, hi)
    span = max((hi - lo) / 30.0, 1e-3)
    isi = np.diff(taps) if len(taps) >= 2 else np.array([])
    return {
        "tap_count": float(len(taps)),
        "tap_rate": len(taps) / span,
        "tap_mean_isi": float(np.mean(isi)) if len(isi) else float("nan"),
    }
