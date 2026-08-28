#!/usr/bin/env python3
"""Split the merged 10-class export into two specialist exports.

glove/hand: classes 0-1, every frame that has a glove or hand box (includes the
            2-class hard-glove batch, whose unlabeled catchers are harmless here
            because this model has no catcher classes to suppress).
gear:       classes 2-9 remapped to 0-7, only frames from the fully-labeled
            10-class batches where those parts are actually annotated.

Usage:
  python cv/preflight/split_specialist_labels.py data/labels/apex_labels_merged_v3.json
"""
from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path

GLOVE_HAND = [0, 1]
GEAR = [2, 3, 4, 5, 6, 7, 8, 9]


def subset(data: dict, keep: list[int], frames: list[dict]) -> dict:
    names = [c["name"] for c in data["classes"]]
    remap = {old: new for new, old in enumerate(keep)}
    out_images = []
    for im in frames:
        boxes = [b for b in im["boxes"] if b["class_id"] in remap]
        if not boxes:
            continue
        im2 = copy.deepcopy(im)
        im2["boxes"] = [dict(b, class_id=remap[b["class_id"]]) for b in boxes]
        out_images.append(im2)
    return {
        "format": "apex-parts-labels-v1",
        "angle": data.get("angle", "CF"),
        "classes": [{"name": names[i]} for i in keep],
        "note": f"specialist subset: {[names[i] for i in keep]}",
        "images": out_images,
    }


def report(tag: str, d: dict) -> None:
    names = [c["name"] for c in d["classes"]]
    c = Counter(names[b["class_id"]] for im in d["images"] for b in im["boxes"])
    print(f"{tag}: {len(d['images'])} frames, {sum(c.values())} boxes")
    for i, n in enumerate(names):
        print(f"   {i} {n:<14} {c.get(n, 0)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("merged", type=Path)
    ap.add_argument("--outdir", type=Path, default=Path("data/labels"))
    args = ap.parse_args()

    data = json.loads(args.merged.read_text())
    all_frames = data["images"]
    ten_class = [im for im in all_frames if not im["file_name"].startswith("media/detection/hard_gloves/")]

    gh = subset(data, GLOVE_HAND, all_frames)
    gear = subset(data, GEAR, ten_class)
    (args.outdir / "apex_labels_glovehand.json").write_text(json.dumps(gh, indent=1))
    (args.outdir / "apex_labels_gear.json").write_text(json.dumps(gear, indent=1))
    report("glove/hand", gh)
    report("gear", gear)


if __name__ == "__main__":
    main()
