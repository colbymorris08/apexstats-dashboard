"""Track pitcher presentation cues on a single clip (Apex Preflight CV).

Outputs frame-level tracks for pitcher glove, hands, and optional face landmarks.
Designed so club angles (X1–X4) plug in via the same schema with a different
camera_id — no dependency on third-party research repos.

Requires: opencv-python, ultralytics (optional; falls back to motion heuristics).
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import cv2


FEATURE_WINDOW_NOTE = "Use only frames in [release-2.0s, release-0.1s] for modeling."


def _try_yolo():
    try:
        from ultralytics import YOLO  # type: ignore

        return YOLO
    except Exception:
        return None


def track_clip(
    clip_path: Path,
    out_dir: Path,
    *,
    camera_id: str = "CF",
    weights: str | None = None,
) -> Path:
    """
    Run per-frame detection/tracking and write CSV + summary JSON.

    Columns: frame, t_sec, glove_cx, glove_cy, hand_cx, hand_cy, conf, camera_id
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = clip_path.stem
    csv_path = out_dir / f"{stem}_tracks.csv"
    summary_path = out_dir / f"{stem}_summary.json"

    cap = cv2.VideoCapture(str(clip_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open clip: {clip_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    YOLO = _try_yolo()
    model = None
    if YOLO is not None:
        # Prefer a club-trained pitcher-glove checkpoint when available.
        model = YOLO(weights or "yolov8n.pt")

    rows: list[dict[str, Any]] = []
    frame_i = 0
    prev_gray = None

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t_sec = frame_i / fps
        h, w = frame.shape[:2]
        glove_cx = glove_cy = hand_cx = hand_cy = None
        conf = 0.0

        if model is not None:
            # Generic person/sports objects until Apex pitcher-glove weights are loaded.
            results = model.predict(frame, verbose=False)
            boxes = results[0].boxes if results else None
            if boxes is not None and len(boxes):
                # Take highest-confidence box as provisional torso/glove proxy.
                best = max(boxes, key=lambda b: float(b.conf[0]))
                x1, y1, x2, y2 = [float(v) for v in best.xyxy[0].tolist()]
                glove_cx = (x1 + x2) / 2.0 / w
                glove_cy = (y1 + y2) / 2.0 / h
                hand_cx, hand_cy = glove_cx, glove_cy
                conf = float(best.conf[0])
        else:
            # Motion centroid fallback (no weights required) for pipeline wiring.
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            if prev_gray is not None:
                delta = cv2.absdiff(prev_gray, gray)
                _, thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)
                m = cv2.moments(thresh)
                if m["m00"] > 0:
                    glove_cx = (m["m10"] / m["m00"]) / w
                    glove_cy = (m["m01"] / m["m00"]) / h
                    hand_cx, hand_cy = glove_cx, glove_cy
                    conf = 0.2
            prev_gray = gray

        rows.append(
            {
                "frame": frame_i,
                "t_sec": round(t_sec, 4),
                "glove_cx": "" if glove_cx is None else round(glove_cx, 5),
                "glove_cy": "" if glove_cy is None else round(glove_cy, 5),
                "hand_cx": "" if hand_cx is None else round(hand_cx, 5),
                "hand_cy": "" if hand_cy is None else round(hand_cy, 5),
                "conf": round(conf, 4),
                "camera_id": camera_id,
            }
        )
        frame_i += 1

    cap.release()

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "frame",
                "t_sec",
                "glove_cx",
                "glove_cy",
                "hand_cx",
                "hand_cy",
                "conf",
                "camera_id",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "clip": str(clip_path),
        "camera_id": camera_id,
        "n_frames": len(rows),
        "fps": fps,
        "backend": "ultralytics" if model is not None else "opencv_motion_fallback",
        "feature_window_note": FEATURE_WINDOW_NOTE,
        "tracks_csv": str(csv_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2))
    return csv_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Apex Preflight — clip tracker")
    p.add_argument("--clip", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("tracks"))
    p.add_argument("--camera-id", default="CF", help="CF | X1 | X2 | X3 | X4 | TEAM")
    p.add_argument("--weights", default=None, help="Optional YOLO weights path")
    args = p.parse_args(argv)
    path = track_clip(args.clip, args.out, camera_id=args.camera_id, weights=args.weights)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
