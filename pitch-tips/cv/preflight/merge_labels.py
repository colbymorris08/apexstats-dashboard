#!/usr/bin/env python3
"""Merge Preflight label JSON exports into one training export, with validation.

Usage:
  python cv/preflight/merge_labels.py out.json in1.json in2.json ...
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("inputs", type=Path, nargs="+")
    args = ap.parse_args()

    canon: list[str] = []
    by_id: dict[str, dict] = {}
    origin: dict[str, str] = {}
    problems: list[str] = []

    for p in args.inputs:
        d = json.loads(p.read_text())
        names = [c["name"] for c in d["classes"]]
        # A shorter class list must be a prefix of the canonical one, otherwise
        # class_id integers mean different things across exports.
        if len(names) > len(canon):
            if names[: len(canon)] != canon:
                problems.append(f"CLASS MISMATCH {p.name}: {names} vs canon {canon}")
            canon = names
        elif names != canon[: len(names)]:
            problems.append(f"CLASS MISMATCH {p.name}: {names} vs canon prefix {canon[:len(names)]}")

        for im in d.get("images") or []:
            iid = im["id"]
            if iid in by_id:
                prev, new = by_id[iid], im
                if len(new["boxes"]) >= len(prev["boxes"]):
                    by_id[iid] = new
                    problems.append(f"DUP id {iid}: {origin[iid]} ({len(prev['boxes'])} boxes) -> {p.name} ({len(new['boxes'])} boxes), kept newer")
                else:
                    problems.append(f"DUP id {iid}: kept {origin[iid]} ({len(prev['boxes'])}) over {p.name} ({len(new['boxes'])})")
                    continue
            by_id[iid] = im
            origin[iid] = p.name

    # Geometry + class-range validation.
    per_class = Counter()
    n_boxes = 0
    for iid, im in by_id.items():
        src = ROOT / im["file_name"]
        if not src.is_file():
            problems.append(f"MISSING IMAGE {iid}: {im['file_name']}")
        for b in im["boxes"]:
            n_boxes += 1
            cid = int(b["class_id"])
            if not (0 <= cid < len(canon)):
                problems.append(f"BAD CLASS ID {iid}: {cid}")
                continue
            if canon[cid] != b["class"]:
                problems.append(f"CLASS/ID DISAGREE {iid}: id {cid} says {canon[cid]!r} but label is {b['class']!r}")
            per_class[canon[cid]] += 1
            cx, cy, w, h = b["yolo"]
            if w <= 0 or h <= 0:
                problems.append(f"ZERO-AREA BOX {iid}: {b['yolo']}")
            if not (0 <= cx - w / 2 and cx + w / 2 <= 1.0001 and 0 <= cy - h / 2 and cy + h / 2 <= 1.0001):
                problems.append(f"OUT OF BOUNDS {iid}: {b['yolo']}")

    images = sorted(by_id.values(), key=lambda i: i["id"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "format": "apex-parts-labels-v1",
        "angle": "CF",
        "classes": [{"name": n} for n in canon],
        "note": f"merged from {', '.join(p.name for p in args.inputs)}",
        "images": images,
    }, indent=1))

    print(f"merged -> {args.out}")
    print(f"images: {len(images)}  boxes: {n_boxes}")
    print("classes:", ", ".join(f"{i}:{n}" for i, n in enumerate(canon)))
    print("\nper-class box counts:")
    for i, n in enumerate(canon):
        print(f"  {i:2d} {n:<14} {per_class.get(n, 0)}")
    print("\nframes with glove but no hand (expected, hand is inside glove pre-break):",
          sum(1 for im in images
              if any(b["class_id"] == 0 for b in im["boxes"]) and not any(b["class_id"] == 1 for b in im["boxes"])))
    if problems:
        print(f"\n!! {len(problems)} problems:")
        for x in problems:
            print("  -", x)
    else:
        print("\nvalidation: OK (classes consistent, boxes in bounds, no zero-area, no dup clobber)")
    sys.exit(0)


if __name__ == "__main__":
    main()
