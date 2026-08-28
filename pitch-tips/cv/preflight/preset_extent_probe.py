"""
Where should the PitchCom segment open?

Builds a profile of tap-like activity as a function of distance BEFORE the set
frame, so the opening is chosen from where activity actually lives rather than
from a round number. Also reports how much pre-set footage the cached tracks
carry, which bounds how early any segment can open at all.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cv.preflight.window import actionable_window, _clean, _travel  # noqa: E402

TAP_SPEED = 0.015
# Profile this far back from the set, in 5-frame bins (~0.17s each).
PROFILE_BACK = 120
BIN = 5


def speed_of(df: pd.DataFrame) -> np.ndarray:
    if "wrist_speed" in df.columns:
        s = pd.to_numeric(df["wrist_speed"], errors="coerce").to_numpy(dtype=float)
    else:
        s = _travel(_clean(df, "glove_x"), _clean(df, "glove_y"))
    return np.nan_to_num(s, nan=0.0)


def run(tracks_dir: Path) -> dict:
    nbins = PROFILE_BACK // BIN
    tap_hist = np.zeros(nbins)
    frames_hist = np.zeros(nbins)
    tracked_hist = np.zeros(nbins)
    preset_avail = []
    set_zero = 0
    n = 0

    for f in sorted(tracks_dir.glob("*_tracks.csv")):
        df = pd.read_csv(f)
        if len(df) < 8:
            continue
        win = actionable_window(df)
        if not win.valid or win.set_frame is None:
            continue
        n += 1
        if win.start == 0:
            set_zero += 1
        preset_avail.append(int(win.start))

        sp = speed_of(df)
        gx = pd.to_numeric(df["glove_x"], errors="coerce").to_numpy(dtype=float) if "glove_x" in df else np.zeros(len(df))
        s = int(win.start)
        for b in range(nbins):
            hi = s - b * BIN
            lo = s - (b + 1) * BIN
            if hi <= 0:
                break
            lo = max(0, lo)
            seg = sp[lo:hi]
            if not seg.size:
                continue
            frames_hist[b] += seg.size
            tracked_hist[b] += int(np.isfinite(gx[lo:hi]).sum())
            # local maxima above an absolute threshold, same shape as production
            for i in range(lo + 1, hi - 1):
                if sp[i] >= TAP_SPEED and sp[i] >= sp[i - 1] and sp[i] >= sp[i + 1]:
                    tap_hist[b] += 1

    profile = []
    for b in range(nbins):
        if frames_hist[b] == 0:
            continue
        profile.append(
            {
                "frames_before_set": f"-{(b+1)*BIN} .. -{b*BIN}",
                "tap_rate_per_frame": round(tap_hist[b] / frames_hist[b], 4),
                "clip_coverage_frac": round(frames_hist[b] / (n * BIN), 3),
                "glove_tracked_frac": round(tracked_hist[b] / frames_hist[b], 3),
            }
        )

    pa = np.array(preset_avail) if preset_avail else np.array([0])
    return {
        "tracks_dir": str(tracks_dir),
        "clips_valid": n,
        "set_frame_eq_0": set_zero,
        "set_frame_eq_0_rate": round(set_zero / n, 4) if n else None,
        "preset_frames_available": {
            "p10": float(np.percentile(pa, 10)),
            "median": float(np.median(pa)),
            "p90": float(np.percentile(pa, 90)),
            "frac_ge_20": float((pa >= 20).mean()),
            "frac_ge_30": float((pa >= 30).mean()),
            "frac_ge_45": float((pa >= 45).mean()),
            "frac_ge_60": float((pa >= 60).mean()),
        },
        "activity_profile_before_set": profile,
    }


if __name__ == "__main__":
    root = ROOT / "runs"
    for t in sys.argv[1:] or ["merrill_kelly_poc"]:
        print(json.dumps(run(root / t / "tracks"), indent=2))
