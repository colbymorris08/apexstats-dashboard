"""
Per-landmark measurement noise floor, in torso lengths.

Why this exists
---------------
``pitchcom_tap_count`` was retired with a number rather than an opinion: wrist
jitter measured 0.116 torso lengths/frame against a maximum plausible tap of
0.060, so the thing it claimed to detect sat under the noise. Every primitive
added after that has to clear the same bar, and the bar is different for every
body part — a hip landmark is far steadier than a finger landmark.

Method
------
During the set the pitcher is, by construction, still: ``window.actionable_window``
locates the set as a sustained quiet run. So whatever per-frame landmark
displacement is observed over the set interval is measurement noise, not motion.
That displacement, divided by the pitch's own torso length, is the floor.

Two numbers are reported per landmark:

``jitter``    median per-frame displacement over the set interval. A trajectory
              feature that integrates frame to frame accumulates this, so it is
              the number that kills path-length features.
``anchor_sd`` standard deviation of a LIFT_HALF_WIN-frame median about the set
              interval's own mean. This is the floor that matters for a
              single-anchor feature, and it is much lower than ``jitter``
              because medianing several frames averages the noise down.

Read-only over cached tracks; no video decode, no re-tracking.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from preflight.primitives import LIFT_HALF_WIN, MAX_TORSO, MIN_TORSO, _col, _mid
from preflight.window import actionable_window

# Landmark groups the taxonomy actually needs a floor for.
GROUPS = {
    "nose": ("nose_x", "nose_y"),
    "shoulder_l": ("lsho_x", "lsho_y"),
    "shoulder_r": ("rsho_x", "rsho_y"),
    "elbow_l": ("lelb_x", "lelb_y"),
    "elbow_r": ("relb_x", "relb_y"),
    "wrist_l": ("lwri_x", "lwri_y"),
    "wrist_r": ("rwri_x", "rwri_y"),
    "index_l": ("lidx_x", "lidx_y"),
    "index_r": ("ridx_x", "ridx_y"),
    "hip_l": ("lhip_x", "lhip_y"),
    "hip_r": ("rhip_x", "rhip_y"),
    "knee_l": ("lkne_x", "lkne_y"),
    "knee_r": ("rkne_x", "rkne_y"),
    "ankle_l": ("lank_x", "lank_y"),
    "ankle_r": ("rank_x", "rank_y"),
}


def _set_interval(df: pd.DataFrame) -> tuple[int, int] | None:
    """The quiet set run, where true landmark motion is ~zero by construction."""
    lwri_x, lwri_y = _col(df, "lwri_x"), _col(df, "lwri_y")
    rwri_x, rwri_y = _col(df, "rwri_x"), _col(df, "rwri_y")
    wdf = df.copy()
    wdf["glove_x"] = _mid(lwri_x, rwri_x)
    wdf["glove_y"] = _mid(lwri_y, rwri_y)
    wdf["wrist_dist"] = np.hypot(lwri_x - rwri_x, lwri_y - rwri_y)
    win = actionable_window(wdf)
    if not win.valid or win.set_frame is None:
        return None
    lo = int(win.set_frame)
    # Only the still part: stop well before the lift so the leg kick and the
    # glove coming up cannot be counted as noise.
    hi = min(lo + 15, int(win.lift_frame) if win.lift_frame else lo + 15)
    if hi - lo < 8:
        return None
    return lo, hi


def probe_pitch(df: pd.DataFrame) -> dict[str, tuple[float, float, float]] | None:
    iv = _set_interval(df)
    if iv is None:
        return None
    lo, hi = iv

    sho_x, sho_y = _mid(_col(df, "lsho_x"), _col(df, "rsho_x")), _mid(_col(df, "lsho_y"), _col(df, "rsho_y"))
    hip_x, hip_y = _mid(_col(df, "lhip_x"), _col(df, "rhip_x")), _mid(_col(df, "lhip_y"), _col(df, "rhip_y"))
    torso = np.hypot(sho_x - hip_x, sho_y - hip_y)
    seg = torso[lo:hi]
    scale = float(np.nanmedian(seg)) if np.isfinite(seg).any() else float("nan")
    if not np.isfinite(scale) or not (MIN_TORSO <= scale <= MAX_TORSO):
        return None

    out: dict[str, tuple[float, float, float]] = {}
    for name, (cx, cy) in GROUPS.items():
        if cx not in df.columns:
            continue
        # Raw, NOT the smoothed _col(): smoothing is part of what we are trying
        # to measure the benefit of, so measuring on smoothed data would
        # understate the true sensor noise.
        x = pd.to_numeric(df[cx], errors="coerce").to_numpy(dtype=float)[lo:hi]
        y = pd.to_numeric(df[cy], errors="coerce").to_numpy(dtype=float)[lo:hi]
        vis_col = cx.replace("_x", "_v")
        v = (
            pd.to_numeric(df[vis_col], errors="coerce").to_numpy(dtype=float)[lo:hi]
            if vis_col in df.columns
            else np.full(len(x), np.nan)
        )
        if np.isfinite(x).sum() < 6:
            continue
        step = np.hypot(np.diff(x), np.diff(y)) / scale
        jitter = float(np.nanmedian(step)) if np.isfinite(step).any() else float("nan")

        # Anchor noise: how much a LIFT_HALF_WIN-frame median moves around.
        k = 2 * LIFT_HALF_WIN + 1
        med_x = pd.Series(x).rolling(k, min_periods=3).median().to_numpy(dtype=float)
        med_y = pd.Series(y).rolling(k, min_periods=3).median().to_numpy(dtype=float)
        ok = np.isfinite(med_x) & np.isfinite(med_y)
        if ok.sum() >= 3:
            anchor = float(np.hypot(np.nanstd(med_x[ok]), np.nanstd(med_y[ok])) / scale)
        else:
            anchor = float("nan")
        out[name] = (jitter, anchor, float(np.nanmean(v)) if np.isfinite(v).any() else float("nan"))
    return out


def run(run_dirs: list[Path], limit: int | None = None) -> dict:
    acc: dict[str, list[tuple[float, float, float]]] = {}
    n_used = 0
    n_seen = 0
    for rd in run_dirs:
        for path in sorted((rd / "lift_tracks").glob("*.csv")):
            if limit and n_used >= limit:
                break
            n_seen += 1
            try:
                df = pd.read_csv(path)
            except Exception:
                continue
            got = probe_pitch(df)
            if not got:
                continue
            n_used += 1
            for k, v in got.items():
                acc.setdefault(k, []).append(v)

    report = {"n_tracks_seen": n_seen, "n_tracks_used": n_used, "landmarks": {}}
    for name, vals in sorted(acc.items()):
        arr = np.array(vals, dtype=float)
        report["landmarks"][name] = {
            "n": int(len(arr)),
            "jitter_median_torso_per_frame": round(float(np.nanmedian(arr[:, 0])), 4),
            "jitter_p90": round(float(np.nanpercentile(arr[:, 0], 90)), 4),
            "anchor_sd_torso": round(float(np.nanmedian(arr[:, 1])), 4),
            "anchor_sd_p90": round(float(np.nanpercentile(arr[:, 1], 90)), 4),
            "visibility_mean": round(float(np.nanmean(arr[:, 2])), 3),
        }
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, nargs="+", type=Path)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    rep = run(args.run_dir, args.limit)
    text = json.dumps(rep, indent=2)
    print(text)
    if args.out:
        args.out.write_text(text)


if __name__ == "__main__":
    main()
