"""
Discovery under the recency protocol, reported stage by stage and tiered.

Protocol: discover on the **3 most recent starts**, validate on the **next 6 going
back**. Discovery sits on the freshest film because that is where a live tip would
be; validation gets 2-3x the pitches, which is what a precision estimate needs.

Every gate is unchanged — BH-FDR q=0.10, the standardized effect floor, the
0.05-torso visibility floor, delivery-type stratification, disjoint non-empty game
sets. The tiers change what is *shown*, not what counts as evidence.

Five columns rather than a survivor count, because earlier reporting jumped from
"comparisons performed" to "differences surviving" and hid how much raw signal
exists before correction:

    comparisons -> raw (p<0.05) -> cleared FDR -> validated -> cleared precision

A caution stated in advance: at nine starts there will be more apparent survivors
than on a deep arm. Smaller samples produce larger apparent effects, which is
exactly what the partial-sample artifact was. The convergence check is materially
weaker here than at twenty-five games and is reported as suggestive only; for any
dispersion statistic the permutation null is the binding check, because that
family's replication rate is biased by group size and a raw survivor count in it
means nothing on its own.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from preflight import game_dates, snapshot, spot_diff, temporal, tiering
from preflight.publication_eval import evaluate
from preflight.spot_diff import hedges_g, load_pitcher
from preflight.trajectory import TRAJECTORY_FEATURES
from preflight.trajectory_discover import (
    TRAJECTORY_CUES,
    load_trajectory,
    permute_labels,
    to_dispersion,
)

FAMILIES = ("position", "movement", "consistency")


def stage_counts(res: dict[str, Any]) -> dict[str, Any]:
    """The reported stages, derived from what ``analyse`` recorded."""
    att = res.get("attrition") or {}
    comparisons = int(res.get("comparisons", 0))
    return {
        "comparisons": comparisons,
        "raw": int(res.get("n_nominal_discovery", 0)),
        "expected_by_chance": float(res.get("n_nominal_expected_by_chance", 0.0)),
        "fdr": comparisons - int(att.get("fdr", 0)) if comparisons else 0,
        "validated": int(res.get("n_surviving", 0)),
    }


def _scope(df: pd.DataFrame, stratum: str, a: str, b: str) -> pd.DataFrame:
    sub = df[df["_delivery"] == stratum] if "_delivery" in df.columns else df
    sub = sub.copy()
    if b == "REST":
        sub["pitch_type"] = np.where(sub["pitch_type"].astype(str) == a, a, "REST")
    return sub


def tier_validated(df, diff, disc_games, val_games, family, n_banked: int) -> dict[str, Any]:
    """Precision, base rate, lift and tier for one validated difference."""
    col, a, b = diff.get("feature"), diff.get("pitch_a"), diff.get("pitch_b")
    sub = _scope(df, diff.get("delivery"), a, b)
    keys = temporal.game_keys(sub)
    d = sub[keys.isin(set(map(int, disc_games)))]
    v = sub[keys.isin(set(map(int, val_games)))]
    pr = {}
    try:
        pr = evaluate(d, v, col, a, b) or {}
    except Exception:
        pr = {}
    t = tiering.assess(
        feature=col,
        precision=pr.get("precision", float("nan")),
        tp=pr.get("tp", 0),
        n_fire=pr.get("n_fire", 0),
        base=pr.get("base_rate", float("nan")),
        validated=True,
        n_games_available=n_banked,
    )
    t.update({k: pr.get(k) for k in ("accuracy", "majority", "margin", "n_hold",
                                     "threshold", "fire_rate")})
    t["family"] = family
    return t


def cell_sizes(df, ld, disc_games, val_games) -> dict[str, Any]:
    """Pitches per side of a contrast, in each half of the split."""
    a, b = ld.get("pitch_a"), ld.get("pitch_b")
    sub = _scope(df, ld.get("delivery"), a, b)
    keys = temporal.game_keys(sub)
    out = {}
    for tag, games in (("disc", disc_games), ("val", val_games)):
        s = sub[keys.isin(set(map(int, games)))]
        pt = s["pitch_type"].astype(str)
        col = ld.get("col")
        na = int(pd.to_numeric(s.loc[pt == a, col], errors="coerce").notna().sum())
        other = (pt != a) if b == "REST" else (pt == b)
        nb = int(pd.to_numeric(s.loc[other, col], errors="coerce").notna().sum())
        out[f"n_{tag}_a"], out[f"n_{tag}_b"] = na, nb
    out["n_smallest_cell"] = min(out["n_disc_a"], out["n_disc_b"],
                                 out["n_val_a"], out["n_val_b"])
    return out


def convergence(df, col, a, b, stratum, games) -> list[tuple]:
    """Effect size as starts accumulate, oldest to newest.

    At nine starts this yields a handful of points: enough to expose a wild swing,
    not enough to establish that an effect is tightening. Reported as suggestive.
    """
    sub = df[df["_delivery"] == stratum] if "_delivery" in df.columns else df
    out = []
    for k in range(2, len(games) + 1):
        s = sub[temporal.game_keys(sub).isin(set(map(int, games[:k])))]
        x = pd.to_numeric(s[s.pitch_type.astype(str) == a][col], errors="coerce").dropna()
        other = s[s.pitch_type.astype(str) != a] if b == "REST" else s[s.pitch_type.astype(str) == b]
        y = pd.to_numeric(other[col], errors="coerce").dropna()
        if len(x) >= 5 and len(y) >= 5:
            out.append((k, len(x), len(y), hedges_g(x.values, y.values)))
    return out


# Delivery verdicts, read from the calibration output. A stretch-only arm has no
# windup population, so analysing a "windup" stratum on him spends comparisons on
# pitches that are simply the ones where set detection failed — raising the FDR bar
# for the stratum that is real, and reporting an ABSENT stratum as an underpowered
# one. Those are different claims and only one of them is true.
def delivery_verdict(run: Path) -> str:
    f = run.parent / "delivery_calibration.json"
    if not f.exists():
        return "unknown"
    for r in json.loads(f.read_text()):
        if r.get("arm") == run.name:
            return r.get("calibration", {}).get("verdict", "unknown")
    return "unknown"


def restrict_to_real_strata(df: pd.DataFrame, verdict: str) -> tuple[pd.DataFrame, dict]:
    """Drop strata that do not exist for this arm.

    For a stretch-only arm only the set-anchored pitches are analysed. The
    fixed-lookback pitches are NOT merged into them: the geometry flag alone shifts
    cue values by mean |g| = 0.23 for at-set cues and 0.16 for at-lift cues on Webb,
    so they are unlike measurements, and every ``*_at_set`` value among them is
    measured at a fabricated moment 45 frames before the lift rather than at a set.
    Merging would buy sample by mixing in mismeasured pitches.
    """
    geom = spot_diff._delivery_series(df)
    info = {"verdict": verdict,
            "n_set_anchored": int((geom == "stretch").sum()),
            "n_fixed_lookback": int((geom == "windup").sum())}
    if verdict == "single_delivery":
        info["windup_stratum"] = "absent (arm throws only from the set)"
        info["dropped_fixed_lookback"] = info["n_fixed_lookback"]
        return df[geom == "stretch"].copy(), info
    info["windup_stratum"] = ("present" if verdict == "uses_both"
                              else "undetermined — not analysed as a delivery")
    return df, info


def load_family(run: Path, family: str) -> pd.DataFrame:
    if family == "position":
        return load_pitcher(run)
    df = load_trajectory(run)
    return to_dispersion(df, TRAJECTORY_FEATURES) if family == "consistency" else df


def run_arm(run: Path, family: str, args, cache):
    """One arm, one family. Returns (counts, result, tiers, leads) or None."""
    name = run.name.replace("_poc", "").replace("_rich", "").replace("_", " ").title()
    snapshot.assert_quiescent(run, allow_unready=args.allow_unready)
    df = load_family(run, family)
    n_banked = temporal.n_games_available(df)
    disc_g, val_g = temporal.temporal_split(df, args.n_disc, args.n_val, cache)
    keep = set(map(int, disc_g)) | set(map(int, val_g))
    sub = df[temporal.game_keys(df).isin(keep)].copy()

    verdict = delivery_verdict(run)
    strat_info = {"verdict": verdict}
    if getattr(args, "delivery_aware", False):
        before = len(sub)
        sub, strat_info = restrict_to_real_strata(sub, verdict)
        strat_info["n_pitches_dropped"] = before - len(sub)

    cues = spot_diff.CUES if family == "position" else TRAJECTORY_CUES
    original = spot_diff.CUES
    orig_delivery = spot_diff._delivery_series
    try:
        spot_diff.CUES = cues
        if getattr(args, "real_delivery", False):
            lab = pd.read_csv(run / "delivery_label.csv").set_index("play_id")["delivery_actual"]
            # Stratify on the validated delivery rather than the set-detection flag.
            # Patched rather than passed because analyse() reads the label itself in
            # several places, and one missed call site would silently mix strata.
            def _real(d, _m=lab):
                return d["play_id"].map(_m).fillna("unknown") if "play_id" in d.columns \
                    else pd.Series("unknown", index=d.index)
            spot_diff._delivery_series = _real
        with temporal.chronological(disc_g, val_g):
            res = spot_diff.analyse(sub, name)
    finally:
        spot_diff.CUES = original
        spot_diff._delivery_series = orig_delivery

    res["selection"] = temporal.describe(sub, disc_g, val_g, cache)
    res["stratification"] = strat_info
    res["sample"] = snapshot.fingerprint(run, "features.csv", sub)
    if getattr(args, "real_delivery", False):
        lab = pd.read_csv(run / "delivery_label.csv")
        sub = sub.merge(lab[["play_id", "delivery_actual"]], on="play_id", how="left")
        sub["_delivery"] = sub["delivery_actual"].fillna("unknown")
    else:
        sub["_delivery"] = spot_diff._delivery_series(sub)
    ordered = temporal.game_order(df, cache)  # every banked start, oldest -> newest

    tiers = []
    for diff in res.get("differences", []):
        t = tier_validated(sub, diff, disc_g, val_g, family, n_banked)
        t["arm"], t["cue"] = name, diff.get("cue")
        t["delivery"], t["contrast"] = diff.get("delivery"), diff.get("contrast")
        t["g_discovery"], t["g_validation"] = diff.get("g_discovery"), diff.get("g_holdout")
        t["q_discovery"], t["p_validation"] = diff.get("q_discovery"), diff.get("p_holdout")
        t["unit"], t["scouting_note"] = diff.get("unit"), diff.get("scouting_note")
        t["n_games"] = len(keep)
        t["n_games_banked"] = n_banked
        # Computed over every banked start, not just the nine analysed: the cap
        # limits what is analysed, not what exists.
        t["convergence"] = convergence(sub, diff["feature"], diff["pitch_a"],
                                       diff["pitch_b"], diff["delivery"], ordered)
        tiers.append(t)

    leads = []
    for ld in res.get("leads", []):
        t = tiering.assess(ld["col"], float("nan"), 0, 0, float("nan"), validated=False,
                           n_games_available=n_banked)
        t.update({"arm": name, "cue": ld["cue"], "delivery": ld["delivery"],
                  "contrast": ld["contrast"], "g_discovery": ld["g_discovery"],
                  "q_discovery": ld["q_discovery"], "unit": ld["unit"],
                  "failed_at": ld["failed_at"], "family": family,
                  "n_games": len(keep), "n_games_banked": n_banked})
        # Cell sizes, shown on every lead. A LOW lead resting on six pitches has to
        # say so: at this sample most cells are thin, and a lead without its n is
        # indistinguishable from one backed by real coverage.
        t.update(cell_sizes(sub, ld, disc_g, val_g))
        leads.append(t)

    sc = stage_counts(res)
    sc.update({"arm": name, "verdict": verdict, "games": len(keep), "banked": n_banked,
               "pitches": int(len(sub)),
               "precision": sum(1 for t in tiers if t["tier"] in
                                (tiering.TIER_HIGH, tiering.TIER_MEDIUM))})
    return sc, res, tiers, leads


def permutation_null(args, cache, n: int):
    """How many "survivors" the dispersion estimator manufactures by itself.

    An absolute deviation is taken from a median estimated on the same group, so a
    rare pitch type looks spuriously tight for purely arithmetic reasons, and that
    bias replicates across a game boundary exactly as a real cue would. Shuffling
    labels within game preserves group sizes and destroys every real association.
    """
    draws = []
    for seed in range(n):
        rng = np.random.default_rng(seed)
        acc = {"raw": 0, "fdr": 0, "validated": 0}
        for d in args.run_dir:
            run = Path(d)
            try:
                snapshot.assert_quiescent(run, allow_unready=args.allow_unready)
                f = to_dispersion(load_trajectory(run), TRAJECTORY_FEATURES)
                dg, vg = temporal.temporal_split(f, args.n_disc, args.n_val, cache)
            except (Exception, SystemExit):
                # The snapshot guard exits rather than raising. An arm it refuses
                # must drop out of the null exactly as it dropped out of the
                # observed run, or the two are not comparable.
                continue
            f = f[temporal.game_keys(f).isin(set(map(int, dg)) | set(map(int, vg)))]
            f = permute_labels(f, rng)
            oc = spot_diff.CUES
            try:
                spot_diff.CUES = TRAJECTORY_CUES
                with temporal.chronological(dg, vg):
                    r = spot_diff.analyse(f, run.name)
            finally:
                spot_diff.CUES = oc
            c = stage_counts(r)
            for k in acc:
                acc[k] += c[k]
        draws.append(acc)
        print(f"  seed {seed}: raw={acc['raw']:4d} fdr={acc['fdr']:3d} "
              f"validated={acc['validated']:3d}", flush=True)
    return draws


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, nargs="+")
    ap.add_argument("--n-disc", type=int, default=temporal.N_DISCOVERY_STARTS)
    ap.add_argument("--n-val", type=int, default=temporal.N_VALIDATION_STARTS)
    ap.add_argument("--families", nargs="+", default=list(FAMILIES), choices=FAMILIES)
    ap.add_argument("--permutations", type=int, default=0)
    ap.add_argument("--allow-unready", action="store_true")
    ap.add_argument("--delivery-aware", action="store_true",
                    help="drop strata that do not exist for an arm (stretch-only "
                         "arms lose their phantom windup stratum)")
    ap.add_argument("--real-delivery", action="store_true",
                    help="stratify on the validated delivery label from delivery.py "
                         "instead of the set-detection flag")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if args.allow_unready:
        print("!" * 100)
        print("PROVISIONAL — arms are still being tracked; this sample is still changing "
              "and nothing here can publish.")
        print("!" * 100)

    cache = game_dates.load_cache()
    rows, all_tiers, all_leads, skipped, details = [], [], [], [], []

    for family in args.families:
        print(f"\n### family: {family}", flush=True)
        for d in args.run_dir:
            run = Path(d)
            try:
                out = run_arm(run, family, args, cache)
            except SystemExit as e:
                skipped.append((run.name, family, "still being tracked"))
                print(f"  SKIP {run.name}: {e}", flush=True)
                continue
            except Exception as e:
                skipped.append((run.name, family, str(e)))
                continue
            sc, res, tiers, leads = out
            sc["family"] = family
            rows.append(sc)
            details.append(res)
            all_tiers += tiers
            all_leads += leads
            print(f"  {sc['arm']:20s} {sc['comparisons']:5d} comp  {sc['raw']:4d} raw  "
                  f"{sc['fdr']:3d} fdr  {sc['validated']:3d} valid", flush=True)

    # --------------------------------------------------------- consistency null
    null = None
    if args.permutations and "consistency" in args.families:
        print(f"\n{'=' * 100}\nPERMUTATION NULL — {args.permutations} replicates, "
              f"labels shuffled within game\n{'=' * 100}")
        draws = permutation_null(args, cache, args.permutations)
        obs = {k: sum(r[k] for r in rows if r["family"] == "consistency")
               for k in ("raw", "fdr", "validated")}
        null = {"observed": obs, "draws": draws, "summary": {}}
        for k in ("raw", "fdr", "validated"):
            vals = [x[k] for x in draws]
            ge = sum(1 for v in vals if v >= obs[k])
            null["summary"][k] = {"observed": obs[k], "null_min": min(vals),
                                  "null_max": max(vals), "null_mean": float(np.mean(vals)),
                                  "replicates_ge_observed": ge, "n": len(vals),
                                  "p": (ge + 1) / (len(vals) + 1)}
            print(f"  {k:10s} observed={obs[k]:4d}  null {min(vals)}-{max(vals)} "
                  f"(mean {np.mean(vals):.1f})  >= observed: {ge}/{len(vals)}  "
                  f"p={(ge + 1) / (len(vals) + 1):.3f}")

        # A dispersion finding inside its own null does not appear at any tier.
        v = null["summary"]["validated"]
        if v["p"] >= 0.05:
            n_drop = sum(1 for t in all_tiers if t.get("family") == "consistency")
            for t in all_tiers:
                if t.get("family") == "consistency":
                    t["excluded"] = "inside_permutation_null"
                    t["tier"] = None
            print(f"\n  -> consistency family sits INSIDE its permutation null "
                  f"(p={v['p']:.3f}); {n_drop} finding(s) withheld from every tier.")
        else:
            print(f"\n  -> consistency family is outside its permutation null "
                  f"(p={v['p']:.3f}); findings retained, label carries this caveat.")

    # ------------------------------------------------------------------ report
    print("\n" + "=" * 100)
    print(f"RECENCY PROTOCOL: discover on {args.n_disc} most recent starts | "
          f"validate on the next {args.n_val} going back")
    print("=" * 100)
    hdr = (f"{'Arm':20s} {'Family':12s} {'Gm':>3s} {'Bank':>5s} {'Pitch':>6s} {'Compar':>7s} "
           f"{'RAW':>5s} {'(chance)':>9s} {'FDR':>4s} {'Valid':>6s} {'Tiered':>7s}")
    print(hdr)
    print("-" * len(hdr))
    tot = dict(comparisons=0, raw=0, expected_by_chance=0.0, fdr=0, validated=0, precision=0)
    for r in sorted(rows, key=lambda x: (x["family"], -x["comparisons"])):
        print(f"{r['arm']:20s} {r['family']:12s} {r['games']:3d} {r['banked']:5d} {r['pitches']:6d} "
              f"{r['comparisons']:7d} {r['raw']:5d} {r['expected_by_chance']:9.1f} "
              f"{r['fdr']:4d} {r['validated']:6d} {r['precision']:7d}")
        for k in tot:
            tot[k] += r[k]
    print("-" * len(hdr))
    print(f"{'TOTAL':20s} {'':12s} {'':3s} {'':5s} {'':6s} {tot['comparisons']:7d} "
          f"{tot['raw']:5d} {tot['expected_by_chance']:9.1f} {tot['fdr']:4d} "
          f"{tot['validated']:6d} {tot['precision']:7d}")

    counts = tiering.summarise(all_tiers + all_leads)
    print(f"\nTIERS   high={counts['high']}  medium={counts['medium']}  "
          f"low={counts['low']}  excluded={counts['excluded']}")
    print(f"AT OR ABOVE 50% PRECISION (high + medium): {counts['at_or_above_50']}")

    shown = [t for t in all_tiers if t.get("tier") in (tiering.TIER_HIGH, tiering.TIER_MEDIUM)]
    if shown:
        print("\n" + "=" * 100)
        print("TIPS AT MEDIUM OR HIGH")
        print("=" * 100)
        for t in sorted(shown, key=lambda x: -(x.get("lift") or 0)):
            print(f"\n[{t['tier'].upper()}] {t['arm']} — {t['cue']} "
                  f"({t['contrast']}, {t['delivery']})")
            print(f"   precision {t['precision']:.3f} vs base rate {t['base_rate']:.3f} "
                  f"= lift {t['lift']:+.3f} (p={t.get('p_lift', float('nan')):.4f})")
            print(f"   stability: {t['stability']} ({t.get('n_games_banked')} starts banked)"
                  + ("  [WARRANTS DEEPENING]" if t.get("warrants_deepening") else ""))
            print(f"   fires {t['n_fire']}/{t.get('n_hold')} | accuracy "
                  f"{t.get('accuracy', float('nan')):.3f} vs majority "
                  f"{t.get('majority', float('nan')):.3f} | g_val={t['g_validation']}")
            print(f"   {t.get('scouting_note') or ''}")

    excluded = [t for t in all_tiers + all_leads if t.get("excluded")]
    if excluded:
        print(f"\nexcluded from every tier ({len(excluded)}):")
        for t in excluded[:20]:
            print(f"  {t.get('arm', '?'):20s} {t['feature']:28s} {t['excluded']}")

    if skipped:
        print("\nnot analysed:")
        for n, f, why in skipped:
            print(f"  {n} [{f}]: {why}")

    print("\ncolumn meanings")
    print("  RAW      : nominal differences at discovery, before any correction")
    print("  (chance) : how many RAW hits are expected with no signal at all")
    print("  FDR      : cleared Benjamini-Hochberg at q=0.10")
    print("  Valid    : also replicated, same direction, on the earlier starts")
    print("  Tiered   : also cleared lift over base rate -> labelled MEDIUM or HIGH")

    if args.out:
        Path(args.out).write_text(json.dumps({
            "protocol": {"n_discovery": args.n_disc, "n_validation": args.n_val,
                         "discovery": "most recent starts",
                         "validation": "the starts immediately before them",
                         "ordering": "calendar date via game_dates.json"},
            "provisional": bool(args.allow_unready),
            "thresholds": {"high_precision": tiering.HIGH_PRECISION,
                           "medium_precision": tiering.MEDIUM_PRECISION,
                           "min_lift": tiering.MIN_LIFT,
                           "lift_alpha": tiering.LIFT_ALPHA,
                           "min_fires": tiering.MIN_FIRES},
            "totals": tot, "tier_counts": counts, "per_arm": rows,
            "tiers": all_tiers, "leads": all_leads,
            "permutation_null": null, "not_analysed": skipped,
        }, indent=2, default=str))
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
