#!/usr/bin/env python3
"""
Render the catcher-gear detections on real frames so a human can see what the
detector is pointing at.

The placement statistics from catcher_detect_probe.py are suspicious in a
familiar way: at conf >= 0.7 the four catcher classes stack vertically at
cx ~= 0.505 spanning cy 0.31-0.52, which is one body roughly a fifth of the
frame tall, centred, with its top ABOVE the pitcher's hip line (median 0.573).
That is the pitcher's silhouette, not a catcher squatting at the bottom of a CF
view. Numbers this shaped have twice now turned out to be the wrong subject, so
the boxes get looked at rather than argued about.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

COLOURS = {
    "catcher_mitt": (0, 255, 255),
    "catcher_mask": (255, 0, 255),
    "catcher_shin": (0, 255, 0),
    "catcher_cleat": (0, 128, 255),
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe", type=Path, default=Path("runs/catcher_detect_probe.json"))
    ap.add_argument("--clips-dir", type=Path, required=True)
    ap.add_argument("--min-conf", type=float, default=0.5)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--out-dir", type=Path, default=Path("runs/catcher_box_peek"))
    a = ap.parse_args(argv)

    report = json.loads(a.probe.read_text())
    a.out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for rec in report["frames"]:
        keep = [d for d in rec["dets"] if d["conf"] >= a.min_conf]
        if not keep:
            continue
        clip = a.clips_dir / f"{rec['clip']}.mp4"
        cap = cv2.VideoCapture(str(clip))
        cap.set(cv2.CAP_PROP_POS_FRAMES, rec["frame"])
        ok, frame = cap.read()
        cap.release()
        if not ok:
            continue
        h, w = frame.shape[:2]
        for d in keep:
            x1 = int((d["cx"] - d["bw"] / 2) * w)
            y1 = int((d["cy"] - d["bh"] / 2) * h)
            x2 = int((d["cx"] + d["bw"] / 2) * w)
            y2 = int((d["cy"] + d["bh"] / 2) * h)
            c = COLOURS[d["name"]]
            cv2.rectangle(frame, (x1, y1), (x2, y2), c, 2)
            cv2.putText(frame, f"{d['name']} {d['conf']:.2f}", (x1, max(12, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 1, cv2.LINE_AA)
        p = a.out_dir / f"{rec['clip']}_{rec['frame']}.png"
        cv2.imwrite(str(p), frame)
        print(p)
        written += 1
        if written >= a.n:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
