"""
Build the league-wide, priority-ordered tracking plan.

Phases, executed in order by scale_nlwest --plan:
  A  nlw_rotation  NL West starting rotations (GS-ranked, active arms first)
  B  nlw_rest      remaining NL West pitchers (relievers + fringe starters)
  C  mlb           every other club's pitchers, starters before relievers

Starter/reliever comes from MLB StatsAPI gamesStarted (GS > 0), never from the
stale `role_guess` / pitch-volume heuristic in league_queue_*.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from preflight.roster_roles import (
    NL_WEST,
    NL_WEST_IDS,
    all_teams,
    classify,
    display_name,
    rotation_by_team,
)

ROOT = Path(__file__).resolve().parents[2]


def build(
    season: int,
    runs: Path,
    top_n: int,
    min_gs: int,
    min_pitches: int,
    active_only_phase_a: bool = True,
) -> dict:
    queue = json.loads((runs / f"league_queue_{season}.json").read_text())

    nlw_rows = classify(season, queue, team_ids=NL_WEST_IDS, min_pitches=min_pitches)
    rotation = rotation_by_team(nlw_rows, NL_WEST, top_n=top_n, min_gs=min_gs)

    # Phase A ships a board of every currently-ACTIVE starter first; rotation arms
    # on the IL are still tracked, just demoted to the head of phase B.
    il_rotation: list[dict] = []
    if active_only_phase_a:
        active = [r for r in rotation if (r.get("status") or "") == "Active"]
        il_rotation = [r for r in rotation if (r.get("status") or "") != "Active"]
        rotation = active

    rot_ids = {int(r["mlbam"]) for r in rotation}
    il_ids = {int(r["mlbam"]) for r in il_rotation}

    # Phase B: IL rotation arms first, then everything else on an NL West roster.
    nlw_other = [
        r for r in nlw_rows if int(r["mlbam"]) not in rot_ids and int(r["mlbam"]) not in il_ids
    ]
    nlw_other.sort(
        key=lambda r: (
            NL_WEST.index(r["team"]) if r["team"] in NL_WEST else 99,
            0 if r["role"] == "SP" else 1,
            -int(r.get("games_started") or 0),
            -int(r.get("n_pitches") or 0),
        )
    )
    il_rotation.sort(
        key=lambda r: (
            NL_WEST.index(r["team"]) if r["team"] in NL_WEST else 99,
            -int(r.get("games_started") or 0),
        )
    )
    nlw_rest = il_rotation + nlw_other

    # Phase C: the rest of MLB.
    teams = all_teams(season)
    rest_ids = {a: i for a, i in teams.items() if a not in NL_WEST_IDS}
    mlb_rows = classify(season, queue, team_ids=rest_ids, min_pitches=min_pitches)
    seen = rot_ids | il_ids | {int(r["mlbam"]) for r in nlw_other}
    mlb_rows = [r for r in mlb_rows if int(r["mlbam"]) not in seen]
    mlb_rows.sort(
        key=lambda r: (
            r["team"],
            0 if r["role"] == "SP" else 1,
            -int(r.get("games_started") or 0),
            -int(r.get("n_pitches") or 0),
        )
    )

    def stamp(rows: list[dict], phase: str) -> list[dict]:
        out = []
        for r in rows:
            out.append({**r, "phase": phase, "display": display_name(r["name"])})
        return out

    plan_rows = (
        stamp(rotation, "nlw_rotation") + stamp(nlw_rest, "nlw_rest") + stamp(mlb_rows, "mlb")
    )
    return {
        "season": season,
        "criterion": "MLB StatsAPI gamesStarted>0 on 40-man roster; min pitches "
        f"{min_pitches}; rotation top {top_n} per club (GS>={min_gs}), active before IL",
        "phases": ["nlw_rotation", "nlw_rest", "mlb"],
        "counts": {
            "nlw_rotation": len(rotation),
            "nlw_rest": len(nlw_rest),
            "mlb": len(mlb_rows),
            "total": len(plan_rows),
        },
        "rows": plan_rows,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--runs", type=Path, default=ROOT / "runs")
    p.add_argument("--top-n", type=int, default=6)
    p.add_argument("--min-gs", type=int, default=3)
    p.add_argument("--min-pitches", type=int, default=100)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    plan = build(args.season, args.runs, args.top_n, args.min_gs, args.min_pitches)
    out = args.out or (args.runs / f"league_plan_{args.season}.json")
    out.write_text(json.dumps(plan, indent=2))
    print(json.dumps(plan["counts"], indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
