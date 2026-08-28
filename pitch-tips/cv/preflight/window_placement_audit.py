#!/usr/bin/env python3
"""
Where in the clip does the actionable window actually land?

Raised by the catcher work rather than aimed at it. On three Gallen clips the
window opened at frame 0 and closed by frame 54-77 of a 412-452 frame clip — the
first ~1.3 s of a ~7.5 s clip, which is broadcast lead-in. Home plate is not
visible there, which is why in-window plate detection was 0.00 on those clips
against 1.00 on the Woo clips.

If that placement is common it matters well beyond the catcher: it is the same
failure the delivery-anchored rewrite was introduced to fix ("Savant clips open on
seconds of pre-pitch idle footage... the window then opens and closes before the
delivery even starts"), and every window-derived cue on the board would be
partially computed on lead-in frames.

Cheap to answer at scale because it needs no pixels: window placement is a
function of the cached track alone. Runs read-only over cached tracks.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as st
from pathlib import Path

import pandas as pd

from preflight.window import actionable_window, preset_segment


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs-dir", type=Path, default=Path("runs"))
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--out", type=Path, default=Path("runs/window_placement_audit.json"))
    a = ap.parse_args(argv)

    files = sorted(a.runs_dir.glob("*_poc/tracks/*_tracks.csv"))
    random.Random(0).shuffle(files)
    files = files[: a.n]

    recs = []
    for f in files:
        try:
            df = pd.read_csv(f, low_memory=False)
        except Exception:
            continue
        n = len(df)
        if n < 10:
            continue
        win = actionable_window(df)
        rec = {"arm": f.parent.parent.name, "clip_frames": n, "valid": bool(win.valid),
               "method": win.method, "delivery_type": win.delivery_type}
        if win.valid:
            pre = preset_segment(df, win)
            lo = pre[0] if pre else win.start
            rec.update(
                lo=int(lo), hi=int(win.end), span=int(win.end - lo),
                has_preset=pre is not None,
                delivery_frame=None if win.delivery_frame is None else int(win.delivery_frame),
                # Position of the window close as a fraction of clip length. A
                # real delivery sits well into a Savant clip, so a close in the
                # first quarter is a strong hint the window is on lead-in.
                close_frac=round(win.end / n, 4),
                opens_at_zero=bool(lo == 0),
            )
        recs.append(rec)

    valid = [r for r in recs if r["valid"]]
    closes = [r["close_frac"] for r in valid]
    report = {
        "n_tracks": len(recs),
        "n_valid": len(valid),
        "valid_rate": round(len(valid) / len(recs), 4) if recs else None,
        "opens_at_frame_zero_rate": round(sum(1 for r in valid if r["opens_at_zero"]) / len(valid), 4) if valid else None,
        "has_preset_segment_rate": round(sum(1 for r in valid if r["has_preset"]) / len(valid), 4) if valid else None,
        "close_frac": {
            "p10": round(sorted(closes)[len(closes) // 10], 4) if closes else None,
            "median": round(st.median(closes), 4) if closes else None,
            "p90": round(sorted(closes)[int(len(closes) * 0.9)], 4) if closes else None,
        },
        "closes_in_first_quarter_rate": round(sum(1 for c in closes if c < 0.25) / len(closes), 4) if closes else None,
        "closes_in_first_third_rate": round(sum(1 for c in closes if c < 0.3333) / len(closes), 4) if closes else None,
        "span_frames": {
            "median": round(st.median([r["span"] for r in valid]), 1) if valid else None,
        },
        "by_arm": {},
        "tracks": recs,
    }
    for arm in sorted({r["arm"] for r in valid}):
        rs = [r for r in valid if r["arm"] == arm]
        cs = [r["close_frac"] for r in rs]
        report["by_arm"][arm] = {
            "n": len(rs),
            "median_close_frac": round(st.median(cs), 4),
            "closes_in_first_quarter_rate": round(sum(1 for c in cs if c < 0.25) / len(cs), 4),
        }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "tracks"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
