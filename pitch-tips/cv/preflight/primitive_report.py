"""
Preflight — sanity report for the lift-anchored tip primitives.

This does not mine tips and does not gate anything. Its only job is to answer
"is this primitive measuring something real, and does it separate pitch types?"
before any of it is allowed near the tip pipeline.

For each pitcher and primitive it prints the by-pitch-type means plus a
one-vs-rest standardised effect size (Cohen's d) for the best-separated pitch
type. Interpretation, deliberately conservative given per-pitcher sample sizes
of ~100 pitches:

    |d| < 0.2   noise
    0.2 - 0.5   weak
    0.5 - 0.8   moderate, worth mining
    > 0.8       strong

A primitive that is near zero everywhere is not implemented usefully. A
primitive with a consistent sign across several pitchers is the interesting
case, because that is a real mechanical tendency rather than one arm's quirk.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

from preflight.primitives import PRIMITIVES

MIN_TYPE_N = 8


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or len(b) < 3:
        return float("nan")
    s1, s2 = np.nanstd(a, ddof=1), np.nanstd(b, ddof=1)
    pooled = math.sqrt((s1**2 + s2**2) / 2)
    if not np.isfinite(pooled) or pooled < 1e-12:
        return float("nan")
    return float((np.nanmean(a) - np.nanmean(b)) / pooled)


def report_run(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    name = path.parent.name
    if "pitch_type" not in df.columns:
        print(f"{name}: no pitch_type join available")
        return pd.DataFrame()

    df = df[df["pitch_type"].notna()]
    counts = df["pitch_type"].value_counts()
    types = [t for t, n in counts.items() if n >= MIN_TYPE_N]
    print(f"\n=== {name}: {len(df)} usable pitches; types {dict(counts)}")
    if not types:
        print("  too few pitches per type to say anything")
        return pd.DataFrame()

    rows = []
    for prim in PRIMITIVES:
        if prim not in df.columns:
            continue
        vals = pd.to_numeric(df[prim], errors="coerce")
        cover = float(vals.notna().mean())
        if cover < 0.5:
            print(f"  {prim:26s} coverage {cover:.0%} — too sparse to evaluate")
            continue
        best = (None, 0.0)
        per_type = {}
        for t in types:
            a = vals[df["pitch_type"] == t].to_numpy(dtype=float)
            b = vals[df["pitch_type"] != t].to_numpy(dtype=float)
            per_type[t] = float(np.nanmean(a))
            d = cohens_d(a, b)
            if np.isfinite(d) and abs(d) > abs(best[1]):
                best = (t, d)
        spread = " ".join(f"{t}={per_type[t]:+.3f}" for t in types)
        print(
            f"  {prim:26s} cov {cover:.0%} | {spread} | best {best[0]} d={best[1]:+.2f}"
        )
        rows.append(
            {
                "pitcher": name,
                "primitive": prim,
                "coverage": cover,
                "best_type": best[0],
                "best_d": best[1],
                "sd": float(np.nanstd(vals)),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="+", required=True)
    args = ap.parse_args()

    allrows = []
    for r in args.runs:
        p = Path(r) / "primitives.csv"
        if not p.is_file():
            print(f"{r}: no primitives.csv")
            continue
        allrows.append(report_run(p))

    allrows = [d for d in allrows if not d.empty]
    if not allrows:
        return
    comb = pd.concat(allrows)
    print("\n\n=== Cross-pitcher summary (|d| for best-separated pitch type) ===")
    piv = comb.pivot_table(index="primitive", columns="pitcher", values="best_d")
    piv["mean_abs_d"] = piv.abs().mean(axis=1)
    piv["n_pitchers_ge_0.5"] = (piv.drop(columns=["mean_abs_d"]).abs() >= 0.5).sum(axis=1)
    print(piv.sort_values("mean_abs_d", ascending=False).round(2).to_string())


if __name__ == "__main__":
    main()
