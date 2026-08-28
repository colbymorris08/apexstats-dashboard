"""
Empirical probe: WHEN do tap-like events occur relative to the actionable window?

Detects tap-like bursts across the WHOLE clip with an absolute (not
window-relative) threshold, then bins each event against the window boundaries
found by ``window.actionable_window``. Read-only: computes nothing that feeds a
tip, so it cannot influence any published result.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from cv.preflight.window import actionable_window, _clean, _travel  # noqa: E402

# Absolute burst threshold for a candidate tap, in normalized image units per
# frame. Deliberately fixed rather than a percentile of the segment under test:
# a percentile threshold finds "peaks" in any segment, however still, which is
# exactly the defect being investigated.
TAP_SPEED = 0.015
TAP_DEBOUNCE = 3


def detect_taps_wholeclip(df: pd.DataFrame) -> list[int]:
    """Local maxima of glove speed over the entire clip, absolute threshold."""
    if "wrist_speed" in df.columns:
        sp = pd.to_numeric(df["wrist_speed"], errors="coerce").to_numpy(dtype=float)
    else:
        sp = _travel(_clean(df, "glove_x"), _clean(df, "glove_y"))
    sp = np.nan_to_num(sp, nan=0.0)
    peaks = [
        i
        for i in range(1, len(sp) - 1)
        if sp[i] >= TAP_SPEED and sp[i] >= sp[i - 1] and sp[i] >= sp[i + 1]
    ]
    taps: list[int] = []
    for i in peaks:
        if not taps or (i - taps[-1]) >= TAP_DEBOUNCE:
            taps.append(i)
    return taps


def probe(tracks_dir: Path, limit: int | None = None) -> dict:
    files = sorted(tracks_dir.glob("*_tracks.csv"))
    if limit:
        files = files[:limit]

    bins = {"before_set": 0, "in_window": 0, "after_window_pre_delivery": 0, "at_or_after_delivery": 0}
    n_clips = 0
    n_invalid = 0
    per_clip = []
    window_speed_stats = []

    for f in files:
        df = pd.read_csv(f)
        if len(df) < 8:
            continue
        win = actionable_window(df)
        if not win.valid or win.set_frame is None:
            n_invalid += 1
            continue
        n_clips += 1
        taps = detect_taps_wholeclip(df)
        c = {"before_set": 0, "in_window": 0, "after_window_pre_delivery": 0, "at_or_after_delivery": 0}
        for t in taps:
            if t < win.start:
                c["before_set"] += 1
            elif t < win.end:
                c["in_window"] += 1
            elif win.delivery_frame is not None and t < win.delivery_frame:
                c["after_window_pre_delivery"] += 1
            else:
                c["at_or_after_delivery"] += 1
        for k in bins:
            bins[k] += c[k]

        # How much room is there before the set, and is the window actually quiet?
        sp = pd.to_numeric(df.get("wrist_speed"), errors="coerce").to_numpy(dtype=float) \
            if "wrist_speed" in df.columns else _travel(_clean(df, "glove_x"), _clean(df, "glove_y"))
        sp = np.nan_to_num(sp, nan=0.0)
        wseg = sp[win.start : win.end]
        preseg = sp[max(0, win.start - 60) : win.start]
        window_speed_stats.append(
            {
                "win_mean": float(np.mean(wseg)) if wseg.size else np.nan,
                "win_p75": float(np.percentile(wseg, 75)) if wseg.size else np.nan,
                "pre_mean": float(np.mean(preseg)) if preseg.size else np.nan,
                "pre_p75": float(np.percentile(preseg, 75)) if preseg.size else np.nan,
                "preset_frames": int(win.start),
            }
        )
        per_clip.append(
            {
                "play_id": f.name.split("_tracks")[0],
                "n_frames": len(df),
                "set_frame": win.start,
                "window_end": win.end,
                "lift_frame": win.lift_frame,
                "delivery_frame": win.delivery_frame,
                "method": win.method,
                **c,
            }
        )

    total = sum(bins.values()) or 1
    ws = pd.DataFrame(window_speed_stats)
    return {
        "tracks_dir": str(tracks_dir),
        "clips_with_valid_window": n_clips,
        "clips_dropped_invalid_window": n_invalid,
        "tap_events_total": sum(bins.values()),
        "counts": bins,
        "fractions": {k: round(v / total, 4) for k, v in bins.items()},
        "median_preset_frames_available": float(ws["preset_frames"].median()) if len(ws) else None,
        "median_window_mean_speed": float(ws["win_mean"].median()) if len(ws) else None,
        "median_preset_mean_speed": float(ws["pre_mean"].median()) if len(ws) else None,
        "median_window_p75_speed": float(ws["win_p75"].median()) if len(ws) else None,
        "median_preset_p75_speed": float(ws["pre_p75"].median()) if len(ws) else None,
        "per_clip": per_clip,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2] / "runs"
    targets = sys.argv[1:] or ["merrill_kelly_poc"]
    for t in targets:
        res = probe(root / t / "tracks")
        out = {k: v for k, v in res.items() if k != "per_clip"}
        print(json.dumps(out, indent=2))
        (root / t / "pitchcom_timing_probe.json").write_text(json.dumps(res, indent=2))
