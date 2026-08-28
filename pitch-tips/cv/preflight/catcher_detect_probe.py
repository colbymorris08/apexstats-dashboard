#!/usr/bin/env python3
"""
Does the trained parts detector actually find the catcher in a CF frame?

This question gates the whole detector-based catcher localisation plan in
docs/catcher_subject_bug.md. The plan is: crop the catcher region with
``parts_gear.pt``, then run pose on the crop. If the gear classes do not fire on
real frames, there is no crop and the plan is dead before any feature is written.

The detector's own validation is not evidence here: ``catcher_mitt`` reports
mAP50 0.995 on **5 instances in 5 images** (runs/yolo_parts_v2.log), which is a
number with no power behind it. So the hit rate is measured directly on frames
sampled out of real clips.

Read-only with respect to the league pipeline: it opens cached mp4s and writes
nothing but its own JSON report.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import cv2

from preflight.parts_detect import CLASSES, detect_parts

# Classes that could anchor a catcher crop. The mitt is the primary target named
# in the deferral note; mask/shin/cleat are worth measuring alongside it because
# any of them localises the same body, and the mask in particular is the largest
# and least deformable piece of catcher gear in the CF view.
CATCHER_CLASSES = ("catcher_mitt", "catcher_mask", "catcher_shin", "catcher_cleat")


def probe_clip(clip: Path, n_frames: int, conf: float) -> list[dict]:
    cap = cv2.VideoCapture(str(clip))
    if not cap.isOpened():
        return []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total <= 0:
        cap.release()
        return []
    # Sample the middle 60% of the clip: Savant clips open and close on broadcast
    # framing that contains no CF view at all, and a hit rate diluted by frames
    # with no catcher in them would understate the detector rather than measure it.
    lo, hi = int(total * 0.2), int(total * 0.8)
    idxs = sorted(random.Random(0).sample(range(lo, hi), min(n_frames, hi - lo)))
    out = []
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, frame = cap.read()
        if not ok:
            continue
        h, w = frame.shape[:2]
        dets = detect_parts(frame, conf=conf)
        rec = {"clip": clip.stem, "frame": i, "w": w, "h": h, "dets": []}
        for d in dets:
            if d["name"] not in CATCHER_CLASSES:
                continue
            x1, y1, x2, y2 = d["xyxy"]
            rec["dets"].append({
                "name": d["name"],
                "conf": round(d["conf"], 4),
                # Normalised centre and size, so placement can be judged against
                # the CF geometry the same way pitcher torso length was.
                "cx": round((x1 + x2) / 2 / w, 4),
                "cy": round((y1 + y2) / 2 / h, 4),
                "bw": round((x2 - x1) / w, 4),
                "bh": round((y2 - y1) / h, 4),
            })
        out.append(rec)
    cap.release()
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clips-dir", type=Path, required=True)
    ap.add_argument("--n-clips", type=int, default=6)
    ap.add_argument("--n-frames", type=int, default=12)
    ap.add_argument("--conf", type=float, default=0.05)
    ap.add_argument("--out", type=Path, default=Path("runs/catcher_detect_probe.json"))
    a = ap.parse_args(argv)

    clips = sorted(a.clips_dir.glob("*.mp4"))[: a.n_clips]
    recs: list[dict] = []
    for c in clips:
        recs.extend(probe_clip(c, a.n_frames, a.conf))
        print(f"{c.stem}: {len(recs)} frames probed", flush=True)

    n = len(recs)
    by_class = {}
    for name in CATCHER_CLASSES:
        hits = [r for r in recs if any(d["name"] == name for d in r["dets"])]
        by_class[name] = {
            "frames_with_hit": len(hits),
            "hit_rate": round(len(hits) / n, 4) if n else None,
        }
    any_hit = sum(1 for r in recs if r["dets"])
    report = {
        "n_frames": n,
        "n_clips": len(clips),
        "conf": a.conf,
        "any_catcher_class_hit_rate": round(any_hit / n, 4) if n else None,
        "by_class": by_class,
        "frames": recs,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "frames"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
