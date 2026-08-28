"""
Does ``pitchcom_tap_count`` measure taps, or generic motion?

Three checks, each of which a real discrete-tap detector should pass:

1. SCALE. A PitchCom press is a finger/thumb movement of a few centimetres on a
   forearm device. Expressed in the same normalized image units the detector
   thresholds on (TAP_SPEED = 0.015/frame), how large is that relative to the
   pitcher's torso? If one "tap" implies motion of a sizeable fraction of a
   torso length per frame, the detector cannot be seeing fingers.

2. DROPOUT. ``wrist_speed`` is written as ``hypot(glove - prev_glove)`` where
   ``prev_glove`` is only updated on frames the glove was found. Across a
   tracking gap it therefore reports multi-frame displacement as single-frame
   speed — a large spike with no physical motion behind it. What share of
   detected "taps" sit on a dropout re-acquisition?

3. THRESHOLD SELF-REFERENCE. Production uses
   ``thr = max(p75(window speed), 0.015)``. On pure noise a percentile
   threshold always yields peaks. Compare tap counts on real windows against
   tap counts on phase-shuffled speed (same distribution, destroyed timing).
   A genuine event detector should collapse on shuffled input.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from cv.preflight.window import actionable_window, _clean, _travel  # noqa: E402

RNG = np.random.default_rng(7)


def production_taps(speed: np.ndarray) -> list[int]:
    """Exact reproduction of run_poc.window_features tap logic."""
    speed = np.nan_to_num(speed, nan=0.0)
    thr = max(float(np.nanpercentile(speed, 75)) if len(speed) else 0.0, 0.015)
    peaks = [
        i
        for i in range(1, len(speed) - 1)
        if speed[i] >= thr and speed[i] >= speed[i - 1] and speed[i] >= speed[i + 1]
    ]
    taps: list[int] = []
    for i in peaks:
        if not taps or (i - taps[-1]) >= 3:
            taps.append(i)
    return taps


def torso_scale(df: pd.DataFrame) -> float:
    need = ("lsho_x", "rsho_x", "lsho_y", "rsho_y", "lhip_x", "rhip_x", "lhip_y", "rhip_y")
    if not all(c in df.columns for c in need):
        return float("nan")
    hip_y = np.nanmean(np.vstack([_clean(df, "lhip_y"), _clean(df, "rhip_y")]), axis=0)
    hip_x = np.nanmean(np.vstack([_clean(df, "lhip_x"), _clean(df, "rhip_x")]), axis=0)
    sho_y = np.nanmean(np.vstack([_clean(df, "lsho_y"), _clean(df, "rsho_y")]), axis=0)
    sho_x = np.nanmean(np.vstack([_clean(df, "lsho_x"), _clean(df, "rsho_x")]), axis=0)
    return float(np.nanmedian(np.hypot(sho_x - hip_x, sho_y - hip_y)))


def run(tracks_dir: Path) -> dict:
    files = sorted(tracks_dir.glob("*_tracks.csv"))
    torsos, real_counts, shuf_counts, isis = [], [], [], []
    dropout_adjacent = 0
    total_taps = 0
    still_window_taps = []

    for f in files:
        df = pd.read_csv(f)
        if len(df) < 8:
            continue
        win = actionable_window(df)
        if not win.valid:
            continue
        t = torso_scale(df)
        if np.isfinite(t):
            torsos.append(t)

        raw = pd.to_numeric(df["wrist_speed"], errors="coerce").to_numpy(dtype=float) \
            if "wrist_speed" in df.columns else _travel(_clean(df, "glove_x"), _clean(df, "glove_y"))
        seg = raw[win.start : win.end]
        taps = production_taps(seg)
        real_counts.append(len(taps))
        total_taps += len(taps)
        if len(taps) >= 2:
            isis.extend(np.diff(taps).tolist())

        # dropout: glove untracked on the frame before the peak
        if "glove_x" in df.columns:
            gx = pd.to_numeric(df["glove_x"], errors="coerce").to_numpy(dtype=float)
            gseg = gx[win.start : win.end]
            for i in taps:
                lo = max(0, i - 3)
                if np.isnan(gseg[lo:i]).any():
                    dropout_adjacent += 1

        shuf = seg.copy()
        RNG.shuffle(shuf)
        shuf_counts.append(len(production_taps(shuf)))

        # what does the detector do on a window that is genuinely still?
        finite = seg[np.isfinite(seg)]
        if finite.size and float(np.nanmax(finite)) < 0.015:
            still_window_taps.append(len(taps))

    med_torso = float(np.nanmedian(torsos)) if torsos else float("nan")
    return {
        "tracks_dir": str(tracks_dir),
        "clips": len(real_counts),
        "median_torso_normalized": med_torso,
        "tap_threshold_in_torso_lengths_per_frame": (0.015 / med_torso) if np.isfinite(med_torso) else None,
        "mean_taps_real": float(np.mean(real_counts)) if real_counts else 0.0,
        "mean_taps_phase_shuffled": float(np.mean(shuf_counts)) if shuf_counts else 0.0,
        "total_taps": total_taps,
        "dropout_adjacent_taps": dropout_adjacent,
        "dropout_adjacent_fraction": round(dropout_adjacent / total_taps, 4) if total_taps else None,
        "isi_frames_median": float(np.median(isis)) if isis else None,
        "isi_frames_mean": float(np.mean(isis)) if isis else None,
        "windows_with_no_motion_above_threshold": len(still_window_taps),
        "taps_reported_in_those_still_windows": int(np.sum(still_window_taps)) if still_window_taps else 0,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2] / "runs"
    for t in sys.argv[1:] or ["merrill_kelly_poc"]:
        print(json.dumps(run(root / t / "tracks"), indent=2))
