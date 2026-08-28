"""
Resolve or retract glove_angle_at_lift.

The fixed cue's surviving distribution is bimodal near +/-80 degrees, which was
recorded rather than settled. The scouting documents name this cue directly
("WRIST ANGLED UP", "TOP OF GLOVE UP"), so a half-working version is worse than
none: it is a cue a buyer would look for and therefore trust.

The hypothesis to test is that _elevation's arctangent saturates. It computes
``atan2(fy, |fx|)`` on the elbow->glove forearm. In the CF view the forearm
points close to the camera axis, so the horizontal extent |fx| collapses toward
zero while the vertical fy survives. When |fx| -> 0 the arctangent goes to
+/-90 regardless of the true tilt, so the reported magnitude stops varying with
the posture and only the SIGN of fy carries information. That would make a
one-bit measurement wearing a degrees label and an 8-degree threshold.

Three things decide it:

  1. Is |fx| actually unresolved? Compare it to the landmark noise floor. If the
     horizontal extent is below the jitter, no angle is recoverable from it.
  2. Is the magnitude informative, or is it saturation? If |angle| is pinned
     near 90 and the sign does the work, the cue is binary.
  3. Does the vertical component alone behave like a real cue? fy is a
     torso-normalised distance — how far the glove sits above the elbow — which
     carries the standard 0.05-torso visibility threshold and needs no angle
     gate, so it should recover the coverage the gate cost.

Read-only over cached rich tracks.
"""
from __future__ import annotations

import argparse
import glob
import math
import os

import numpy as np
import pandas as pd

MEASURED_JITTER = 0.10  # torso lengths/frame, from landmark_noise_probe.py
VISIBLE_TORSO = 0.05  # the standard normalised-distance threshold
LANDMARKS = (
    "nose", "lsho", "rsho", "lelb", "relb", "lwri", "rwri",
    "lpnk", "rpnk", "lidx", "ridx", "lhip", "rhip",
    "lkne", "rkne", "lank", "rank",
)


def _components(df: pd.DataFrame):
    """The forearm components the cue is built from, exactly as primitives does."""
    from preflight.primitives import _col, _mid, pitch_primitives

    r = pitch_primitives(df, "x")
    if r is None:
        return None
    lf = r.get("lift_frame")
    if lf is None or not np.isfinite(lf):
        return None
    i = int(lf)
    scale = float(r["torso_scale"])
    if not np.isfinite(scale) or scale <= 0:
        return None

    def at(s):
        a = np.asarray(s, dtype=float)
        return a[i] if 0 <= i < len(a) else float("nan")

    lw, rw = _col(df, "lwri_x"), _col(df, "rwri_x")
    lwy, rwy = _col(df, "lwri_y"), _col(df, "rwri_y")
    le, re_ = _col(df, "lelb_x"), _col(df, "relb_x")
    ley, rey = _col(df, "lelb_y"), _col(df, "relb_y")
    gx, gy = _mid(lw, rw), _mid(lwy, rwy)
    ex, ey = _mid(le, re_), _mid(ley, rey)
    fx = (at(gx) - at(ex)) / scale
    fy = (at(ey) - at(gy)) / scale
    return {
        "fx": float(fx),
        "fy": float(fy),
        "angle": r.get("glove_angle_at_lift"),
        "scale": scale,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", default=["../runs/drew_thorpe_rich_poc"])
    args = ap.parse_args()

    rng = np.random.default_rng(11)
    rows, pert = [], []
    for run in args.runs:
        for p in sorted(glob.glob(os.path.join(run, "lift_tracks", "*.csv"))):
            try:
                df = pd.read_csv(p)
            except Exception:
                continue
            c = _components(df)
            if c is None:
                continue
            nz = df.copy()
            for lm in LANDMARKS:
                for ax in ("x", "y"):
                    col = f"{lm}_{ax}"
                    if col in nz.columns:
                        nz[col] = pd.to_numeric(nz[col], errors="coerce") + rng.normal(
                            0, MEASURED_JITTER * c["scale"], len(nz)
                        )
            c_p = _components(nz)
            # Keep a pitch only when BOTH passes produced a value, so the two
            # frames stay row-for-row comparable. Filtering them independently
            # afterwards is what corrupted the noise estimate.
            if c_p is None:
                continue
            rows.append(c)
            pert.append(c_p)

    d = pd.DataFrame(rows)
    q = pd.DataFrame(pert)
    n = len(d)
    print(f"pitches with a resolvable lift frame: {n}\n")

    # --- 1. is the horizontal extent resolved at all? ------------------------
    absfx = d["fx"].abs().dropna()
    print("1. HORIZONTAL EXTENT |fx| of the elbow->glove forearm, torso lengths")
    print(f"   landmark jitter floor           : {MEASURED_JITTER:.3f}")
    print(f"   median |fx|                     : {absfx.median():.3f}")
    print(f"   share of pitches |fx| < jitter  : {(absfx < MEASURED_JITTER).mean():.1%}")
    print(f"   share |fx| < 2x jitter          : {(absfx < 2 * MEASURED_JITTER).mean():.1%}")
    fy = d["fy"].abs().dropna()
    print(f"   median |fy| (vertical) for scale: {fy.median():.3f}")
    print(f"   => vertical/horizontal ratio    : {fy.median() / max(1e-9, absfx.median()):.2f}\n")

    # --- 2. is the magnitude informative, or saturation? --------------------
    a = pd.to_numeric(d["angle"], errors="coerce").dropna()
    print("2. IS THE ANGLE MAGNITUDE INFORMATIVE?")
    if len(a):
        print(f"   n with an angle                 : {len(a)} (coverage {len(a)/n:.1%})")
        print(f"   median |angle|                  : {a.abs().median():.1f} deg")
        print(f"   share |angle| > 75 deg          : {(a.abs() > 75).mean():.1%}")
        print(f"   share |angle| within +/-45 deg  : {(a.abs() < 45).mean():.1%}")
        print(f"   sd of |angle| (magnitude only)  : {a.abs().std():.1f} deg")
        print(f"   sd of angle (with sign)         : {a.std():.1f} deg")
        # If the sign explains nearly all the variance, the cue is one bit.
        expl = 1 - (a.abs().std() ** 2) / max(1e-9, a.std() ** 2)
        print(f"   variance explained by SIGN alone: {expl:.1%}")
    print()

    # --- 3. does the vertical component behave like a real cue? ------------
    print("3. VERTICAL COMPONENT as its own cue (glove rise above the elbow, torso)")
    # Pair by position, not by index: `join` aligns on the index, and because
    # the perturbed pass drops a different set of pitches the two frames are not
    # index-comparable. Joining them subtracted unrelated pitches from each other
    # and inflated the apparent noise from 0.13 to 0.30 torso lengths, which read
    # as "no recoverable signal" when the real answer is the opposite.
    merged = pd.DataFrame(
        {
            "fy": d["fy"].to_numpy(),
            "fy_p": q["fy"].to_numpy()[: len(d)],
            "angle": pd.to_numeric(d["angle"], errors="coerce").to_numpy(),
            "angle_p": pd.to_numeric(q["angle"], errors="coerce").to_numpy()[: len(d)],
        }
    )
    dv = (merged["fy"] - merged["fy_p"]).dropna()
    ind_v = float(dv.std() / math.sqrt(2)) if len(dv) > 2 else float("nan")
    betw_v = float(d["fy"].std())
    sig_v = math.sqrt(max(0.0, betw_v**2 - ind_v**2))
    da = (pd.to_numeric(merged["angle"], errors="coerce") - pd.to_numeric(merged["angle_p"], errors="coerce")).dropna()
    ind_a = float(da.std() / math.sqrt(2)) if len(da) > 2 else float("nan")
    print(f"   coverage                        : {d['fy'].notna().mean():.1%}  (angle version: {len(a)/n:.1%})")
    print(f"   between-pitch sd                : {betw_v:.4f} torso")
    print(f"   induced landmark noise          : {ind_v:.4f} torso")
    print(f"   recovered signal sd             : {sig_v:.4f} torso")
    print(f"   noise / signal                  : {ind_v/max(1e-9,sig_v):.2f}   (PitchCom retired at 1.9)")
    print(f"   visibility threshold            : {VISIBLE_TORSO:.3f} torso")
    print(f"   std error of a 50-pitch group   : {ind_v/math.sqrt(50):.4f}  clears threshold: {ind_v/math.sqrt(50) < VISIBLE_TORSO}")
    print(f"   (angle version induced noise    : {ind_a:.1f} deg against an 8.0 deg threshold)")
    print()
    print("   vertical-component quantiles, torso lengths:")
    print("  ", {k: round(float(v), 3) for k, v in d["fy"].dropna().quantile([.05, .25, .5, .75, .95]).items()})


if __name__ == "__main__":
    main()
