#!/usr/bin/env python3
"""Production parts detector: two specialist models merged into one result.

The single 10-class model was poisoned by the 2-class hard-glove batch, whose
frames contain unlabeled catchers and plates -- YOLO reads those as background
and learns to suppress the gear classes. Splitting removes the conflict:

  parts_glovehand.pt  pitcher_glove, bare_hand  (all 64 glove/hand frames)
  parts_gear.pt       belt .. plate             (28 fully-labeled frames only)

Detections are returned in the ORIGINAL 10-class index space, so this is a
drop-in superset of what the old single model produced.

  from cv.preflight.parts_detect import detect_parts, CLASSES
  for d in detect_parts("frame.jpg"):
      d["cls"], d["name"], d["conf"], d["xyxy"]
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

CLASSES = ["pitcher_glove", "bare_hand", "belt", "cheek", "knee",
           "catcher_mitt", "catcher_mask", "catcher_shin", "catcher_cleat", "plate"]

MODELS = Path(__file__).resolve().parent / "models"
GLOVEHAND_W = MODELS / "parts_glovehand.pt"
GEAR_W = MODELS / "parts_gear.pt"

# Specialist class index -> canonical 10-class index.
_OFFSET = {"glovehand": 0, "gear": 2}


@lru_cache(maxsize=None)
def _load(weights: str):
    from ultralytics import YOLO

    return YOLO(weights)


def detect_parts(image, conf: float = 0.05, imgsz: int = 640, device: str = "cpu") -> list[dict]:
    """Run both specialists and merge. Returns detections sorted by confidence."""
    out: list[dict] = []
    for tag, w in (("glovehand", GLOVEHAND_W), ("gear", GEAR_W)):
        if not w.is_file():
            continue
        res = _load(str(w)).predict(image, imgsz=imgsz, conf=conf, device=device, verbose=False)[0]
        off = _OFFSET[tag]
        for b in res.boxes:
            cid = int(b.cls) + off
            out.append({
                "cls": cid,
                "name": CLASSES[cid],
                "conf": float(b.conf),
                "xyxy": [float(v) for v in b.xyxy[0]],
                "model": tag,
            })
    out.sort(key=lambda d: d["conf"], reverse=True)
    return out


def best_part(image, name: str, **kw) -> dict | None:
    """Highest-confidence detection for one class, or None."""
    want = CLASSES.index(name)
    hits = [d for d in detect_parts(image, **kw) if d["cls"] == want]
    return hits[0] if hits else None


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--conf", type=float, default=0.05)
    a = ap.parse_args()
    print(json.dumps(detect_parts(a.image, conf=a.conf), indent=2))
