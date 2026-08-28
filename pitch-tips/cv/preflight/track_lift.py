"""
Apex Preflight — rich landmark pass for lift-anchored tip primitives.

The original tracker (``track_pitcher.py``) persists only a handful of derived
scalars (glove x/y, belt y, shoulder y). Those are enough for the set-window
features already in production, but they cannot support the scouting vocabulary
that clubs actually use, because that vocabulary is anchored to the LEG LIFT and
needs a stable body scale:

  * knee height is required to locate the lift at all
  * shoulder/hip left+right are required for a scale that survives camera zoom
  * elbow + both wrists are required for glove angle and hand break
  * pose hand landmarks (index/pinky) give a cheap proxy for how much of the
    bare hand is out of the glove, without depending on the parts detector

So this pass writes the landmarks themselves rather than pre-derived scalars,
and leaves all interpretation to ``primitives.py``. Face landmarks are skipped:
nothing in the lift vocabulary needs them, and dropping the face model roughly
halves runtime, which matters while the league pipeline is running.

Output: ``runs/<pitcher>_poc/lift_tracks/<play_id>.csv``, one row per frame.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from preflight.track_pitcher import _ensure_model, POSE_URL, _xy, _mid

# Classic MediaPipe Pose topology.
NOSE = 0
L_SHOULDER, R_SHOULDER = 11, 12
L_ELBOW, R_ELBOW = 13, 14
L_WRIST, R_WRIST = 15, 16
L_PINKY, R_PINKY = 17, 18
L_INDEX, R_INDEX = 19, 20
L_HIP, R_HIP = 23, 24
L_KNEE, R_KNEE = 25, 26
L_ANKLE, R_ANKLE = 27, 28

# Landmarks persisted as <name>_x, <name>_y, <name>_v (visibility).
# Plausible CF-view pitcher geometry, in normalised image units. Measured from
# the shipped Savant clips: pitcher torso y-extent sits around 0.13 (p25-p75
# 0.11-0.15), while broadcast close-up subjects run 0.28-0.55.
PITCHER_TORSO_MIN, PITCHER_TORSO_MAX = 0.05, 0.22
PITCHER_HIP_Y_MIN, PITCHER_HIP_Y_MAX = 0.20, 0.80

KEEP: dict[str, int] = {
    "nose": NOSE,
    "lsho": L_SHOULDER,
    "rsho": R_SHOULDER,
    "lelb": L_ELBOW,
    "relb": R_ELBOW,
    "lwri": L_WRIST,
    "rwri": R_WRIST,
    "lpnk": L_PINKY,
    "rpnk": R_PINKY,
    "lidx": L_INDEX,
    "ridx": R_INDEX,
    "lhip": L_HIP,
    "rhip": R_HIP,
    "lkne": L_KNEE,
    "rkne": R_KNEE,
    "lank": L_ANKLE,
    "rank": R_ANKLE,
}

FIELDS = ["frame", "t_sec", "camera_id"] + [
    f"{name}_{suffix}" for name in KEEP for suffix in ("x", "y", "v")
]


def _raw(landmarks, idx: int):
    """Landmark with visibility, without the confidence gate in ``_xy``.

    Visibility is itself a feature here (a bare hand inside the glove reads as
    low-visibility), so it must not be thresholded away at write time.
    """
    if landmarks is None or idx >= len(landmarks):
        return None
    lm = landmarks[idx]
    return float(lm.x), float(lm.y), float(getattr(lm, "visibility", 0.0) or 0.0)


def track_clip_lift(
    clip_path: Path,
    out_dir: Path,
    *,
    camera_id: str = "CF",
    max_frames: int | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{clip_path.stem}.csv"

    pose_model = _ensure_model(POSE_URL, "pose_landmarker_lite.task")
    pose_options = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(pose_model)),
        running_mode=vision.RunningMode.VIDEO,
        # Three is enough to have the pitcher among the candidates alongside the
        # catcher and hitter, without paying for a fourth landmark pass.
        num_poses=3,
        min_pose_detection_confidence=0.4,
        min_pose_presence_confidence=0.4,
        min_tracking_confidence=0.4,
    )

    cap = cv2.VideoCapture(str(clip_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {clip_path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)

    def pitcher_score(cand) -> float:
        """
        Rank a detected pose by how much it looks like the CF-view pitcher.

        "Largest torso" (what the original tracker uses) is wrong on Savant
        clips: they open on a broadcast close-up of the hitter, whose torso
        fills the frame and dwarfs the pitcher. That close-up subject was being
        tracked instead of the pitcher on roughly 11% of pitches. The pitcher in
        the CF view is instead identifiable by scale and placement — a small
        torso, in the upper-middle of the frame, near the horizontal centre —
        so score on those and reject anything outside the plausible band.
        """
        ls, rs = _xy(cand, L_SHOULDER), _xy(cand, R_SHOULDER)
        lh, rh = _xy(cand, L_HIP), _xy(cand, R_HIP)
        if not all([ls, rs, lh, rh]):
            return -1.0
        sho_y = (ls[1] + rs[1]) / 2
        hip_y = (lh[1] + rh[1]) / 2
        hip_x = (lh[0] + rh[0]) / 2
        torso = abs(hip_y - sho_y)
        if not (PITCHER_TORSO_MIN <= torso <= PITCHER_TORSO_MAX):
            return -1.0
        if not (PITCHER_HIP_Y_MIN <= hip_y <= PITCHER_HIP_Y_MAX):
            return -1.0
        # Among survivors prefer the one nearest frame centre horizontally; the
        # catcher and hitter sit off-centre and lower in the CF framing.
        return 1.0 - abs(hip_x - 0.5)

    rows: list[dict[str, object]] = []
    frame_i = 0
    with vision.PoseLandmarker.create_from_options(pose_options) as pose:
        while True:
            ok, frame = cap.read()
            if not ok or (max_frames is not None and frame_i >= max_frames):
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            res = pose.detect_for_video(mp_image, int(frame_i * 1000 / fps))

            # Pitcher = largest torso, matching track_pitcher.py so the two
            # passes describe the same person.
            plm = None
            if res.pose_landmarks:
                best = max(res.pose_landmarks, key=pitcher_score)
                if pitcher_score(best) > 0:
                    plm = best

            row: dict[str, object] = {
                "frame": frame_i,
                "t_sec": round(frame_i / fps, 4),
                "camera_id": camera_id,
            }
            for name, idx in KEEP.items():
                got = _raw(plm, idx)
                row[f"{name}_x"] = "" if got is None else round(got[0], 5)
                row[f"{name}_y"] = "" if got is None else round(got[1], 5)
                row[f"{name}_v"] = "" if got is None else round(got[2], 4)
            rows.append(row)
            frame_i += 1
    cap.release()

    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, help="runs/<pitcher>_poc")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--camera-id", default="CF")
    # The actionable window closes at hand break, which lands well inside the
    # first 180 frames on Savant clips (p99 ~176), so decoding past that is
    # pure waste. This matches the cap the original tracker used.
    ap.add_argument("--max-frames", type=int, default=180)
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    clips = sorted((run_dir / "clips").glob("*.mp4"))
    out_dir = run_dir / "lift_tracks"
    out_dir.mkdir(parents=True, exist_ok=True)
    todo = [c for c in clips if not (out_dir / f"{c.stem}.csv").is_file()]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{run_dir.name}: {len(clips)} clips, {len(todo)} to track", flush=True)
    for i, clip in enumerate(todo, 1):
        try:
            track_clip_lift(clip, out_dir, camera_id=args.camera_id, max_frames=args.max_frames)
        except Exception as exc:  # a single bad clip must not stop the batch
            print(f"  [{i}] FAIL {clip.stem}: {exc}", flush=True)
            continue
        if i % 25 == 0 or i == len(todo):
            print(f"  [{i}/{len(todo)}] {clip.stem}", flush=True)


if __name__ == "__main__":
    main()
