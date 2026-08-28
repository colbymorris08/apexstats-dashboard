"""
Delivery detection: windup versus the set, built from pose evidence and calibrated
per pitcher against base state.

Why this module exists
----------------------
The project ran for its whole life on ``delivery_type``, which was described as a
delivery label read off the pose track. It is not one. ``window._find_set_before``
returns None when it cannot find a sustained quiet run before hand break — because
the segment is too short, has no finite speed values, or is simply noisy — and
``actionable_window`` calls that case "windup". It never tests what the pitcher
actually did.

The proof is that its rate is invariant to base state, which is impossible for a
real delivery label:

    Kelly  0.200 windup with the bases empty | 0.202 with a runner on second
    Webb   0.222                             | 0.249

No pitcher uses a full windup a fifth of the time with a runner on second. So
``delivery_type`` is a **set-detection failure flag running at about 20%**, and
every "windup stratum" result in this project was computed on the pitches where
set detection failed.

The trap that produced it
-------------------------
A real windup also contains a still point: the pitcher stands motionless on the
rubber before he starts. So "no still point" does not mean windup, and "still
point" does not mean set. Stillness cannot separate the two, which is exactly why
the old detector failed. The separating evidence has to be the *motion between the
still point and the leg lift*.

Design: base state as prior, pose as evidence, calibrated per arm
----------------------------------------------------------------
Base state is a strong prior — with a runner on, a pitcher is essentially always in
the set, because a windup surrenders the running game. But it is not sufficient on
its own, because a growing number of arms work exclusively from the set regardless
of base state. Woo measures ~88% "stretch" with the bases empty and ~88% with a
runner on second; a pure base-state rule would label most of his pitches windup and
every stretch-versus-windup comparison on him would silently be stretch versus
stretch.

So, per arm:

1. Compute pose features over the pre-lift segment that describe *how the motion
   started* rather than whether it paused.
2. Test whether those features differ between bases-empty and runners-on pitches.
   Under the prior, runners-on is the set. If a pitcher uses both deliveries, his
   bases-empty motion must look different. If it does not, he throws one delivery
   from both base states and his windup stratum is **absent**, not empty.
3. Only for arms that pass that test is a per-pitch delivery label assigned.

This turns the user's prior into something checked rather than asserted, and the
reference is the pitcher's own bases-empty film.

Validation, and its honest limit
--------------------------------
I could not hand-label clips from video, so the labelling accuracy reported here is
**not** against human ground truth. Stated plainly so no future reader repeats the
mistake this module exists to correct.

What is available is a **one-sided external check** grounded in the rules of the
game rather than in our own pose data: with a runner on first or second, a windup
is essentially never used. So a correct detector must label those pitches "set"
almost always, and its windup rate there is a directly measurable false-positive
rate. That check can only falsify, never confirm — it cannot detect a detector that
calls everything "set" — so it is reported alongside the calibration test, which is
what carries the positive evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from preflight.primitives import _col, _mid
from preflight.trajectory import _smooth
from preflight.trajectory import play_id_of, resolve_track_dir  # noqa: F401
from preflight.window import actionable_window

# Pose features describing how the motion STARTS, which is what separates a windup
# from the set. Stillness does not, since both contain a still point.
DELIVERY_FEATURES = {
    "back_step_travel": "how far the feet travel backward/laterally before the leg "
                        "lift — the rocker step that opens a windup",
    "ankle_span_change": "change in stance width from motion onset to lift; a "
                         "windup's step back widens it, the set does not",
    "hip_lateral_travel": "sideways hip travel before lift — the rock and turn of a "
                          "windup versus a set that goes straight up",
    "hip_vertical_travel": "vertical hip travel before lift; a windup rocks the "
                           "body, the set stays level",
    "onset_to_lift_frames": "frames from first motion to peak leg lift — a windup "
                            "is a longer motion",
    "hands_start_height": "glove height relative to the belt at motion onset; a "
                          "windup often starts the hands low and raises them",
    "hands_rise": "how far the hands travel upward before lift, the pump of a windup",
    "shoulder_turn": "shoulder-line rotation before lift — a windup turns the torso "
                     "away, the set is already closed",
}

# Base states where a windup is effectively impossible. Used for the one-sided
# external check and to define the "set" reference group for calibration.
RUNNER_COLS = ("on_1b", "on_2b", "on_3b")

# A pitcher counts as using both deliveries only if his bases-empty motion differs
# from his runners-on motion. Conventional alpha, applied to the combined test.
CALIBRATION_ALPHA = 0.05
# Minimum pitches per side before the calibration question can be asked at all.
MIN_PER_SIDE = 20


def _torso(df: pd.DataFrame) -> float:
    sho_y = _mid(_col(df, "lsho_y"), _col(df, "rsho_y"))
    hip_y = _mid(_col(df, "lhip_y"), _col(df, "rhip_y"))
    t = np.nanmedian(np.abs(hip_y - sho_y))
    return float(t) if np.isfinite(t) and t > 1e-6 else float("nan")


def pitch_delivery_pose(df: pd.DataFrame, play_id: str) -> dict[str, Any] | None:
    """Pose evidence for one pitch over the segment before peak leg lift.

    Returns None rather than guessing when the window is unusable or the legs are
    not visible: the feet are the primary evidence for a rocker step, and a
    detector that falls back to torso-only evidence when the legs drop out would
    be least reliable exactly where it matters.
    """
    lwri_x, lwri_y = _col(df, "lwri_x"), _col(df, "lwri_y")
    rwri_x, rwri_y = _col(df, "rwri_x"), _col(df, "rwri_y")
    glove_x, glove_y = _mid(lwri_x, rwri_x), _mid(lwri_y, rwri_y)

    wdf = df.copy()
    wdf["glove_x"], wdf["glove_y"] = glove_x, glove_y
    wdf["wrist_dist"] = np.hypot(lwri_x - rwri_x, lwri_y - rwri_y)
    win = actionable_window(wdf)
    if not win.valid or win.lift_frame is None:
        return None

    torso = _torso(df)
    if not np.isfinite(torso):
        return None

    start = int(win.start)
    lift = int(win.lift_frame)
    if lift - start < 4:
        return None
    sl = slice(start, lift + 1)

    lank_x, lank_y = _smooth(_col(df, "lank_x")), _smooth(_col(df, "lank_y"))
    rank_x, rank_y = _smooth(_col(df, "rank_x")), _smooth(_col(df, "rank_y"))
    lhip_x, lhip_y = _smooth(_col(df, "lhip_x")), _smooth(_col(df, "lhip_y"))
    rhip_x, rhip_y = _smooth(_col(df, "rhip_x")), _smooth(_col(df, "rhip_y"))
    lsho_x, rsho_x = _smooth(_col(df, "lsho_x")), _smooth(_col(df, "rsho_x"))
    lsho_y, rsho_y = _smooth(_col(df, "lsho_y")), _smooth(_col(df, "rsho_y"))
    belt_y = _mid(lhip_y, rhip_y)
    gy = _smooth(glove_y)

    lv = np.nanmean(_col(df, "lank_v")[sl])
    rv = np.nanmean(_col(df, "rank_v")[sl])
    if not (np.isfinite(lv) and np.isfinite(rv) and min(lv, rv) >= 0.30):
        return None  # feet not reliably visible: the rocker-step evidence is absent

    def seg(a):
        v = a[sl]
        return v[np.isfinite(v)]

    out: dict[str, Any] = {"play_id": play_id}

    # Feet: the free foot's travel away from its start is the rocker step.
    trav = []
    for ax, ay in ((lank_x, lank_y), (rank_x, rank_y)):
        x, y = seg(ax), seg(ay)
        if len(x) < 4 or len(y) < 4:
            return None
        trav.append(float(np.nanmax(np.hypot(x - x[0], y - y[0]))) / torso)
    out["back_step_travel"] = max(trav)

    span = np.abs(lank_x - rank_x)[sl]
    span = span[np.isfinite(span)]
    out["ankle_span_change"] = (float(span.max() - span[0]) / torso) if len(span) >= 4 else np.nan

    hx, hy = seg(_mid(lhip_x, rhip_x)), seg(_mid(lhip_y, rhip_y))
    out["hip_lateral_travel"] = float(np.nanmax(np.abs(hx - hx[0]))) / torso if len(hx) >= 4 else np.nan
    out["hip_vertical_travel"] = float(np.nanmax(np.abs(hy - hy[0]))) / torso if len(hy) >= 4 else np.nan

    out["onset_to_lift_frames"] = float(lift - start)

    gb = (gy - belt_y)[sl]
    gb = gb[np.isfinite(gb)]
    if len(gb) >= 4:
        # Image y grows downward, so negate to make "above the belt" positive.
        out["hands_start_height"] = float(-gb[0]) / torso
        out["hands_rise"] = float(np.nanmax(-gb) - (-gb[0])) / torso
    else:
        out["hands_start_height"] = out["hands_rise"] = np.nan

    sw = (np.abs(lsho_x - rsho_x))[sl]
    sw = sw[np.isfinite(sw)]
    out["shoulder_turn"] = float(sw.max() - sw.min()) / torso if len(sw) >= 4 else np.nan

    # Recorded for diagnostics ONLY, never for stratification. This window is
    # rebuilt here from wrist midpoints, so it is not the window the published
    # features were computed under and it disagrees with the authoritative flag on
    # a meaningful fraction of pitches (Webb: 44 of 91). The authoritative
    # window-geometry flag is ``delivery_type`` in features.csv, which is exactly
    # "did production set detection succeed". Stratify on that.
    out["window_geometry_rederived"] = ("set_anchored" if win.set_frame is not None
                                        else "fixed_lookback")
    return out


def build_run(run_dir: Path) -> Path:
    """Pose delivery evidence for every track in a run."""
    _, tracks = resolve_track_dir(run_dir)
    rows, skipped = [], 0
    for tp in tracks:
        try:
            df = pd.read_csv(tp)
        except Exception:
            skipped += 1
            continue
        rec = pitch_delivery_pose(df, play_id_of(tp))
        if rec is None:
            skipped += 1
            continue
        rows.append(rec)
    out = run_dir / "delivery_pose.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"{run_dir.name}: {len(tracks)} tracks -> {len(rows)} usable "
          f"({skipped} unusable)")
    return out


def runners_on(df: pd.DataFrame) -> pd.Series:
    cols = [c for c in RUNNER_COLS if c in df.columns]
    if not cols:
        raise ValueError("no base-state columns available")
    return df[cols].fillna(False).astype(bool).any(axis=1)


def calibrate(df: pd.DataFrame) -> dict[str, Any]:
    """Does this arm's motion actually differ between bases-empty and runners-on?

    Under the base-state prior, runners-on is the set. If the pitcher also uses a
    windup, his bases-empty pitches must look mechanically different. If they do
    not, he throws one delivery from both base states.

    Reported per feature and combined. The combined test is the minimum p-value
    with a Bonferroni correction across the features: conservative on purpose,
    because the expensive error here is deciding an arm uses both deliveries when
    he does not — that would manufacture a windup stratum out of noise, which is
    the failure this module exists to fix.
    """
    on = runners_on(df)
    empty, set_pos = df[~on], df[on]
    out: dict[str, Any] = {
        "n_bases_empty": int(len(empty)),
        "n_runners_on": int(len(set_pos)),
        "features": {},
    }
    if min(len(empty), len(set_pos)) < MIN_PER_SIDE:
        out.update({"testable": False, "verdict": "undetermined",
                    "why": f"needs {MIN_PER_SIDE} pitches per side"})
        return out

    ps = []
    for f in DELIVERY_FEATURES:
        a = pd.to_numeric(empty.get(f), errors="coerce").dropna()
        b = pd.to_numeric(set_pos.get(f), errors="coerce").dropna()
        if min(len(a), len(b)) < MIN_PER_SIDE:
            continue
        p = float(stats.ttest_ind(a, b, equal_var=False).pvalue)
        sd = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
        d = float((a.mean() - b.mean()) / sd) if sd > 1e-12 else 0.0
        out["features"][f] = {"p": p, "cohens_d": round(d, 3),
                              "mean_bases_empty": round(float(a.mean()), 4),
                              "mean_runners_on": round(float(b.mean()), 4)}
        ps.append(p)

    if not ps:
        out.update({"testable": False, "verdict": "undetermined",
                    "why": "no feature had enough coverage on both sides"})
        return out

    p_comb = float(min(1.0, min(ps) * len(ps)))
    out.update({
        "testable": True,
        "p_combined": p_comb,
        "n_features_tested": len(ps),
        "verdict": "uses_both" if p_comb < CALIBRATION_ALPHA else "single_delivery",
    })
    out["why"] = (
        "bases-empty motion differs from runners-on motion, so this arm uses both"
        if out["verdict"] == "uses_both" else
        "bases-empty motion is indistinguishable from runners-on motion, so this "
        "arm throws one delivery regardless of base state; its windup stratum is "
        "ABSENT, not empty"
    )
    return out


def external_check(df: pd.DataFrame, label_col: str) -> dict[str, Any]:
    """One-sided check against the rules of the game, not against our own data.

    With a runner on first or second a windup is effectively never used, so a
    correct label must almost never say "windup" there. This can falsify a
    detector but cannot confirm one — a detector that labels everything "set"
    passes it perfectly — so it is reported next to the calibration test rather
    than instead of it.
    """
    cols = [c for c in ("on_1b", "on_2b") if c in df.columns]
    if not cols or label_col not in df.columns:
        return {"testable": False}
    holding = df[cols].fillna(False).astype(bool).any(axis=1)
    sub = df[holding]
    if len(sub) == 0:
        return {"testable": False}
    fp = float((sub[label_col].astype(str) == "windup").mean())
    return {
        "testable": True,
        "n_pitches_with_runner_on_1b_or_2b": int(len(sub)),
        "windup_rate_where_windup_is_impossible": round(fp, 4),
        "interpretation": ("this is a false-positive rate; it should be near zero "
                           "and can only falsify, never confirm"),
    }


def label(df: pd.DataFrame, cal: dict[str, Any]) -> pd.Series:
    """Per-pitch delivery label, or "unknown" when it cannot be determined.

    Only assigned for arms the calibration says use both deliveries. For a
    single-delivery arm every pitch is "set" — labelling some of them windup would
    reintroduce exactly the phantom stratum this module exists to remove.
    """
    # "stretch" rather than "set" so the label is interchangeable with the stratum
    # names the rest of the pipeline already recognises; a name outside
    # spot_diff.KNOWN_DELIVERIES is silently dropped from every contrast.
    if cal.get("verdict") == "uses_both":
        return pd.Series(np.where(runners_on(df), "stretch", "windup"),
                         index=df.index, name="delivery_actual")
    if cal.get("verdict") == "single_delivery":
        return pd.Series("stretch", index=df.index, name="delivery_actual")
    return pd.Series("unknown", index=df.index, name="delivery_actual")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, nargs="+")
    ap.add_argument("--build", action="store_true",
                    help="extract pose evidence from tracks first (slow)")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    from preflight.spot_diff import load_pitcher

    results = []
    for d in args.run_dir:
        run = Path(d)
        if args.build or not (run / "delivery_pose.csv").exists():
            try:
                build_run(run)
            except Exception as e:
                print(f"  {run.name}: build failed: {e}")
                continue
        try:
            pose = pd.read_csv(run / "delivery_pose.csv")
            feat = load_pitcher(run)
        except Exception as e:
            print(f"  {run.name}: load failed: {e}")
            continue
        if "play_id" not in feat.columns or pose.empty:
            print(f"  {run.name}: cannot join pose evidence")
            continue
        m = feat.merge(pose, on="play_id", how="inner", suffixes=("", "_pose"))
        cal = calibrate(m)
        m["delivery_actual"] = label(m, cal)
        results.append({"arm": run.name, "n_joined": int(len(m)),
                        "calibration": cal,
                        "external_check_old_label": external_check(m, "delivery_type"),
                        "external_check_new_label": external_check(m, "delivery_actual"),
                        "label_counts": m["delivery_actual"].value_counts().to_dict(),
                        "window_geometry_authoritative": (
                            m["delivery_type"].value_counts().to_dict()
                            if "delivery_type" in m.columns else {})})
        m[["play_id", "delivery_actual", "window_geometry_rederived"]].to_csv(
            run / "delivery_label.csv", index=False)

    print("\n" + "=" * 104)
    print("DELIVERY CALIBRATION — does this arm's motion differ by base state?")
    print("=" * 104)
    hdr = (f"{'Arm':22s} {'N':>5s} {'empty':>6s} {'onbase':>6s} {'p_comb':>9s} "
           f"{'verdict':16s} {'old FP':>7s} {'new FP':>7s}")
    print(hdr); print("-" * len(hdr))
    def fp(x):
        k = "windup_rate_where_windup_is_impossible"
        return f"{x[k]:.3f}" if x.get("testable") else "-"

    for r in results:
        c = r["calibration"]
        pc = c.get("p_combined")
        print(f"{r['arm'][:22]:22s} {r['n_joined']:5d} {c['n_bases_empty']:6d} "
              f"{c['n_runners_on']:6d} {('-' if pc is None else f'{pc:.2e}'):>9s} "
              f"{c['verdict']:16s} {fp(r['external_check_old_label']):>7s} "
              f"{fp(r['external_check_new_label']):>7s}")

    both = [r for r in results if r["calibration"].get("verdict") == "uses_both"]
    single = [r for r in results if r["calibration"].get("verdict") == "single_delivery"]
    und = [r for r in results if r["calibration"].get("verdict") == "undetermined"]
    print(f"\nuses both deliveries: {len(both)} | single-delivery: {len(single)} | "
          f"undetermined: {len(und)}")
    for r in single:
        print(f"  SINGLE-DELIVERY {r['arm']}: every prior 'windup stratum' result on "
              f"this arm measured the pitches where set detection failed")

    print("\nVALIDATION LIMITS — read before trusting either column above")
    print("  1. No clip was hand-labelled from video, so NO accuracy against human")
    print("     ground truth is reported. This detector is not validated in that sense.")
    print("  2. 'new FP' is 0.000 BY CONSTRUCTION and is NOT evidence. The new label is")
    print("     a function of base state, so checking it against base state is circular.")
    print("     It is printed only to show the old label's rate is not similarly forced.")
    print("  3. 'old FP' IS meaningful: delivery_type is independent of base state, so")
    print("     its 8-17% windup rate where a windup is impossible is a real error rate.")
    print("  4. The positive evidence is the calibration test alone: whether pose differs")
    print("     between bases-empty and runners-on. That is what distinguishes an arm")
    print("     using both deliveries from a single-delivery arm.")

    if args.out:
        Path(args.out).write_text(json.dumps(results, indent=2, default=str))
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
