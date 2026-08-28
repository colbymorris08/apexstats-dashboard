"""
How the pitcher MOVES through the actionable window, rather than where he is at a point.

The gap this fills
------------------
Every cue in the audited 20-cue vocabulary is a scalar sampled at an anchor
frame: ``glove_height_at_lift``, ``glove_flare_at_lift``, ``stance_width_at_set``.
Point measurements at the set or at peak lift. Two pitches can arrive at an
identical glove position by visibly different paths, at different speeds, with
different tempo, and none of the existing cues can tell them apart.

That is untested rather than re-litigated. The one prior attempt at movement, the
sway family, was excluded on coverage (31.8%, capped by where the set falls inside
a fixed 180-frame render) and on lacking documentary support — not because
trajectory features were measured and failed.

Discipline
----------
Trajectory features can be generated endlessly and every one raises the FDR bar
for all the others, so this is a deliberately small set: ten features in four
groups, each with a stated reason to exist. Tempo is a classic scouted read and is
pure trajectory. Velocity profile, path shape and cross-landmark coordination are
the three ways a path can differ while its endpoints match.

Trajectory features are far more exposed to tracking dropout than point features:
a gap corrupts an entire path rather than one sample. So every feature here is
computed on a smoothed path behind a coverage guard, and returns NaN rather than
bridging a gap — a landmark that vanishes and reappears elsewhere would otherwise
read as a large, fast, tortuous movement.

Normalisation. Distances are in torso lengths, so a zoom change cannot become a
speed. Durations are in frames at a fixed 30 fps render. Shape features are ratios
and therefore already dimensionless, which is deliberate: it means they cannot be
re-expressions of the amplitude cues the existing vocabulary already covers.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preflight.primitives import (  # noqa: E402
    MAX_KNEE_RISE,
    MAX_TORSO,
    MIN_SET_TO_LIFT,
    MIN_TORSO,
    _col,
    _med,
    _mid,
    play_id_of,
    resolve_track_dir,
)
from preflight.window import actionable_window  # noqa: E402

# Path smoothing. Wider than the point features' 3-frame median because a
# trajectory integrates noise along its whole length: unsmoothed frame-to-frame
# path length on a pre-lift glove summed to double-digit torso lengths, which is
# physically impossible and is pure jitter accumulation.
PATH_SMOOTH = 5

# A path needs this fraction of its frames actually tracked, and this many frames,
# to be described at all. Stricter than the point features because a point cue
# needs one good frame and a path needs most of them.
MIN_PATH_COVERAGE = 0.70
MIN_PATH_FRAMES = 8

# Net displacement below this (torso lengths) makes a direction ratio meaningless:
# dividing path length by a near-zero net displacement produces an arbitrarily
# large "tortuosity" that is describing noise, not wandering.
MIN_NET_DISPLACEMENT = 0.03

# Speed below this per frame is inside the landmark jitter floor, so the timing of
# a "peak" that small is not a real event.
MIN_PEAK_SPEED = 0.004

# Correlation and lag need enough overlapping frames to mean anything.
MIN_CORR_FRAMES = 10
MAX_LAG = 10

TRAJECTORY_FEATURES = [
    # --- tempo: how long the movement takes and how it is distributed ---------
    "set_to_lift_frames",
    "knee_rise_duration_frac",
    "hold_at_top_frac",
    # --- velocity profile: speed through the window, not position at a point --
    "glove_speed_mean",
    "glove_speed_cv",
    "glove_peak_speed_timing",
    # --- path shape: how the glove got there ---------------------------------
    "glove_tortuosity",
    "glove_vertical_reversals",
    # --- coordination between body parts -------------------------------------
    "glove_knee_lag_frames",
    "hip_glove_x_coupling",
]

# One plain sentence per feature, describing what the code computes rather than
# what the name suggests. Written from the implementation.
FEATURE_MEANING = {
    "set_to_lift_frames": (
        "Number of frames between the set and the peak-leg-lift frame — his tempo "
        "from settled to the top of the kick."
    ),
    "knee_rise_duration_frac": (
        "Frames taken for the lead knee to travel from 20% to 80% of its peak "
        "rise, divided by the set-to-lift duration — how abruptly the leg comes "
        "up, independent of overall tempo."
    ),
    "hold_at_top_frac": (
        "Fraction of set-to-lift frames in which the lead knee is at or above 90% "
        "of its peak rise — distinguishes a held lift from a quick tap."
    ),
    "glove_speed_mean": (
        "Mean frame-to-frame displacement of the glove (wrist midpoint) along its "
        "smoothed path from set to lift, in torso lengths per frame."
    ),
    "glove_speed_cv": (
        "Standard deviation of that per-frame glove speed divided by its mean — a "
        "pulsing, stop-start move scores high and a single smooth move low."
    ),
    "glove_peak_speed_timing": (
        "Where in the set-to-lift interval the glove reaches its maximum smoothed "
        "speed, as a fraction from 0 at the set to 1 at lift."
    ),
    "glove_tortuosity": (
        "Length of the glove's smoothed path from set to lift divided by the "
        "straight-line distance between its start and end — 1.0 is a direct move, "
        "higher means it wandered to get there."
    ),
    "glove_vertical_reversals": (
        "Number of times the glove's smoothed vertical velocity changes sign "
        "between set and lift, per 10 frames — separates a single settle from a "
        "rock, which amplitude alone cannot."
    ),
    "glove_knee_lag_frames": (
        "Frame offset maximising the cross-correlation between the glove's "
        "vertical displacement and the lead knee's rise — negative means the glove "
        "leads the leg."
    ),
    "hip_glove_x_coupling": (
        "Pearson correlation between the hips' horizontal position and the glove's "
        "horizontal position from set to lift — whether the glove travels with the "
        "body or moves independently of it."
    ),
}


def _smooth(a: np.ndarray) -> np.ndarray:
    return (
        pd.Series(a)
        .rolling(PATH_SMOOTH, center=True, min_periods=2)
        .median()
        .to_numpy(dtype=float)
    )


def _path_ok(x: np.ndarray, y: np.ndarray) -> bool:
    """Whether a segment was tracked well enough to describe as a movement."""
    if len(x) < MIN_PATH_FRAMES:
        return False
    tracked = np.isfinite(x) & np.isfinite(y)
    return bool(tracked.mean() >= MIN_PATH_COVERAGE)


def _reversals(v: np.ndarray) -> float:
    """Sign changes in a velocity series, ignoring near-zero segments.

    Near-zero velocities are excluded before counting because the sign of a
    velocity inside the jitter floor flips constantly and would make every pitch
    look like a rock.
    """
    v = v[np.isfinite(v)]
    v = v[np.abs(v) > MIN_PEAK_SPEED / 2.0]
    if len(v) < 3:
        return float("nan")
    s = np.sign(v)
    return float(np.sum(s[1:] != s[:-1]))


def _best_lag(a: np.ndarray, b: np.ndarray) -> float:
    """Lag maximising correlation between two series, in frames."""
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < MIN_CORR_FRAMES:
        return float("nan")
    a, b = a[ok], b[ok]
    if np.std(a) < 1e-9 or np.std(b) < 1e-9:
        return float("nan")
    a = (a - a.mean()) / np.std(a)
    b = (b - b.mean()) / np.std(b)
    best, best_r = float("nan"), -np.inf
    lim = min(MAX_LAG, len(a) // 3)
    for lag in range(-lim, lim + 1):
        if lag < 0:
            x, y = a[-lag:], b[: len(b) + lag]
        elif lag > 0:
            x, y = a[: len(a) - lag], b[lag:]
        else:
            x, y = a, b
        if len(x) < MIN_CORR_FRAMES:
            continue
        r = float(np.mean(x * y))
        if r > best_r:
            best_r, best = r, float(lag)
    return best


def pitch_trajectory(df: pd.DataFrame, play_id: str) -> dict[str, Any] | None:
    """Trajectory features for one pitch, or None when the pitch is unusable.

    The window, torso scale and lift anchor are established exactly as the point
    primitives establish them, so the two families describe the same segment of
    the same pitches and any difference between them is the representation rather
    than the sample.
    """
    lsho_x, lsho_y = _col(df, "lsho_x"), _col(df, "lsho_y")
    rsho_x, rsho_y = _col(df, "rsho_x"), _col(df, "rsho_y")
    lhip_x, lhip_y = _col(df, "lhip_x"), _col(df, "lhip_y")
    rhip_x, rhip_y = _col(df, "rhip_x"), _col(df, "rhip_y")
    lwri_x, lwri_y = _col(df, "lwri_x"), _col(df, "lwri_y")
    rwri_x, rwri_y = _col(df, "rwri_x"), _col(df, "rwri_y")
    lkne_y, rkne_y = _col(df, "lkne_y"), _col(df, "rkne_y")

    sho_x, sho_y = _mid(lsho_x, rsho_x), _mid(lsho_y, rsho_y)
    hip_x, hip_y = _mid(lhip_x, rhip_x), _mid(lhip_y, rhip_y)
    glove_x, glove_y = _mid(lwri_x, rwri_x), _mid(lwri_y, rwri_y)

    wdf = df.copy()
    wdf["glove_x"], wdf["glove_y"] = glove_x, glove_y
    wdf["wrist_dist"] = np.hypot(lwri_x - rwri_x, lwri_y - rwri_y)
    win = actionable_window(wdf)
    if not win.valid:
        return None
    start, end = int(win.start), int(win.end)
    set_frame = int(win.set_frame if win.set_frame is not None else start)

    torso = np.hypot(sho_x - hip_x, sho_y - hip_y)
    scale = _med(torso, start, end)
    if not np.isfinite(scale) or not (MIN_TORSO <= scale <= MAX_TORSO):
        return None

    knee_rise = np.nanmax(
        np.vstack([(hip_y - lkne_y) / scale, (hip_y - rkne_y) / scale]), axis=0
    )
    if win.lift_frame is None:
        return None
    lift = int(win.lift_frame)
    if lift - set_frame < MIN_SET_TO_LIFT:
        return None

    out: dict[str, Any] = {"play_id": play_id, "delivery_type": win.delivery_type}
    for k in TRAJECTORY_FEATURES:
        out[k] = float("nan")

    lo, hi = set_frame, lift + 1
    n = hi - lo
    gx, gy = glove_x[lo:hi] / scale, glove_y[lo:hi] / scale
    px, py = _smooth(gx), _smooth(gy)
    knee_seg = knee_rise[lo:hi]

    # --- tempo -----------------------------------------------------------
    out["set_to_lift_frames"] = float(n)

    kfin = knee_seg[np.isfinite(knee_seg)]
    if len(kfin) >= MIN_PATH_FRAMES:
        base, peak = float(np.percentile(kfin, 20)), float(np.nanmax(knee_seg))
        span = peak - base
        if np.isfinite(span) and span > 0 and peak <= MAX_KNEE_RISE:
            frac = (knee_seg - base) / span
            above20 = np.where(np.isfinite(frac) & (frac >= 0.2))[0]
            above80 = np.where(np.isfinite(frac) & (frac >= 0.8))[0]
            if len(above20) and len(above80) and above80[0] >= above20[0]:
                out["knee_rise_duration_frac"] = float(
                    (above80[0] - above20[0]) / max(1, n)
                )
            out["hold_at_top_frac"] = float(
                np.nansum(frac >= 0.9) / max(1, np.isfinite(frac).sum())
            )

    # --- velocity, shape, coordination: all need a usable path -----------
    if not _path_ok(gx, gy):
        return out

    vx, vy = np.diff(px), np.diff(py)
    speed = np.hypot(vx, vy)
    sfin = speed[np.isfinite(speed)]
    if len(sfin) >= MIN_PATH_FRAMES - 1:
        m = float(np.mean(sfin))
        out["glove_speed_mean"] = m
        if m > 1e-9:
            out["glove_speed_cv"] = float(np.std(sfin) / m)
        if np.nanmax(sfin) >= MIN_PEAK_SPEED:
            out["glove_peak_speed_timing"] = float(
                np.nanargmax(np.where(np.isfinite(speed), speed, -np.inf))
                / max(1, len(speed) - 1)
            )

        # Tortuosity: path length over net displacement, gated on the net
        # displacement being resolvable at all.
        fin = np.isfinite(px) & np.isfinite(py)
        if fin.sum() >= MIN_PATH_FRAMES:
            xi, yi = px[fin], py[fin]
            net = float(np.hypot(xi[-1] - xi[0], yi[-1] - yi[0]))
            length = float(np.nansum(speed))
            if net >= MIN_NET_DISPLACEMENT and np.isfinite(length):
                out["glove_tortuosity"] = length / net

        rev = _reversals(vy)
        if np.isfinite(rev):
            out["glove_vertical_reversals"] = float(rev * 10.0 / max(1, len(vy)))

    # Glove rise against knee rise: both are vertical, both in torso units.
    out["glove_knee_lag_frames"] = _best_lag(-(py - np.nanmean(py)), knee_seg)

    hx = hip_x[lo:hi] / scale
    ok = np.isfinite(hx) & np.isfinite(px)
    if ok.sum() >= MIN_CORR_FRAMES and np.nanstd(hx[ok]) > 1e-9 and np.nanstd(px[ok]) > 1e-9:
        out["hip_glove_x_coupling"] = float(np.corrcoef(hx[ok], px[ok])[0, 1])

    return out


def build_run(run_dir: Path) -> Path:
    tdir, tracks = resolve_track_dir(run_dir)
    rows, skipped = [], 0
    for tp in tracks:
        try:
            df = pd.read_csv(tp)
        except Exception:
            skipped += 1
            continue
        rec = pitch_trajectory(df, play_id_of(tp))
        if rec is None:
            skipped += 1
            continue
        rows.append(rec)
    out = run_dir / "trajectory.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"{run_dir.name}: {len(tracks)} tracks -> {len(rows)} pitches "
          f"({skipped} unusable) [{tdir.name}]")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, nargs="+")
    args = ap.parse_args()
    for d in args.run_dir:
        build_run(Path(d))


if __name__ == "__main__":
    main()
