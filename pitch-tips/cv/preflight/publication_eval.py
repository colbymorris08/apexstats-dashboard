"""
The publication test: would this difference actually work as a rule?

A surviving difference and a usable tip are not the same thing. A difference says
two pitch types sit apart on average. A tip is a rule a hitter applies to ONE
pitch in real time, so it has to be evaluated the way it would be used:

  fire count    how often the rule triggers at all. A rule that never fires is
                not a tip regardless of how accurate it is when it does.
  precision     when it fires, how often it is right. This is the number that
                matters to a hitter, who only experiences the rule when it fires,
                and it carries the 0.75 publication floor.
  accuracy      overall agreement, reported alongside the MAJORITY BASELINE,
                because a lopsided arsenal makes a high accuracy meaningless.

Why precision alone is not enough
---------------------------------
Precision against base rate is the most legible form of the "versus random pitches"
test and it is kept, but on a lopsided mix it scores the wrong thing in two ways:

1. **A binary contrast has one degree of freedom.** "Fires on the fastball" and
   "fires on the slider" are one rule read in two directions. Scoring a single
   direction discards half the information, then penalises the rule for the
   pitcher's usage — which says nothing about whether the cue physically separates
   the two pitches.
2. **It aims at the wrong target.** A rule calling four-seamer on an arm that throws
   four-seamers 81% of the time tells a hitter what he already assumes. The value
   lives almost entirely in the rare pitch: moving off-speed from 1-in-5 to 1-in-2
   changes an at-bat, while moving fastball from 81% to 88% does not.

So two further measures are computed:

  youden_j     hit rate minus false-alarm rate. Usage-invariant, so a cue scores the
               same at 50/50 as at 85/15, and symmetric, so a tip and its inverse
               score identically. This is the separation measure.
  lr_pos       likelihood ratios, with the resulting shift in a coach's odds. These
  lr_neg       are directional and usage-aware, so the two readings of one cue can
               be worth very different amounts. This is the actionability measure.

J answers "does the cue separate the pitches"; the likelihood ratios answer "is the
shift worth acting on". They are different questions and both are reported. J is
subject to the same small-sample inflation as any other effect measure, so it is
benchmarked against a per-arm permutation null in ``jcalib.py`` rather than against
a threshold chosen by hand.

Method, fixed before looking at any result
-----------------------------------------
* The threshold is the midpoint of the two group medians, fitted on the DISCOVERY
  games only and then frozen.
* It is evaluated on the HOLDOUT games, which share no game with discovery.
* Direction is taken from discovery, so the holdout cannot pick the sign that
  flatters the result.

Nothing here is tuned. The threshold rule and the 0.75 floor are stated above and
applied as written whatever comes out.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from scipy import stats

from preflight.spot_diff import (
    MIN_PER_GROUP,
    _groups,
    hedges_g,
    load_pitcher,
    split_by_game,
)

PRECISION_FLOOR = 0.75

CANDIDATES = [
    ("stance_width_at_set", "CU", "REST"),
    ("glove_flare_at_lift", "CU", "SL"),
    ("glove_flare_at_lift", "CH", "CU"),
    ("glove_off_body_at_lift", "CU", "SL"),
    ("glove_flare_at_lift", "FF", "SL"),
]


def evaluate(disc, hold, cue: str, a: str, b: str) -> dict | None:
    """Fit on discovery, evaluate as a classifier on the holdout."""
    da, db = _groups(disc, cue, a, b)
    ha, hb = _groups(hold, cue, a, b)
    if min(len(da), len(db)) < MIN_PER_GROUP or min(len(ha), len(hb)) < MIN_PER_GROUP:
        return {"too_few": (len(da), len(db), len(ha), len(hb))}

    g_disc = hedges_g(da, db)
    thr = (np.median(da) + np.median(db)) / 2.0
    # "high value means type a" is decided on discovery and frozen.
    high_is_a = np.median(da) > np.median(db)

    x = np.r_[ha, hb]
    y = np.r_[np.ones(len(ha)), np.zeros(len(hb))]  # 1 == type a
    fires = (x > thr) if high_is_a else (x < thr)

    tp = int((fires & (y == 1)).sum())
    fp = int((fires & (y == 0)).sum())
    n_fire = int(fires.sum())
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    # Hit rate and false-alarm rate, the two quantities that describe how well the
    # cue separates the two pitch types without reference to how often each is
    # thrown. Precision cannot do this: it mixes separation with usage, so the same
    # cue scores differently on a 50/50 arm and an 85/15 arm.
    tpr = tp / n_pos if n_pos else float("nan")
    fpr = fp / n_neg if n_neg else float("nan")
    # Youden's J. Usage-invariant and symmetric, so a rule and its inverse score
    # identically — which is correct, because a two-pitch contrast has one degree of
    # freedom and "fires on the fastball" and "fires on the slider" are the same
    # rule read in opposite directions.
    youden_j = tpr - fpr
    # Likelihood ratios, the form a coach acts on: they convert prior odds on a
    # pitch into posterior odds given the cue. Unlike J these are directional and
    # usage-aware, so the two readings of one cue can be worth very different
    # amounts — the whole point when one pitch is rare.
    lr_pos = (tpr / fpr) if fpr > 0 else float("inf")
    lr_neg = ((1 - tpr) / (1 - fpr)) if fpr < 1 else float("inf")
    prior = n_pos / len(y) if len(y) else float("nan")
    prior_odds = prior / (1 - prior) if 0 < prior < 1 else float("nan")

    def _posterior(odds_ratio: float) -> float:
        o = prior_odds * odds_ratio
        return float(o / (1 + o)) if np.isfinite(o) else float("nan")
    pred = fires.astype(int) if high_is_a else fires.astype(int)
    acc = float((pred == y).mean())
    maj = float(max((y == 1).mean(), (y == 0).mean()))
    return {
        "g_disc": g_disc,
        "g_hold": hedges_g(ha, hb),
        "threshold": float(thr),
        "n_hold": int(len(x)),
        "n_fire": n_fire,
        "fire_rate": n_fire / len(x),
        "tp": tp,
        "fp": fp,
        "precision": (tp / n_fire) if n_fire else float("nan"),
        # Prevalence of the predicted type among exactly the pitches this
        # evaluation scored. Computed here rather than by the caller so it cannot
        # drift from the scope precision was measured on — a precision figure
        # compared against a base rate from a different set of pitches is worse
        # than no comparison at all.
        "base_rate": float((y == 1).mean()),
        "recall": tp / max(1, n_pos),
        "n_pos": n_pos,
        "n_neg": n_neg,
        "tpr": tpr,
        "fpr": fpr,
        "youden_j": youden_j,
        "lr_pos": lr_pos,
        "lr_neg": lr_neg,
        # What the cue does to a coach's odds, in both directions. The first is the
        # rare-pitch question when the rule fires; the second is what silence buys.
        "prior": prior,
        "post_fire": _posterior(lr_pos),
        "post_quiet": _posterior(lr_neg),
        "accuracy": acc,
        "majority": maj,
        "margin": acc - maj,
        "p_hold": float(stats.ttest_ind(ha, hb, equal_var=False).pvalue),
        "separation": float(ha.mean() - hb.mean()),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", default="../runs/merrill_kelly_poc")
    ap.add_argument("--stratum", default="stretch")
    args = ap.parse_args()

    df = load_pitcher(Path(args.run_dir))
    col = "delivery_type" if "delivery_type" in df.columns else "delivery"
    sub = df[df[col] == args.stratum]
    disc, hold = split_by_game(sub)
    print(f"=== publication evaluation: {Path(args.run_dir).name} / {args.stratum} ===")
    print(
        f"n={len(sub)} games={sub['game_pk'].nunique()} "
        f"discovery={len(disc)} holdout={len(hold)}"
    )
    print(f"precision floor = {PRECISION_FLOOR} (fixed)\n")

    print(
        f"{'cue':24s} {'contrast':10s} {'g_disc':>7s} {'g_hold':>7s} {'nHold':>6s} "
        f"{'fires':>6s} {'prec':>6s} {'acc':>6s} {'base':>6s} {'PUBLISH?'}"
    )
    any_pass = False
    for cue, a, b in CANDIDATES:
        r = evaluate(disc, hold, cue, a, b)
        if r is None or "too_few" in r:
            print(f"{cue:24s} {a+' v '+b:10s} insufficient group sizes {r and r.get('too_few')}")
            continue
        ok = (
            np.isfinite(r["precision"])
            and r["precision"] >= PRECISION_FLOOR
            and r["n_fire"] > 0
            and r["margin"] > 0
        )
        any_pass = any_pass or ok
        print(
            f"{cue:24s} {a+' v '+b:10s} {r['g_disc']:+7.3f} {r['g_hold']:+7.3f} "
            f"{r['n_hold']:6d} {r['n_fire']:6d} {r['precision']:6.3f} {r['accuracy']:6.3f} "
            f"{r['majority']:6.3f} {'YES' if ok else 'no'}"
        )
    print()
    print(
        "PUBLISHABLE: none"
        if not any_pass
        else "PUBLISHABLE: at least one contrast clears the floor"
    )


if __name__ == "__main__":
    main()
