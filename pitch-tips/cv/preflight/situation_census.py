"""
What is testable inside each situation, before any statistics are run.

This exists because a situational grid is mostly empty at nine starts, and a grid
of empty cells presented as "we tested everything" would be misleading. The
distinction the census draws, per cell:

``testable``     >= MIN_PER_GROUP pitches on both sides of the contrast in BOTH the
                 discovery and the validation half. Only these can produce a
                 result of any kind.
``underpowered`` The pitch type occurs in the situation but too thinly to test. A
                 real tip here would be invisible to us. This is not evidence of
                 no tip.
``absent``       The pitch type never appears in the situation at all. Nothing to
                 say either way.

Reporting the three separately is the whole point: "no difference found" means
something only for the testable cells, and the honest denominator for any claim
about situational tipping is the testable count, not the size of the grid.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from preflight import game_dates, situations, spot_diff, temporal
from preflight.spot_diff import MIN_PER_GROUP, load_pitcher

STRATA = ("stretch", "windup")


def census_arm(run: Path, cache, n_disc: int, n_val: int) -> dict:
    df = load_pitcher(run)
    df["_delivery"] = spot_diff._delivery_series(df)
    n_banked = temporal.n_games_available(df)
    disc_g, val_g = temporal.temporal_split(df, n_disc, n_val, cache)
    keys = temporal.game_keys(df)
    df = df[keys.isin(set(map(int, disc_g)) | set(map(int, val_g)))].copy()
    keys = temporal.game_keys(df)
    in_disc = keys.isin(set(map(int, disc_g)))
    in_val = keys.isin(set(map(int, val_g)))

    out = {"arm": run.name, "n_games_banked": n_banked,
           "n_games_analysed": len(set(map(int, disc_g)) | set(map(int, val_g))),
           "n_pitches": int(len(df)), "situations": {}}

    for key, spec in situations.SITUATIONS.items():
        m = situations.mask_for(df, key)
        ent = {"label": spec["label"], "why": spec["why"],
               "n_pitches": int(m.sum()),
               "purity": situations.purity(df, key, df["_delivery"]),
               "strata": {}}
        for stratum in STRATA:
            sel = m & (df["_delivery"] == stratum)
            sub = df[sel]
            types = sorted(sub["pitch_type"].astype(str).dropna().unique())
            cells = {}
            for t in types:
                is_t = sub["pitch_type"].astype(str) == t
                d, v = sel & in_disc, sel & in_val
                nd_a = int((is_t & in_disc[sub.index]).sum())
                nd_b = int(((~is_t) & in_disc[sub.index]).sum())
                nv_a = int((is_t & in_val[sub.index]).sum())
                nv_b = int(((~is_t) & in_val[sub.index]).sum())
                total = nd_a + nv_a
                if total == 0:
                    state = "absent"
                elif min(nd_a, nd_b, nv_a, nv_b) >= MIN_PER_GROUP:
                    state = "testable"
                else:
                    state = "underpowered"
                cells[t] = {"state": state, "n_total": total,
                            "disc": [nd_a, nd_b], "val": [nv_a, nv_b]}
            ent["strata"][stratum] = {
                "n_pitches": int(sel.sum()),
                "cells": cells,
                "n_testable": sum(1 for c in cells.values() if c["state"] == "testable"),
                "n_underpowered": sum(1 for c in cells.values() if c["state"] == "underpowered"),
            }
        ent["n_testable"] = sum(s["n_testable"] for s in ent["strata"].values())
        ent["n_underpowered"] = sum(s["n_underpowered"] for s in ent["strata"].values())
        out["situations"][key] = ent
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True, nargs="+")
    ap.add_argument("--n-disc", type=int, default=temporal.N_DISCOVERY_STARTS)
    ap.add_argument("--n-val", type=int, default=temporal.N_VALIDATION_STARTS)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    cache = game_dates.load_cache()
    arms = []
    for d in args.run_dir:
        try:
            arms.append(census_arm(Path(d), cache, args.n_disc, args.n_val))
        except Exception as e:
            print(f"  skip {Path(d).name}: {e}")

    hdr = (f"{'Arm':20s} {'Bank':>4s} {'Situation':16s} {'N':>5s} {'%str':>5s} "
           f"{'testable':>8s} {'underpow':>8s}")
    print(hdr); print("-" * len(hdr))
    for a in arms:
        for key, e in a["situations"].items():
            ps = e["purity"]["share_stretch"]
            print(f"{a['arm'][:20]:20s} {a['n_games_banked']:4d} {key:16s} "
                  f"{e['n_pitches']:5d} {('-' if ps is None else f'{ps:.2f}'):>5s} "
                  f"{e['n_testable']:8d} {e['n_underpowered']:8d}")

    print("\ntestable cells by situation (summed over arms and strata):")
    for key in situations.SITUATIONS:
        t = sum(a["situations"][key]["n_testable"] for a in arms if key in a["situations"])
        u = sum(a["situations"][key]["n_underpowered"] for a in arms if key in a["situations"])
        print(f"  {key:16s} testable={t:3d}  underpowered={u:3d}")

    if args.out:
        Path(args.out).write_text(json.dumps(arms, indent=2, default=str))
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
