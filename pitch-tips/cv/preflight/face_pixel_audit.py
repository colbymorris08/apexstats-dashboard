"""
Read-only feasibility measurement: how many pixels does the pitcher's FACE
occupy in Savant CF clips, inside the actionable window, and can the MediaPipe
Face Landmarker actually find it?

Why this exists
---------------
The scouting documents contain a facial cue — Bubic 2024, "we had issues with
him from 2nd, open and closed side ... and his mouth" — and the codebase already
carries a Face Landmarker path plus ``cheek_x`` / ``cheek_y`` / ``cheek_motion``
columns. That combination makes "facial movements" look shipped. It is not, and
the honest way to settle it is to measure the pixels rather than to argue about
them, exactly as the PitchCom tap cue was retired against a measured number.

Two independent measurements
----------------------------
1. Geometric, from cached tracks: head scale in pixels, taken as the nose to
   shoulder-midpoint distance. No model involved, so it cannot be confounded by
   a detector's failure modes. A mouth is roughly 0.35 of head width, which
   turns head pixels into an upper bound on mouth pixels.
2. Empirical, by running the Face Landmarker on sampled window frames: does it
   return a face at all, and if so how wide is the mouth in pixels
   (landmarks 61 and 291 are the mouth corners).

The second matters because ``track_pitcher.py`` silently falls back to the POSE
nose landmark whenever the face model returns nothing:

    if cheek is None:
        cheek = _xy(plm, NOSE)

so ``cheek_motion`` can be 100% populated while containing zero facial
information. This audit reports the detection rate that fallback is hiding.

Writes nothing except an optional CSV. Decodes a bounded number of frames.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preflight.window import actionable_window  # noqa: E402

# Mouth corners and eye outer corners in the 478-point Face Landmarker mesh.
MOUTH_L, MOUTH_R = 61, 291
EYE_L, EYE_R = 33, 263
# A mouth spans roughly this fraction of the nose-to-shoulder head scale. Used
# only to turn the model-free geometric measurement into a mouth upper bound.
MOUTH_FRACTION_OF_HEAD = 0.35


def clip_dims(path: str) -> tuple[int, int]:
    cap = cv2.VideoCapture(path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return w, h


def _px(df: pd.DataFrame, a: str, b: str, W: int, H: int) -> np.ndarray:
    dx = (pd.to_numeric(df[f"{a}_x"], errors="coerce") - pd.to_numeric(df[f"{b}_x"], errors="coerce")) * W
    dy = (pd.to_numeric(df[f"{a}_y"], errors="coerce") - pd.to_numeric(df[f"{b}_y"], errors="coerce")) * H
    return np.hypot(dx, dy).to_numpy(dtype=float)


def _face_landmarker():
    """The same model and options track_pitcher.py uses, or None if unavailable."""
    try:
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
    except Exception:
        return None, None
    from preflight.track_pitcher import FACE_URL, _ensure_model

    try:
        path = _ensure_model(FACE_URL, "face_landmarker.task")
    except Exception:
        return None, None
    # CPU delegate explicitly: the default tries GL first and the face graph
    # hard-fails without it, which would otherwise read as "no faces found"
    # rather than "the model never ran".
    opts = vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(
            model_asset_path=str(path), delegate=mp_python.BaseOptions.Delegate.CPU
        ),
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1,
    )
    return vision.FaceLandmarker.create_from_options(opts), vision


def geometric(run: str, limit: int) -> pd.DataFrame:
    """Head pixel scale from cached tracks; no model, no video decode beyond dims."""
    tracks = sorted(glob.glob(os.path.join(run, "lift_tracks", "*.csv")))
    if limit:
        tracks = tracks[:limit]
    rows = []
    dims: dict[str, int] = {}
    for tp in tracks:
        pid = os.path.basename(tp).replace(".csv", "")
        clip = os.path.join(run, "clips", f"{pid}.mp4")
        if not os.path.exists(clip):
            continue
        W, H = clip_dims(clip)
        if W <= 0:
            continue
        dims[f"{W}x{H}"] = dims.get(f"{W}x{H}", 0) + 1
        df = pd.read_csv(tp)
        wdf = df.copy()
        lw = pd.to_numeric(df.get("lwri_x"), errors="coerce")
        rw = pd.to_numeric(df.get("rwri_x"), errors="coerce")
        lwy = pd.to_numeric(df.get("lwri_y"), errors="coerce")
        rwy = pd.to_numeric(df.get("rwri_y"), errors="coerce")
        wdf["glove_x"] = (lw + rw) / 2
        wdf["glove_y"] = (lwy + rwy) / 2
        wdf["wrist_dist"] = np.hypot(lw - rw, lwy - rwy)
        win = actionable_window(wdf)
        if not win.valid:
            continue
        w = df.iloc[win.start : win.end]
        if not len(w):
            continue
        # Nose to shoulder midpoint: a head-scale proxy that needs only pose.
        sx = (pd.to_numeric(w["lsho_x"], errors="coerce") + pd.to_numeric(w["rsho_x"], errors="coerce")) / 2
        sy = (pd.to_numeric(w["lsho_y"], errors="coerce") + pd.to_numeric(w["rsho_y"], errors="coerce")) / 2
        nx = pd.to_numeric(w["nose_x"], errors="coerce")
        ny = pd.to_numeric(w["nose_y"], errors="coerce")
        head = np.hypot((nx - sx) * W, (ny - sy) * H).to_numpy(dtype=float)
        sho = _px(w, "lsho", "rsho", W, H)
        rows.append(
            {
                "play_id": pid,
                "W": W,
                "H": H,
                "head_scale_px": float(np.nanmedian(head)) if np.isfinite(head).any() else np.nan,
                "sho_width_px": float(np.nanmedian(sho)) if np.isfinite(sho).any() else np.nan,
            }
        )
    out = pd.DataFrame(rows)
    out.attrs["resolutions"] = dims
    return out


def empirical(run: str, n_clips: int, per_clip: int) -> dict:
    """Run the Face Landmarker on sampled window frames; report what it finds."""
    lm, _vision = _face_landmarker()
    if lm is None:
        return {"error": "face landmarker unavailable"}
    import mediapipe as mp

    tracks = sorted(glob.glob(os.path.join(run, "lift_tracks", "*.csv")))[:n_clips]
    attempted = 0
    detected = 0
    mouth_px: list[float] = []
    eye_px: list[float] = []
    face_to_nose: list[float] = []
    on_pitcher = 0
    for tp in tracks:
        pid = os.path.basename(tp).replace(".csv", "")
        clip = os.path.join(run, "clips", f"{pid}.mp4")
        if not os.path.exists(clip):
            continue
        df = pd.read_csv(tp)
        wdf = df.copy()
        lw = pd.to_numeric(df.get("lwri_x"), errors="coerce")
        rw = pd.to_numeric(df.get("rwri_x"), errors="coerce")
        lwy = pd.to_numeric(df.get("lwri_y"), errors="coerce")
        rwy = pd.to_numeric(df.get("rwri_y"), errors="coerce")
        wdf["glove_x"] = (lw + rw) / 2
        wdf["glove_y"] = (lwy + rwy) / 2
        wdf["wrist_dist"] = np.hypot(lw - rw, lwy - rwy)
        win = actionable_window(wdf)
        if not win.valid:
            continue
        # Pose nose, used to check whether a detected face is actually the
        # pitcher's. A face found somewhere else in the frame is a fan or the
        # hitter, and counting it as a detection is the same class of error that
        # made the catcher features measure the pitcher.
        nose_x = pd.to_numeric(df.get("nose_x"), errors="coerce").to_numpy(dtype=float)
        nose_y = pd.to_numeric(df.get("nose_y"), errors="coerce").to_numpy(dtype=float)
        sho_l = pd.to_numeric(df.get("lsho_x"), errors="coerce").to_numpy(dtype=float)
        sho_r = pd.to_numeric(df.get("rsho_x"), errors="coerce").to_numpy(dtype=float)

        idxs = np.linspace(win.start, max(win.start, win.end - 1), per_clip).astype(int)
        cap = cv2.VideoCapture(clip)
        for fi in idxs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(fi))
            ok, frame = cap.read()
            if not ok:
                continue
            H, W = frame.shape[:2]
            attempted += 1
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            try:
                res = lm.detect(img)
            except Exception:
                continue
            if not res.face_landmarks:
                continue
            detected += 1
            fl = res.face_landmarks[0]
            if len(fl) <= max(MOUTH_R, EYE_R):
                continue
            mouth_px.append(float(np.hypot((fl[MOUTH_L].x - fl[MOUTH_R].x) * W, (fl[MOUTH_L].y - fl[MOUTH_R].y) * H)))
            eye_px.append(float(np.hypot((fl[EYE_L].x - fl[EYE_R].x) * W, (fl[EYE_L].y - fl[EYE_R].y) * H)))

            # Is this the pitcher? Compare the face centre to the pose nose, in
            # units of the pitcher's own shoulder width, so the tolerance scales
            # with how big he is in frame.
            fcx = float(np.mean([p.x for p in fl]))
            fcy = float(np.mean([p.y for p in fl]))
            if fi < len(nose_x) and np.isfinite(nose_x[fi]) and np.isfinite(sho_l[fi]) and np.isfinite(sho_r[fi]):
                shw = abs(sho_l[fi] - sho_r[fi])
                if shw > 1e-6:
                    d = float(np.hypot(fcx - nose_x[fi], fcy - nose_y[fi]) / shw)
                    face_to_nose.append(d)
                    if d <= 1.0:
                        on_pitcher += 1
        cap.release()
    lm.close()

    def stat(v: list[float]) -> dict:
        if not v:
            return {"n": 0}
        a = np.array(v)
        return {
            "n": int(a.size),
            "median_px": round(float(np.median(a)), 2),
            "p5_px": round(float(np.percentile(a, 5)), 2),
            "p95_px": round(float(np.percentile(a, 95)), 2),
        }

    return {
        "frames_attempted": attempted,
        "frames_with_face": detected,
        "detection_rate": round(detected / attempted, 4) if attempted else None,
        "mouth_width": stat(mouth_px),
        "inter_eye": stat(eye_px),
        # A detection only counts as the pitcher's face if it sits within one
        # shoulder width of his pose nose.
        "faces_on_pitcher": on_pitcher,
        "face_to_nose_shoulder_widths": stat(face_to_nose),
        "pitcher_face_rate": round(on_pitcher / attempted, 4) if attempted else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", default="runs/drew_thorpe_rich_poc")
    ap.add_argument("--limit", type=int, default=120, help="clips for the geometric pass")
    ap.add_argument("--face-clips", type=int, default=25, help="clips for the model pass")
    ap.add_argument("--per-clip", type=int, default=6, help="frames sampled per clip")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    geo = geometric(args.run, args.limit)
    report: dict = {"run": args.run}
    if geo.empty:
        report["geometric"] = {"error": "no valid windows"}
    else:
        head = geo["head_scale_px"].dropna()
        report["resolutions"] = geo.attrs.get("resolutions", {})
        report["geometric"] = {
            "n_clips": int(len(geo)),
            "head_scale_px": {
                "median": round(float(head.median()), 2),
                "p5": round(float(head.quantile(0.05)), 2),
                "p95": round(float(head.quantile(0.95)), 2),
            },
            "sho_width_px_median": round(float(geo["sho_width_px"].median()), 2),
            "implied_mouth_width_px_median": round(float(head.median() * MOUTH_FRACTION_OF_HEAD), 2),
        }

    # The geometric pass is the load-bearing measurement and must survive a
    # model-side failure, which is itself a reportable result.
    try:
        report["empirical"] = empirical(args.run, args.face_clips, args.per_clip)
    except Exception as exc:  # noqa: BLE001
        report["empirical"] = {"error": f"{type(exc).__name__}: {exc}"}
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w") as f:
            f.write(text)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
