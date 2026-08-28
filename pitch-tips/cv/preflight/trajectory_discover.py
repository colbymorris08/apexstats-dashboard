"""
Discovery over the trajectory features, and over pitch-to-pitch CONSISTENCY.

Two hypotheses are tested here, both untested before, each as its own
pre-registered family with its own false-discovery control.

Family A — does the MOVEMENT differ?
    Mean contrasts on the ten trajectory features, run through exactly the same
    machinery the point cues face: delivery-type stratification, disjoint
    game-level holdout, practical-visibility floor, standardized effect floor,
    direction-flip rejection, BH-FDR at q=0.10. Nothing is re-implemented, so
    nothing can be accidentally loosened; ``spot_diff.analyse`` is called with a
    different cue table.

Family B — does the CONSISTENCY differ?
    The user's "variance" half, and a genuinely different statistic. A pitcher
    may be perfectly repeatable on one pitch and variable on another while the
    means match exactly, and no mean contrast can see that.

    Method, fixed before any result was read:
      1. For each cue, stratum, pitch type and GAME, take the median of that cue
         over those pitches.
      2. Replace each pitch's value with its absolute deviation from that
         within-game, within-type median. Doing it within game matters: a
         pitcher who sits slightly differently from one park to the next would
         otherwise read as inconsistent, when what varies is the venue.
      3. Compare those absolute deviations between the two pitch types. This is
         the Brown-Forsythe form of a spread test, chosen because it uses medians
         and so is not driven by a single outlier pitch.
      4. Everything downstream is unchanged: same holdout, same stratification,
         same FDR, same effect floor.

    A survivor here would read as "he is more consistent with his glove on the
    slider than on the curveball", which is a scouting statement in its own right.

Anything surviving either family then faces two further checks that no earlier
survivor in this project has passed: a convergence check, because the Kelly
artifact was exposed by an effect that wandered and decayed as games were added
where a real cue tightens, and the precision/fire evaluation at the 0.75 floor.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from preflight import snapshot, spot_diff
from preflight.spot_diff import Cue, hedges_g
from preflight.trajectory import TRAJECTORY_FEATURES

# Visibility thresholds follow the existing convention rather than being invented
# per feature. Durations and counts get a floor in their own unit; correlations
# reuse the 0.25 already carried by drift_lift_sync; dimensionless ratios and
# speeds get None, which the Cue contract defines as "no fixed real-world size,
# so practical significance is carried entirely by the standardized effect floor".
# Three frames is 0.1 s at 30 fps, about the limit of a perceptible tempo change.
TRAJECTORY_CUES: dict[str, Cue] = {
    "set_to_lift_frames": Cue(
        "tempo from set to peak leg lift", "frames", 3.0, 0.90,
        "takes longer to get to the top of his kick",
        "gets to the top of his kick quicker"),
    "knee_rise_duration_frac": Cue(
        "how abruptly the leg comes up", "fraction of the set-to-lift interval", None, 0.75,
        "raises the leg more gradually", "snaps the leg up more abruptly"),
    "hold_at_top_frac": Cue(
        "time spent held at the top of the kick", "fraction of the interval", None, 0.80,
        "hangs at the top of his kick longer", "comes straight off the top of his kick"),
    "glove_speed_mean": Cue(
        "average glove speed into the lift", "torso lengths per frame", None, 0.80,
        "moves the glove faster into the lift", "moves the glove more slowly into the lift"),
    "glove_speed_cv": Cue(
        "how evenly the glove moves", "ratio", None, 0.65,
        "moves the glove in stops and starts", "moves the glove at an even pace"),
    "glove_peak_speed_timing": Cue(
        "when the glove moves fastest", "fraction of the interval", None, 0.70,
        "moves the glove fastest late, near the lift",
        "moves the glove fastest early, off the set"),
    "glove_tortuosity": Cue(
        "how directly the glove travels", "ratio", None, 0.70,
        "wanders the glove on the way up", "takes the glove straight up"),
    "glove_vertical_reversals": Cue(
        "up-and-down changes of glove direction", "reversals per 10 frames", 1.0, 0.70,
        "rocks the glove up and down", "settles the glove in one move"),
    "glove_knee_lag_frames": Cue(
        "glove timing against the leg kick", "frames", 3.0, 0.60,
        "starts the glove later than the leg", "starts the glove before the leg"),
    "hip_glove_x_coupling": Cue(
        "glove travelling with the body or apart from it", "correlation", 0.25, 0.60,
        "carries the glove with his body", "moves the glove independently of his body"),
}


def load_trajectory(run_dir: Path) -> pd.DataFrame:
    """Join the feature table to the trajectory table on play_id.

    Carries the same overlap guard ``load_pitcher`` carries, for the same reason:
    a key mismatch under an outer merge does not raise, it produces two disjoint
    halves and a run that reports every cue as available while every contrast
    finds an empty group.
    """
    feats = pd.read_csv(run_dir / "features.csv", dtype={"play_id": str})
    traj = pd.read_csv(run_dir / "trajectory.csv", dtype={"play_id": str})
    traj = traj.drop(columns=[c for c in ("pitch_type", "delivery") if c in traj.columns])
    overlap = len(set(feats["play_id"]) & set(traj["play_id"]))
    if overlap < 0.5 * min(len(feats), len(traj)):
        raise SystemExit(
            f"{run_dir.name}: features.csv and trajectory.csv share only {overlap} "
            f"play_ids ({len(feats)} / {len(traj)}). Rebuild trajectory.csv rather "
            "than running discovery on a half-empty frame."
        )
    return feats.merge(traj, on="play_id", how="outer", suffixes=("", "_dup"))


def to_dispersion(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Replace each cue value with its absolute deviation from the within-game,
    within-pitch-type median, so a spread contrast becomes a mean contrast.

    Within game rather than overall: a pitcher who sets slightly differently from
    one park to another would otherwise register as inconsistent when what
    actually varies is the venue.
    """
    d = df.copy()
    key = ["game_pk", "pitch_type"]
    if "delivery_type" in d.columns:
        key.append("delivery_type")
    for c in cols:
        if c not in d.columns:
            continue
        med = d.groupby(key, dropna=False)[c].transform("median")
        d[c] = (d[c] - med).abs()
    return d


def cue_column(diff: dict) -> str | None:
    """Map a reported difference back to its dataframe column.

    ``spot_diff`` reports the human-readable cue label, not the column name, so a
    survivor has to be resolved back through the cue table before it can be
    re-measured for the convergence check.
    """
    val = diff.get("cue")
    if val in TRAJECTORY_CUES:
        return val
    for key, cue in TRAJECTORY_CUES.items():
        if cue.label == val:
            return key
    return None


def parse_contrast(diff: dict) -> tuple[str, str]:
    """Pull the two sides out of a difference's contrast string.

    ``spot_diff`` records the contrast as text such as "CU vs SL" or
    "CH vs the rest"; the "rest" form is the sentinel ``_groups`` understands.
    """
    for key in ("type_a", "type_b"):
        if key in diff:
            return diff["type_a"], diff["type_b"]
    txt = str(diff.get("contrast", ""))
    left, _, right = txt.partition(" vs ")
    right = right.strip()
    return left.strip(), ("REST" if "rest" in right.lower() else right)


def permute_labels(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Shuffle pitch-type labels within each game.

    This is the null the sign-hold rate has to be judged against, and getting it
    wrong is what made the consistency family briefly look real.

    Shuffling within game preserves the number of pitches of each type in each
    game exactly, while destroying every association between pitch type and
    anything measured. So any structure that survives it is a property of the
    estimator and the pitch mix rather than a tip.

    That matters most for the dispersion family. An absolute deviation is taken
    from a median estimated on the same small group, and a group of five pitches
    has systematically smaller deviations from its own median than a group of
    forty. The pitch mix is similar from game to game, so that bias points the
    same way in the discovery and holdout halves — which produces a high
    sign-hold rate with no signal underneath it. Measured: the real data held
    sign on 72% of checks, and shuffled labels held it on 48-81%.

    It also shows the sign-hold rate is not a binomial with independent trials.
    The same pitches enter many cue-by-contrast tests, so the statistic is far
    more dispersed than a coin-flip null implies, and a p-value computed against
    0.5 overstates its own precision. Comparing to this null instead is the fix.
    """
    d = df.copy()
    d["pitch_type"] = d.groupby("game_pk", dropna=False)["pitch_type"].transform(
        lambda s: rng.permutation(s.values)
    )
    return d


def convergence(df: pd.DataFrame, cue: str, a: str, b: str, stratum: str) -> list[tuple]:
    """Effect size as games accumulate.

    A real cue tightens as n grows. The Kelly artifact peaked near game 18 and
    decayed to a third of its apparent size by game 25, which is what a
    subsample looks like when it is mistaken for a signal.
    """
    col = "delivery_type" if "delivery_type" in df.columns else "delivery"
    sub = df[df[col] == stratum]
    games = sorted(sub["game_pk"].dropna().unique())
    out = []
    for k in range(2, len(games) + 1):
        s = sub[sub["game_pk"].isin(games[:k])]
        x = pd.to_numeric(s[s.pitch_type == a][cue], errors="coerce").dropna()
        other = s[s.pitch_type != a] if b == "REST" else s[s.pitch_type == b]
        y = pd.to_numeric(other[cue], errors="coerce").dropna()
        if len(x) >= 8 and len(y) >= 8:
            out.append((k, len(x), len(y), hedges_g(x.values, y.values)))
    return out


def run_family(df: pd.DataFrame, name: str, label: str) -> dict[str, Any]:
    """Run spot_diff.analyse with the trajectory cue table swapped in."""
    original = spot_diff.CUES
    try:
        spot_diff.CUES = TRAJECTORY_CUES
        res = spot_diff.analyse(df, f"{name} [{label}]")
    finally:
        spot_diff.CUES = original
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, nargs="+")
    ap.add_argument("--out", default="")
    ap.add_argument("--allow-unready", action="store_true")
    ap.add_argument(
        "--skip-unready",
        action="store_true",
        help="in a sweep, report and skip arms still being tracked rather than "
        "aborting the whole run",
    )
    args = ap.parse_args()

    all_res, skipped = [], []
    for d in args.run_dir:
        run = Path(d)
        try:
            snapshot.assert_quiescent(run, allow_unready=args.allow_unready)
        except SystemExit as e:
            if not args.skip_unready:
                raise
            skipped.append(run.name)
            print(f"\n=== {run.name}: SKIPPED — {e}", flush=True)
            continue
        name = run.name.replace("_poc", "").replace("_", " ").title()
        df = load_trajectory(run)

        for label in ("movement", "consistency"):
            frame = df if label == "movement" else to_dispersion(df, TRAJECTORY_FEATURES)
            res = run_family(frame, name, label)
            res["family"] = label
            res["sample"] = snapshot.fingerprint(run, "features.csv", frame)
            all_res.append(res)
            print(spot_diff.report_text(res), flush=True)

            for diff in res.get("differences", []):
                ta, tb = parse_contrast(diff)
                col = cue_column(diff)
                if col is None:
                    print(f"    convergence unavailable: cannot resolve {diff['cue']!r}")
                    continue
                cur = convergence(frame, col, ta, tb, diff["delivery"])
                print(f"    convergence for {col} {ta} vs {tb} [{diff['delivery']}]:")
                for k, na, nb, g in cur:
                    print(f"       {k:2d} games  n=({na:3d},{nb:3d})  g={g:+.3f}")
                diff["convergence"] = cur
                diff["cue_column"] = col

    tot = sum(r["comparisons"] for r in all_res)
    surv = sum(r.get("n_surviving", 0) for r in all_res)
    n_arms = len(args.run_dir) - len(skipped)
    print(f"\nTOTAL: {tot} comparisons across {n_arms} arms x 2 families "
          f"-> {surv} surviving, FDR controlled at q={spot_diff.FDR_Q} within each family.")
    if skipped:
        print(f"skipped as still being tracked: {skipped}")
    if args.out:
        Path(args.out).write_text(json.dumps(
            {"arms": all_res, "total_comparisons": tot, "total_surviving": surv}, indent=2))


if __name__ == "__main__":
    main()
