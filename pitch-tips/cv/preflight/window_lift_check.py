"""
Window/lift interaction check.

The lift-anchored primitives are only meaningful if peak leg lift actually falls
inside the actionable window (set -> hand break). If lift lands after the break,
the window is closing before the cue exists and every lift primitive on that
pitch is measured outside the region features are drawn from.

Reads ``primitives.csv``, which carries set_frame / lift_frame / break_frame per
pitch, so the check runs on the full sample with no extra tracking pass.

Verdict per pitch:
  inside        set_frame <= lift_frame <= break_frame
  lift_after    lift_frame > break_frame   (window closes too early)
  lift_before   lift_frame < set_frame     (lift detected in the pre-set noise)
  unassessable  any of the three frames missing
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def classify(row: pd.Series) -> str:
    s, l, b = row.get("set_frame"), row.get("lift_frame"), row.get("break_frame")
    if pd.isna(s) or pd.isna(l) or pd.isna(b):
        return "unassessable"
    if l > b:
        return "lift_after"
    if l < s:
        return "lift_before"
    return "inside"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    run_dir = Path(args.run_dir)

    prim = pd.read_csv(run_dir / "primitives.csv", dtype={"play_id": str})
    prim["verdict"] = prim.apply(classify, axis=1)
    n = len(prim)

    print(f"WINDOW/LIFT CHECK — {run_dir.name}, {n} pitches with primitives\n")
    counts = prim["verdict"].value_counts()
    for k in ("inside", "lift_after", "lift_before", "unassessable"):
        c = int(counts.get(k, 0))
        print(f"  {k:14s} {c:4d}  ({100.0 * c / n:5.1f}%)")

    ok = prim[prim.verdict == "inside"]
    assessable = prim[prim.verdict != "unassessable"]
    if len(assessable):
        print(
            f"\n  assessable: {len(assessable)}  |  inside-window rate among assessable: "
            f"{100.0 * len(ok) / len(assessable):.1f}%"
        )
    if len(ok):
        # how much room the window leaves around lift, in frames
        lead = (ok.lift_frame - ok.set_frame).astype(float)
        trail = (ok.break_frame - ok.lift_frame).astype(float)
        print(
            f"  margin (frames): set->lift median {lead.median():.0f} "
            f"(p10 {lead.quantile(0.10):.0f})   lift->break median {trail.median():.0f} "
            f"(p10 {trail.quantile(0.10):.0f})"
        )
    if "window_method" in prim.columns:
        print("\n  break-detection method mix:")
        for m, c in prim["window_method"].value_counts().items():
            print(f"    {m:24s} {c:4d}")
    if "lift_style" in prim.columns:
        print("\n  lift style mix:")
        for m, c in prim["lift_style"].value_counts().items():
            print(f"    {str(m):24s} {c:4d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
