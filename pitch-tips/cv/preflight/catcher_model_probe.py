#!/usr/bin/env python3
"""
Which pose model finds the catcher, and how often?

Clip-level localisation identifies a catcher on 3.3% of frames with the ``lite``
pose model, and the dominant rejection is ``no_pose_in_crop`` at 50-67%: the crop
is on the catcher and the model returns nothing in it. That is a capability
limit, not a threshold to loosen, so the question is whether a larger model has
the capability.

This is a change of estimator, not of gate: the accept criteria (squatting,
inside the region core) are identical across variants, so the comparison is
purely how many frames each model can resolve a catcher on.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path

import cv2

from preflight.catcher_locate import catcher_in_region, clip_catcher_region, make_pose_landmarker


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clips-dir", type=Path, required=True)
    ap.add_argument("--n-clips", type=int, default=3)
    ap.add_argument("--stride", type=int, default=8)
    ap.add_argument("--variants", default="lite,full,heavy")
    ap.add_argument("--out", type=Path, default=Path("runs/catcher_model_probe.json"))
    a = ap.parse_args(argv)

    clips = sorted(a.clips_dir.glob("*.mp4"))[: a.n_clips]
    # Regions are computed once and shared, so the only thing that varies between
    # variants is the pose model.
    regions = {}
    for clip in clips:
        region, diag = clip_catcher_region(clip)
        regions[clip] = region
        print(f"region {clip.stem}: {diag.get('reason')}", flush=True)

    out = {}
    for variant in a.variants.split(","):
        reasons: dict[str, int] = {}
        seen = 0
        torsos: list[float] = []
        hipys: list[float] = []
        with make_pose_landmarker(variant) as pose:
            for clip in clips:
                region = regions[clip]
                if region is None:
                    continue
                cap = cv2.VideoCapture(str(clip))
                i = 0
                while True:
                    ok, frame = cap.read()
                    if not ok:
                        break
                    if i % a.stride == 0:
                        seen += 1
                        cp, why = catcher_in_region(frame, pose, region)
                        reasons[why] = reasons.get(why, 0) + 1
                        if cp is not None:
                            torsos.append(cp.torso)
                            hipys.append((cp.landmarks["clhip"][1] + cp.landmarks["crhip"][1]) / 2)
                    i += 1
                cap.release()
        out[variant] = {
            "n_frames_seen": seen,
            "identification_rate": round(reasons.get("catcher", 0) / seen, 4) if seen else None,
            "reasons": reasons,
            "median_torso": round(st.median(torsos), 4) if torsos else None,
            "median_hip_y": round(st.median(hipys), 4) if hipys else None,
        }
        print(f"{variant}: {json.dumps(out[variant])}", flush=True)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
