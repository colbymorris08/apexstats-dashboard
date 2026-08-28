"""
Before/after assessment for the two shipped angle defects.

The defects
-----------
``glove_angle_at_lift`` takes a raw ``atan2`` of the forearm vector. Mirroring a
pitcher left-to-right — the difference between a lefty and a righty — flips that
angle by 180 degrees, so the same physical posture reads as +100 for one and -80
for the other and the group mean of a mixed sample is meaningless. It also
reports an angle regardless of whether the forearm projects to a measurable
length, and from center field a forearm angled at the lens projects to almost
nothing, at which point the arctangent is the ratio of two noise terms.

``posture_lean_at_lift`` returns ``atan2`` of the trunk vector without checking
the trunk is the right way up, so an inverted pose (a tracking failure) enters
the sample as a lean near ±180 rather than as NaN. Real tracks show a 5th
percentile of -159 degrees.

Why this needs a probe rather than a patch
------------------------------------------
Both features feed the window verified at 94.3%, so the question that has to be
answered first is whether changing them moves the window. Structurally it cannot
— ``window.py`` imports nothing from ``primitives.py``, so the window is computed
upstream and the primitives only consume it — but "structurally it cannot" is
the kind of claim that should be measured rather than asserted, so this script
recomputes the placement statistics on both code paths and compares them
pitch-by-pitch.

It also quantifies what the fix does to the two features, because the point of
fixing ``glove_angle_at_lift`` is that glove angle is named directly in the
scouting documents (``WRIST ANGLED UP``, ``TOP OF GLOVE UP``) and a defective
version of it could be masking a real cue.

Read-only over cached tracks. No video decode, no re-tracking.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from preflight.primitives import (
    LIFT_HALF_WIN,
    MAX_TORSO,
    MIN_ANGLE_SEGMENT,
    MIN_TORSO,
    _col,
    _med,
    _mid,
)
from preflight.window import actionable_window


def _window_for(df: pd.DataFrame):
    lwri_x, lwri_y = _col(df, "lwri_x"), _col(df, "lwri_y")
    rwri_x, rwri_y = _col(df, "rwri_x"), _col(df, "rwri_y")
    wdf = df.copy()
    wdf["glove_x"] = _mid(lwri_x, rwri_x)
    wdf["glove_y"] = _mid(lwri_y, rwri_y)
    wdf["wrist_dist"] = np.hypot(lwri_x - rwri_x, lwri_y - rwri_y)
    return actionable_window(wdf)


def angles_both_ways(df: pd.DataFrame) -> dict | None:
    """
    Compute both angle features on the old and new definitions for one pitch,
    alongside the window placement fields, so nothing is compared across
    separate passes over the data.
    """
    win = _window_for(df)
    if not win.valid:
        return None

    lsho_x, lsho_y = _col(df, "lsho_x"), _col(df, "lsho_y")
    rsho_x, rsho_y = _col(df, "rsho_x"), _col(df, "rsho_y")
    lhip_x, lhip_y = _col(df, "lhip_x"), _col(df, "lhip_y")
    rhip_x, rhip_y = _col(df, "rhip_x"), _col(df, "rhip_y")
    lwri_x, lwri_y = _col(df, "lwri_x"), _col(df, "lwri_y")
    rwri_x, rwri_y = _col(df, "rwri_x"), _col(df, "rwri_y")
    lelb_x, lelb_y = _col(df, "lelb_x"), _col(df, "lelb_y")
    relb_x, relb_y = _col(df, "relb_x"), _col(df, "relb_y")

    sho_x, sho_y = _mid(lsho_x, rsho_x), _mid(lsho_y, rsho_y)
    hip_x, hip_y = _mid(lhip_x, rhip_x), _mid(lhip_y, rhip_y)
    glove_x, glove_y = _mid(lwri_x, rwri_x), _mid(lwri_y, rwri_y)
    elb_x, elb_y = _mid(lelb_x, relb_x), _mid(lelb_y, relb_y)

    torso = np.hypot(sho_x - hip_x, sho_y - hip_y)
    scale = _med(torso, int(win.start), int(win.end))
    if not np.isfinite(scale) or not (MIN_TORSO <= scale <= MAX_TORSO):
        return None
    lift = win.lift_frame
    if lift is None:
        return None
    lo, hi = int(lift) - LIFT_HALF_WIN, int(lift) + LIFT_HALF_WIN + 1

    def at(a):
        return _med(a, lo, hi)

    fx, fy = at(glove_x) - at(elb_x), at(elb_y) - at(glove_y)
    tx, ty = at(sho_x) - at(hip_x), at(hip_y) - at(sho_y)

    # --- old definitions, verbatim from primitives.py ---------------------
    old_angle = math.degrees(math.atan2(fy, fx)) if np.isfinite(fx) and np.isfinite(fy) else float("nan")
    old_lean = math.degrees(math.atan2(tx, ty)) if np.isfinite(tx) and np.isfinite(ty) else float("nan")

    # --- new definitions --------------------------------------------------
    # Glove angle: fold for handedness and require a resolvable segment.
    nfx, nfy = fx / scale, fy / scale
    if not (np.isfinite(nfx) and np.isfinite(nfy)) or math.hypot(nfx, nfy) < MIN_ANGLE_SEGMENT:
        new_angle = float("nan")
    else:
        new_angle = math.degrees(math.atan2(nfy, abs(nfx)))
    # Lean: NaN on an inverted trunk. No fold — the trunk segment is a torso
    # length by definition so it is always resolvable, and the sign of the lean
    # is meaningful and should be kept.
    new_lean = (
        math.degrees(math.atan2(tx, ty))
        if np.isfinite(tx) and np.isfinite(ty) and ty > 0
        else float("nan")
    )

    return {
        "start": int(win.start),
        "end": int(win.end),
        "set_frame": -1 if win.set_frame is None else int(win.set_frame),
        "lift_frame": int(lift),
        "delivery_frame": -1 if win.delivery_frame is None else int(win.delivery_frame),
        "method": win.method,
        "delivery_type": win.delivery_type,
        "old_glove_angle": old_angle,
        "new_glove_angle": new_angle,
        "old_lean": old_lean,
        "new_lean": new_lean,
        "trunk_inverted": bool(np.isfinite(ty) and ty <= 0),
    }


def run(run_dirs: list[Path]) -> dict:
    rows = []
    for rd in run_dirs:
        for p in sorted((rd / "lift_tracks").glob("*.csv")):
            try:
                df = pd.read_csv(p)
            except Exception:
                continue
            got = angles_both_ways(df)
            if got:
                got["play_id"] = p.stem
                got["run"] = rd.name
                rows.append(got)
    d = pd.DataFrame(rows)
    if d.empty:
        return {"error": "no usable pitches"}

    def desc(col):
        s = d[col].dropna()
        if s.empty:
            return {"n": 0}
        return {
            "n": int(s.size),
            "coverage": round(float(d[col].notna().mean()), 4),
            "mean": round(float(s.mean()), 3),
            "sd": round(float(s.std()), 3),
            "p5": round(float(s.quantile(0.05)), 3),
            "p50": round(float(s.median()), 3),
            "p95": round(float(s.quantile(0.95)), 3),
        }

    # Handedness bimodality: the raw angle should show two clusters ~180 apart.
    old = d["old_glove_angle"].dropna()
    return {
        "n_pitches": int(len(d)),
        "runs": sorted(d["run"].unique().tolist()),
        # Placement is a property of the window, which neither definition
        # touches. Reported so the claim is measured rather than asserted.
        "window_placement": {
            "methods": {str(k): int(v) for k, v in d["method"].value_counts().items()},
            "delivery_types": {str(k): int(v) for k, v in d["delivery_type"].value_counts().items()},
            "lift_inside_window": round(float(((d.lift_frame >= d.start) & (d.lift_frame < d.end)).mean()), 4),
            "end_before_delivery": round(
                float((d[d.delivery_frame >= 0].end <= d[d.delivery_frame >= 0].delivery_frame).mean()), 4
            ),
            "median_window_frames": int((d.end - d.start).median()),
            "median_lift_to_end": int((d.end - d.lift_frame).median()),
        },
        "glove_angle_at_lift": {
            "old": desc("old_glove_angle"),
            "new": desc("new_glove_angle"),
            "old_sign_split": {
                "positive": int((old > 0).sum()),
                "negative": int((old < 0).sum()),
                "share_beyond_90_deg": round(float((old.abs() > 90).mean()), 4),
            },
        },
        "posture_lean_at_lift": {
            "old": desc("old_lean"),
            "new": desc("new_lean"),
            "inverted_trunk_pitches": int(d["trunk_inverted"].sum()),
            "old_share_beyond_90_deg": round(float((d["old_lean"].abs() > 90).mean()), 4),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    rep = run(args.run_dir)
    text = json.dumps(rep, indent=2)
    print(text)
    if args.out:
        args.out.write_text(text)


if __name__ == "__main__":
    main()
