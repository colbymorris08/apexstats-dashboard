"""
Thorpe acceptance test — diagnostics.

Two questions the headline numbers cannot answer on their own:

1. WHY are pitches lost? Replicates the rejection ladder inside
   ``primitives.pitch_primitives`` and attributes each dropped pitch to the
   specific gate that dropped it.

2. Is the window/lift check meaningful? ``_find_lift`` searches only between the
   set frame and the window end, so "lift is inside the window" is true by
   construction and cannot fail. The honest test is whether the UNCONSTRAINED
   peak knee rise (searched across the whole clip) also lands inside the window.
   Where it does not, the constrained search is anchoring on the wrong frame.
"""
from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np
import pandas as pd

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from preflight.primitives import (  # noqa: E402
    MAX_KNEE_RISE,
    MAX_TORSO,
    MIN_SET_TO_LIFT,
    MIN_TORSO,
    _col,
    _find_lift,
    _med,
    _mid,
)
from preflight.window import actionable_window  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    run_dir = Path(args.run_dir)

    reasons: dict[str, int] = {}
    lift_cmp: list[dict] = []

    paths = sorted(glob.glob(str(run_dir / "lift_tracks" / "*.csv")))
    for p in paths:
        df = pd.read_csv(p)
        pid = Path(p).stem

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
        hand_gap = np.hypot(lwri_x - rwri_x, lwri_y - rwri_y)

        # Must match the frame primitives.py builds exactly, or this diagnostic
        # measures a different window than the one actually in use.
        wdf = df.copy()
        wdf["glove_x"] = glove_x
        wdf["glove_y"] = glove_y
        wdf["wrist_dist"] = hand_gap
        win = actionable_window(wdf)
        if not win.valid:
            reasons[f"window:{win.method}"] = reasons.get(f"window:{win.method}", 0) + 1
            continue
        start, end = int(win.start), int(win.end)
        set_frame = int(win.set_frame if win.set_frame is not None else start)

        torso = np.hypot(sho_x - hip_x, sho_y - hip_y)
        scale = _med(torso, start, end)
        if not np.isfinite(scale) or not (MIN_TORSO <= scale <= MAX_TORSO):
            reasons["torso_out_of_band"] = reasons.get("torso_out_of_band", 0) + 1
            continue

        knee_l = (hip_y - lkne_y) / scale
        knee_r = (hip_y - rkne_y) / scale
        lift, knee_peak, _ = _find_lift(knee_l, knee_r, set_frame, end)
        if lift is None or not np.isfinite(knee_peak):
            reasons["no_knee_signal"] = reasons.get("no_knee_signal", 0) + 1
            continue
        if knee_peak > MAX_KNEE_RISE:
            reasons["knee_rise_implausible"] = reasons.get("knee_rise_implausible", 0) + 1
            continue
        if lift - set_frame < MIN_SET_TO_LIFT:
            reasons["lift_too_close_to_set"] = reasons.get("lift_too_close_to_set", 0) + 1
            continue
        reasons["ACCEPTED"] = reasons.get("ACCEPTED", 0) + 1

        # --- honest window/lift check: unconstrained peak across whole clip ---
        lead = np.nanmax(np.vstack([knee_l, knee_r]), axis=0)
        if np.isfinite(lead).sum() >= 3:
            free_peak = int(np.nanargmax(lead))
            lift_cmp.append(
                {
                    "play_id": pid,
                    "set_frame": set_frame,
                    "end": end,
                    "constrained_lift": lift,
                    "free_peak": free_peak,
                    "free_inside": set_frame <= free_peak <= end,
                    "offset": free_peak - lift,
                }
            )

    total = len(paths)
    print(f"REJECTION LADDER — {run_dir.name}, {total} tracked clips\n")
    for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  {k:34s} {v:4d}  ({100.0 * v / total:5.1f}%)")

    if lift_cmp:
        c = pd.DataFrame(lift_cmp)
        inside = int(c.free_inside.sum())
        print(f"\nHONEST WINDOW/LIFT CHECK — {len(c)} accepted pitches")
        print(
            f"  unconstrained peak knee rise inside [set, break]: {inside}/{len(c)} "
            f"({100.0 * inside / len(c):.1f}%)"
        )
        agree = int((c.offset.abs() <= 3).sum())
        print(
            f"  unconstrained peak within 3 frames of the anchored lift: {agree}/{len(c)} "
            f"({100.0 * agree / len(c):.1f}%)"
        )
        out = c[~c.free_inside]
        if len(out):
            print(f"  of the {len(out)} landing outside: "
                  f"{int((out.free_peak > out.end).sum())} after break, "
                  f"{int((out.free_peak < out.set_frame).sum())} before set")
        c.to_csv(run_dir / "window_lift_check.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
