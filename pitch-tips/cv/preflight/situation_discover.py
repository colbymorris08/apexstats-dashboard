"""
Situation-specific discovery: compare pitch types *within* a situation.

All sliders with a runner on second against every other pitch type with a runner on
second, and so on across the prioritised situations in ``situations.py``. The
hypothesis is that pooling situations, which is what the analysis has done until
now, would wash out a tip that only exists when the pitcher has something to hold.

The correction family, chosen deliberately and stated
-----------------------------------------------------
**One BH-FDR family per arm**, spanning every situation, cue, pitch-type contrast
and window stratum tested on that arm.

The alternative — correcting inside each situation separately — would be p-hacking
by partition. Splitting one family of 900 tests into four families of 225 lowers
the bar for every test without adding any information, and would let a cue reach
the board purely because it was filed under "two strikes". The question a club is
actually asking is "does this arm tip anywhere, in any situation", so the arm is
the family, and adding a situation correctly makes it harder to find anything in
all the others. q stays at 0.10.

The pooled all-situations analysis is a separate, earlier family and is not merged
into this one; these are new tests, and they are counted as such.

Cell size is the binding constraint
-----------------------------------
A contrast is only attempted where both sides clear ``MIN_PER_GROUP`` in BOTH the
discovery and the validation half. At nine starts most cells do not, and those are
reported as **underpowered — not null**. A real tip in an underpowered cell would
be invisible to this analysis, and the honest denominator for any statement about
situational tipping is the testable count.

Stratification caveat
---------------------
The stratum here is window geometry, not delivery: see the corrected note in
``spot_diff.DELIVERY_COLS``. ``delivery_type``'s "windup" label means the set
detector failed, and its share is invariant to base state (Kelly 0.200 bases empty
versus 0.202 with a runner on second), so it cannot support a windup-versus-stretch
claim. It is still stratified on, because the two labels carry different window
spans and comparing across them would compare unlike measurements.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from preflight import game_dates, situations, snapshot, spot_diff, temporal, tiering
from preflight.publication_eval import evaluate
from preflight.spot_diff import (
    CUES,
    FDR_Q,
    HOLDOUT_ALPHA,
    MIN_G_DISCOVERY,
    MIN_G_HOLDOUT,
    MIN_PER_GROUP,
    hedges_g,
    load_pitcher,
)

STRATA = ("stretch", "windup")


def _vals(df, col, a, b):
    va = pd.to_numeric(df.loc[df["pitch_type"].astype(str) == a, col], errors="coerce").dropna()
    other = df["pitch_type"].astype(str) != a if b == "REST" else df["pitch_type"].astype(str) == b
    vb = pd.to_numeric(df.loc[other, col], errors="coerce").dropna()
    return va.to_numpy(), vb.to_numpy()


def contrasts(types: list[str]) -> list[tuple[str, str]]:
    out = [(a, "REST") for a in types]
    for i, a in enumerate(types):
        for b in types[i + 1:]:
            out.append((a, b))
    return out


def collect(df, disc_mask, val_mask, cue_cols) -> tuple[list[dict], dict]:
    """Every attempted contrast on this arm, with its uncorrected discovery p.

    Returns candidates plus the testable / underpowered / absent census, so the
    two can never disagree: the census is a by-product of the attempt, not a
    separate calculation.
    """
    cand, census = [], {"testable": 0, "underpowered": 0, "absent": 0}
    for skey in situations.SITUATIONS:
        m = situations.mask_for(df, skey)
        for stratum in STRATA:
            sel = m & (df["_delivery"] == stratum)
            if sel.sum() == 0:
                census["absent"] += 1
                continue
            d, v = df[sel & disc_mask], df[sel & val_mask]
            types = sorted(set(d["pitch_type"].astype(str)) | set(v["pitch_type"].astype(str)))
            for a, b in contrasts(types):
                for col in cue_cols:
                    da, db = _vals(d, col, a, b)
                    va, vb = _vals(v, col, a, b)
                    if min(len(da), len(db), len(va), len(vb)) < MIN_PER_GROUP:
                        census["underpowered"] += 1
                        continue
                    census["testable"] += 1
                    p = float(stats.ttest_ind(da, db, equal_var=False).pvalue)
                    if not np.isfinite(p):
                        continue
                    cand.append({
                        "situation": skey, "stratum": stratum, "col": col,
                        "a": a, "b": b, "p": p, "g": hedges_g(da, db),
                        "n_disc": [len(da), len(db)], "n_val": [len(va), len(vb)],
                    })
    return cand, census


def run_arm(run: Path, cache, args) -> dict[str, Any]:
    snapshot.assert_quiescent(run, allow_unready=args.allow_unready)
    df = load_pitcher(run)
    df["_delivery"] = spot_diff._delivery_series(df)
    n_banked = temporal.n_games_available(df)
    disc_g, val_g = temporal.temporal_split(df, args.n_disc, args.n_val, cache)
    keys = temporal.game_keys(df)
    df = df[keys.isin(set(map(int, disc_g)) | set(map(int, val_g)))].copy()
    keys = temporal.game_keys(df)
    disc_mask = keys.isin(set(map(int, disc_g)))
    val_mask = keys.isin(set(map(int, val_g)))

    cue_cols = [c for c in CUES if c in df.columns and not tiering.retraction_reason(c)]
    cand, census = collect(df, disc_mask, val_mask, cue_cols)

    # ---- one BH-FDR family for the whole arm --------------------------------
    raw = [c for c in cand if c["p"] < 0.05]
    fdr_pass: list[dict] = []
    if cand:
        order = np.argsort([c["p"] for c in cand])
        n = len(cand)
        thresh = 0.0
        for rank, idx in enumerate(order, start=1):
            if cand[idx]["p"] <= FDR_Q * rank / n:
                thresh = cand[idx]["p"]
        fdr_pass = [c for c in cand if c["p"] <= thresh and thresh > 0]

    # effect floor at discovery, then temporal validation
    validated, leads = [], []
    for c in fdr_pass:
        if abs(c["g"]) < MIN_G_DISCOVERY:
            continue
        sel = (situations.mask_for(df, c["situation"]) & (df["_delivery"] == c["stratum"]))
        d, v = df[sel & disc_mask], df[sel & val_mask]
        va, vb = _vals(v, c["col"], c["a"], c["b"])
        g_val = hedges_g(va, vb)
        p_val = float(stats.ttest_ind(va, vb, equal_var=False).pvalue)
        ok = (np.sign(g_val) == np.sign(c["g"]) and p_val < HOLDOUT_ALPHA
              and abs(g_val) >= MIN_G_HOLDOUT)
        rec = dict(c, g_val=g_val, p_val=p_val, n_games_banked=n_banked)
        if ok:
            pr = evaluate(d, v, c["col"], c["a"], c["b"]) or {}
            t = tiering.assess(c["col"], pr.get("precision", float("nan")),
                               pr.get("tp", 0), pr.get("n_fire", 0),
                               pr.get("base_rate", float("nan")), True, n_banked)
            t.update({k: pr.get(k) for k in ("accuracy", "majority", "n_hold")})
            rec["tier"] = t
            validated.append(rec)
        else:
            rec["tier"] = tiering.assess(c["col"], float("nan"), 0, 0, float("nan"),
                                         False, n_banked)
            leads.append(rec)

    return {
        "arm": run.name, "n_games_banked": n_banked,
        "n_games_analysed": len(set(map(int, disc_g)) | set(map(int, val_g))),
        "n_pitches": int(len(df)),
        "family": "one BH-FDR family per arm across all situations",
        "comparisons": len(cand), "census": census,
        "n_raw": len(raw), "n_fdr": len(fdr_pass),
        "n_validated": len(validated), "n_leads": len(leads),
        "validated": validated, "leads": leads,
        "purity": {k: situations.purity(df, k, df["_delivery"])
                   for k in situations.SITUATIONS},
        "sample": snapshot.fingerprint(run, "features.csv", df),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, nargs="+")
    ap.add_argument("--n-disc", type=int, default=temporal.N_DISCOVERY_STARTS)
    ap.add_argument("--n-val", type=int, default=temporal.N_VALIDATION_STARTS)
    ap.add_argument("--allow-unready", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    cache = game_dates.load_cache()
    arms, skipped = [], []
    for d in args.run_dir:
        try:
            arms.append(run_arm(Path(d), cache, args))
        except (Exception, SystemExit) as e:
            skipped.append((Path(d).name, str(e)[:90]))

    print("=" * 108)
    print("SITUATIONAL DISCOVERY — pitch types compared inside a situation")
    print(f"correction: one BH-FDR family per arm at q={FDR_Q}, spanning every "
          f"situation/cue/contrast/stratum")
    print("=" * 108)
    hdr = (f"{'Arm':22s} {'Bank':>4s} {'Cmp':>5s} {'Test':>5s} {'Underp':>6s} "
           f"{'RAW':>4s} {'chance':>6s} {'FDR':>4s} {'Valid':>5s} {'Tiered':>6s}")
    print(hdr); print("-" * len(hdr))
    tot = dict(comparisons=0, testable=0, underpowered=0, n_raw=0, n_fdr=0,
               n_validated=0, tiered=0)
    for a in arms:
        tiered = sum(1 for v in a["validated"]
                     if v["tier"]["tier"] in (tiering.TIER_HIGH, tiering.TIER_MEDIUM))
        print(f"{a['arm'][:22]:22s} {a['n_games_banked']:4d} {a['comparisons']:5d} "
              f"{a['census']['testable']:5d} {a['census']['underpowered']:6d} "
              f"{a['n_raw']:4d} {0.05 * a['comparisons']:6.1f} {a['n_fdr']:4d} {a['n_validated']:5d} {tiered:6d}")
        tot["comparisons"] += a["comparisons"]; tot["testable"] += a["census"]["testable"]
        tot["underpowered"] += a["census"]["underpowered"]; tot["n_raw"] += a["n_raw"]
        tot["n_fdr"] += a["n_fdr"]; tot["n_validated"] += a["n_validated"]
        tot["tiered"] += tiered
    print("-" * len(hdr))
    print(f"{'TOTAL':22s} {'':4s} {tot['comparisons']:5d} {tot['testable']:5d} "
          f"{tot['underpowered']:6d} {tot['n_raw']:4d} "
          f"{0.05 * tot['comparisons']:6.1f} {tot['n_fdr']:4d} "
          f"{tot['n_validated']:5d} {tot['tiered']:6d}")
    exp = 0.05 * tot["comparisons"]
    print(f"\nraw nominal hits {tot['n_raw']} against {exp:.1f} expected from pure "
          f"chance ({tot['n_raw'] / max(exp, 1e-9):.2f}x)")
    tot["expected_by_chance"] = exp
    frac = tot["testable"] / max(1, tot["testable"] + tot["underpowered"])
    print(f"\ntestable share of attempted cells: {frac:.1%} — the rest are "
          f"UNDERPOWERED, not null")

    print("\nrunner on second, per arm (the question underneath this request):")
    for a in arms:
        r2 = a["purity"].get("runner_on_2nd", {})
        cells = [c for c in a["validated"] + a["leads"] if c["situation"] == "runner_on_2nd"]
        print(f"  {a['arm'][:22]:22s} n={r2.get('n', 0):4d} pitches  "
              f"raw-surviving differences={len(cells)}")

    shown = [(a, v) for a in arms for v in a["validated"]
             if v["tier"]["tier"] in (tiering.TIER_HIGH, tiering.TIER_MEDIUM)]
    if shown:
        print("\n" + "=" * 108)
        print("SITUATIONAL TIPS AT MEDIUM OR HIGH")
        for a, v in shown:
            t = v["tier"]
            print(f"\n[{t['tier'].upper()}] {a['arm']} — {v['col']} | "
                  f"{v['a']} vs {v['b']} | {situations.SITUATIONS[v['situation']]['label']} "
                  f"| {v['stratum']}")
            print(f"   precision {t['precision']:.3f} vs base rate {t['base_rate']:.3f} "
                  f"= lift {t['lift']:+.3f} | fires {t['n_fire']} | "
                  f"g_val={v['g_val']:.3f} | stability={t['stability']}")
    else:
        print("\nno situational contrast reached MEDIUM or HIGH.")

    if skipped:
        print("\nnot analysed:")
        for n, w in skipped:
            print(f"  {n}: {w}")

    if args.out:
        Path(args.out).write_text(json.dumps(
            {"totals": tot, "arms": arms, "not_analysed": skipped}, indent=2, default=str))
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
