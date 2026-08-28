"""
Rank every comparison by how big the movement difference physically is.

The tiered board answers "what survived the gates". This answers a different
question, and it is the one a club asks first: **how big is the difference?**

Why the two are not the same report
-----------------------------------
Reporting only survivors makes two completely different situations look identical
-- both simply absent:

  * a cue whose separation is trivially small, where there is nothing to find; and
  * a cue with a large physical separation that ran out of sample.

Only the second is a case where more film would help, and the gated report cannot
distinguish them. So this module prints the full effect-size distribution with the
gate verdicts alongside, ranked by physical separation.

The ranking unit
----------------
Raw deltas are not comparable across cues: the units are torso lengths, frames and
unit-free ratios all at once, so sorting them together is meaningless. The common
denominator used here is each cue's own **visibility floor** -- the separation at
which a person could see the difference at all. A rank of 3.0 means "three times
the size a human needs to see it". That is a physical quantity, not a p-value.

What this module must never do
------------------------------
**Magnitude sets display order. It never sets confidence.** A large effect on a
small sample is exactly what a small sample produces: the Kelly artifact peaked at
g = 0.491 and was pure noise, and its curve was still *rising* at 11 games. So a
large separation that has not passed the gates is reported as a large observed
difference, not yet validated -- it stays LOW, with its cell size shown. Nothing
here can promote anything.

The two "versus random pitches" tests
-------------------------------------
When a cue fires, is it doing better than drawing a pitch at random from this
pitcher's mix? Both tests below are run on anything surfaced by magnitude, because
they answer that question at different strengths:

  precision vs base rate   The direct form. If the rule fires and calls slider,
                           how often is it right, against how often you would be
                           right guessing from the arsenal? This is what caught
                           the three near-misses at 0.884, 0.833 and 0.775 --
                           every one of them beaten by random guessing.
  permutation null         The stronger form. Shuffle the pitch labels within game
                           to destroy every real association while preserving
                           group sizes, refit, and re-measure. If the observed
                           precision sits inside the distribution the shuffle
                           produces, the finding is an artifact of the estimator
                           rather than of the pitcher. This is what dissolved the
                           consistency family's apparent 72% replication.

Nothing here is tuned: no threshold, floor, minimum or gate is touched. This is a
reporting view over the same run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from preflight import game_dates, publication_eval, snapshot, spot_diff, temporal
from preflight.temporal_discover import (
    delivery_verdict,
    load_family,
    restrict_to_real_strata,
)

# How many of the largest separations to run the expensive versus-random tests on.
# A reporting choice, not a gate: every comparison is still listed in the JSON.
TOP_N = 12


def _fires_vs_random(sub: pd.DataFrame, entry: dict, disc_g, val_g) -> dict | None:
    """Precision when the rule fires, against guessing from the arsenal."""
    # Scored inside the cue's own stratum. Set-anchored and fixed-lookback windows
    # are unlike measurements, so pooling them would score a rule against pitches
    # it was never fitted on.
    stratum = sub[sub["_delivery"] == entry["delivery"]]
    sk = temporal.game_keys(stratum)
    disc = stratum[sk.isin(set(map(int, disc_g)))]
    hold = stratum[sk.isin(set(map(int, val_g)))]
    if disc.empty or hold.empty:
        return None
    r = publication_eval.evaluate(disc, hold, entry["col"], entry["pitch_a"], entry["pitch_b"])
    if r is None or "too_few" in r:
        return None
    return r


def _permutation_null(sub: pd.DataFrame, entry: dict, disc_g, val_g, n: int, seed: int = 0) -> dict:
    """Precision the same rule reaches on shuffled labels.

    Labels are shuffled **within game**, which preserves both group sizes and the
    game structure the split relies on, and destroys only the association between
    the cue and the pitch type. Anything the rule still achieves under that shuffle
    is manufactured by the estimator, not read off the pitcher.
    """
    rng = np.random.default_rng(seed)
    got: list[float] = []
    for _ in range(n):
        shuffled = sub.copy()
        shuffled["pitch_type"] = (
            shuffled.groupby(temporal.game_keys(shuffled), group_keys=False)["pitch_type"]
            .apply(lambda s: pd.Series(rng.permutation(s.to_numpy()), index=s.index))
        )
        r = _fires_vs_random(shuffled, entry, disc_g, val_g)
        if r and np.isfinite(r.get("precision", np.nan)):
            got.append(float(r["precision"]))
    if not got:
        return {"n": 0}
    arr = np.array(got)
    return {
        "n": len(got),
        "mean": round(float(arr.mean()), 3),
        "p10": round(float(np.percentile(arr, 10)), 3),
        "p90": round(float(np.percentile(arr, 90)), 3),
        "max": round(float(arr.max()), 3),
    }


def analyse_arm(run: Path, args, cache) -> dict[str, Any]:
    """Magnitude-ranked view for one arm, with gates and versus-random alongside."""
    name = run.name.replace("_poc", "").replace("_rich", "").replace("_", " ").title()
    snapshot.assert_quiescent(run, allow_unready=args.allow_unready)
    df = load_family(run, "position")
    n_banked = temporal.n_games_available(df)
    disc_g, val_g = temporal.temporal_split(df, args.n_disc, args.n_val, cache)
    keep = set(map(int, disc_g)) | set(map(int, val_g))
    sub = df[temporal.game_keys(df).isin(keep)].copy()

    verdict = delivery_verdict(run)
    if getattr(args, "delivery_aware", False):
        sub, _ = restrict_to_real_strata(sub, verdict)

    with temporal.chronological(disc_g, val_g):
        res = spot_diff.analyse(sub, name)
    sub["_delivery"] = spot_diff._delivery_series(sub)

    dist = [d for d in res.get("distribution", []) if d.get("floor_multiples") is not None]
    dist.sort(key=lambda d: d["floor_multiples"], reverse=True)

    for entry in dist[: args.top]:
        r = _fires_vs_random(sub, entry, disc_g, val_g)
        if r is None:
            entry["vs_random"] = {"status": "too few pitches to score as a rule"}
            continue
        entry["vs_random"] = {
            "precision": round(float(r["precision"]), 3) if np.isfinite(r["precision"]) else None,
            "base_rate": round(float(r["base_rate"]), 3),
            "lift": round(float(r["precision"] - r["base_rate"]), 3)
            if np.isfinite(r["precision"]) else None,
            "n_fire": int(r["n_fire"]),
            "n_holdout": int(r["n_hold"]),
        }
        if args.permutations:
            entry["permutation_null"] = _permutation_null(
                sub, entry, disc_g, val_g, args.permutations
            )

    return {
        "arm": name,
        "run": str(run),
        "n_games_analysed": len(keep),
        "n_games_banked": n_banked,
        "n_pitches": int(len(sub)),
        "delivery_verdict": verdict,
        "comparisons": res.get("comparisons", 0),
        "n_surviving": res.get("n_surviving", 0),
        "sample": snapshot.fingerprint(run, "features.csv", sub),
        "ranked": dist,
    }


def _gate_word(entry: dict) -> str:
    f = entry.get("failed_at")
    return "PASSED ALL GATES" if f is None else f"failed: {f}"


def report_text(arm: dict, top: int) -> str:
    lines = [
        f"\n=== {arm['arm']} — largest movement differences ===",
        f"pitches {arm['n_pitches']} | games analysed {arm['n_games_analysed']} "
        f"(banked {arm['n_games_banked']}) | comparisons {arm['comparisons']} "
        f"| cleared every gate {arm['n_surviving']}",
        "ranked by physical separation, in multiples of the cue's own human-visibility floor",
        "magnitude sets display order only — it is never evidence",
        "",
        f"{'x floor':>8s} {'delta':>10s} {'g':>7s} {'q':>8s} {'rarer':>6s}  "
        f"{'cue / contrast':44s} gate",
    ]
    for e in arm["ranked"][:top]:
        lines.append(
            f"{e['floor_multiples']:8.2f} {e['delta']:+10.4f} {e['g_discovery']:+7.3f} "
            f"{e['q_discovery']:8.3g} {e.get('n_smaller_group', 0):6d}  "
            f"{(e['cue'][:26] + ' | ' + e['contrast'])[:44]:44s} {_gate_word(e)}"
        )
        vr = e.get("vs_random")
        if vr and "precision" in vr and vr["precision"] is not None:
            lines.append(
                f"{'':8s} when this fires it is right {vr['precision']:.1%} of the time; "
                f"guessing at random on this pitcher gives {vr['base_rate']:.1%} "
                f"(lift {vr['lift']:+.3f}, fires {vr['n_fire']} of {vr['n_holdout']})"
            )
        elif vr:
            lines.append(f"{'':8s} {vr.get('status', 'not scored')}")
        pn = e.get("permutation_null")
        if pn and pn.get("n"):
            lines.append(
                f"{'':8s} shuffled labels reach {pn['mean']:.1%} on average "
                f"(10-90% {pn['p10']:.1%}-{pn['p90']:.1%}, best {pn['max']:.1%}) "
                f"over {pn['n']} shuffles"
            )
    return "\n".join(lines)


def needed_per_group(g: float) -> int | None:
    """Pitches per group needed to detect an effect this size at nominal p<0.05.

    Standard two-sample formula at 80% power. Two honest caveats, both of which cut
    the same way:

    * The FDR correction is stricter than nominal 0.05, so clearing BH inside a
      300-comparison family needs materially more than this.
    * The observed ``g`` is itself inflated when the sample is small -- that is the
      winner's curse, and it is the mechanism behind the Kelly artifact. So the true
      effect is probably smaller and the real requirement correspondingly larger.

    The number is therefore a **floor on what more film would cost**, not a promise
    that collecting it would produce a finding.
    """
    if not np.isfinite(g) or abs(g) < 1e-6:
        return None
    return int(np.ceil(2 * (1.96 + 0.8416) ** 2 / g**2))


def sample_limited(arm: dict) -> list[dict]:
    """Large separations that failed only because one pitch type is rare.

    This is the single case where gathering more film would change the answer, so
    it is called out separately rather than left inside the ranked list. The test
    is not "which gate did it die at" but "was it underpowered for its own observed
    effect": a separation above the visibility floor, with a large standardized
    effect, whose smaller group holds fewer pitches than that effect needs. A cue
    that failed with ample pitches on both sides is a real null and is excluded.
    """
    out = []
    for e in arm["ranked"]:
        if e.get("failed_at") is None or e["floor_multiples"] < 1.0:
            continue
        need = needed_per_group(e["g_discovery"])
        if need is None:
            continue
        smaller = e.get("n_smaller_group")
        if smaller is not None and smaller < need:
            out.append({**e, "n_needed_per_group": need, "n_have_smaller_group": smaller})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", nargs="+", required=True)
    ap.add_argument("--n-disc", type=int, default=temporal.N_DISCOVERY_STARTS)
    ap.add_argument("--n-val", type=int, default=temporal.N_VALIDATION_STARTS)
    ap.add_argument("--top", type=int, default=TOP_N)
    ap.add_argument("--permutations", type=int, default=0,
                    help="shuffles for the permutation null on surfaced cues")
    ap.add_argument("--delivery-aware", action="store_true")
    ap.add_argument("--allow-unready", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    cache = game_dates.load_cache()
    arms, limited = [], []
    for r in args.run_dir:
        run = Path(r)
        try:
            arm = analyse_arm(run, args, cache)
        except (Exception, SystemExit) as exc:
            print(f"\n=== {run.name} === skipped: {exc}")
            continue
        arms.append(arm)
        print(report_text(arm, args.top))
        limited.extend({"arm": arm["arm"], **e} for e in sample_limited(arm))

    print("\n=== large differences failing only on sample size ===")
    if not limited:
        print("none: no separation above the visibility floor died at a sample-size gate.")
        print("more film would not change any result currently on the board.")
    else:
        print(f"{len(limited)} — these are the cases where more film would help.")
        print("'need' is a floor at nominal p<0.05: clearing FDR needs more, and the")
        print("observed effect is inflated by the small sample that makes it a candidate.")
        for e in sorted(limited, key=lambda x: x["floor_multiples"], reverse=True)[:20]:
            print(f"  {e['arm']:14s} {e['floor_multiples']:6.2f}x floor  g={e['g_discovery']:+.2f}  "
                  f"have {e['n_have_smaller_group']:3d} need {e['n_needed_per_group']:4d}  "
                  f"{e['cue'][:28]:28s} {e['contrast'][:16]:16s} ({e['failed_at']})")

    if args.out:
        Path(args.out).write_text(json.dumps(
            {"arms": arms, "sample_limited": limited,
             "top_n": args.top, "permutations": args.permutations}, indent=2, default=str))
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
