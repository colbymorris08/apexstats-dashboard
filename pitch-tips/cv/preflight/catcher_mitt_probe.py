#!/usr/bin/env python3
"""
Can the pre-pitch glove target be measured from the DETECTOR alone?

Pose-on-crop identifies the catcher on 3-4% of frames and the rate does not
improve with a bigger pose model (catcher_model_probe.py: lite 4.4%, full 3.96%,
heavy 1.76%). That ceiling kills any cue needing articulated landmarks — squat
depth, stance width, body angle, mitt orientation all need them.

The pre-pitch glove TARGET does not. Where the mitt is set is a position, and a
position needs a box, not a skeleton: ``catcher_mitt`` gives the mitt and
``plate`` gives the reference it should be measured against. So this probe asks
the only question that matters for that family — how often, and how precisely,
can the detector place the mitt and the plate on the same frame.

Reported per confidence level, because the answer at conf 0.05 and conf 0.5 are
different measurements and only one of them is trustworthy. Note the prior on
these two classes is weak: ``parts_gear.pt`` was trained on 28 fully-labeled
frames and ``catcher_mitt`` is validated on 5 instances in 5 images
(runs/yolo_parts_v2.log), so nothing here should be inferred from the model's own
reported mAP.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path

import cv2
import numpy as np

from preflight.parts_detect import detect_parts

CONF_LEVELS = (0.05, 0.15, 0.25, 0.50)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clips-dir", type=Path, required=True)
    ap.add_argument("--n-clips", type=int, default=8)
    ap.add_argument("--stride", type=int, default=10)
    ap.add_argument("--out", type=Path, default=Path("runs/catcher_mitt_probe.json"))
    a = ap.parse_args(argv)

    per_frame: list[dict] = []
    for clip in sorted(a.clips_dir.glob("*.mp4"))[: a.n_clips]:
        cap = cv2.VideoCapture(str(clip))
        i = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if i % a.stride == 0:
                h, w = frame.shape[:2]
                rec = {"clip": clip.stem, "frame": i, "mitt": [], "plate": []}
                for d in detect_parts(frame, conf=0.05):
                    if d["name"] not in ("catcher_mitt", "plate"):
                        continue
                    x1, y1, x2, y2 = d["xyxy"]
                    rec["mitt" if d["name"] == "catcher_mitt" else "plate"].append({
                        "conf": round(d["conf"], 4),
                        "cx": round((x1 + x2) / 2 / w, 5),
                        "cy": round((y1 + y2) / 2 / h, 5),
                        "bw": round((x2 - x1) / w, 5),
                    })
                per_frame.append(rec)
            i += 1
        cap.release()
        print(f"{clip.stem}: {len(per_frame)} frames", flush=True)

    n = len(per_frame)
    out: dict = {"n_frames": n, "n_clips": a.n_clips, "stride": a.stride, "by_conf": {}}
    for c in CONF_LEVELS:
        mitt = [r for r in per_frame if any(d["conf"] >= c for d in r["mitt"])]
        plate = [r for r in per_frame if any(d["conf"] >= c for d in r["plate"])]
        both = [r for r in per_frame
                if any(d["conf"] >= c for d in r["mitt"]) and any(d["conf"] >= c for d in r["plate"])]
        # Positional stability of the mitt WITHIN a clip. The catcher does move
        # his mitt, but only inches; a detector whose per-frame scatter is as
        # large as the plate is wide cannot resolve inside from outside, which is
        # the whole cue. Measured as the interdecile spread of the best-box
        # centre x, per clip, then summarised across clips.
        spreads = []
        for clipname in {r["clip"] for r in mitt}:
            xs = [max((d for d in r["mitt"] if d["conf"] >= c), key=lambda d: d["conf"])["cx"]
                  for r in mitt if r["clip"] == clipname]
            if len(xs) >= 5:
                spreads.append(float(np.percentile(xs, 90) - np.percentile(xs, 10)))
        out["by_conf"][str(c)] = {
            "mitt_frame_rate": round(len(mitt) / n, 4) if n else None,
            "plate_frame_rate": round(len(plate) / n, 4) if n else None,
            "both_frame_rate": round(len(both) / n, 4) if n else None,
            "n_clips_with_any_mitt": len({r["clip"] for r in mitt}),
            "mitt_cx_interdecile_spread_within_clip": {
                "median": round(st.median(spreads), 5) if spreads else None,
                "max": round(max(spreads), 5) if spreads else None,
                "n_clips": len(spreads),
            },
        }
    out["frames"] = per_frame
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "frames"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
