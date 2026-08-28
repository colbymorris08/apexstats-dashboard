"""
Validation gate for any PitchCom tap detector.

The retracted detector passed every statistical gate in the system while
measuring glove-motion variance rather than taps. What caught it was not a
significance test but two structural checks, and those are encoded here so no
future tap feature can be trusted without clearing them.

  PHASE SHUFFLE — real footage must yield meaningfully more detections than
  footage whose frame order has been shuffled. Shuffling destroys all temporal
  structure, so a genuine event detector must collapse on it. The old detector
  returned MORE detections on shuffled input, proving its output was a function
  of the amplitude distribution alone.

  ACTIVITY PROFILE — detections must concentrate near the set rather than firing
  uniformly back through broadcast lead-in footage. The old detector's rate was
  flat from 5 to 120 frames before the set, i.e. it fired just as often with the
  pitcher standing around off the rubber.

These are written to be FAILABLE. If a rebuilt detector cannot clear them the
correct action is to report that PitchCom is not resolvable at this resolution,
not to relax the checks. The synthetic tests below pin the detector's mechanics
(dropout exclusion, out-and-back shape, amplitude band) and always run; the
real-footage tests skip when the rich tracks are absent.

CURRENT STATE: the noise-floor and activity-profile checks FAIL on Savant CF
footage and are marked ``xfail(strict=True)``. That keeps the suite green over a
known, documented limitation while preserving the failure as a record — and
because the mark is strict, if a future detector or better footage makes either
check PASS, the suite goes red until someone removes the mark deliberately. The
one thing that must not happen is these checks quietly starting to pass.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cv.preflight import tap_detect  # noqa: E402
from cv.preflight.tap_detect import (  # noqa: E402
    TAP_AMPLITUDE_MAX,
    TAP_AMPLITUDE_MIN,
    detect_taps,
    noise_floor,
)
from cv.preflight.window import actionable_window  # noqa: E402

RICH_TRACKS = ROOT / "runs" / "drew_thorpe_rich_poc" / "tracks"
# A detector is credible only if real footage beats shuffled footage by a clear
# margin. 1.5x is a low bar deliberately: the point is to catch a detector with
# NO temporal selectivity, not to certify a good one.
MIN_SHUFFLE_RATIO = 1.5
# The pre-set region must show a detection rate at least this multiple of the
# far-idle region, or the detector is not localising to sign-taking.
MIN_PROFILE_CONTRAST = 1.5


# ---------------------------------------------------------------- synthetic ---

def _frame(n: int, wrist_xy, vis: float = 1.0) -> pd.DataFrame:
    """Minimal rich-format track: static torso, scripted wrist path."""
    d = {
        "frame": np.arange(n),
        "lsho_x": np.full(n, 0.40), "lsho_y": np.full(n, 0.30),
        "rsho_x": np.full(n, 0.60), "rsho_y": np.full(n, 0.30),
        "lhip_x": np.full(n, 0.42), "lhip_y": np.full(n, 0.50),
        "rhip_x": np.full(n, 0.58), "rhip_y": np.full(n, 0.50),
        "rwri_x": wrist_xy[0], "rwri_y": wrist_xy[1], "rwri_v": np.full(n, vis),
        "lwri_x": np.full(n, np.nan), "lwri_y": np.full(n, np.nan), "lwri_v": np.zeros(n),
    }
    return pd.DataFrame(d)


def _torso(df: pd.DataFrame) -> float:
    return tap_detect.torso_scale(df)


def test_detects_a_clean_out_and_back_tap():
    n = 40
    df0 = _frame(n, (np.full(n, 0.5), np.full(n, 0.5)))
    t = _torso(df0)
    amp = (TAP_AMPLITUDE_MIN + TAP_AMPLITUDE_MAX) / 2 * t
    y = np.full(n, 0.5)
    y[20] = 0.5 + amp          # out
    y[21] = 0.5 + amp * 0.1    # and back
    df = _frame(n, (np.full(n, 0.5), y))
    assert 20 in detect_taps(df, 0, n)


def test_rejects_a_step_change_that_never_returns():
    """A wrist that moves and stays moved is repositioning, not tapping."""
    n = 40
    t = _torso(_frame(n, (np.full(n, 0.5), np.full(n, 0.5))))
    amp = (TAP_AMPLITUDE_MIN + TAP_AMPLITUDE_MAX) / 2 * t
    y = np.full(n, 0.5)
    y[20:] = 0.5 + amp
    assert detect_taps(_frame(n, (np.full(n, 0.5), y)), 0, n) == []


def test_rejects_motion_far_above_the_tap_amplitude_band():
    """Arm action is enormous; it must not be the biggest tap in the clip."""
    n = 40
    t = _torso(_frame(n, (np.full(n, 0.5), np.full(n, 0.5))))
    y = np.full(n, 0.5)
    y[20] = 0.5 + TAP_AMPLITUDE_MAX * t * 5
    y[21] = 0.5
    assert detect_taps(_frame(n, (np.full(n, 0.5), y)), 0, n) == []


def test_dropout_reacquisition_is_not_a_tap():
    """
    The single largest source of false detections in the retracted version: the
    landmark vanishes, reappears displaced, and the jump reads as motion.
    """
    n = 40
    t = _torso(_frame(n, (np.full(n, 0.5), np.full(n, 0.5))))
    amp = (TAP_AMPLITUDE_MIN + TAP_AMPLITUDE_MAX) / 2 * t
    y = np.full(n, 0.5)
    x = np.full(n, 0.5)
    y[18:22] = np.nan  # lost
    x[18:22] = np.nan
    y[22] = 0.5 + amp  # reappears displaced, then settles
    y[23] = 0.5
    assert detect_taps(_frame(n, (x, y)), 0, n) == []


def test_low_visibility_frames_are_not_measurements():
    n = 40
    t = _torso(_frame(n, (np.full(n, 0.5), np.full(n, 0.5))))
    amp = (TAP_AMPLITUDE_MIN + TAP_AMPLITUDE_MAX) / 2 * t
    y = np.full(n, 0.5)
    y[20] = 0.5 + amp
    y[21] = 0.5
    assert detect_taps(_frame(n, (np.full(n, 0.5), y), vis=0.1), 0, n) == []


# -------------------------------------------------------------- real footage ---

def _rich_clips(limit: int = 120) -> list[pd.DataFrame]:
    if not RICH_TRACKS.is_dir():
        return []
    out = []
    for f in sorted(RICH_TRACKS.glob("*_tracks.csv"))[:limit]:
        d = pd.read_csv(f)
        if len(d) >= 60:
            out.append(d)
    return out


@pytest.fixture(scope="module")
def clips() -> list[pd.DataFrame]:
    c = _rich_clips()
    if not c:
        pytest.skip("no 72-column tracks available")
    return c


@pytest.mark.xfail(
    strict=True,
    reason=(
        "MEASURED LIMIT, not a bug: wrist landmark jitter on Savant CF is ~0.116 torso "
        "lengths/frame, about 1.9x the largest plausible tap (0.060). Taps are not "
        "separable from tracking noise on this footage. Remove this mark only with "
        "footage that closes the gap."
    ),
)
def test_landmark_noise_floor_is_below_tap_amplitude(clips):
    """
    Physical feasibility, measured rather than assumed.

    If the wrist landmark's own jitter while the pitcher holds still is as large
    as a tap, no threshold separates the two and the detector cannot work on this
    footage. Reported either way so the number is on the record.
    """
    floors = []
    for df in clips:
        win = actionable_window(df)
        if not win.valid or win.set_frame is None:
            continue
        nf = noise_floor(df, int(win.start), int(win.end))
        if np.isfinite(nf):
            floors.append(nf)
    if not floors:
        pytest.skip("no measurable still spans")
    med = float(np.median(floors))
    print(
        f"\nwrist landmark noise floor: median {med:.4f} torso lengths/frame "
        f"vs tap band {TAP_AMPLITUDE_MIN:.3f}-{TAP_AMPLITUDE_MAX:.3f} "
        f"(ratio to max tap amplitude: {med / TAP_AMPLITUDE_MAX:.2f}x)"
    )
    assert med < TAP_AMPLITUDE_MAX, (
        f"wrist landmark jitter ({med:.4f} torso/frame) is at or above the largest "
        f"plausible tap ({TAP_AMPLITUDE_MAX:.4f}); taps are not separable from "
        f"tracking noise on this footage"
    )


def test_phase_shuffle_real_beats_shuffled(clips):
    """Mandatory. A detector with no temporal selectivity fails here."""
    rng = np.random.default_rng(11)
    real = shuf = 0
    for df in clips:
        win = actionable_window(df)
        if not win.valid:
            continue
        lo, hi = 0, len(df)
        real += len(detect_taps(df, lo, hi))
        s = df.copy()
        order = rng.permutation(len(s))
        for c in ("lwri_x", "lwri_y", "lwri_v", "rwri_x", "rwri_y", "rwri_v"):
            if c in s.columns:
                s[c] = s[c].to_numpy()[order]
        shuf += len(detect_taps(s, lo, hi))
    ratio = real / shuf if shuf else float("inf")
    print(f"\nphase shuffle: real={real} shuffled={shuf} ratio={ratio:.2f}x "
          f"(need >= {MIN_SHUFFLE_RATIO}x)")
    assert real > 0, "detector found nothing on real footage"
    assert ratio >= MIN_SHUFFLE_RATIO, (
        f"real/shuffled = {ratio:.2f}x; detector is not responding to temporal "
        f"structure and is therefore not detecting discrete events"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "MEASURED LIMIT, not a bug: pre-set detection rate is 0.83x the broadcast-idle "
        "rate, i.e. detections do not localise to sign-taking. Follows from the noise "
        "floor above — what is being detected is wrist trajectory, not taps."
    ),
)
def test_activity_profile_is_not_flat(clips):
    """
    Mandatory. Detections must concentrate near the set, where programming
    happens, rather than firing uniformly through broadcast lead-in footage.
    """
    near = far = near_f = far_f = 0
    for df in clips:
        win = actionable_window(df)
        if not win.valid or win.set_frame is None:
            continue
        s = int(win.start)
        # near: the 45 frames before the set, where programming lives.
        # far: 75-120 frames before the set, broadcast lead-in.
        n_lo, n_hi = max(0, s - 45), s
        f_lo, f_hi = max(0, s - 120), max(0, s - 75)
        if n_hi - n_lo >= 10:
            near += len(detect_taps(df, n_lo, n_hi))
            near_f += n_hi - n_lo
        if f_hi - f_lo >= 10:
            far += len(detect_taps(df, f_lo, f_hi))
            far_f += f_hi - f_lo
    if not near_f or not far_f:
        pytest.skip("insufficient pre-set footage to build a profile")
    near_rate = near / near_f
    far_rate = far / far_f
    contrast = near_rate / far_rate if far_rate else float("inf")
    print(f"\nactivity profile: pre-set rate={near_rate:.4f}/frame "
          f"idle rate={far_rate:.4f}/frame contrast={contrast:.2f}x "
          f"(need >= {MIN_PROFILE_CONTRAST}x)")
    assert near > 0, "no detections in the pre-set region"
    assert contrast >= MIN_PROFILE_CONTRAST, (
        f"pre-set/idle detection rate = {contrast:.2f}x; the profile is flat, so "
        f"the detector fires as readily on broadcast idle footage as on sign-taking"
    )
