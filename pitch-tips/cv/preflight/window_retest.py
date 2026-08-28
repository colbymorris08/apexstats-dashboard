"""
Re-derive the full feature set under the segmented window and re-run spot_diff.

Writes to ``features_segmented.csv`` / ``spot_diff_segmented.json`` rather than
overwriting the live tables, so this can run while the scale pipeline is going.

Reports window-placement stats alongside the result, because the thing most
likely to go wrong when the opening moves earlier is the idle-footage bug coming
back — that shows up as a spike in the ``set_frame == 0`` rate.

Nothing is tuned: FDR_Q, effect floors, visibility floors and the degenerate-rule
gate all come from spot_diff unmodified, and the split stays game-level.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CVROOT = ROOT / "cv"
if str(CVROOT) not in sys.path:
    sys.path.insert(0, str(CVROOT))

from cv.preflight import spot_diff  # noqa: E402
from cv.preflight.run_poc import _feature_vector  # noqa: E402
from cv.preflight.window import actionable_window, preset_segment  # noqa: E402

FEATURE_PREFIXES = ("glove", "wrist", "cheek", "pitchcom", "window", "delivery", "catcher", "preset")


def rederive(run_dir: Path) -> tuple[pd.DataFrame, dict]:
    src = pd.read_csv(run_dir / "features.csv", dtype={"play_id": str})
    meta_cols = [c for c in src.columns if not c.startswith(FEATURE_PREFIXES)]
    meta = {str(r["play_id"]): r.to_dict() for _, r in src[meta_cols].iterrows()}

    rows, stats = [], []
    dropped_invalid = dropped_meta = 0
    for t in sorted((run_dir / "tracks").glob("*_tracks.csv")):
        play_id = t.name.replace("_tracks.csv", "")
        m = meta.get(play_id)
        if m is None:
            dropped_meta += 1
            continue
        feats = _feature_vector(t)
        if not feats:
            dropped_invalid += 1
            continue
        row = dict(m)
        row.update(feats)
        row["play_id"] = play_id
        rows.append(row)

        df = pd.read_csv(t)
        win = actionable_window(df)
        seg = preset_segment(df, win)
        stats.append(
            {
                "set_frame": win.start,
                "window_end": win.end,
                "n_frames": win.n_frames,
                "preset_start": seg[0] if seg else None,
                "preset_frames": (seg[1] - seg[0]) if seg else 0,
                "clip_len": len(df),
                "method": win.method,
                "delivery_type": win.delivery_type,
            }
        )

    df = pd.DataFrame(rows)
    s = pd.DataFrame(stats)
    placement = {
        "clips_featured": len(df),
        "dropped_invalid_window": dropped_invalid,
        "dropped_no_metadata": dropped_meta,
        "set_frame_eq_0": int((s["set_frame"] == 0).sum()) if len(s) else 0,
        "set_frame_eq_0_rate": round(float((s["set_frame"] == 0).mean()), 4) if len(s) else None,
        "set_frame_median": float(s["set_frame"].median()) if len(s) else None,
        "window_n_frames_median": float(s["n_frames"].median()) if len(s) else None,
        "preset_available_rate": round(float((s["preset_frames"] > 0).mean()), 4) if len(s) else None,
        "preset_frames_median": float(s.loc[s["preset_frames"] > 0, "preset_frames"].median()) if len(s) else None,
        "preset_start_eq_0_rate": round(float((s["preset_start"] == 0).mean()), 4) if len(s) else None,
        "method_mix": s["method"].value_counts().to_dict() if len(s) else {},
        "delivery_type_mix": s["delivery_type"].value_counts().to_dict() if len(s) else {},
    }
    return df, placement


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, nargs="+")
    args = ap.parse_args()

    for rd in args.run_dir:
        run_dir = Path(rd)
        df, placement = rederive(run_dir)
        print(f"\n===== {run_dir.name} =====")
        print("window placement:")
        print(json.dumps(placement, indent=2, default=str))
        if df.empty:
            continue
        df.to_csv(run_dir / "features_segmented.csv", index=False)

        res = spot_diff.analyse(df, f"{run_dir.name} [segmented window]")
        summary = {k: v for k, v in res.items() if k != "differences"}
        print("spot_diff:")
        print(json.dumps(summary, indent=2, default=str))
        diffs = res.get("differences") or []
        print(f"surviving differences: {len(diffs)}")
        for d in diffs:
            print("  -", d.get("cue") or d.get("col"), "|", (d.get("note") or "")[:200])
        pc = [d for d in diffs if str(d.get("col", "")).startswith("pitchcom")]
        print(f"surviving PitchCom cues: {len(pc)}")
        (run_dir / "spot_diff_segmented.json").write_text(
            json.dumps({"placement": placement, "result": res}, indent=2, default=str)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
