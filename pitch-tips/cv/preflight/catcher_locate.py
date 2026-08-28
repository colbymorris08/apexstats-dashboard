#!/usr/bin/env python3
"""
Detector-based catcher localisation: find the catcher region, run pose on the
crop, and require the pose to agree with the detector box before believing it.

This is the approach docs/catcher_subject_bug.md deferred to, and it exists
because the pose-based selector could not work. In the CF framing MediaPipe
returns a single pose on 65-77% of frames, so "the lowest-hip pose that is not
the pitcher" had nothing to return and an unconditional fallback handed back the
pitcher himself on 71-91% of frames. Every catcher feature was therefore
describing the pitcher.

What the framing actually looks like, measured rather than assumed
------------------------------------------------------------------
The camera is elevated behind the pitcher. Consequences that matter here:

  * The catcher appears ABOVE the pitcher in image space (catcher body centre
    ~0.49 normalised y, pitcher hip midpoint ~0.573). "Lowest hips in frame" was
    not merely unreliable, it had the sign wrong: the catcher is never the lowest
    pose. This is why ``catcher_hip_y`` median 0.574 matching the pitcher's 0.573
    was such a clean tell.
  * The catcher does face the camera, which is the geometric reason to expect
    more from his mitt than from the pitcher's glove.
  * The catcher is SMALL: his gear boxes run ~0.04 of frame width and ~0.06 of
    frame height, i.e. roughly 50x43 px in a 1280x720 frame. Landmarks on a
    subject that size are the binding constraint on every cue derived here, so
    pose is run on an upscaled crop, and the noise floor is measured on the
    catcher's own landmarks rather than inherited from the pitcher's.

Which detector classes are trustworthy
--------------------------------------
Measured on 40 frames sampled from 4 clips (catcher_detect_probe.py), then the
boxes were rendered and inspected (catcher_box_peek.py):

  catcher_shin    fires on the catcher's body at conf 0.85-0.93. Usable anchor.
  catcher_cleat   fires low on the catcher. Usable, lower confidence.
  catcher_mitt    fires on the catcher but rarely clears conf 0.5 (2.5% of
                  frames), so it cannot be the primary anchor even though it is
                  the class named in the deferral note.
  catcher_mask    EXCLUDED. It lands on the UMPIRE's head, not the catcher's.
                  The umpire stands directly behind the catcher wearing the same
                  piece of equipment and the class cannot tell them apart. It is
                  also the highest-rate class (77.5%), so using it would have
                  produced the best-looking coverage and the wrong body a third
                  time.

The detector's own validation carries no weight here: ``catcher_mitt`` reports
mAP50 0.995 on **5 instances in 5 images** (runs/yolo_parts_v2.log). That is not
evidence, which is why the rates above were measured directly.

Why the detector box verifies the subject rather than only framing it
--------------------------------------------------------------------
The first version of this module cropped on the detector and then ran pose with
``num_poses=1``, and it identified a catcher on 2.5% of frames. Rendering the
crops showed why, and it was not a small-subject problem: the crop was correctly
centred on the catcher, and pose was returning the HITTER standing at the edge of
it. The catcher was in the picture and losing to a larger, fully-visible body —
the same competition that the whole-frame selector lost.

Cropping is therefore necessary but not sufficient. What makes the identification
sound is that the gear box is independent evidence of where the catcher is: a
``catcher_shin`` detection at conf 0.93 is on the catcher, so a pose is only
accepted when it actually reaches that box. That is the same structure as the
face-to-nose shoulder-width test that fixed the cheek columns — an independent
localiser adjudicating between candidate subjects — rather than a scoring
heuristic hoping to rank the right one first.

Contract
--------
``locate_catcher`` returns None whenever the catcher is not independently
identified, and its ``reason`` output records which stage refused. There is
deliberately no fallback to a nearby pose, to the highest-scoring pose, or to the
previous frame's position. Four of this project's six failure modes were a silent
fallback filling a column with plausible wrong values; the caller writes NaN.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from preflight.parts_detect import detect_parts

# Classes that may anchor a catcher crop, and the confidence each must clear.
#
# Thresholds are set from the measured confidence distributions, not tuned
# against any downstream result: shin/cleat/mitt separate into a noise lobe with
# median conf ~0.09-0.13 and a real lobe above ~0.5, and 0.5 sits in the gap.
# No cue outcome was consulted in choosing them.
ANCHOR_CLASSES: dict[str, float] = {
    "catcher_shin": 0.50,
    "catcher_cleat": 0.50,
    "catcher_mitt": 0.50,
}
# catcher_mask is absent by design — see the module docstring. It is the umpire.
EXCLUDED_CLASSES = ("catcher_mask",)

# Crop geometry, in units of the anchor gear box.
#
# These are measured, not chosen. Over the sampled frames the median catcher gear
# box (conf >= 0.5, mask excluded) is 0.0531 of frame height and 0.045 of frame
# width, and the identified catcher's torso is 0.047 of frame height. A squatting
# body is about 2.5 torso lengths tall, so:
#
#   body height / gear box height = 2.5 * 0.047 / 0.0531 = 2.21
#   body width  / gear box width  = 1.3 * 0.047 / 0.045  = 1.36
#
# The multipliers below are those ratios with margin, and the margin is the point
# rather than an afterthought: the anchor sits on the lower body so the crop has
# to reach up past the head, and it must stay wide enough to contain the mitt on
# the pitches where the catcher sets up wide, because mitt position is the signal
# the third cue family measures. Cropping it out would manufacture a null.
#
# The first version used 5.0 and 4.0, picked by eye. That is 2.3x and 2.9x too
# large, and it is why the hitter and the umpire were inside the crop and winning
# the pose competition: "standing_not_squatting" was the single largest rejection
# reason at 23-59% of frames.
CROP_H_MULT = 3.5
CROP_W_MULT = 3.0
# The gear classes are all lower-body (shin, cleat, mitt), so the anchor centroid
# sits below the middle of the body. Half a gear-box height of upward shift
# centres the crop on the torso instead of on the shins.
CROP_UP_SHIFT_MULT = 0.5
# Never crop smaller than this in pixels; below it upscaling invents detail.
CROP_MIN_PX = 96
# Pose is run at this size. The crop is upscaled to it because MediaPipe's pose
# landmarker degrades badly on subjects a few tens of pixels tall.
POSE_INPUT_PX = 384
# Candidate poses per crop. More than one is essential: the crop contains the
# hitter and the umpire as well as the catcher, and with num_poses=1 the hitter
# won on the frames that were inspected.
CROP_NUM_POSES = 3

# The accepted pose must reach the gear box that located the catcher. Distance is
# from the box centre to the nearest of the pose's hip midpoint and knee
# midpoint, in that pose's own torso lengths, because shin/cleat/mitt all sit in
# the lower body.
#
# 2.0 torso lengths is generous for a true match — a squatting catcher's shin is
# well under one torso length from his hips — and rejects the failure that was
# actually observed, where the hitter's pose sat 4+ torso lengths from the box.
MAX_ANCHOR_TO_POSE_TORSOS = 2.0

# The accepted pose must also look like a squatting catcher seen from the front.
#
# In a squat the knees rise toward or above the hips, so hip_y - knee_y (image y
# grows downward) is near zero or positive, where a standing subject is strongly
# negative. The bound is deliberately loose: it is there to reject the umpire
# standing behind the catcher and a fielder crossing the crop, not to grade the
# depth of the squat, which is what the stance cue measures.
MAX_STANDING_KNEE_DROP = 0.35  # in the pose's own torso lengths
# A pose whose torso is a large fraction of the crop is the crop's intended
# subject; a much smaller one is somebody in the background of it.
MIN_TORSO_FRAC_OF_CROP = 0.12

NOSE = 0
L_SHOULDER, R_SHOULDER = 11, 12
L_ELBOW, R_ELBOW = 13, 14
L_WRIST, R_WRIST = 15, 16
L_PINKY, R_PINKY = 17, 18
L_INDEX, R_INDEX = 19, 20
L_HIP, R_HIP = 23, 24
L_KNEE, R_KNEE = 25, 26
L_ANKLE, R_ANKLE = 27, 28

# Catcher landmarks persisted per frame, mirroring the pitcher's KEEP_LANDMARKS
# so catcher cues can be re-derived later without another tracking pass — the
# expensive part. Prefixed ``c`` to keep them unambiguously separate from the
# pitcher's columns and from the retracted ``catcher_*`` family.
KEEP_LANDMARKS: dict[str, int] = {
    "cnose": NOSE,
    "clsho": L_SHOULDER,
    "crsho": R_SHOULDER,
    "clelb": L_ELBOW,
    "crelb": R_ELBOW,
    "clwri": L_WRIST,
    "crwri": R_WRIST,
    "clpnk": L_PINKY,
    "crpnk": R_PINKY,
    "clidx": L_INDEX,
    "cridx": R_INDEX,
    "clhip": L_HIP,
    "crhip": R_HIP,
    "clkne": L_KNEE,
    "crkne": R_KNEE,
    "clank": L_ANKLE,
    "crank": R_ANKLE,
}


@dataclass(frozen=True)
class CatcherCrop:
    """Pixel crop believed to contain the catcher, plus how it was chosen."""

    x1: int
    y1: int
    x2: int
    y2: int
    anchor_class: str
    anchor_conf: float
    anchor_cx: float
    anchor_cy: float
    n_anchor_classes: int


@dataclass(frozen=True)
class CatcherPose:
    """
    An identified catcher.

    ``landmarks`` maps the names in ``KEEP_LANDMARKS`` to (x, y, visibility) in
    FULL-FRAME normalised coordinates, so downstream code never has to know a
    crop was involved. ``anchor_dist_torsos`` and ``torso`` are kept because they
    are the evidence that this is the catcher, and a reader auditing a surprising
    result needs them without re-running the tracker.
    """

    landmarks: dict[str, tuple[float, float, float]]
    torso: float
    anchor_class: str
    anchor_conf: float
    anchor_dist_torsos: float
    n_anchor_classes: int
    crop_px: tuple[int, int]


POSE_VARIANTS = {
    "lite": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
        "pose_landmarker_lite.task",
    ),
    "full": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_full/float16/1/pose_landmarker_full.task",
        "pose_landmarker_full.task",
    ),
    "heavy": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task",
        "pose_landmarker_heavy.task",
    ),
}


def make_pose_landmarker(variant: str = "lite"):
    """
    Pose landmarker configured for crops.

    IMAGE mode, not VIDEO: VIDEO carries tracking state between calls, and the
    crop moves and changes size from frame to frame, so that state would be
    describing a different image each time.

    ``variant`` selects the model size. The pitcher tracker uses ``lite`` on
    full frames, where the pitcher is large; the catcher is a much harder subject
    (small, squatting, occluded by the umpire) so the variant is a parameter and
    the choice is made by measurement in catcher_model_probe.py.
    """
    from preflight.track_pitcher import _ensure_model

    url, name = POSE_VARIANTS[variant]
    model = _ensure_model(url, name)
    opts = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(
            model_asset_path=str(model),
            # Explicit CPU delegate: the default tries to stand up an OpenGL
            # context, which is not always available and fails at construction.
            delegate=mp_python.BaseOptions.Delegate.CPU,
        ),
        running_mode=vision.RunningMode.IMAGE,
        num_poses=CROP_NUM_POSES,
        min_pose_detection_confidence=0.3,
        min_pose_presence_confidence=0.3,
    )
    return vision.PoseLandmarker.create_from_options(opts)


def _anchors(dets: list[dict]) -> list[dict]:
    return [
        d
        for d in dets
        if d["name"] in ANCHOR_CLASSES
        and d["name"] not in EXCLUDED_CLASSES
        and d["conf"] >= ANCHOR_CLASSES[d["name"]]
    ]


def catcher_crop(frame: np.ndarray, dets: list[dict] | None = None, *, conf: float = 0.05) -> CatcherCrop | None:
    """
    Pixel region containing the catcher, or None if he was not localised.

    When several gear classes fire they are required to agree spatially before
    the crop is built: two independent pieces of catcher gear landing in the same
    place is much stronger evidence than one high-confidence box, and
    disagreement means at least one of them is on somebody else.
    """
    h, w = frame.shape[:2]
    if dets is None:
        dets = detect_parts(frame, conf=conf)
    anchors = _anchors(dets)
    if not anchors:
        return None

    # The single most confident gear box is the reference. Anchoring on the
    # median of all of them instead let a stray low-agreement box pull the crop
    # off the catcher and toward the umpire.
    best = max(anchors, key=lambda d: d["conf"])
    bx1, by1, bx2, by2 = best["xyxy"]
    bh, bw = by2 - by1, bx2 - bx1
    ax, ay = (bx1 + bx2) / 2, (by1 + by2) / 2
    # Crop centre, shifted up off the lower-body gear onto the torso. Kept
    # separate from the anchor centre, which stays where the detector put it
    # because it is the evidence the accepted pose has to reach.
    mx, my = ax, ay - CROP_UP_SHIFT_MULT * bh

    tol = max(CROP_H_MULT * bh / 2, CROP_MIN_PX / 2)
    agree = [
        d
        for d in anchors
        if abs((d["xyxy"][0] + d["xyxy"][2]) / 2 - ax) <= tol
        and abs((d["xyxy"][1] + d["xyxy"][3]) / 2 - ay) <= tol
    ]

    ch = max(CROP_H_MULT * bh, CROP_MIN_PX)
    cw = max(CROP_W_MULT * bw, CROP_MIN_PX)
    x1 = int(max(0, mx - cw / 2))
    x2 = int(min(w, mx + cw / 2))
    y1 = int(max(0, my - ch / 2))
    y2 = int(min(h, my + ch / 2))
    if x2 - x1 < CROP_MIN_PX // 2 or y2 - y1 < CROP_MIN_PX // 2:
        return None
    return CatcherCrop(
        x1, y1, x2, y2,
        anchor_class=best["name"],
        anchor_conf=float(best["conf"]),
        anchor_cx=float(ax),
        anchor_cy=float(ay),
        n_anchor_classes=len({d["name"] for d in agree}),
    )


def _pose_geometry(lm) -> tuple[float, float, float, float, float] | None:
    """(hip_x, hip_y, knee_x, knee_y, torso) in crop-normalised units."""
    def pt(i):
        if lm is None or i >= len(lm):
            return None
        return float(lm[i].x), float(lm[i].y)

    ls, rs, lh, rh = pt(L_SHOULDER), pt(R_SHOULDER), pt(L_HIP), pt(R_HIP)
    if not all([ls, rs, lh, rh]):
        return None
    sho_y = (ls[1] + rs[1]) / 2
    hip_x = (lh[0] + rh[0]) / 2
    hip_y = (lh[1] + rh[1]) / 2
    torso = abs(hip_y - sho_y)
    lk, rk = pt(L_KNEE), pt(R_KNEE)
    knees = [k for k in (lk, rk) if k is not None]
    if not knees:
        return None
    knee_x = float(np.mean([k[0] for k in knees]))
    knee_y = max(k[1] for k in knees)
    return hip_x, hip_y, knee_x, knee_y, torso


def locate_catcher(
    frame: np.ndarray,
    pose,
    dets: list[dict] | None = None,
    *,
    conf: float = 0.05,
) -> tuple[CatcherPose | None, str]:
    """
    Identify the catcher in one frame. Returns (pose or None, reason).

    ``reason`` is always populated, including on success, so a track can report
    why the catcher columns are empty on the frames where they are empty. A blank
    that could mean either "not detected" or "detected and still" is the defect
    this project keeps rediscovering.
    """
    if dets is None:
        dets = detect_parts(frame, conf=conf)
    crop = catcher_crop(frame, dets, conf=conf)
    if crop is None:
        return None, "no_gear_anchor"

    sub = frame[crop.y1:crop.y2, crop.x1:crop.x2]
    if sub.size == 0:
        return None, "empty_crop"
    ch, cw = sub.shape[:2]
    scale = POSE_INPUT_PX / max(ch, cw)
    up = cv2.resize(sub, (max(1, int(cw * scale)), max(1, int(ch * scale))), interpolation=cv2.INTER_CUBIC)
    rgb = cv2.cvtColor(up, cv2.COLOR_BGR2RGB)
    res = pose.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
    if not res.pose_landmarks:
        return None, "no_pose_in_crop"

    # Anchor position expressed in the crop's normalised coordinates, so it can
    # be compared with the pose landmarks directly.
    ax = (crop.anchor_cx - crop.x1) / cw
    ay = (crop.anchor_cy - crop.y1) / ch

    best = None
    best_d = None
    reason = "no_pose_reached_anchor"
    for lm in res.pose_landmarks:
        geo = _pose_geometry(lm)
        if geo is None:
            reason = "incomplete_pose"
            continue
        hip_x, hip_y, knee_x, knee_y, torso = geo
        if torso <= 1e-6:
            reason = "degenerate_torso"
            continue
        if torso < MIN_TORSO_FRAC_OF_CROP:
            reason = "torso_too_small_for_crop"
            continue
        if (hip_y - knee_y) / torso < -MAX_STANDING_KNEE_DROP:
            reason = "standing_not_squatting"
            continue
        # Crop coordinates are anisotropic (the crop is not square) but the
        # upscale preserves aspect, so distances in crop-normalised units must be
        # converted back to a common scale before comparing to a torso length.
        d = min(
            float(np.hypot((ax - hip_x) * cw, (ay - hip_y) * ch)),
            float(np.hypot((ax - knee_x) * cw, (ay - knee_y) * ch)),
        ) / (torso * ch)
        if d > MAX_ANCHOR_TO_POSE_TORSOS:
            reason = "pose_too_far_from_anchor"
            continue
        if best_d is None or d < best_d:
            best, best_d = lm, d

    if best is None:
        return None, reason

    geo = _pose_geometry(best)
    assert geo is not None
    torso_crop = geo[4]
    out: dict[str, tuple[float, float, float]] = {}
    for name, idx in KEEP_LANDMARKS.items():
        if idx >= len(best):
            continue
        p = best[idx]
        # Back to full-frame normalised coordinates.
        fx = (crop.x1 + float(p.x) * cw) / frame.shape[1]
        fy = (crop.y1 + float(p.y) * ch) / frame.shape[0]
        out[name] = (fx, fy, float(getattr(p, "visibility", 0.0) or 0.0))

    # Torso length in FULL-FRAME units: every catcher cue normalises by the
    # catcher's own torso, not the pitcher's, and not the crop's.
    sy = (out["clsho"][1] + out["crsho"][1]) / 2
    hy = (out["clhip"][1] + out["crhip"][1]) / 2
    sx = (out["clsho"][0] + out["crsho"][0]) / 2
    hx = (out["clhip"][0] + out["crhip"][0]) / 2
    torso_frame = float(np.hypot(sx - hx, sy - hy))

    return (
        CatcherPose(
            landmarks=out,
            torso=torso_frame,
            anchor_class=crop.anchor_class,
            anchor_conf=crop.anchor_conf,
            anchor_dist_torsos=float(best_d),
            n_anchor_classes=crop.n_anchor_classes,
            crop_px=(cw, ch),
        ),
        "catcher",
    )


# --- clip-level localisation --------------------------------------------------
# Per-frame localisation identified a catcher on 3.3% of frames (60 frames, 5
# clips). The breakdown says why, and it is not one problem:
#
#   no_gear_anchor            56.7%  the detector fired nothing above conf 0.50
#   standing_not_squatting    23.3%  a crop was found, but the three poses
#                                    returned in it were the hitter and umpire;
#                                    the catcher was in the picture and lost
#   torso_too_small_for_crop  11.7%
#   no_pose_in_crop            3.3%
#   catcher                    3.3%
#
# The accepted frames were rendered and the landmarks are on the catcher, so the
# accept test is sound; the problem is recall, and the fix is not a looser
# threshold. It is to stop asking each frame independently.
#
# The catcher is very nearly stationary before the pitch. So the detector is
# sampled across the clip and the agreeing high-confidence boxes are pooled into
# ONE catcher region for the whole clip. That converts a 50%-of-frames detector
# into a region available on every frame, and it lets the crop be tight enough
# that the hitter and umpire stop winning the pose competition.
#
# Why this does not smuggle the signal into the crop
# --------------------------------------------------
# The third cue family measures where the catcher sets up (inside/outside), so a
# crop whose position tracked the catcher frame by frame would put the answer
# into the frame of reference and the cue would measure zero by construction —
# the proxy failure this project screens for. A clip-level median CANNOT do that:
# it is one fixed rectangle per clip, identical for every frame in it, so it
# carries no within-pitch positional information at all. The measurement is the
# pose inside the crop, in full-frame coordinates.
#
# It does mean the crop is fixed while the catcher shifts a few inches within it,
# which is fine: the crop only has to contain him.
CLIP_SAMPLE_STRIDE = 6
# Minimum agreeing gear detections across the sampled frames before a clip is
# considered to have a located catcher. Set so a couple of stray boxes cannot
# invent a region; with the default stride a real catcher produces dozens.
MIN_CLIP_ANCHORS = 6
# Spread allowed among pooled anchors, in units of the median anchor box height.
# Anchors further than this from the pooled centre are dropped as being on
# another body rather than averaged in.
CLIP_ANCHOR_SPREAD = 6.0
# A pose is only the catcher if its hip midpoint lands inside the core of the
# clip region. Without a per-frame gear box to point at, this is what keeps the
# umpire — who stands within the same crop — from being accepted.
CLIP_CORE_FRAC = 0.45


@dataclass(frozen=True)
class ClipRegion:
    """One catcher region for a whole clip, pooled from sampled gear detections."""

    x1: int
    y1: int
    x2: int
    y2: int
    n_anchors: int
    n_sampled_frames: int
    anchor_classes: tuple[str, ...]
    cx: float
    cy: float


def clip_catcher_region(
    clip_path,
    *,
    stride: int = CLIP_SAMPLE_STRIDE,
    conf: float = 0.05,
    max_frames: int | None = None,
) -> tuple[ClipRegion | None, dict]:
    """
    Pool gear detections across a clip into a single catcher region.

    Returns (region or None, diagnostics). None means the catcher was never
    localised in this clip, and every frame of it must yield NaN.
    """
    cap = cv2.VideoCapture(str(clip_path))
    if not cap.isOpened():
        return None, {"reason": "cannot_open"}
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    boxes: list[dict] = []
    n_sampled = 0
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if max_frames is not None and i >= max_frames:
            break
        if i % stride == 0:
            n_sampled += 1
            h, w = frame.shape[:2]
            for d in _anchors(detect_parts(frame, conf=conf)):
                x1, y1, x2, y2 = d["xyxy"]
                boxes.append({
                    "name": d["name"],
                    "conf": d["conf"],
                    "cx": (x1 + x2) / 2,
                    "cy": (y1 + y2) / 2,
                    "bw": x2 - x1,
                    "bh": y2 - y1,
                    "w": w,
                    "h": h,
                })
        i += 1
    cap.release()

    diag = {"n_sampled_frames": n_sampled, "n_raw_anchors": len(boxes), "total_frames": total}
    if len(boxes) < MIN_CLIP_ANCHORS:
        diag["reason"] = "too_few_anchors"
        return None, diag

    cx = np.array([b["cx"] for b in boxes])
    cy = np.array([b["cy"] for b in boxes])
    bh = float(np.median([b["bh"] for b in boxes]))
    bw = float(np.median([b["bw"] for b in boxes]))
    mx, my = float(np.median(cx)), float(np.median(cy))
    tol = CLIP_ANCHOR_SPREAD * bh
    keep = [b for b in boxes if abs(b["cx"] - mx) <= tol and abs(b["cy"] - my) <= tol]
    diag["n_kept_anchors"] = len(keep)
    if len(keep) < MIN_CLIP_ANCHORS:
        diag["reason"] = "anchors_disagree"
        return None, diag

    mx = float(np.median([b["cx"] for b in keep]))
    my = float(np.median([b["cy"] for b in keep])) - CROP_UP_SHIFT_MULT * bh
    W, H = keep[0]["w"], keep[0]["h"]
    ch = max(CROP_H_MULT * bh, CROP_MIN_PX)
    cw = max(CROP_W_MULT * bw, CROP_MIN_PX)
    x1 = int(max(0, mx - cw / 2))
    x2 = int(min(W, mx + cw / 2))
    y1 = int(max(0, my - ch / 2))
    y2 = int(min(H, my + ch / 2))
    diag["reason"] = "located"
    diag["anchor_spread_px"] = {
        "x": round(float(np.percentile([b["cx"] for b in keep], 90) - np.percentile([b["cx"] for b in keep], 10)), 1),
        "y": round(float(np.percentile([b["cy"] for b in keep], 90) - np.percentile([b["cy"] for b in keep], 10)), 1),
    }
    return (
        ClipRegion(
            x1, y1, x2, y2,
            n_anchors=len(keep),
            n_sampled_frames=n_sampled,
            anchor_classes=tuple(sorted({b["name"] for b in keep})),
            cx=mx / W,
            cy=my / H,
        ),
        diag,
    )


def catcher_in_region(frame: np.ndarray, pose, region: ClipRegion) -> tuple[CatcherPose | None, str]:
    """
    Identify the catcher in one frame using a clip-level region.

    The subject test has two independent parts, both required:

      * the pose must be squatting, which excludes the umpire and the hitter by
        posture rather than by position, and
      * its hip midpoint must land in the core of the region, which excludes
        anyone who is squatting elsewhere in the crop.

    Returns (pose or None, reason). Never falls back to the best available pose.
    """
    sub = frame[region.y1:region.y2, region.x1:region.x2]
    if sub.size == 0:
        return None, "empty_crop"
    ch, cw = sub.shape[:2]
    scale = POSE_INPUT_PX / max(ch, cw)
    up = cv2.resize(sub, (max(1, int(cw * scale)), max(1, int(ch * scale))), interpolation=cv2.INTER_CUBIC)
    rgb = cv2.cvtColor(up, cv2.COLOR_BGR2RGB)
    res = pose.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
    if not res.pose_landmarks:
        return None, "no_pose_in_crop"

    best = None
    best_d = None
    reason = "no_pose_in_core"
    for lm in res.pose_landmarks:
        geo = _pose_geometry(lm)
        if geo is None:
            reason = "incomplete_pose"
            continue
        hip_x, hip_y, _kx, knee_y, torso = geo
        if torso <= 1e-6:
            reason = "degenerate_torso"
            continue
        if torso < MIN_TORSO_FRAC_OF_CROP:
            reason = "torso_too_small_for_crop"
            continue
        if (hip_y - knee_y) / torso < -MAX_STANDING_KNEE_DROP:
            reason = "standing_not_squatting"
            continue
        # Distance from the crop centre, as a fraction of the crop half-extent.
        d = max(abs(hip_x - 0.5), abs(hip_y - 0.5)) / 0.5
        if d > CLIP_CORE_FRAC:
            reason = "pose_outside_region_core"
            continue
        if best_d is None or d < best_d:
            best, best_d = lm, d

    if best is None:
        return None, reason

    out: dict[str, tuple[float, float, float]] = {}
    for name, idx in KEEP_LANDMARKS.items():
        if idx >= len(best):
            continue
        p = best[idx]
        fx = (region.x1 + float(p.x) * cw) / frame.shape[1]
        fy = (region.y1 + float(p.y) * ch) / frame.shape[0]
        out[name] = (fx, fy, float(getattr(p, "visibility", 0.0) or 0.0))

    sy = (out["clsho"][1] + out["crsho"][1]) / 2
    hy = (out["clhip"][1] + out["crhip"][1]) / 2
    sx = (out["clsho"][0] + out["crsho"][0]) / 2
    hx = (out["clhip"][0] + out["crhip"][0]) / 2
    torso_frame = float(np.hypot(sx - hx, sy - hy))

    return (
        CatcherPose(
            landmarks=out,
            torso=torso_frame,
            anchor_class="clip_region:" + "+".join(region.anchor_classes),
            anchor_conf=float(region.n_anchors),
            anchor_dist_torsos=float(best_d),
            n_anchor_classes=len(region.anchor_classes),
            crop_px=(cw, ch),
        ),
        "catcher",
    )


__all__ = [
    "ANCHOR_CLASSES",
    "EXCLUDED_CLASSES",
    "KEEP_LANDMARKS",
    "CatcherCrop",
    "CatcherPose",
    "ClipRegion",
    "catcher_crop",
    "catcher_in_region",
    "clip_catcher_region",
    "locate_catcher",
    "make_pose_landmarker",
]
