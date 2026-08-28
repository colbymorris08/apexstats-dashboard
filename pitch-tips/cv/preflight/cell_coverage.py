"""
Which (situation x pitch type x delivery) cells are already testable, and which
would need fetching.

Acquisition is moving from "track every pitch in the last 6 starts" to "fill a
quota per cell". Before fetching anything, this reports what the arms already on
disk cover, because ~500 tracked pitches per arm buys a lot of the common cells
and the banked arms are a superset for many of them.

A cell is TESTABLE only if a chronological, game-disjoint split can give
QUOTA_PER_HALF usable windows on each side. That is the constraint a naive quota
filler breaks: 20 pitches taken from two games cannot be split into disjoint
train and test game sets, which is how a single game ends up named as both.

Selection rule within a cell, stated so the sample is reproducible: take every
pitch in the cell, ordered by game_date descending, up to quota. No filtering, no
convenience subset.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

# 10 usable per half. A 10-total cell splits 5/5, below the 8-per-group minimum
# on both sides, so it is untestable by construction; 10 per half is the smallest
# quota that yields a testable cell without touching any minimum.
QUOTA_PER_HALF = 10

# Recency: pitchers are told when they tip and correct it, so a cue from months
# back may be gone. A cell filled across five months is not measuring the same
# pitcher as one filled across three weeks. Cells that cannot fill inside the
# window are reported unfillable rather than silently reaching further back.
RECENCY_DAYS = 45


def _runner_situation(row) -> str:
    """Situation labels, ordered by where a tip can actually be relayed."""
    if bool(row["on_2b"]):
        return "runner_on_2nd"
    if bool(row["on_1b"]) or bool(row["on_3b"]):
        return "runner_on_base_no_2nd"
    return "bases_empty"


def split_ok(cell: pd.DataFrame, quota: int = QUOTA_PER_HALF) -> tuple[bool, dict]:
    """
    Can this cell be split chronologically into game-disjoint halves with
    ``quota`` rows on each side?

    Walks the game boundary from earliest forward and takes the first cut where
    both sides clear the quota. Splitting on a game boundary is what keeps the
    sets disjoint; splitting on row count would put one game on both sides.
    """
    games = sorted(cell["game_date"].dropna().unique())
    if len(games) < 2:
        return False, {"reason": f"only {len(games)} distinct game(s)", "games": len(games)}
    for i in range(1, len(games)):
        early, late = games[:i], games[i:]
        n_e = int(cell["game_date"].isin(early).sum())
        n_l = int(cell["game_date"].isin(late).sum())
        if n_e >= quota and n_l >= quota:
            return True, {
                "fit_games": early,
                "validate_games": late,
                "n_fit": n_e,
                "n_validate": n_l,
                "disjoint": set(early).isdisjoint(set(late)),
            }
    return False, {
        "reason": f"no game boundary gives {quota} on both sides",
        "games": len(games),
        "n_total": len(cell),
    }


def analyse(features: Path, recency_days: int = RECENCY_DAYS) -> dict:
    df = pd.read_csv(features)
    if "game_date" not in df.columns or df["game_date"].isna().all():
        return {"error": "no game_date; cannot order chronologically"}
    df = df.dropna(subset=["game_date", "delivery_type", "pitch_type"])
    latest = pd.to_datetime(df["game_date"]).max()
    cutoff = latest - pd.Timedelta(days=recency_days)
    recent = df[pd.to_datetime(df["game_date"]) >= cutoff]

    out = {
        "quota_per_half": QUOTA_PER_HALF,
        "recency_days": recency_days,
        "latest_game": str(latest.date()),
        "cutoff": str(cutoff.date()),
        "n_total_banked": len(df),
        "n_within_recency": len(recent),
        "cells": {},
    }
    recent = recent.copy()
    recent["situation"] = recent.apply(_runner_situation, axis=1)
    for (sit, delivery, ptype), cell in recent.groupby(
        ["situation", "delivery_type", "pitch_type"]
    ):
        ok, detail = split_ok(cell)
        out["cells"][f"{sit}|{delivery}|{ptype}"] = {
            "n": len(cell),
            "n_games": int(cell["game_date"].nunique()),
            "testable": ok,
            **detail,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=Path, default=Path(__file__).resolve().parents[2] / "runs")
    ap.add_argument("--recency-days", type=int, default=RECENCY_DAYS)
    ap.add_argument("--situation", default="runner_on_2nd")
    args = ap.parse_args()

    summary = {}
    for f in sorted(args.runs.glob("*_poc/features.csv")):
        arm = f.parent.name
        res = analyse(f, args.recency_days)
        if "error" in res:
            print(f"{arm}: {res['error']}")
            continue
        cells = res["cells"]
        want = {k: v for k, v in cells.items() if k.startswith(args.situation + "|")}
        testable = [k for k, v in want.items() if v["testable"]]
        print(
            f"{arm}: {res['n_within_recency']}/{res['n_total_banked']} pitches within "
            f"{args.recency_days}d (to {res['latest_game']}) | "
            f"{args.situation}: {len(testable)}/{len(want)} cells testable"
        )
        for k, v in sorted(want.items()):
            mark = "TESTABLE" if v["testable"] else "underpowered"
            extra = (
                f"fit={v['n_fit']} val={v['n_validate']}"
                if v["testable"]
                else v.get("reason", "")
            )
            print(f"    {k.split('|', 1)[1]:<18} n={v['n']:<4} games={v['n_games']:<3} {mark:<13} {extra}")
        summary[arm] = res
    (args.runs / "cell_coverage.json").write_text(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
