#!/usr/bin/env python3
"""Convert Apex part-label JSON exports into an Ultralytics YOLO dataset layout.

Usage:
  python cv/preflight/yolo_from_labels.py data/labels/apex_labels_YYYY-MM-DD.json

Writes:
  data/yolo_parts/{images,labels}/{train,val}/...
  data/yolo_parts/data.yaml

Then (after `pip install ultralytics`):
  yolo detect train data=data/yolo_parts/data.yaml model=yolov8n.pt epochs=50 imgsz=640
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("labels_json", type=Path, help="Export from label.html")
    ap.add_argument("--out", type=Path, default=Path("data/yolo_parts"))
    ap.add_argument("--val-frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--val-ids", type=Path, help="File of image ids (one per line) to force into val; disables random split")
    ap.add_argument("--only-ids", type=Path, help="File of image ids to restrict the dataset to")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    data = json.loads(args.labels_json.read_text())
    classes = [c["name"] for c in data["classes"]]
    images = list(data.get("images") or [])
    if not images:
        raise SystemExit("No labeled images in export")

    if args.only_ids:
        keep = {ln.strip() for ln in args.only_ids.read_text().splitlines() if ln.strip()}
        images = [im for im in images if im["id"] in keep]

    if args.val_ids:
        val_set = {ln.strip() for ln in args.val_ids.read_text().splitlines() if ln.strip()}
    else:
        rng = random.Random(args.seed)
        rng.shuffle(images)
        n_val = max(1, int(len(images) * args.val_frac)) if len(images) > 4 else max(0, len(images) // 5)
        val_set = set(im["id"] for im in images[:n_val])

    out = args.out if args.out.is_absolute() else root / args.out
    for split in ("train", "val"):
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)

    for im in images:
        split = "val" if im["id"] in val_set else "train"
        src = root / im["file_name"]
        if not src.is_file():
            # allow absolute or already-relative
            src = Path(im["file_name"])
        if not src.is_file():
            print("skip missing", im["file_name"])
            continue
        dst_img = out / "images" / split / f"{im['id']}{src.suffix}"
        shutil.copy2(src, dst_img)
        lines = []
        for b in im["boxes"]:
            cid = int(b["class_id"])
            cx, cy, w, h = b["yolo"]
            lines.append(f"{cid} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        (out / "labels" / split / f"{im['id']}.txt").write_text("\n".join(lines) + ("\n" if lines else ""))

    yaml = out / "data.yaml"
    yaml.write_text(
        "\n".join(
            [
                f"path: {out.resolve()}",
                "train: images/train",
                "val: images/val",
                f"nc: {len(classes)}",
                "names:",
                *[f"  {i}: {n}" for i, n in enumerate(classes)],
                "",
            ]
        )
    )
    print(f"wrote {out} · {len(images)} images · {len(classes)} classes")
    print(f"train: yolo detect train data={yaml} model=yolov8n.pt epochs=50 imgsz=640")


if __name__ == "__main__":
    main()
