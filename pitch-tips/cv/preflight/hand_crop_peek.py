"""
Read-only visual check: crop the pitcher's hand region from real clips inside
the actionable window and upscale it, so the resolution verdict can be seen
rather than argued about.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preflight.window import actionable_window  # noqa: E402

BOX = 48  # px side of the crop taken from the source frame
ZOOM = 6
# CF-framed pitcher shoulder width. Outside this the tracked pose is a
# broadcast close-up (hitter, catcher, dugout), not the pitcher we care about.
SHO_MIN, SHO_MAX = 25.0, 75.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/drew_thorpe_rich_poc")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--out", default="runs/drew_thorpe_rich_poc/audit/hand_crops.png")
    args = ap.parse_args()

    tiles = []
    for tp in sorted(glob.glob(os.path.join(args.run, "tracks", "*_tracks.csv"))):
        if len(tiles) >= args.n:
            break
        pid = os.path.basename(tp).replace("_tracks.csv", "")
        clip = os.path.join(args.run, "clips", f"{pid}.mp4")
        if not os.path.exists(clip):
            continue
        df = pd.read_csv(tp)
        win = actionable_window(df)
        if not win.valid or win.end - win.start < 5:
            continue
        w = df.iloc[win.start : win.end]
        cand = w.dropna(subset=["rwri_x", "rwri_y", "lsho_x", "rsho_x"])
        if cand.empty:
            continue
        sho = np.hypot(
            (cand["lsho_x"] - cand["rsho_x"]) * 1280, (cand["lsho_y"] - cand["rsho_y"]) * 720
        )
        cand = cand[(sho >= SHO_MIN) & (sho <= SHO_MAX)]
        if cand.empty:
            continue
        # Savant clips open on a broadcast close-up, and the window starts at
        # frame 0, so early frames are not the CF pitcher. Sample near the end
        # of the window, just before hand break, where the CF view is live.
        row = cand.iloc[int(len(cand) * 0.9)]
        cap = cv2.VideoCapture(clip)
        W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(row["frame"]))
        ok, frame = cap.read()
        cap.release()
        if not ok:
            continue
        cx, cy = int(row["rwri_x"] * W), int(row["rwri_y"] * H)
        x0, y0 = max(0, cx - BOX // 2), max(0, cy - BOX // 2)
        crop = frame[y0 : y0 + BOX, x0 : x0 + BOX]
        if crop.shape[0] != BOX or crop.shape[1] != BOX:
            crop = cv2.copyMakeBorder(
                crop, 0, BOX - crop.shape[0], 0, BOX - crop.shape[1], cv2.BORDER_CONSTANT
            )
        big = cv2.resize(crop, (BOX * ZOOM, BOX * ZOOM), interpolation=cv2.INTER_NEAREST)
        cv2.putText(big, pid[:8], (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        tiles.append(big)

    if not tiles:
        print("no crops")
        return
    cols = 4
    rows = [np.hstack(tiles[i : i + cols]) for i in range(0, len(tiles) - len(tiles) % cols, cols)]
    grid = np.vstack(rows)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    cv2.imwrite(args.out, grid)
    print("wrote", args.out, grid.shape, f"({BOX}px source crops at {ZOOM}x)")


if __name__ == "__main__":
    main()
