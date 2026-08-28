"""
Read-only feasibility measurement: how many pixels does the pitcher's hand
occupy in Savant CF clips, inside the actionable window?

Answers whether finger-level cues (index-finger curl) are recoverable at all,
independent of which model we point at the problem. Writes nothing except an
optional CSV under the run directory's audit/ subfolder.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preflight.window import actionable_window  # noqa: E402


def clip_dims(path: str) -> tuple[int, int]:
    cap = cv2.VideoCapture(path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return w, h


def px(df: pd.DataFrame, ax: str, bx: str, W: int, H: int) -> np.ndarray:
    dx = (pd.to_numeric(df[f"{ax}_x"], errors="coerce") - pd.to_numeric(df[f"{bx}_x"], errors="coerce")) * W
    dy = (pd.to_numeric(df[f"{ax}_y"], errors="coerce") - pd.to_numeric(df[f"{bx}_y"], errors="coerce")) * H
    return np.hypot(dx, dy).to_numpy(dtype=float)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/drew_thorpe_rich_poc")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    tracks = sorted(glob.glob(os.path.join(args.run, "tracks", "*_tracks.csv")))
    if args.limit:
        tracks = tracks[: args.limit]

    dim_cache: dict[tuple[int, int], int] = {}
    rows = []
    for tp in tracks:
        pid = os.path.basename(tp).replace("_tracks.csv", "")
        clip = os.path.join(args.run, "clips", f"{pid}.mp4")
        if not os.path.exists(clip):
            continue
        W, H = clip_dims(clip)
        if W <= 0 or H <= 0:
            continue
        dim_cache[(W, H)] = dim_cache.get((W, H), 0) + 1
        df = pd.read_csv(tp)
        win = actionable_window(df)
        if not win.valid:
            continue
        w = df.iloc[win.start : win.end]
        if len(w) == 0:
            continue

        rec = {"play_id": pid, "W": W, "H": H, "win_frames": len(w), "method": win.method}
        for side in ("l", "r"):
            wi = px(w, f"{side}wri", f"{side}idx", W, H)
            wp = px(w, f"{side}wri", f"{side}pnk", W, H)
            ip = px(w, f"{side}idx", f"{side}pnk", W, H)
            vis = pd.to_numeric(w[f"{side}idx_v"], errors="coerce").to_numpy(dtype=float)
            rec[f"{side}_wri_idx_px"] = float(np.nanmedian(wi)) if np.isfinite(wi).any() else np.nan
            rec[f"{side}_wri_pnk_px"] = float(np.nanmedian(wp)) if np.isfinite(wp).any() else np.nan
            rec[f"{side}_idx_pnk_px"] = float(np.nanmedian(ip)) if np.isfinite(ip).any() else np.nan
            rec[f"{side}_idx_v"] = float(np.nanmedian(vis)) if np.isfinite(vis).any() else np.nan
            rec[f"{side}_frac_tracked"] = float(np.isfinite(wi).mean())
        # torso scale for sanity: shoulder-to-shoulder width in px
        sho = px(w, "lsho", "rsho", W, H)
        rec["sho_width_px"] = float(np.nanmedian(sho)) if np.isfinite(sho).any() else np.nan
        rows.append(rec)

    out = pd.DataFrame(rows)
    if out.empty:
        print("no valid windows")
        return

    print(f"clips with valid actionable window: {len(out)} / {len(tracks)}")
    print("resolutions:", {f"{w}x{h}": n for (w, h), n in sorted(dim_cache.items())})
    cols = [
        "l_wri_idx_px", "r_wri_idx_px",
        "l_wri_pnk_px", "r_wri_pnk_px",
        "l_idx_pnk_px", "r_idx_pnk_px",
        "sho_width_px",
        "l_idx_v", "r_idx_v",
        "l_frac_tracked", "r_frac_tracked",
    ]
    q = out[cols].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).T
    pd.set_option("display.width", 200)
    print(q[["count", "mean", "5%", "25%", "50%", "75%", "95%", "max"]].round(2).to_string())

    # hand bounding box proxy: max pairwise span among wrist/index/pinky, x1.6 to
    # cover the fingers the pose model does not emit.
    for side in ("l", "r"):
        span = out[[f"{side}_wri_idx_px", f"{side}_wri_pnk_px", f"{side}_idx_pnk_px"]].max(axis=1)
        print(f"\n{side} hand span (px) median={span.median():.1f} "
              f"p5={span.quantile(0.05):.1f} p95={span.quantile(0.95):.1f}  "
              f"est bbox={1.6*span.median():.1f}px")

    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        out.to_csv(args.out, index=False)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
