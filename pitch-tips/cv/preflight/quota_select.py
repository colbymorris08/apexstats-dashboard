"""
Choose which pitches to fetch, by (situation x pitch type) quota.

Game-based acquisition tracked every pitch in the last N starts, which cost 345
clips per testable runner-on-second cell — Kelly's 2180 clips produced two such
cells, at 1090 clips each. Common cells were massively over-sampled while the
cells that carry the commercial question were starved. Savant addresses clips by
playId, so the game was never the necessary unit.

QUOTA ARITHMETIC
----------------
The tests need MIN_PER_GROUP=8 per group in both the discovery and validation
halves. The target is 10 usable windows per half, 20 per cell: a 10-total cell
splits 5/5 and is untestable by construction.

Only ~70% of tracked clips yield a valid window (measured 0.56-0.75 across six
arms, median 0.70), so landing 20 usable means fetching 29. Fetching 20 would
yield 14, splitting 7/7 — below the minimum on both sides, the same
untestable case reached by a different route. The quota absorbs the loss;
no minimum is touched.

DELIVERY IS CONFIRMED, NOT ASSUMED
----------------------------------
Cells are defined with delivery explicit, because situation and delivery are
correlated and pooling them hides near-empty cells. But the game feed only
carries a delivery *inferred* from the runner state, and that inference is known
to be wrong often enough to matter — plenty of arms work from the stretch with
the bases empty. So selection keys on the situation, which the feed states
factually, and the observed delivery is read from the tracked window afterwards.
For runner-on-second this is nearly lossless: the windup cells were empty
(0 of 52 testable, largest n=16) precisely because a runner on second means the
stretch.

SELECTION RULE (stated so the sample is reproducible)
-----------------------------------------------------
Walk the cell's games newest first; from each game take its pitches ordered by
play_id, at most MAX_PER_GAME; repeat over the games in that order until the
quota is met. Recency is preserved (newest games contribute first) while no game
can supply more than a quarter of the cell. No filtering, no convenience subset.
Recorded in the output.
"""
from __future__ import annotations

from collections import Counter

QUOTA_PER_HALF = 10
# Measured, not assumed. Woo's first quota run landed 19 usable windows in the
# runner-on-second sinker cell from 29 fetched — a 0.655 yield, one short of the
# 20 needed, so the cell failed on acquisition rather than on effect. Yield ran
# 0.63-0.70 across arms, so 20/0.63 = 32 carries the target through the low end.
# This is an acquisition parameter: no threshold, minimum, or gate moves.
FETCH_PER_CELL = 32
RECENCY_DAYS = 45
TOP_N_PITCH_TYPES = 5

# Game diversity is a hard requirement, not a side effect of taking recent
# pitches. Taking the 29 most recent pitches in a cell straight down the list
# concentrates them: Woo's runner-on-second four-seam cell filled entirely from
# 2 games, because he throws enough fastballs that two starts cover the quota.
# Two games splits 1-versus-1, so a single anomalous game becomes the whole
# validation half — the fragility that made Kelly's flare effect look real at 8
# games. Requiring 4 games puts at least 2 on each side of the split, so no one
# game can carry a result.
MIN_GAMES_PER_CELL = 4
# Follows from the above: no game may supply more than a quarter of a cell.
MAX_PER_GAME = -(-FETCH_PER_CELL // MIN_GAMES_PER_CELL)  # ceil

# Priority order. Each cell added multiplies acquisition cost and raises the FDR
# bar for every other cell, so this is deliberately short. Count states are
# omitted until the first two tiers complete.
SITUATION_PRIORITY = ("runner_on_2nd", "runner_on_base_no_2nd")


def situation_of(row: dict) -> str:
    if bool(row.get("on_2b")):
        return "runner_on_2nd"
    if bool(row.get("on_1b")) or bool(row.get("on_3b")):
        return "runner_on_base_no_2nd"
    return "bases_empty"


def within_recency(catalog: list[dict], recency_days: int = RECENCY_DAYS) -> list[dict]:
    """Keep pitches inside the recency window, measured back from the latest game."""
    dated = [r for r in catalog if r.get("game_date")]
    if not dated:
        return []
    import datetime as dt

    latest = max(dt.date.fromisoformat(str(r["game_date"])) for r in dated)
    cutoff = latest - dt.timedelta(days=recency_days)
    return [r for r in dated if dt.date.fromisoformat(str(r["game_date"])) >= cutoff]


def _take_spread(cell: list[dict], quota: int, max_per_game: int = MAX_PER_GAME) -> list[dict]:
    """
    Fill ``quota`` from ``cell`` without letting any one game dominate.

    Games are visited newest first so recency still drives the sample, but each
    pass takes at most ``max_per_game`` from a game before moving on.
    """
    by_game: dict[str, list[dict]] = {}
    for r in cell:
        by_game.setdefault(str(r["game_date"]), []).append(r)
    for rows in by_game.values():
        rows.sort(key=lambda r: str(r["play_id"]))
    order = sorted(by_game, reverse=True)

    out: list[dict] = []
    took: Counter = Counter()
    progressed = True
    while len(out) < quota and progressed:
        progressed = False
        for gd in order:
            if len(out) >= quota:
                break
            if took[gd] >= max_per_game:
                continue
            rows = by_game[gd]
            if took[gd] >= len(rows):
                continue
            out.append(rows[took[gd]])
            took[gd] += 1
            progressed = True
    return out


def select(
    catalog: list[dict],
    already_tracked: set[str] | None = None,
    fetch_per_cell: int = FETCH_PER_CELL,
    recency_days: int = RECENCY_DAYS,
    situations: tuple[str, ...] = SITUATION_PRIORITY,
    top_n_types: int = TOP_N_PITCH_TYPES,
) -> tuple[list[dict], dict]:
    """
    Return (pitches to fetch, report).

    ``already_tracked`` play ids count towards a cell's quota without being
    re-fetched, so an arm partially covered by earlier game-based tracking is
    topped up rather than redone.
    """
    already = already_tracked or set()
    recent = within_recency(catalog, recency_days)
    report: dict = {
        "selection_rule": (
            "games newest first by game_date; from each take pitches ordered by play_id, "
            f"at most {MAX_PER_GAME} per game per pass; repeat until quota met"
        ),
        "min_games_per_cell": MIN_GAMES_PER_CELL,
        "max_per_game": MAX_PER_GAME,
        "quota_per_half": QUOTA_PER_HALF,
        "fetch_per_cell": fetch_per_cell,
        "recency_days": recency_days,
        "n_catalog": len(catalog),
        "n_within_recency": len(recent),
        "cells": {},
    }
    if not recent:
        report["error"] = "no dated pitches in catalog"
        return [], report

    # Top pitch types by frequency inside the window, so the quota goes to the
    # pitches the arm actually throws rather than a fixed list.
    top_types = [t for t, _ in Counter(r["pitch_type"] for r in recent).most_common(top_n_types)]
    report["top_pitch_types"] = top_types

    selected: list[dict] = []
    chosen_ids: set[str] = set()
    for sit in situations:
        for ptype in top_types:
            cell = [r for r in recent if situation_of(r) == sit and r["pitch_type"] == ptype]
            take = _take_spread(cell, fetch_per_cell)
            have = [r for r in take if str(r["play_id"]) in already]
            need = [r for r in take if str(r["play_id"]) not in already]
            games = sorted({str(r["game_date"]) for r in take})
            report["cells"][f"{sit}|{ptype}"] = {
                "n_available": len(cell),
                "n_selected": len(take),
                "n_already_tracked": len(have),
                "n_to_fetch": len(need),
                "n_distinct_games": len(games),
                "game_dates": games,
                # A cell drawn from too few games cannot be split into disjoint
                # train and test game sets with either side standing on more than
                # one game. Refused rather than filled.
                "usable": len(games) >= MIN_GAMES_PER_CELL and len(take) >= 2 * QUOTA_PER_HALF,
                "games_per_split_side": len(games) // 2,
                "shortfall_reason": (
                    f"only {len(games)} distinct games, need {MIN_GAMES_PER_CELL}"
                    if len(games) < MIN_GAMES_PER_CELL
                    else f"only {len(take)} available in window, need {2 * QUOTA_PER_HALF}"
                    if len(take) < 2 * QUOTA_PER_HALF
                    else None
                ),
            }
            for r in need:
                if str(r["play_id"]) not in chosen_ids:
                    chosen_ids.add(str(r["play_id"]))
                    selected.append(r)

    report["n_to_fetch_total"] = len(selected)
    report["n_cells"] = len(report["cells"])
    report["n_cells_usable"] = sum(1 for c in report["cells"].values() if c["usable"])
    return selected, report
