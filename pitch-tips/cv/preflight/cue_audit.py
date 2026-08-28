"""
Systematic audit: for every publishable cue, what does the code actually compute,
and can it clear its own visibility threshold?

Why
---
Four features shipped tonight while measuring something other than their name,
and an incidental spot check of two more shipped glove cues found both defective
— two for two. That base rate says the known-bad set is not the full set, so
every cue gets the same three questions:

  1. what the implementation computes, read from the code rather than the name;
  2. its measured noise floor against its own visibility threshold, the
     comparison that retired pitchcom_tap_count and caught glove_angle_at_lift;
  3. what fills the column when the real measurement is unavailable — the
     answer has to be NaN.

This module answers (2) and (3) numerically. (1) and the verdicts live in
docs/cue_audit.md, because they are readings of code rather than computations.

Two noise standards, because the cues come from two different schemas
--------------------------------------------------------------------
``primitives``   54-column rich lift_tracks (landmarks). Noise is induced by
                 adding Gaussian jitter to every landmark at the measured
                 0.10 torso lengths/frame and recomputing, which is the standard
                 used in test_primitives.py.
``window``       16-column legacy tracks, carrying pre-derived scalars
                 (glove_vs_belt_y, glove_flare, wrist_speed, cheek_motion). The
                 landmarks that produced them were not persisted, so jitter
                 cannot be re-injected. Instead noise is read off the SET
                 INTERVAL, where the pitcher is still by construction, so
                 observed variation there is measurement error. This is the same
                 standard that retired the PitchCom cue.

Read-only over cached tracks. No video decode, no re-tracking.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os

import numpy as np
import pandas as pd

from preflight.primitives import PRIMITIVES, _col, _mid, pitch_primitives
from preflight.spot_diff import CUES
from preflight.window import actionable_window

MEASURED_JITTER = 0.10
LANDMARKS = (
    "nose", "lsho", "rsho", "lelb", "relb", "lwri", "rwri",
    "lpnk", "rpnk", "lidx", "ridx", "lhip", "rhip",
    "lkne", "rkne", "lank", "rank",
)

# Cues computed by run_poc.window_features off the legacy scalar tracks.
WINDOW_CUES = {
    "glove_vs_belt_mean": ("glove_vs_belt_y", "mean"),
    "glove_vs_belt_std": ("glove_vs_belt_y", "std"),
    "glove_flare_mean": ("glove_flare", "mean"),
    "glove_flare_std": ("glove_flare", "std"),
    "wrist_speed_mean": ("wrist_speed", "mean"),
    "wrist_speed_p90": ("wrist_speed", "p90"),
    "cheek_motion_mean": ("cheek_motion", "mean"),
    "cheek_motion_std": ("cheek_motion", "std"),
    "catcher_glove_x_mean": ("catcher_glove_x", "mean"),
    "catcher_glove_y_mean": ("catcher_glove_y", "mean"),
    "catcher_stance_mean": ("catcher_stance_width", "mean"),
    "catcher_hip_y_mean": ("catcher_hip_y", "mean"),
    "catcher_glove_speed_mean": ("catcher_glove_speed", "mean"),
    "catcher_glove_speed_p90": ("catcher_glove_speed", "p90"),
}


def _win_for_rich(df: pd.DataFrame):
    lw, lwy = _col(df, "lwri_x"), _col(df, "lwri_y")
    rw, rwy = _col(df, "rwri_x"), _col(df, "rwri_y")
    w = df.copy()
    w["glove_x"] = _mid(lw, rw)
    w["glove_y"] = _mid(lwy, rwy)
    w["wrist_dist"] = np.hypot(lw - rw, lwy - rwy)
    return actionable_window(w)


# --- (3) what fills the column when the measurement is missing ---------------

def coercion_audit(runs: list[str]) -> dict:
    """
    How often ``window_features`` would emit a fabricated 0.0.

    The final line of run_poc.window_features is

        return {k: (0.0 if np.isnan(v) else v) for k, v in out.items()}

    so any feature whose window contained no usable data is published as
    exactly 0.0 — which for glove_vs_belt_mean is the specific claim "the glove
    sat exactly at belt height", and for the catcher features is "the catcher
    was at the origin". This counts how many real pitches hit that path.
    """
    counts: dict[str, int] = {k: 0 for k in WINDOW_CUES}
    absent: dict[str, int] = {k: 0 for k in WINDOW_CUES}
    n = 0
    for run in runs:
        for tp in sorted(glob.glob(os.path.join(run, "tracks", "*_tracks.csv"))):
            try:
                df = pd.read_csv(tp)
            except Exception:
                continue
            win = actionable_window(df)
            if not win.valid:
                continue
            pre = df.iloc[win.start : win.end]
            if not len(pre):
                continue
            n += 1
            for cue, (col, how) in WINDOW_CUES.items():
                if col not in pre.columns:
                    # The `if col in pre` guard hands back 0.0 outright.
                    absent[cue] += 1
                    counts[cue] += 1
                    continue
                s = pd.to_numeric(pre[col], errors="coerce")
                if how == "mean":
                    v = s.mean()
                elif how == "std":
                    v = s.std(ddof=0)
                else:
                    v = s.quantile(0.9)
                if not np.isfinite(v):
                    counts[cue] += 1
    return {
        "n_pitches": n,
        "fabricated_zero": {
            k: {
                "n": counts[k],
                "share": round(counts[k] / n, 4) if n else None,
                "column_absent_n": absent[k],
            }
            for k in WINDOW_CUES
        },
    }


# --- (2) noise floor vs the cue's own visibility threshold -------------------

def primitive_noise(runs: list[str], limit: int = 400) -> dict:
    """Induced-noise reliability for every primitive, via landmark jitter."""
    rng = np.random.default_rng(23)
    base, pert = [], []
    for run in runs:
        for p in sorted(glob.glob(os.path.join(run, "lift_tracks", "*.csv")))[:limit]:
            try:
                df = pd.read_csv(p)
            except Exception:
                continue
            r0 = pitch_primitives(df, "b")
            if r0 is None:
                continue
            t = float(r0["torso_scale"])
            nz = df.copy()
            for lm in LANDMARKS:
                for ax in ("x", "y"):
                    c = f"{lm}_{ax}"
                    if c in nz.columns:
                        nz[c] = pd.to_numeric(nz[c], errors="coerce") + rng.normal(
                            0, MEASURED_JITTER * t, len(nz)
                        )
            r1 = pitch_primitives(nz, "p")
            if r1 is None:
                continue
            base.append(r0)
            pert.append(r1)
    if not base:
        return {}
    b, q = pd.DataFrame(base), pd.DataFrame(pert)
    out = {}
    for c in PRIMITIVES:
        if c not in b.columns:
            continue
        d = (b[c] - q[c]).dropna()
        between = float(b[c].std())
        induced = float(d.std() / np.sqrt(2)) if len(d) > 2 else float("nan")
        out[c] = {
            "schema": "primitives",
            "n": int(len(d)),
            "coverage": round(float(b[c].notna().mean()), 4),
            "between_sd": round(between, 4),
            "induced_noise": round(induced, 4) if np.isfinite(induced) else None,
            "signal_sd": round(math.sqrt(max(0.0, between**2 - induced**2)), 4)
            if np.isfinite(induced)
            else None,
        }
    return out


def window_noise(runs: list[str]) -> dict:
    """
    Set-interval noise for the legacy window cues.

    The set is located by the shared window module as a sustained quiet run, so
    within it the pitcher is still and the observed spread of a scalar is that
    scalar's measurement error. Between-pitch spread is taken over the whole
    window, which is how the cue is actually computed.
    """
    per_cue: dict[str, list[float]] = {k: [] for k in WINDOW_CUES}
    noise: dict[str, list[float]] = {k: [] for k in WINDOW_CUES}
    for run in runs:
        for tp in sorted(glob.glob(os.path.join(run, "tracks", "*_tracks.csv"))):
            try:
                df = pd.read_csv(tp)
            except Exception:
                continue
            win = actionable_window(df)
            if not win.valid or win.set_frame is None:
                continue
            pre = df.iloc[win.start : win.end]
            lo = int(win.set_frame)
            hi = min(lo + 15, int(win.lift_frame) if win.lift_frame else lo + 15)
            if hi - lo < 8 or not len(pre):
                continue
            quiet = df.iloc[lo:hi]
            for cue, (col, how) in WINDOW_CUES.items():
                if col not in df.columns:
                    continue
                s = pd.to_numeric(pre[col], errors="coerce")
                qs = pd.to_numeric(quiet[col], errors="coerce")
                if how == "mean":
                    v = s.mean()
                elif how == "std":
                    v = s.std(ddof=0)
                else:
                    v = s.quantile(0.9)
                if np.isfinite(v):
                    per_cue[cue].append(float(v))
                # Noise: how much the same statistic wobbles over the still set.
                if qs.notna().sum() >= 6:
                    if how == "std":
                        # For a spread statistic the noise floor IS the quiet
                        # spread: it is what the cue reports on a still pitcher.
                        nv = qs.std(ddof=0)
                    elif how == "p90":
                        nv = qs.quantile(0.9) - qs.median()
                    else:
                        # Standard error of the quiet mean, scaled to the
                        # window length the cue is actually averaged over.
                        nv = qs.std(ddof=0) / math.sqrt(max(1, len(s.dropna())))
                    if np.isfinite(nv):
                        noise[cue].append(float(abs(nv)))
    out = {}
    for cue in WINDOW_CUES:
        vals = np.array(per_cue[cue], dtype=float)
        nz = np.array(noise[cue], dtype=float)
        if vals.size < 3 or nz.size < 3:
            out[cue] = {"schema": "window", "n": int(vals.size), "note": "insufficient data"}
            continue
        between = float(np.nanstd(vals))
        induced = float(np.nanmedian(nz))
        out[cue] = {
            "schema": "window",
            "n": int(vals.size),
            "between_sd": round(between, 5),
            "induced_noise": round(induced, 5),
            "signal_sd": round(math.sqrt(max(0.0, between**2 - induced**2)), 5),
        }
    return out


def verdict_table(noise: dict) -> list[dict]:
    """
    Join measured noise to each cue's declared visibility threshold.

    The disqualifying comparison is induced noise against ``visible_delta``: if
    the tracker's own error exceeds the smallest change a human could see, the
    cue cannot resolve its own subject.
    """
    rows = []
    for cue, c in CUES.items():
        m = noise.get(cue, {})
        ind = m.get("induced_noise")
        vd = c.visible_delta
        if ind is None or vd is None:
            ratio = None
        else:
            ratio = round(ind / vd, 2) if vd else None
        rows.append(
            {
                "cue": cue,
                "label": c.label,
                "unit": c.unit,
                "visible_delta": vd,
                "schema": m.get("schema"),
                "n": m.get("n"),
                "coverage": m.get("coverage"),
                "between_sd": m.get("between_sd"),
                "induced_noise": ind,
                "signal_sd": m.get("signal_sd"),
                "noise_over_visible_delta": ratio,
                "disqualified_by_noise": bool(ratio is not None and ratio > 1.0),
                "no_visibility_threshold": vd is None,
            }
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rich-run", nargs="+", default=["../runs/drew_thorpe_rich_poc"])
    ap.add_argument("--window-run", nargs="+", default=["../runs/drew_thorpe_poc"])
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    noise = {}
    noise.update(primitive_noise(args.rich_run))
    noise.update(window_noise(args.window_run))
    report = {
        "coercion_audit": coercion_audit(args.window_run),
        "cue_verdicts": verdict_table(noise),
        "primitives_not_in_CUES": [
            k for k in PRIMITIVES if k not in CUES and k in noise
        ],
        "noise": noise,
    }
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)


if __name__ == "__main__":
    main()
