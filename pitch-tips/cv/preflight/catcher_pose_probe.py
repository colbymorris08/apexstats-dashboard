#!/usr/bin/env python3
"""
What fraction of frames yield an independently identified catcher, and is the
subject actually the catcher?

Two questions, deliberately kept together, because the pitcher fix taught that a
coverage rate is meaningless without a placement check beside it: the pose-based
catcher selector populated its columns on 98.6% of frames and that 98.6% was the
hit rate of a fallback returning the pitcher.

So this reports the identification rate at every stage AND the geometry of what
was identified, in the catcher's own torso units, the way the pitcher selector
was verified (median torso 0.1245, 0 implausible frames of 380). It also renders
overlays, because both wrong-subject bugs on this project were settled by looking
at the picture rather than by argument.

Read-only with respect to the league pipeline: it opens cached mp4s and writes
nothing but its own report and images.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as st
from pathlib import Path

import cv2

from preflight.catcher_locate import KEEP_LANDMARKS, catcher_crop, locate_catcher, make_pose_landmarker
from preflight.parts_detect import detect_parts

SKELETON = [(11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24),
            (23, 24), (23, 25), (25, 27), (24, 26), (26, 28)]
NAME_BY_IDX = {v: k for k, v in KEEP_LANDMARKS.items()}


def _draw(frame, cp, out_path: Path) -> None:
    h, w = frame.shape[:2]
    vis = frame.copy()

    def px(nm):
        x, y, _ = cp.landmarks[nm]
        return int(x * w), int(y * h)

    for p, q in SKELETON:
        a, b = NAME_BY_IDX.get(p), NAME_BY_IDX.get(q)
        if a in cp.landmarks and b in cp.landmarks:
            cv2.line(vis, px(a), px(b), (0, 255, 0), 2)
    for nm in cp.landmarks:
        cv2.circle(vis, px(nm), 3, (0, 0, 255), -1)
    cv2.putText(vis, f"{cp.anchor_class} {cp.anchor_conf:.2f} d={cp.anchor_dist_torsos:.2f}T torso={cp.torso:.3f}",
                (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.imwrite(str(out_path), vis)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clips-dir", type=Path, required=True)
    ap.add_argument("--n-clips", type=int, default=6)
    ap.add_argument("--n-frames", type=int, default=12)
    ap.add_argument("--out", type=Path, default=Path("runs/catcher_pose_probe.json"))
    ap.add_argument("--peek-dir", type=Path, default=None)
    ap.add_argument("--n-peek", type=int, default=6)
    a = ap.parse_args(argv)

    recs: list[dict] = []
    n_peek = 0
    if a.peek_dir:
        a.peek_dir.mkdir(parents=True, exist_ok=True)

    with make_pose_landmarker() as pose:
        for clip in sorted(a.clips_dir.glob("*.mp4"))[: a.n_clips]:
            cap = cv2.VideoCapture(str(clip))
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            if total <= 0:
                cap.release()
                continue
            lo, hi = int(total * 0.2), int(total * 0.8)
            for i in sorted(random.Random(0).sample(range(lo, hi), min(a.n_frames, hi - lo))):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ok, frame = cap.read()
                if not ok:
                    continue
                dets = detect_parts(frame, conf=0.05)
                crop = catcher_crop(frame, dets)
                cp, reason = locate_catcher(frame, pose, dets)
                rec = {
                    "clip": clip.stem,
                    "frame": i,
                    "reason": reason,
                    "had_crop": crop is not None,
                }
                if cp is not None:
                    lmk = cp.landmarks
                    hip_y = (lmk["clhip"][1] + lmk["crhip"][1]) / 2
                    hip_x = (lmk["clhip"][0] + lmk["crhip"][0]) / 2
                    knee_y = max(lmk["clkne"][1], lmk["crkne"][1])
                    rec.update(
                        torso=round(cp.torso, 5),
                        hip_x=round(hip_x, 4),
                        hip_y=round(hip_y, 4),
                        # Positive = knees above hips = squatting.
                        knee_rise_torsos=round((hip_y - knee_y) / cp.torso, 3),
                        stance_width_torsos=round(abs(lmk["clhip"][0] - lmk["crhip"][0]) / cp.torso, 3),
                        anchor_class=cp.anchor_class,
                        anchor_conf=round(cp.anchor_conf, 3),
                        anchor_dist_torsos=round(cp.anchor_dist_torsos, 3),
                        n_anchor_classes=cp.n_anchor_classes,
                        crop_px=list(cp.crop_px),
                        vis_hip=round(min(lmk["clhip"][2], lmk["crhip"][2]), 3),
                        vis_wri=round(min(lmk["clwri"][2], lmk["crwri"][2]), 3),
                    )
                    if a.peek_dir and n_peek < a.n_peek:
                        _draw(frame, cp, a.peek_dir / f"{clip.stem}_{i}_catcher.png")
                        n_peek += 1
                recs.append(rec)
            cap.release()
            print(f"{clip.stem}: {len(recs)} frames", flush=True)

    n = len(recs)
    reasons: dict[str, int] = {}
    for r in recs:
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    hits = [r for r in recs if r["reason"] == "catcher"]

    def q(key):
        v = sorted(r[key] for r in hits if key in r)
        if not v:
            return None
        return {
            "p10": round(v[len(v) // 10], 4),
            "median": round(st.median(v), 4),
            "p90": round(v[min(len(v) - 1, int(len(v) * 0.9))], 4),
            "min": round(v[0], 4),
            "max": round(v[-1], 4),
        }

    report = {
        "n_frames": n,
        "n_clips": a.n_clips,
        "identification_rate": round(len(hits) / n, 4) if n else None,
        "crop_rate": round(sum(1 for r in recs if r["had_crop"]) / n, 4) if n else None,
        "reasons": reasons,
        # Placement verification. A real squatting catcher in this framing should
        # show knees at or above the hips (knee_rise_torsos >= ~0), a stance
        # wider than the 0.012 that exposed the pitcher-substitution bug, a hip_y
        # ABOVE the pitcher's 0.573, and a torso in a narrow, plausible band.
        "placement": {k: q(k) for k in (
            "torso", "hip_x", "hip_y", "knee_rise_torsos", "stance_width_torsos",
            "anchor_dist_torsos", "vis_hip", "vis_wri")},
        "implausible": {
            "knees_below_hips": sum(1 for r in hits if r["knee_rise_torsos"] < -0.35),
            "hip_y_at_pitcher_band": sum(1 for r in hits if r["hip_y"] > 0.56),
            "stance_narrower_than_bug": sum(1 for r in hits if r["stance_width_torsos"] < 0.05),
        },
        "frames": recs,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "frames"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
