#!/usr/bin/env python3
"""
Identification rate and subject verification for clip-level catcher localisation.

Reports, per clip: whether a region was located, and then over every frame of the
clip whether the catcher was identified in it and what his geometry was.

Two verifications are run, not one, because a rate alone is what let the previous
catcher columns look healthy at 98.6% coverage while carrying the pitcher:

  1. Placement. The catcher's own geometry, in his own torso lengths — squat
     depth, stance width, hip height. A squatting catcher must show knees at or
     near the hips and a stance far wider than the 0.012 that exposed the bug.

  2. Not-the-pitcher. The pitcher's tracked landmarks are already cached in the
     run's ``*_tracks.csv``, so the distance from the identified catcher to the
     TRACKED PITCHER is measured directly, in pitcher torso lengths, on the same
     frame. This is the test that would have caught the original bug immediately:
     it reported a catcher hip_y median of 0.574 against the pitcher's 0.573, a
     distance of essentially zero. Anything close to zero here means the same
     failure has recurred under a new name.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from preflight.catcher_locate import catcher_in_region, clip_catcher_region, make_pose_landmarker


def _pitcher_frame_geometry(tracks_csv: Path) -> dict[int, tuple[float, float, float]]:
    """
    frame -> (hip_x, hip_y, torso) for the tracked pitcher, where available.

    Note on why this can be empty: the clip janitor deletes an mp4 as soon as its
    track exists, so within a run directory the clips still on disk are exactly
    the ones with NO cached track. Getting both pixels and a pitcher track for the
    same play therefore requires tracking the clip here (--track-pitcher), which
    is what the caller does.
    """
    if not tracks_csv.is_file():
        return {}
    df = pd.read_csv(tracks_csv, low_memory=False)
    need = ("lhip_x", "rhip_x", "lhip_y", "rhip_y", "lsho_x", "rsho_x", "lsho_y", "rsho_y")
    if not all(c in df.columns for c in need):
        return {}
    out = {}
    for _, r in df.iterrows():
        try:
            hx = (float(r["lhip_x"]) + float(r["rhip_x"])) / 2
            hy = (float(r["lhip_y"]) + float(r["rhip_y"])) / 2
            sx = (float(r["lsho_x"]) + float(r["rsho_x"])) / 2
            sy = (float(r["lsho_y"]) + float(r["rsho_y"])) / 2
        except (TypeError, ValueError):
            continue
        t = float(np.hypot(sx - hx, sy - hy))
        if not np.isfinite(t) or t <= 0:
            continue
        out[int(r["frame"])] = (hx, hy, t)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", type=Path, required=True, help="run dir with clips/ and tracks/")
    ap.add_argument("--n-clips", type=int, default=8)
    ap.add_argument("--stride", type=int, default=3, help="frame stride for the per-frame pass")
    ap.add_argument("--out", type=Path, default=Path("runs/catcher_clip_probe.json"))
    ap.add_argument(
        "--track-pitcher",
        type=Path,
        default=None,
        help="write pitcher tracks for these clips here, so the not-the-pitcher "
             "check has something to compare against",
    )
    a = ap.parse_args(argv)

    clips = sorted((a.work / "clips").glob("*.mp4"))[: a.n_clips]
    per_clip: list[dict] = []
    frames: list[dict] = []

    with make_pose_landmarker() as pose:
        for clip in clips:
            region, diag = clip_catcher_region(clip)
            rec = {"clip": clip.stem, "region": diag}
            if region is None:
                per_clip.append(rec)
                print(f"{clip.stem}: NO REGION ({diag.get('reason')})", flush=True)
                continue
            rec["region_box"] = [region.x1, region.y1, region.x2, region.y2]
            rec["region_centre"] = [round(region.cx, 4), round(region.cy, 4)]
            rec["anchor_classes"] = list(region.anchor_classes)

            tracks_csv = a.work / "tracks" / f"{clip.stem}_tracks.csv"
            if a.track_pitcher is not None and not tracks_csv.is_file():
                from preflight.track_pitcher import track_clip as track_pitcher_clip

                tracks_csv = track_pitcher_clip(clip, a.track_pitcher)
            pitcher = _pitcher_frame_geometry(tracks_csv)
            cap = cv2.VideoCapture(str(clip))
            i = 0
            reasons: dict[str, int] = {}
            n_seen = 0
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if i % a.stride == 0:
                    n_seen += 1
                    cp, why = catcher_in_region(frame, pose, region)
                    reasons[why] = reasons.get(why, 0) + 1
                    if cp is not None:
                        lm = cp.landmarks
                        hip_x = (lm["clhip"][0] + lm["crhip"][0]) / 2
                        hip_y = (lm["clhip"][1] + lm["crhip"][1]) / 2
                        knee_y = max(lm["clkne"][1], lm["crkne"][1])
                        f = {
                            "clip": clip.stem,
                            "frame": i,
                            "torso": round(cp.torso, 5),
                            "hip_x": round(hip_x, 4),
                            "hip_y": round(hip_y, 4),
                            "knee_rise_torsos": round((hip_y - knee_y) / cp.torso, 3),
                            "stance_width_torsos": round(abs(lm["clhip"][0] - lm["crhip"][0]) / cp.torso, 3),
                            "vis_hip": round(min(lm["clhip"][2], lm["crhip"][2]), 3),
                            "vis_wri": round(min(lm["clwri"][2], lm["crwri"][2]), 3),
                        }
                        pg = pitcher.get(i)
                        if pg:
                            phx, phy, pt_ = pg
                            f["dist_to_pitcher_torsos"] = round(
                                float(np.hypot(hip_x - phx, hip_y - phy)) / pt_, 3)
                            f["pitcher_hip_y"] = round(phy, 4)
                        frames.append(f)
                i += 1
            cap.release()
            rec["n_frames_seen"] = n_seen
            rec["reasons"] = reasons
            rec["identification_rate"] = round(reasons.get("catcher", 0) / n_seen, 4) if n_seen else None
            per_clip.append(rec)
            print(f"{clip.stem}: rate={rec['identification_rate']} {reasons}", flush=True)

    def q(key):
        v = sorted(f[key] for f in frames if key in f)
        if not v:
            return None
        return {"p10": round(v[len(v) // 10], 4), "median": round(st.median(v), 4),
                "p90": round(v[min(len(v) - 1, int(len(v) * 0.9))], 4),
                "min": round(v[0], 4), "max": round(v[-1], 4), "n": len(v)}

    seen = sum(c.get("n_frames_seen", 0) for c in per_clip)
    hit = sum(c.get("reasons", {}).get("catcher", 0) for c in per_clip)
    dists = [f["dist_to_pitcher_torsos"] for f in frames if "dist_to_pitcher_torsos" in f]
    report = {
        "n_clips": len(clips),
        "n_clips_with_region": sum(1 for c in per_clip if "region_box" in c),
        "n_frames_seen": seen,
        "overall_identification_rate": round(hit / seen, 4) if seen else None,
        "placement": {k: q(k) for k in (
            "torso", "hip_x", "hip_y", "knee_rise_torsos", "stance_width_torsos",
            "vis_hip", "vis_wri", "dist_to_pitcher_torsos")},
        # The pitcher-substitution test. A median near zero means the catcher
        # columns are carrying the pitcher again.
        "not_the_pitcher": {
            "n_compared": len(dists),
            "median_dist_torsos": round(st.median(dists), 3) if dists else None,
            "frames_within_1_torso_of_pitcher": sum(1 for d in dists if d < 1.0),
        },
        "implausible": {
            "knees_far_below_hips": sum(1 for f in frames if f["knee_rise_torsos"] < -0.35),
            "stance_narrower_than_bug": sum(1 for f in frames if f["stance_width_torsos"] < 0.05),
        },
        "per_clip": per_clip,
        "frames": frames,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k not in ("frames", "per_clip")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
