"""
The decisive test on a candidate cue: does it survive changing deliveries?

Why this is the test that matters
--------------------------------
A cue that describes how a pitcher grips and presents the ball should read the
same way whether he is in the stretch or the windup. His hand is doing the same
thing; only his legs differ. So a real tip should keep its DIRECTION across the
two deliveries, and an artefact of one delivery's tracking geometry has no reason
to.

This is not a hypothetical failure mode. On Logan Webb, measured earlier,
``glove_off_body_at_set`` on CH vs SI came out at +0.563 in the stretch and
-0.539 in the windup — the same magnitude, the opposite sign — and across 74
cue x contrast combinations testable in both strata only 35% agreed on sign,
below the 50% a coin flip would give.

The test is deliberately hostile to the candidate, because the candidate is the
only lead the project has and that is exactly the circumstance in which a
favourable read is least trustworthy. Two properties keep it honest:

  * the windup measurement is completely independent of the stretch one — no
    pitch appears in both strata, so nothing is being re-tested on its own data;
  * the direction is PRE-SPECIFIED from the stretch result, so the windup gets a
    directional prediction to confirm or refute rather than a free choice of
    sign after the fact.

A per-game breakdown is printed as well, because a stratum-level mean can be
carried by one outing while a tip has to be something a scout would see every
time.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from preflight.spot_diff import (
    MIN_PER_GROUP,
    _groups,
    hedges_g,
    load_pitcher,
    split_by_game,
)

# The four differences that survived holdout + BH-FDR in Kelly's stretch, with
# the sign the stretch result predicts for the windup.
SURVIVORS = [
    ("glove_flare_at_lift", "CU", "SL", +1),
    ("glove_flare_at_lift", "CH", "CU", -1),
    ("glove_off_body_at_lift", "CU", "SL", +1),
    ("glove_flare_at_lift", "FF", "SL", +1),
]


def contrast(df: pd.DataFrame, cue: str, a: str, b: str) -> dict | None:
    """Effect for one cue x contrast on a whole stratum, plus per-game detail."""
    if cue not in df.columns:
        return None
    ga, gb = _groups(df, cue, a, b)
    if min(len(ga), len(gb)) < MIN_PER_GROUP:
        return {"too_few": (len(ga), len(gb))}
    g = hedges_g(ga, gb)
    p = float(stats.ttest_ind(ga, gb, equal_var=False).pvalue)
    per_game = []
    if "game_pk" in df.columns:
        sub = df[df["pitch_type"].isin([a, b])][["game_pk", "pitch_type", cue]].dropna()
        for gk, s in sub.groupby("game_pk"):
            xa = s[s.pitch_type == a][cue]
            xb = s[s.pitch_type == b][cue]
            if len(xa) >= 2 and len(xb) >= 2:
                per_game.append((gk, len(xa), len(xb), float(xa.mean() - xb.mean())))
    return {
        "n": (len(ga), len(gb)),
        "mean_a": float(ga.mean()),
        "mean_b": float(gb.mean()),
        "delta": float(ga.mean() - gb.mean()),
        "g": g,
        "p": p,
        "per_game": per_game,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", default="../runs/merrill_kelly_poc")
    args = ap.parse_args()

    df = load_pitcher(Path(args.run_dir))
    col = "delivery_type" if "delivery_type" in df.columns else "delivery"
    name = Path(args.run_dir).name

    mix = df[col].value_counts().to_dict()
    print(f"=== cross-delivery test: {name} ===")
    print(f"delivery mix: {mix}\n")

    agree = total = 0
    for cue, a, b, predicted in SURVIVORS:
        print(f"--- {cue}  {a} vs {b}  (stretch predicts sign {'+' if predicted>0 else '-'}) ---")
        res = {}
        for stratum in ("stretch", "windup"):
            sub = df[df[col] == stratum]
            r = contrast(sub, cue, a, b) if not sub.empty else None
            res[stratum] = r
            if r is None:
                print(f"  {stratum:8s}: cue absent")
            elif "too_few" in r:
                print(f"  {stratum:8s}: too few per group {r['too_few']} (min {MIN_PER_GROUP})")
            else:
                print(
                    f"  {stratum:8s}: n={r['n']}  {a}={r['mean_a']:+.4f} {b}={r['mean_b']:+.4f}  "
                    f"delta={r['delta']:+.4f}  g={r['g']:+.3f}  p={r['p']:.4f}"
                )
        rs, rw = res.get("stretch"), res.get("windup")
        if rs and rw and "g" in rs and "g" in rw:
            total += 1
            same = np.sign(rs["g"]) == np.sign(rw["g"])
            as_pred = np.sign(rw["g"]) == predicted
            agree += bool(same)
            print(
                f"  => windup sign {'MATCHES' if same else 'REVERSES'} the stretch; "
                f"{'as predicted' if as_pred else 'AGAINST the prediction'}"
            )
            if rw["per_game"]:
                good = sum(1 for *_, d in rw["per_game"] if np.sign(d) == predicted)
                print(
                    f"     windup per-game: {good} of {len(rw['per_game'])} games in the "
                    f"predicted direction"
                )
                for gk, na, nb, d in rw["per_game"]:
                    print(f"        game {int(gk)}  n{a}={na:3d} n{b}={nb:3d}  delta={d:+.4f}")
        print()

    if total:
        print(f"OVERALL: {agree} of {total} survivors keep their direction in the windup")
        print("(Webb baseline for comparison: 35% of 74 combinations agreed across strata)")


if __name__ == "__main__":
    main()
