"""
Where the J floor actually sits, derived rather than chosen.

Youden's J replaces one-sided precision as the separation measure (see
``publication_eval``). That immediately raises the question of what value of J is
worth anything, and the answer must not be picked by hand: a threshold chosen to
make results appear is the same defect as tuning a gate.

Three independent sources, in decreasing order of hardness:

1. **Statistical floor — the permutation null, per arm.**
   Shuffle pitch labels within game, recompute J, repeat. Whatever J the shuffle
   reaches is what noise produces *at that arm's sample size and mix*, and nothing
   below it can mean anything. This is measured, not argued. It has to be per-arm
   because a thin arm with a lopsided mix manufactures far more J than a deep
   balanced one, and a single global floor would be too strict for one and too
   permissive for the other.

2. **Operational floor — the documented tips.**
   A professional scout watched Thorpe, wrote the tip up, and judged it worth
   relaying in a game. Whatever J that cue produces where we can measure it is
   approximately the level a human considered actionable. This is the single most
   informative calibration point available, because it is the only one anchored to
   a real decision rather than to a distribution.

3. **Decision floor — the user's call.**
   Not ours. What this module owes the decision is a translation: what a given J and
   likelihood ratio do to the odds a coach faces. Tier boundaries are therefore
   stated in **likelihood-ratio** terms, because that is the quantity acted on, not
   in J, which is a separation measure.

A note on the number 0.75, which was proposed: J is not a percentage of the same
kind as precision. J = 0.75 implies something like an 85% hit rate against a 10%
false-alarm rate — a tip so blatant that it would already be common knowledge and
corrected. Setting the bar there would empty the board by construction. That is not
a reason to set it low; it is a reason to measure it, which is what this does.
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

# Percentile of the shuffled J distribution used as the per-arm statistical floor.
# 95 is the conventional one-sided 5% false-positive rate and is fixed here before
# any result is looked at. Nothing below this floor can be distinguished from the
# arm's own noise.
NULL_PERCENTILE = 95


def _score(disc, hold, col, a, b) -> dict | None:
    r = publication_eval.evaluate(disc, hold, col, a, b)
    if r is None or "too_few" in r:
        return None
    return r


def _split(sub: pd.DataFrame, disc_g, val_g, stratum: str):
    s = sub[sub["_delivery"] == stratum]
    k = temporal.game_keys(s)
    return s[k.isin(set(map(int, disc_g)))], s[k.isin(set(map(int, val_g)))]


def null_j(sub, disc_g, val_g, cases: list[dict], n: int, seed: int = 0) -> dict:
    """J reachable on shuffled labels, pooled across this arm's own contrasts.

    Labels are shuffled within game so group sizes and the split structure survive
    and only the cue-to-pitch association is destroyed. Pooling across the arm's
    contrasts is deliberate: the floor is a property of the arm's sample size and
    mix, and estimating it per contrast would give each one a floor fitted to
    itself.
    """
    rng = np.random.default_rng(seed)
    got: list[float] = []
    for _ in range(n):
        sh = sub.copy()
        sh["pitch_type"] = (
            sh.groupby(temporal.game_keys(sh), group_keys=False)["pitch_type"]
            .apply(lambda s: pd.Series(rng.permutation(s.to_numpy()), index=s.index))
        )
        for c in cases:
            d, h = _split(sh, disc_g, val_g, c["delivery"])
            if d.empty or h.empty:
                continue
            r = _score(d, h, c["col"], c["pitch_a"], c["pitch_b"])
            if r and np.isfinite(r["youden_j"]):
                got.append(abs(float(r["youden_j"])))
    if not got:
        return {"n": 0, "values": []}
    arr = np.array(got)
    return {
        "n": len(arr),
        "mean": round(float(arr.mean()), 3),
        "p95": round(float(np.percentile(arr, NULL_PERCENTILE)), 3),
        "max": round(float(arr.max()), 3),
        # Kept in full so the exceedance rate can be evaluated at any candidate
        # threshold later. Without it a club could only see our boundary, and the
        # whole point of publishing the distribution is that they can pick their
        # own — informed by what noise does at that level.
        "values": [round(float(v), 4) for v in arr],
    }


# Candidate thresholds a club might choose. Published as a sweep rather than a
# single boundary so a reader with more risk tolerance can draw their own line and
# see what it costs. The range is deliberately wide enough to include values we
# consider indefensible, because hiding them would not stop anyone choosing one.
SWEEP = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]


def sweep_table(scored: list[dict], null_values: list[float]) -> list[dict]:
    """Observed count above each threshold, with the false positives to expect.

    The second column is the one that makes this honest. Lowering a threshold does
    not reveal hidden tips; it admits noise at a rate the permutation null already
    measured. Reporting the expected false-positive count alongside the observed
    count turns "set your own bar" into an informed choice instead of an invitation
    to manufacture findings.
    """
    j = np.array([abs(s["youden_j"]) for s in scored if s.get("youden_j") is not None])
    nulls = np.array(null_values) if null_values else None
    rows = []
    for t in SWEEP:
        above = int((j > t).sum()) if j.size else 0
        exp_fp = None
        if nulls is not None and nulls.size:
            # Share of shuffled scorings that would clear this bar, times the number
            # of real cues scored: how many of the cues above the line are there by
            # chance alone.
            exp_fp = round(float((nulls > t).mean()) * len(j), 1)
        rows.append({
            "threshold": t,
            "n_above": above,
            "n_below": int(j.size) - above,
            "expected_false_positives": exp_fp,
            # Nothing above the line is a finding unless it also passes the gates.
            "n_above_and_gated": int(sum(
                1 for s in scored
                if s.get("youden_j") is not None
                and abs(s["youden_j"]) > t
                and s.get("failed_at") is None
            )),
        })
    return rows


def why_below(scored: list[dict], floor: float | None) -> dict[str, int]:
    """Reasons cues sit below the floor, so the count is never a bare number.

    A club reading "212 cues below our threshold" could reasonably wonder what is
    being withheld. The answer is that each one failed for a stated reason, and
    these are those reasons.
    """
    out: dict[str, int] = {}
    for s in scored:
        jv = s.get("youden_j")
        if jv is None or (floor is not None and abs(jv) > floor):
            continue
        reason = s.get("failed_at") or "cleared the gates but J inside arm noise"
        out[reason] = out.get(reason, 0) + 1
    return out


def analyse_arm(run: Path, args, cache) -> dict[str, Any] | None:
    name = run.name.replace("_poc", "").replace("_rich", "").replace("_", " ").title()
    snapshot.assert_quiescent(run, allow_unready=args.allow_unready)
    df = load_family(run, "position")
    disc_g, val_g = temporal.temporal_split(df, args.n_disc, args.n_val, cache)
    keep = set(map(int, disc_g)) | set(map(int, val_g))
    sub = df[temporal.game_keys(df).isin(keep)].copy()
    if getattr(args, "delivery_aware", False):
        sub, _ = restrict_to_real_strata(sub, delivery_verdict(run))

    with temporal.chronological(disc_g, val_g):
        res = spot_diff.analyse(sub, name)
    sub["_delivery"] = spot_diff._delivery_series(sub)

    dist = [d for d in res.get("distribution", []) if d.get("floor_multiples") is not None]
    dist.sort(key=lambda d: d["floor_multiples"], reverse=True)
    # top=0 means every comparison. The distribution is the deliverable here, so it
    # should not be truncated unless a run is being kept cheap on purpose.
    cases = dist if args.top == 0 else dist[: args.top]

    scored = []
    for c in cases:
        d, h = _split(sub, disc_g, val_g, c["delivery"])
        if d.empty or h.empty:
            continue
        r = _score(d, h, c["col"], c["pitch_a"], c["pitch_b"])
        if r is None:
            continue
        scored.append({
            "cue": c["cue"], "col": c["col"], "contrast": c["contrast"],
            "delivery": c["delivery"], "failed_at": c["failed_at"],
            "q_discovery": c["q_discovery"], "floor_multiples": c["floor_multiples"],
            "g_discovery": c["g_discovery"], "n_smaller_group": c.get("n_smaller_group"),
            "precision": round(float(r["precision"]), 3) if np.isfinite(r["precision"]) else None,
            "base_rate": round(float(r["base_rate"]), 3),
            "tpr": round(float(r["tpr"]), 3), "fpr": round(float(r["fpr"]), 3),
            "youden_j": round(float(r["youden_j"]), 3),
            "lr_pos": round(float(r["lr_pos"]), 2) if np.isfinite(r["lr_pos"]) else None,
            "lr_neg": round(float(r["lr_neg"]), 2) if np.isfinite(r["lr_neg"]) else None,
            "prior": round(float(r["prior"]), 3),
            "post_fire": round(float(r["post_fire"]), 3) if np.isfinite(r["post_fire"]) else None,
            "n_fire": int(r["n_fire"]), "n_holdout": int(r["n_hold"]),
        })

    nl = null_j(sub, disc_g, val_g, cases, args.permutations) if args.permutations else {"n": 0}
    floor = nl.get("p95")
    for s in scored:
        s["beats_null_floor"] = bool(floor is not None and abs(s["youden_j"]) > floor)

    return {
        "arm": name, "run": str(run), "n_pitches": int(len(sub)),
        "n_games_analysed": len(keep),
        "sample": snapshot.fingerprint(run, "features.csv", sub),
        "null_j": {k: v for k, v in nl.items() if k != "values"},
        "null_values": nl.get("values", []),
        "j_floor_p95": floor,
        "n_scored": len(scored),
        "n_above_floor": sum(1 for s in scored if s.get("beats_null_floor")),
        "n_below_floor": sum(1 for s in scored if not s.get("beats_null_floor")),
        "why_below": why_below(scored, floor),
        "sweep": sweep_table(scored, nl.get("values", [])),
        "scored": scored,
    }


def odds_phrase(prior: float, post: float) -> str:
    """The shift in a coach's odds, in the form he would say it."""
    def one_in(p: float) -> str:
        if not np.isfinite(p) or p <= 0:
            return "never"
        return f"1-in-{1 / p:.1f}"
    return f"{one_in(prior)} -> {one_in(post)}"


def report_text(arm: dict) -> str:
    nl = arm["null_j"]
    lines = [
        f"\n=== {arm['arm']} — J and likelihood ratios ===",
        f"pitches {arm['n_pitches']} | games {arm['n_games_analysed']}",
    ]
    if nl.get("n"):
        lines.append(
            f"permutation null on J: mean {nl['mean']:.3f}, p{NULL_PERCENTILE} "
            f"{nl['p95']:.3f}, max {nl['max']:.3f} over {nl['n']} shuffled scorings"
        )
        lines.append(f"-> statistical floor for this arm: J > {nl['p95']:.3f}")
    lines.append("")
    lines.append(f"{'J':>7s} {'TPR':>6s} {'FPR':>6s} {'LR+':>7s} {'prec':>6s} {'base':>6s} "
                 f"{'fires':>6s}  {'cue / contrast':40s} verdict")
    for s in sorted(arm["scored"], key=lambda x: abs(x["youden_j"]), reverse=True):
        v = "above arm noise floor" if s.get("beats_null_floor") else "inside arm noise"
        lines.append(
            f"{s['youden_j']:+7.3f} {s['tpr']:6.3f} {s['fpr']:6.3f} "
            f"{(s['lr_pos'] if s['lr_pos'] is not None else float('nan')):7.2f} "
            f"{(s['precision'] if s['precision'] is not None else float('nan')):6.3f} "
            f"{s['base_rate']:6.3f} {s['n_fire']:6d}  "
            f"{(s['cue'][:22] + ' | ' + s['contrast'])[:40]:40s} {v}"
        )
        if s["post_fire"] is not None:
            lines.append(
                f"{'':8s}when it fires, this pitch goes "
                f"{odds_phrase(s['prior'], s['post_fire'])}  (gate: "
                f"{s['failed_at'] or 'passed all'})"
            )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", nargs="+", required=True)
    ap.add_argument("--n-disc", type=int, default=temporal.N_DISCOVERY_STARTS)
    ap.add_argument("--n-val", type=int, default=temporal.N_VALIDATION_STARTS)
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--permutations", type=int, default=20)
    ap.add_argument("--delivery-aware", action="store_true")
    ap.add_argument("--allow-unready", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    cache = game_dates.load_cache()
    arms = []
    for r in args.run_dir:
        try:
            arm = analyse_arm(Path(r), args, cache)
        except (Exception, SystemExit) as exc:
            print(f"\n=== {Path(r).name} === skipped: {exc}")
            continue
        if arm:
            arms.append(arm)
            print(report_text(arm))

    floors = [a["j_floor_p95"] for a in arms if a.get("j_floor_p95") is not None]
    print("\n=== the statistical floor, measured per arm ===")
    if floors:
        print(f"per-arm J floors (p{NULL_PERCENTILE} of shuffled J): "
              f"min {min(floors):.3f}, median {float(np.median(floors)):.3f}, "
              f"max {max(floors):.3f} across {len(floors)} arms")
        print("a cue must clear its OWN arm's floor. The spread is exactly why a "
              "single global number would be wrong:")
        for a in sorted(arms, key=lambda x: x.get("j_floor_p95") or 0, reverse=True):
            if a.get("j_floor_p95") is None:
                continue
            print(f"  {a['arm']:17s} floor J>{a['j_floor_p95']:.3f}  "
                  f"scored {a['n_scored']:4d}  above {a['n_above_floor']:3d}  "
                  f"below {a['n_below_floor']:4d}  (pitches {a['n_pitches']})")

    survivors = [(a["arm"], s) for a in arms for s in a["scored"] if s.get("beats_null_floor")]
    print(f"\ncues clearing their arm's measured J floor: {len(survivors)}")
    for arm, s in sorted(survivors, key=lambda x: abs(x[1]["youden_j"]), reverse=True)[:20]:
        print(f"  {arm:17s} J={s['youden_j']:+.3f} LR+={s['lr_pos']} "
              f"{odds_phrase(s['prior'], s['post_fire']) if s['post_fire'] else ''}  "
              f"{s['cue'][:26]:26s} {s['contrast'][:14]:14s} (gate: {s['failed_at']})")

    # The distribution, so a club can draw its own line and see what it costs.
    all_scored = [s for a in arms for s in a["scored"]]
    all_nulls = [v for a in arms for v in a["null_values"]]
    print("\n=== set your own threshold: what each bar admits ===")
    print("'expected FP' is drawn from the permutation null: how many of the cues")
    print("above that bar are there by chance alone. Lowering the bar does not")
    print("reveal hidden tips — it admits noise at a rate we have measured.")
    print(f"\n{'J bar':>7s} {'below':>7s} {'above':>7s} {'expected FP':>12s} "
          f"{'above & gated':>14s}  read")
    for row in sweep_table(all_scored, all_nulls):
        exp = row["expected_false_positives"]
        signal = "" if exp is None else (
            "all of it noise" if exp >= row["n_above"] else
            f"~{max(0, row['n_above'] - exp):.0f} beyond chance")
        print(f"{row['threshold']:7.2f} {row['n_below']:7d} {row['n_above']:7d} "
              f"{(exp if exp is not None else float('nan')):12.1f} "
              f"{row['n_above_and_gated']:14d}  {signal}")

    print("\n=== why cues sit below the floor ===")
    agg: dict[str, int] = {}
    for a in arms:
        for k, v in a["why_below"].items():
            agg[k] = agg.get(k, 0) + v
    for k, v in sorted(agg.items(), key=lambda x: -x[1]):
        print(f"  {v:5d}  {k}")

    if args.out:
        Path(args.out).write_text(json.dumps({
            "arms": arms,
            "null_percentile": NULL_PERCENTILE,
            "sweep_corpus": sweep_table(all_scored, all_nulls),
            "why_below_corpus": agg,
        }, indent=2, default=str))
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
