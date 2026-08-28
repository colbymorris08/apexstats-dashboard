"""
Scale Preflight across MLB pitchers with >100 pitches this season — team by team.

Writes pitch-tips/data/progress.json for the Live scale page.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from preflight.merge_demo import main as merge_demo_main  # noqa: E402
from preflight.provenance import validated_counts  # noqa: E402
from preflight.run_poc import run_poc  # noqa: E402

UA = {"User-Agent": "PreflightCV/0.5"}
SITE_DATA = Path(__file__).resolve().parents[2] / "data"
PROGRESS_PATH = SITE_DATA / "progress.json"


def pitchers_over_n(season: int, min_pitches: int = 100) -> list[dict]:
    from pybaseball import statcast

    start, end = f"{season}-03-01", f"{season}-11-30"
    print(f"Loading Statcast {start}→{end} (≥{min_pitches} pitches)…")
    df = statcast(start, end)
    if df is None or df.empty:
        raise RuntimeError("Empty Statcast pull")
    g = (
        df.dropna(subset=["pitcher", "player_name"])
        .groupby(["pitcher", "player_name"], as_index=False)
        .size()
        .rename(columns={"size": "n_pitches"})
    )
    g = g[g["n_pitches"] >= min_pitches].sort_values("n_pitches", ascending=False)
    return [
        {"mlbam": int(r.pitcher), "name": str(r.player_name), "n_pitches": int(r.n_pitches)}
        for r in g.itertuples()
    ]


def display_name(statcast_name: str) -> str:
    if "," in statcast_name:
        last, first = [x.strip() for x in statcast_name.split(",", 1)]
        return f"{first} {last}"
    return statcast_name


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")


def team_abbr(mlbam: int, cache: dict) -> str:
    if mlbam in cache:
        return cache[mlbam]
    try:
        js = requests.get(
            f"https://statsapi.mlb.com/api/v1/people/{mlbam}?hydrate=currentTeam",
            headers=UA,
            timeout=20,
        ).json()
        people = js.get("people") or []
        abbr = ((people[0].get("currentTeam") or {}).get("abbreviation")) if people else None
        cache[mlbam] = abbr or "FA"
    except Exception:
        cache[mlbam] = "UNK"
    return cache[mlbam]


def write_progress(payload: dict) -> None:
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text(json.dumps(payload, indent=2))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--min-pitches", type=int, default=100)
    p.add_argument("--games", type=int, default=5)
    p.add_argument("--runs", type=Path, default=Path(__file__).resolve().parents[2] / "runs")
    p.add_argument("--queue", type=Path, default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--only-teams", nargs="*", default=None)
    p.add_argument("--sec-per-pitch", type=float, default=7.0, help="For ETA")
    p.add_argument("--merge-demo", action="store_true")
    p.add_argument("--est-pitches-per-arm", type=int, default=90)
    args = p.parse_args()

    args.runs.mkdir(parents=True, exist_ok=True)
    queue_path = args.queue or (args.runs / f"league_queue_{args.season}.json")

    if queue_path.is_file():
        queue = json.loads(queue_path.read_text())
    else:
        queue = pitchers_over_n(args.season, args.min_pitches)
        queue_path.write_text(json.dumps(queue, indent=2))

    team_cache: dict[int, str] = {}
    for row in queue:
        row["display"] = display_name(row["name"])
        row["team"] = team_abbr(int(row["mlbam"]), team_cache)

    # Team-by-team order
    queue.sort(key=lambda r: (r.get("team") or "ZZZ", -r["n_pitches"], r["display"]))
    if args.only_teams:
        want = {t.upper() for t in args.only_teams}
        queue = [r for r in queue if (r.get("team") or "").upper() in want]
    if args.limit:
        queue = queue[: args.limit]

    progress_path = args.runs / f"league_progress_{args.season}.json"
    progress = json.loads(progress_path.read_text()) if progress_path.is_file() else {"done": {}, "failed": {}}

    by_team_q: dict[str, int] = defaultdict(int)
    for r in queue:
        by_team_q[r.get("team") or "UNK"] += 1

    total_est_pitches = len(queue) * args.est_pitches_per_arm
    eta_h = round((total_est_pitches * args.sec_per_pitch) / 3600, 1)

    def snapshot(current=None, status="running"):
        by_team = {}
        for t, nq in by_team_q.items():
            by_team[t] = {
                "queued": nq,
                "done": 0,
                "pitcher_tips": 0,
                "catcher_tips": 0,
            }
        for row in (progress.get("done") or {}).values():
            t = row.get("team") or "UNK"
            by_team.setdefault(t, {"queued": 0, "done": 0, "pitcher_tips": 0, "catcher_tips": 0})
            by_team[t]["done"] += 1
            by_team[t]["pitcher_tips"] += int(row.get("tips_ge_75") or 0)
            by_team[t]["catcher_tips"] += int(row.get("catcher_tips") or 0)
        payload = {
            "status": status,
            "season": args.season,
            "games": args.games,
            "queue_total": len(queue),
            "remaining": max(0, len(queue) - len(progress.get("done") or {})),
            "sec_per_pitch": args.sec_per_pitch,
            "eta_hours": eta_h,
            "est_total_pitches": total_est_pitches,
            "current": current,
            "done": progress.get("done") or {},
            "failed": progress.get("failed") or {},
            "by_team": by_team,
            "totals": {
                "pitcher_tips": sum(int(x.get("tips_ge_75") or 0) for x in (progress.get("done") or {}).values()),
                "catcher_tips": sum(int(x.get("catcher_tips") or 0) for x in (progress.get("done") or {}).values()),
            },
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        write_progress(payload)
        progress_path.write_text(json.dumps(progress, indent=2))

    snapshot(status="starting")
    print(f"League scale: {len(queue)} pitchers · ~{total_est_pitches} pitches · ETA ~{eta_h}h @ {args.sec_per_pitch}s/pitch")
    print(f"Live page: pitch-tips/progress.html ← {PROGRESS_PATH}")

    for i, row in enumerate(queue, 1):
        display = row["display"]
        key = str(row["mlbam"])
        team = row.get("team") or "UNK"
        if key in progress.get("done", {}) and int(progress["done"][key].get("n_tracked") or 0) >= 15:
            print(f"[{i}/{len(queue)}] skip {team} {display}")
            continue
        work = args.runs / f"{slug(display)}_poc"
        snapshot(
            current={"name": display, "team": team, "message": f"[{i}/{len(queue)}] last {args.games} games…"},
            status="running",
        )
        print(f"\n[{i}/{len(queue)}] ===== {team} · {display} ({row['n_pitches']} season pitches) =====")
        try:
            rep = run_poc(
                display,
                args.season,
                sample=9999,
                work=work,
                games=args.games,
                mlbam=int(row["mlbam"]),
            )
            progress.setdefault("done", {})[key] = {
                "name": display,
                "team": team,
                "n_tracked": rep.get("n_tracked"),
                "holdout": rep.get("holdout_accuracy"),
                "tips_ge_75": validated_counts(work)[0],
                "catcher_tips": validated_counts(work)[1],
                "legacy_tips_ge_75": (rep.get("situation_coverage") or {}).get("n_tips_ge_floor"),
                "work": str(work),
            }
            if args.merge_demo:
                merge_demo_main()
            snapshot(
                current={"name": display, "team": team, "message": "done"},
                status="running",
            )
        except Exception as e:
            print(f"FAIL {display}: {e}")
            progress.setdefault("failed", {})[key] = {"name": display, "team": team, "error": str(e)}
            snapshot(current={"name": display, "team": team, "message": f"failed: {e}"}, status="running")
        time.sleep(0.3)

    snapshot(current=None, status="complete")
    print("League scale complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
