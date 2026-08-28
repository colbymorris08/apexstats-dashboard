#!/usr/bin/env python3
"""Mine a labeling set for the `bare_hand` class from inside the actionable window.

Why these frames and no others
------------------------------
Labeling trains the computer vision model to identify anatomical markers and equipment
bounding boxes across varied camera angles. Fine-tuning requires diverse training samples
per camera angle accounting for lighting variations (dark vs light / day vs night),
different stadium backgrounds, jersey colors, player complexions, hand positioning, and
glove angles to maximize detection accuracy.

Frames inside the actionable window (set -> peak leg lift -> window close) capture degrees
of hand burial and exposure inside the glove before hand break. Frames where the hand is
cleanly separated land after hand break / arm action onset and are outside the actionable
pre-release window. Pose landmarks cannot resolve hand depth inside the glove because wrists
sit together, so an object detector trained on partial hand-in-glove visibility is required.

Pose landmarks cannot see this: at peak lift the wrists are still together, so
any wrist-separation proxy measures nothing. A detector is the only instrument
that can read it, and it currently has 41 bare_hand boxes.

Bounds
------
Rich 72-column tracks (Thorpe) carry knee/hip landmarks, so the window module
finds peak lift directly. Older 16-column tracks have no knee, so their close is
placed at the median lift+5 offset measured on the rich tracks (0.18s before
arm-action onset) and converted with each clip's own fps.

Selection
---------
Candidate frames are scored with the promoted glove/hand specialist. Frames the
model is unsure about are the informative ones, so the ranking prefers a
confident glove with a weak or absent bare_hand. Each clip contributes at most
one frame, and the per-clip phase is rotated so the set draws burial states
across the whole window rather than clustering at one instant.
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from cv.preflight.parts_detect import detect_parts
from cv.preflight.window import LIFT_TRAIL_MARGIN, actionable_window

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "media" / "detection" / "hand_in_glove"
MANIFEST = ROOT / "data" / "label_manifest_hands.json"

# Median offset of the window's close (peak lift + 5) before arm-action onset,
# measured across the rich Thorpe tracks. Used only for runs whose tracks predate
# the landmark schema and so cannot locate the knee.
CLOSE_BEFORE_ONSET_S = 0.18
# Same, for the set. Older tracks usually do give a set frame; this is the floor.
MAX_WINDOW_S = 1.6

# Sampled positions between set (0.0) and window close (1.0). Weighted late:
# the cue is read "at lift", and burial is most legible as the glove comes up.
PHASES = (0.55, 0.75, 0.9, 1.0, 0.35)


@dataclass
class Source:
    run: str
    pitcher: str
    team: str
    quota: int


SOURCES = [
    Source("drew_thorpe_rich_poc", "Drew Thorpe", "CWS", 45),
    Source("brandon_pfaadt_poc", "Brandon Pfaadt", "ARI", 17),
    Source("bryan_woo_poc", "Bryan Woo", "SEA", 17),
    Source("eduardo_rodriguez_poc", "Eduardo Rodriguez", "ARI", 17),
    Source("merrill_kelly_poc", "Merrill Kelly", "ARI", 17),
    Source("webb_poc", "Logan Webb", "SF", 17),
]


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    """Give the window module the columns it expects, the way primitives does."""
    from cv.preflight.window import _clean

    d = df.copy()
    if all(c in df.columns for c in ("lwri_x", "rwri_x", "lwri_y", "rwri_y")):
        lx, rx = _clean(df, "lwri_x"), _clean(df, "rwri_x")
        ly, ry = _clean(df, "lwri_y"), _clean(df, "rwri_y")
        d["glove_x"] = (lx + rx) / 2
        d["glove_y"] = (ly + ry) / 2
        d["wrist_dist"] = np.hypot(lx - rx, ly - ry)
    return d


def _fps(run: Path, clip_id: str) -> float:
    s = run / "tracks" / f"{clip_id}_summary.json"
    if s.is_file():
        try:
            v = float(json.loads(s.read_text()).get("fps") or 0)
            if v > 1:
                return v
        except Exception:
            pass
    return 30.0


def window_bounds(run: Path, clip_id: str) -> dict | None:
    """[set, close) for one clip, plus the landmarks that explain it."""
    csv = run / "tracks" / f"{clip_id}_tracks.csv"
    if not csv.is_file():
        return None
    try:
        df = _prep(pd.read_csv(csv))
    except Exception:
        return None
    w = actionable_window(df)
    # arm_action_frame is the onset of the delivery burst; delivery_frame is its
    # peak. The window is clamped by onset, so that is the bound to respect.
    onset_raw = w.arm_action_frame if w.arm_action_frame is not None else w.delivery_frame
    if onset_raw is None:
        return None
    fps = _fps(run, clip_id)
    onset = int(onset_raw)

    if w.lift_frame is not None:
        lift = int(w.lift_frame)
        close = min(lift + LIFT_TRAIL_MARGIN, onset)
    else:
        lift = None
        close = max(0, onset - int(round(CLOSE_BEFORE_ONSET_S * fps)))

    start = int(w.set_frame) if w.set_frame is not None else max(0, close - int(round(MAX_WINDOW_S * fps)))
    start = max(0, min(start, close - 2))
    if close - start < 3:
        return None
    return {
        "start": start,
        "close": close,
        "lift": lift,
            "armAction": onset,
        "break": None if w.break_frame is None else int(w.break_frame),
        "fps": fps,
        "method": w.method if w.lift_frame is not None else "lift_offset_estimate",
    }


def read_frame(clip: Path, idx: int):
    cap = cv2.VideoCapture(str(clip))
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, img = cap.read()
        return img if ok else None
    finally:
        cap.release()


def score(img) -> tuple[float, float]:
    """(glove confidence, bare_hand confidence) from the 2-class specialist."""
    g = h = 0.0
    for d in detect_parts(img, conf=0.03):
        if d["cls"] == 0:
            g = max(g, d["conf"])
        elif d["cls"] == 1:
            h = max(h, d["conf"])
    return g, h


def mine_source(src: Source, max_clips: int, seed: int) -> list[dict]:
    run = ROOT / "runs" / src.run
    clips = sorted((run / "clips").glob("*.mp4"))
    random.Random(seed).shuffle(clips)

    kept: list[dict] = []
    for n, clip in enumerate(clips[:max_clips]):
        if len(kept) >= src.quota:
            break
        b = window_bounds(run, clip.stem)
        if b is None:
            continue
        phase = PHASES[n % len(PHASES)]
        idx = int(round(b["start"] + phase * (b["close"] - b["start"])))
        idx = max(b["start"], min(idx, b["close"]))
        img = read_frame(clip, idx)
        if img is None:
            continue
        glove, hand = score(img)
        if glove < 0.15:
            # No glove found at all: the frame is more likely a tracking failure
            # than a hard case, and a labeler cannot read burial without a glove.
            continue
        kept.append({
            "clip": clip.stem,
            "run": src.run,
            "frame": idx,
            "phase": round(phase, 2),
            "gloveConf": round(glove, 3),
            "handConf": round(hand, 3),
            "bounds": b,
            "img": img,
            "pitcher": src.pitcher,
            "team": src.team,
        })
        print(f"  {src.pitcher} {clip.stem[:8]} f{idx} phase {phase:.2f} glove {glove:.2f} hand {hand:.2f}")

    # Uncertainty first: weak or absent bare_hand on a confidently found glove.
    kept.sort(key=lambda r: (r["handConf"], -r["gloveConf"]))
    return kept[: src.quota]


def round_robin(groups: list[list[dict]]) -> list[dict]:
    out = []
    for i in range(max((len(g) for g in groups), default=0)):
        for g in groups:
            if i < len(g):
                out.append(g[i])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-clips", type=int, default=60, help="clips scanned per pitcher")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    groups = []
    for src in SOURCES:
        print(f"{src.pitcher}:")
        rows = mine_source(src, a.max_clips, a.seed)
        print(f"  kept {len(rows)} / quota {src.quota}")
        groups.append(rows)

    frames = []
    for r in round_robin(groups):
        b = r["bounds"]
        span = max(1, b["close"] - b["start"])
        fid = f"hand_{r['run']}_{r['clip'][:8]}_f{r['frame']}"
        path = OUT_DIR / f"{fid}.jpg"
        cv2.imwrite(str(path), r["img"], [cv2.IMWRITE_JPEG_QUALITY, 92])
        frames.append({
            "id": fid,
            "src": f"media/detection/hand_in_glove/{path.name}",
            "pitcher": r["pitcher"],
            "team": r["team"],
            "pitchType": "?",
            "angle": "CF",
            "gloveConf": r["gloveConf"],
            "handConf": r["handConf"],
            "frame": r["frame"],
            "setFrame": b["start"],
            "liftFrame": b["lift"],
            "closeFrame": b["close"],
            "windowPos": round((r["frame"] - b["start"]) / span, 2),
            "boundsMethod": b["method"],
        })

    manifest = {
        "version": 2,
        "angle": "CF_savant",
        "mode": "glove_hand_only",
        "classes": [
            {"id": "pitcher_glove", "label": "Pitcher glove", "color": "#ff8c00"},
            {"id": "bare_hand", "label": "Bare hand (visible portion, even inside glove)", "color": "#f0c040"},
        ],
        "ordering": "round_robin_by_pitcher",
        "note": (
            "Labeling trains the computer vision model to identify anatomical markers and equipment "
            "bounding boxes across varied camera angles. Fine-tuning requires diverse training samples "
            "per camera angle accounting for lighting variations (dark vs light / day vs night), "
            "different stadium backgrounds, jersey colors, player complexions, hand positioning, and "
            "glove angles to maximize detection accuracy. Frames captured from inside the actionable window "
            "(set through peak leg lift + 5) train the detector on degrees of hand burial and exposure inside "
            "the glove. Box the visible portion of the hand even when it is only peeking out of or through "
            "the glove; label glove-only when no hand is visible at all. Both annotations are correct and needed."
        ),
        "frames": frames,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nwrote {len(frames)} frames -> {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
