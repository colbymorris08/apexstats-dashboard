#!/usr/bin/env python3
"""Compare parts-detector checkpoints: the single 10-class models (v2, v3) and
the two-model specialist split (glove/hand + gear).

Evaluates on the 10 held-out hard glove frames (excluded from every training
run), the gear val split, and the hand-labeled Bryan Woo FF/SL frames.

Usage:
  python cv/preflight/eval_parts_models.py
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs/yolo/detect/runs/yolo"

V2 = ROOT / "cv/preflight/models/parts_yolov8n.pt"
V3 = RUNS / "parts_v3/weights/best.pt"
GLOVEHAND = RUNS / "glovehand_v1/weights/best.pt"
GEAR = RUNS / "gear_v1/weights/best.pt"

# Hard-glove eval data, in each model's own label space.
HARD_10CLASS = ROOT / "data/yolo_hardval/data.yaml"      # v2/v3: classes 0-9
HARD_2CLASS = ROOT / "data/yolo_hardval_gh/data.yaml"    # specialist: classes 0-1
GEAR_DATA = ROOT / "data/yolo_gear/data.yaml"

GT_WOO = {
    "FF": {"img": "media/detection/woo_ff_glove_full.jpg", "cx": 457.9, "cy": 331.1},
    "SL": {"img": "media/detection/woo_sl_glove_full.jpg", "cx": 495.9, "cy": 416.8},
}


def per_class_map(ckpt: Path, data: Path, tag: str) -> dict[str, float]:
    r = YOLO(str(ckpt)).val(data=str(data), imgsz=640, device="cpu", workers=0, batch=4,
                            project="runs/yolo/_eval", name=tag, exist_ok=True,
                            plots=False, verbose=False)
    out = {"overall_mAP50": round(float(r.box.map50), 4)}
    for i, ci in enumerate(r.box.ap_class_index):
        out[r.names[int(ci)]] = round(float(r.box.ap50[i]), 4)
    return out


def glove_conf(ckpt: Path, images: list[Path], glove_idx: int = 0) -> dict[str, float]:
    m = YOLO(str(ckpt))
    out = {}
    for p in images:
        r = m.predict(str(p), imgsz=640, device="cpu", conf=0.001, verbose=False)[0]
        c = [float(b.conf) for b in r.boxes if int(b.cls) == glove_idx]
        out[p.stem] = max(c) if c else 0.0
    return out


def woo_test(ckpt: Path, glove_idx: int = 0) -> dict:
    """Is the top-ranked glove box actually on the glove?"""
    m = YOLO(str(ckpt))
    res = {}
    for pitch, g in GT_WOO.items():
        r = m.predict(str(ROOT / g["img"]), imgsz=640, device="cpu", conf=0.001, verbose=False)[0]
        boxes = sorted(([float(b.conf), [float(v) for v in b.xyxy[0]]]
                        for b in r.boxes if int(b.cls) == glove_idx), reverse=True)
        ranked = []
        for rank, (conf, (x1, y1, x2, y2)) in enumerate(boxes[:5], 1):
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            ranked.append({"rank": rank, "conf": round(conf, 4),
                           "px_err": round(((cx - g["cx"]) ** 2 + (cy - g["cy"]) ** 2) ** 0.5, 1)})
        # "Correct" = within 15px of the hand-labeled centre (box side is ~35-50px).
        correct = [b for b in ranked if b["px_err"] <= 15]
        res[pitch] = {
            "top1_px_err": ranked[0]["px_err"] if ranked else None,
            "top1_conf": ranked[0]["conf"] if ranked else None,
            "correct_box_rank": correct[0]["rank"] if correct else None,
            "PASS": bool(ranked and ranked[0]["px_err"] <= 15),
            "top5": ranked,
        }
    return res


def main() -> None:
    argparse.ArgumentParser().parse_args()
    rep: dict = {}

    # 1. Three-way on the held-out hard glove frames.
    rep["heldout_hard_frames_mAP50"] = {
        "v2_10class": per_class_map(V2, HARD_10CLASS, "hard_v2"),
        "v3_10class": per_class_map(V3, HARD_10CLASS, "hard_v3"),
        "glovehand_specialist": per_class_map(GLOVEHAND, HARD_2CLASS, "hard_gh"),
    }

    heldout = {ln.strip() for ln in (ROOT / "data/val_ids_hard.txt").read_text().splitlines() if ln.strip()}
    hard_imgs = sorted((ROOT / "media/detection/hard_gloves").glob("*.jpg"))
    confs = {n: glove_conf(c, hard_imgs) for n, c in
             [("v2", V2), ("v3", V3), ("glovehand", GLOVEHAND)]}
    ho = [p.stem for p in hard_imgs if p.stem in heldout]
    rep["heldout_hard_glove_confidence"] = {
        "median": {n: round(st.median(confs[n][s] for s in ho), 4) for n in confs},
        "mean": {n: round(st.mean(confs[n][s] for s in ho), 4) for n in confs},
        "n_at_or_above_0.25": {n: sum(confs[n][s] >= 0.25 for s in ho) for n in confs},
        "per_frame": {s: {n: round(confs[n][s], 4) for n in confs} for s in ho},
    }

    # 2. Did the catcher/gear classes recover?
    rep["gear_classes_mAP50"] = {
        "v2_10class": per_class_map(V2, GEAR_DATA.parent.parent / "yolo_parts_v3/data.yaml", "gear_cmp_v2"),
        "v3_10class": per_class_map(V3, GEAR_DATA.parent.parent / "yolo_parts_v3/data.yaml", "gear_cmp_v3"),
        "gear_specialist": per_class_map(GEAR, GEAR_DATA, "gear_cmp_gear"),
    }

    # 3. Woo acceptance test.
    rep["woo_acceptance"] = {
        "v2_10class": woo_test(V2),
        "v3_10class": woo_test(V3),
        "glovehand_specialist": woo_test(GLOVEHAND),
    }

    out = ROOT / "runs/yolo/_eval/three_way_comparison.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
