"""
Apex Preflight tracker — pitcher body, glove proxy, face, motion (MediaPipe Tasks).

Savant CF is proof-of-concept; club X1–X4 use the same schema via camera_id.
"""
from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from pathlib import Path
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL_DIR = Path(__file__).resolve().parent / "models"
POSE_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)
FACE_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)

# Pose landmark indices (same topology as classic MediaPipe Pose)
L_SHOULDER, R_SHOULDER = 11, 12
L_WRIST, R_WRIST = 15, 16
L_HIP, R_HIP = 23, 24
NOSE = 0
L_ELBOW, R_ELBOW = 13, 14
L_PINKY, R_PINKY = 17, 18
L_INDEX, R_INDEX = 19, 20
L_KNEE, R_KNEE = 25, 26
L_ANKLE, R_ANKLE = 27, 28

# A detected face counts as the pitcher's only if its centre sits within this
# many of his own shoulder widths of his pose nose. Measured face-to-nose
# distances on real clips are a median 2.24 shoulder widths, i.e. the model is
# usually locking onto the hitter or the crowd; one shoulder width is generous
# for a true positive and rejects those outright.
MAX_FACE_TO_NOSE_SHOULDER_WIDTHS = 1.0

# Raw landmarks persisted alongside the derived scalars as <name>_x/_y/_v.
#
# The derived scalars alone cannot support the lift-anchored scouting vocabulary:
# knee position is needed to locate the leg lift at all, and shoulder/hip left+right
# are needed for a torso-length scale that survives camera zoom. Persisting the
# landmarks themselves means those primitives can be derived later WITHOUT
# re-tracking, which is the expensive part.
#
# Schema mirrors KEEP in track_lift.py. It is duplicated rather than imported
# because track_lift imports from this module, so importing back would be
# circular; worth consolidating into a shared module once tracker edits settle.
KEEP_LANDMARKS: dict[str, int] = {
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

# Plausible CF-view pitcher geometry, in normalised image units. Measured over
# 316 tracked Savant pitches: the pitcher's shoulder-to-hip extent clusters at
# ~0.13 (p25-p75 0.11-0.15), while broadcast close-up subjects run 0.28-0.55.
# The band is deliberately wider than that cluster so zoom variation between
# parks does not silently drop valid pitches.
PITCHER_TORSO_MIN, PITCHER_TORSO_MAX = 0.05, 0.22
PITCHER_HIP_Y_MIN, PITCHER_HIP_Y_MAX = 0.20, 0.80


def _ensure_model(url: str, name: str) -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    path = MODEL_DIR / name
    if path.is_file() and path.stat().st_size > 1000:
        return path
    print(f"Downloading {name}…")
    urllib.request.urlretrieve(url, path)
    return path


def _xy(landmarks, idx: int) -> tuple[float, float] | None:
    if landmarks is None or idx >= len(landmarks):
        return None
    lm = landmarks[idx]
    vis = getattr(lm, "visibility", 1.0)
    if vis is not None and vis < 0.3:
        return None
    return float(lm.x), float(lm.y)


def _raw_landmark(landmarks, idx: int) -> tuple[float, float, float] | None:
    """
    Landmark with visibility, bypassing the confidence gate in ``_xy``.

    Visibility is itself a signal here — a bare hand buried in the glove reads as
    low visibility — so it must not be thresholded away at write time.
    """
    if landmarks is None or idx >= len(landmarks):
        return None
    lm = landmarks[idx]
    return float(lm.x), float(lm.y), float(getattr(lm, "visibility", 0.0) or 0.0)


def _mid(a, b):
    if a is None or b is None:
        return None
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


# How many frames of each clip to track.
#
# The old value of 180 was chosen believing the corpus was 30 fps, i.e. 6.0 s.
# The corpus is 59.6 fps, so 180 frames is 3.0 s, and direct decoding of 33 clips
# across 9 arms and 9 parks found none shorter than 358 frames (median ~440,
# ~7.3 s). The cap was silently discarding a median 61% of every clip.
#
# 240 rather than 360: the truncation falls at the END of the clip and the pitch
# happens early — delivery_frame has median 83 and p90 164 across 5,406 windowed
# pitches. 240 frames (4.0 s) clears that p90 and the observed max of 179 with
# margin, at +33% tracking cost. 360 would cost +100% to capture ball flight, the
# catch and replay, which no pre-pitch tip can use.
#
# This does NOT recover pre-set lead-in. See docs/limits_preset_coverage.md: the
# clip begins after the pitcher has settled, which is a start-of-clip limit no
# cap can address.
MAX_TRACK_FRAMES = 240


def track_clip(
    clip_path: Path,
    out_dir: Path,
    *,
    camera_id: str = "CF",
    max_frames: int | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = clip_path.stem
    csv_path = out_dir / f"{stem}_tracks.csv"

    pose_model = _ensure_model(POSE_URL, "pose_landmarker_lite.task")
    face_model = _ensure_model(FACE_URL, "face_landmarker.task")

    pose_options = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(pose_model)),
        running_mode=vision.RunningMode.VIDEO,
        # Three, not two: the pitcher now has to win on geometry rather than
        # size, so he must actually be among the candidates. With two poses the
        # hitter and catcher can crowd him out of the CF view and the frame gets
        # rejected, trading wrong-subject frames for silently dropped ones.
        num_poses=3,
        min_pose_detection_confidence=0.4,
        min_pose_presence_confidence=0.4,
        min_tracking_confidence=0.4,
    )
    face_options = vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(face_model)),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.4,
        min_face_presence_confidence=0.4,
        min_tracking_confidence=0.4,
    )

    cap = cv2.VideoCapture(str(clip_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {clip_path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)

    rows: list[dict[str, Any]] = []
    prev_wrist = None
    prev_cheek = None
    prev_cheek_frame = -2
    prev_catcher_glove = None
    frame_i = 0

    def pitcher_score(cand) -> float:
        """
        Rank a detected pose by how much it looks like the CF-view pitcher.

        Returns -1.0 for any pose that cannot be the pitcher, so the caller can
        reject the frame outright rather than settle for the best of a bad set.
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
        # Among survivors prefer the pose nearest frame centre horizontally: the
        # catcher and hitter sit off-centre and lower in the CF framing.
        return 1.0 - abs(hip_x - 0.5)

    def pose_hip_y(cand) -> float:
        mid = _mid(_xy(cand, L_HIP), _xy(cand, R_HIP))
        return mid[1] if mid else -1.0

    with vision.PoseLandmarker.create_from_options(pose_options) as pose, vision.FaceLandmarker.create_from_options(
        face_options
    ) as face:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if max_frames is not None and frame_i >= max_frames:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts_ms = int(frame_i * 1000 / fps)

            pose_res = pose.detect_for_video(mp_image, ts_ms)
            face_res = face.detect_for_video(mp_image, ts_ms)

            # Pitcher = best CF-view geometry match; catcher = lowest hips.
            #
            # This used to be "largest torso in frame", which is wrong on Savant
            # clips: they open on a broadcast close-up of the hitter before
            # cutting to the CF view (frame 107 of 434 on a sampled Thorpe
            # clip), and during that lead-in the largest torso is the hitter,
            # not the pitcher. That put a hitter's body into the features on
            # ~11% of pitches. Scoring on CF-view pitcher geometry instead means
            # lead-in frames match nothing and are left blank, which is the
            # correct outcome: there is no pitcher to measure in them.
            plm = None
            clm = None
            if pose_res.pose_landmarks:
                best = max(pose_res.pose_landmarks, key=pitcher_score)
                if pitcher_score(best) > 0:
                    plm = best
                # Catcher: the lowest hip among poses that are NOT the pitcher.
                #
                # This previously ended in `if clm is None: clm = by_hip[0]`, an
                # unconditional fallback. MediaPipe returns a single pose on
                # 65-77% of these frames, so that fallback fired constantly and
                # handed back the pitcher himself: measured 90.9% of frames on
                # McCann and 71.3% on Moreno, with catcher_hip_y median 0.574
                # against the pitcher's 0.573 — the same body. Every catcher
                # feature was therefore describing the pitcher.
                #
                # There is no safe fallback here. If no pose other than the
                # pitcher is found, the catcher was not detected, and the catcher
                # columns must stay empty rather than carry someone else's
                # coordinates. See docs/catcher_subject_bug.md.
                # Two distinct poses are required: one pose in frame cannot be
                # both the pitcher and the catcher.
                if len(pose_res.pose_landmarks) >= 2 and plm is not None:
                    by_hip = sorted(pose_res.pose_landmarks, key=pose_hip_y, reverse=True)
                    for cand in by_hip:
                        if cand is not plm:
                            clm = cand
                            break

            lw = _xy(plm, L_WRIST)
            rw = _xy(plm, R_WRIST)
            glove = None
            if lw and rw:
                glove = lw if lw[1] > rw[1] else rw
            elif lw or rw:
                glove = lw or rw

            belt = _mid(_xy(plm, L_HIP), _xy(plm, R_HIP))
            shoulder = _mid(_xy(plm, L_SHOULDER), _xy(plm, R_SHOULDER))

            # Catcher setup target (glove) + stance width
            clw = _xy(clm, L_WRIST)
            crw = _xy(clm, R_WRIST)
            catcher_glove = None
            if clw and crw:
                # Catcher's glove hand is usually the lower wrist when set
                catcher_glove = clw if clw[1] > crw[1] else crw
            elif clw or crw:
                catcher_glove = clw or crw
            c_hip = _mid(_xy(clm, L_HIP), _xy(clm, R_HIP))
            c_lhip, c_rhip = _xy(clm, L_HIP), _xy(clm, R_HIP)
            catcher_stance = None
            if c_lhip and c_rhip:
                catcher_stance = abs(c_lhip[0] - c_rhip[0])
            catcher_glove_speed = None
            if catcher_glove is not None and prev_catcher_glove is not None:
                catcher_glove_speed = float(
                    np.hypot(
                        catcher_glove[0] - prev_catcher_glove[0],
                        catcher_glove[1] - prev_catcher_glove[1],
                    )
                )
            if catcher_glove is not None:
                prev_catcher_glove = catcher_glove

            # Cheek: face landmarks ONLY, and only when the detected face is
            # actually the pitcher's.
            #
            # This used to fall back to the pose nose whenever the face model
            # returned nothing, which made cheek_motion a fully-populated column
            # that almost never contained facial information. Measured on 288
            # in-window frames (face_pixel_audit.py): the Face Landmarker returns
            # a face on 8.3% of frames, and only 1.04% of frames put that face
            # within a shoulder width of the pitcher's pose nose — the rest are
            # the hitter, the on-deck batter and the crowd, whose inter-eye
            # distance (101.8 px) exceeds the pitcher's whole head (31.4 px).
            # So the fallback was silently substituting head-position jitter for
            # facial motion, and cheek_motion_* have been retracted as cues.
            #
            # Now the invalid state is unrepresentable rather than papered over:
            # no pitcher face means NaN, and cheek_source records which it was so
            # a downstream reader can tell "he did not move" from "we could not
            # see him". Same principle as the catcher NaN guard.
            cheek_motion = None
            cheek = None
            cheek_source = "no_face"
            if face_res.face_landmarks:
                fl = face_res.face_landmarks[0]
                if len(fl) > 280:
                    cand = ((fl[50].x + fl[280].x) / 2.0, (fl[50].y + fl[280].y) / 2.0)
                    nose = _xy(plm, NOSE)
                    l_s, r_s = _xy(plm, L_SHOULDER), _xy(plm, R_SHOULDER)
                    if nose is None or l_s is None or r_s is None:
                        cheek_source = "no_pose_to_verify_subject"
                    else:
                        sho_w = float(np.hypot(l_s[0] - r_s[0], l_s[1] - r_s[1]))
                        if sho_w <= 1e-9:
                            cheek_source = "degenerate_pose"
                        elif (
                            float(np.hypot(cand[0] - nose[0], cand[1] - nose[1])) / sho_w
                            > MAX_FACE_TO_NOSE_SHOULDER_WIDTHS
                        ):
                            # A face was found, but not on this pitcher.
                            cheek_source = "face_not_on_pitcher"
                        else:
                            cheek = cand
                            cheek_source = "face_landmarker"
            # Motion needs two consecutive PITCHER-face frames. Differencing
            # across a gap would report the gap as movement.
            if cheek is not None and prev_cheek is not None and prev_cheek_frame == frame_i - 1:
                cheek_motion = float(np.hypot(cheek[0] - prev_cheek[0], cheek[1] - prev_cheek[1]))
            if cheek is not None:
                prev_cheek = cheek
                prev_cheek_frame = frame_i

            # Bare hand stays inside the glove until hand break, so the gap
            # between the wrists is the cleanest signal for that boundary.
            wrist_dist = None
            if lw and rw:
                wrist_dist = float(np.hypot(lw[0] - rw[0], lw[1] - rw[1]))

            wrist_speed = None
            if glove is not None and prev_wrist is not None:
                wrist_speed = float(np.hypot(glove[0] - prev_wrist[0], glove[1] - prev_wrist[1]))
            if glove is not None:
                prev_wrist = glove

            glove_vs_belt_y = None
            if glove is not None and belt is not None:
                glove_vs_belt_y = float(belt[1] - glove[1])
            flare = None
            if glove is not None and shoulder is not None:
                flare = float(glove[0] - shoulder[0])

            row: dict[str, Any] = {
                "frame": frame_i,
                "t_sec": round(frame_i / fps, 4),
                "camera_id": camera_id,
                    "glove_x": "" if not glove else round(glove[0], 5),
                    "glove_y": "" if not glove else round(glove[1], 5),
                    "belt_y": "" if not belt else round(belt[1], 5),
                    "glove_vs_belt_y": "" if glove_vs_belt_y is None else round(glove_vs_belt_y, 5),
                    "glove_flare": "" if flare is None else round(flare, 5),
                    "wrist_speed": "" if wrist_speed is None else round(wrist_speed, 5),
                    "wrist_dist": "" if wrist_dist is None else round(wrist_dist, 5),
                    "cheek_motion": "" if cheek_motion is None else round(cheek_motion, 5),
                    "shoulder_y": "" if not shoulder else round(shoulder[1], 5),
                    "catcher_glove_x": "" if not catcher_glove else round(catcher_glove[0], 5),
                    "catcher_glove_y": "" if not catcher_glove else round(catcher_glove[1], 5),
                    "catcher_stance_width": "" if catcher_stance is None else round(catcher_stance, 5),
                    "catcher_hip_y": "" if not c_hip else round(c_hip[1], 5),
                    "catcher_glove_speed": "" if catcher_glove_speed is None else round(catcher_glove_speed, 5),
            }

            # Raw pitcher landmarks for lift-anchored primitives.
            for name, idx in KEEP_LANDMARKS.items():
                got = _raw_landmark(plm, idx)
                row[f"{name}_x"] = "" if got is None else round(got[0], 5)
                row[f"{name}_y"] = "" if got is None else round(got[1], 5)
                row[f"{name}_v"] = "" if got is None else round(got[2], 4)

            # Subject-selection provenance: lets downstream reject wrong-subject
            # frames and audit the hitter-close-up failure mode without re-tracking.
            row["pitcher_score"] = "" if plm is None else round(pitcher_score(plm), 5)
            row["n_poses"] = len(pose_res.pose_landmarks) if pose_res.pose_landmarks else 0
            # Raw cheek position, so cheek features can be recomputed over a
            # different window without paying for another tracking pass.
            row["cheek_x"] = "" if cheek is None else round(cheek[0], 5)
            row["cheek_y"] = "" if cheek is None else round(cheek[1], 5)
            # Why the cheek columns are empty when they are empty. Without this
            # a blank is indistinguishable from a pitcher who held still.
            row["cheek_source"] = cheek_source

            rows.append(row)
            frame_i += 1

    cap.release()

    fields = list(rows[0].keys()) if rows else []
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    summary = {
        "clip": str(clip_path),
        "camera_id": camera_id,
        "n_frames": len(rows),
        "fps": fps,
        "backend": "mediapipe_tasks_pose_face_pitcher_catcher",
        "poc_note": "Savant CF PoC — pitcher + catcher setup tracks; club X1–X4 keep schema.",
        "tracks_csv": str(csv_path),
    }
    (out_dir / f"{stem}_summary.json").write_text(json.dumps(summary, indent=2))
    return csv_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Apex Preflight — pitcher tracker")
    p.add_argument("--clip", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("tracks"))
    p.add_argument("--camera-id", default="CF")
    p.add_argument("--max-frames", type=int, default=None)
    args = p.parse_args(argv)
    print(track_clip(args.clip, args.out, camera_id=args.camera_id, max_frames=args.max_frames))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
