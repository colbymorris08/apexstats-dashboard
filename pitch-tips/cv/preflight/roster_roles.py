"""
Roster + games-started based starter/reliever classification.

Replaces the old `role_guess` / pitch-volume heuristic. A pitcher is a STARTER
only if the MLB StatsAPI reports gamesStarted > 0 for the season; rotation order
within a team is ranked by games started (then innings, then pitch volume).

Team assignment comes from the CURRENT active roster, never from the stale
`team` field in runs/league_queue_*.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

UA = {"User-Agent": "PreflightCV/0.6"}
NL_WEST = ["ARI", "COL", "LAD", "SD", "SF"]
NL_WEST_IDS = {"ARI": 109, "COL": 115, "LAD": 119, "SD": 135, "SF": 137}
PITCHER_POS = {"P", "SP", "RP", "TWP"}
MIN_PITCHES = 100


def all_teams(season: int) -> dict[str, int]:
    js = requests.get(
        f"https://statsapi.mlb.com/api/v1/teams?sportId=1&season={season}",
        headers=UA,
        timeout=30,
    ).json()
    out: dict[str, int] = {}
    for t in js.get("teams") or []:
        abbr = t.get("abbreviation")
        if abbr and t.get("id"):
            out[abbr] = int(t["id"])
    return out


def roster_pitchers(
    team_ids: dict[str, int], season: int, roster_type: str = "40Man"
) -> tuple[dict[int, str], dict[int, str]]:
    """
    ({mlbam: team_abbr}, {mlbam: status}) for every pitcher on the given rosters.

    Defaults to 40Man rather than `active` because rotation regulars on the IL are
    missing from the active roster (e.g. ARI's Gallen / Soroka / Nelson) yet are
    exactly the arms a club wants scouted.
    """
    out: dict[int, str] = {}
    status: dict[int, str] = {}
    for abbr, tid in team_ids.items():
        try:
            js = requests.get(
                f"https://statsapi.mlb.com/api/v1/teams/{tid}/roster"
                f"?rosterType={roster_type}&season={season}",
                headers=UA,
                timeout=30,
            ).json()
        except Exception:
            continue
        for r in js.get("roster") or []:
            pos = r.get("position") or {}
            if pos.get("abbreviation") in PITCHER_POS or pos.get("type") == "Pitcher":
                pid = (r.get("person") or {}).get("id")
                if pid:
                    out[int(pid)] = abbr
                    status[int(pid)] = (r.get("status") or {}).get("description") or "Unknown"
    return out, status


def is_available(status: str) -> bool:
    """Active big-league arms rank ahead of IL / optioned arms."""
    return status == "Active"


def pitching_stats(ids: list[int], season: int, chunk: int = 60) -> dict[int, dict]:
    """{mlbam: {gs, ip, pitches}} from batched people hydrate."""
    out: dict[int, dict] = {}
    for i in range(0, len(ids), chunk):
        part = ids[i : i + chunk]
        url = (
            "https://statsapi.mlb.com/api/v1/people"
            f"?personIds={','.join(str(x) for x in part)}"
            f"&hydrate=stats(group=[pitching],type=[season],season={season})"
        )
        try:
            js = requests.get(url, headers=UA, timeout=45).json()
        except Exception:
            continue
        for p in js.get("people") or []:
            gs = 0
            ip = 0.0
            pitches = 0
            for s in p.get("stats") or []:
                for sp in s.get("splits") or []:
                    st = sp.get("stat") or {}
                    gs = max(gs, int(st.get("gamesStarted") or 0))
                    try:
                        ip = max(ip, float(st.get("inningsPitched") or 0))
                    except (TypeError, ValueError):
                        pass
                    pitches = max(
                        pitches,
                        int(st.get("numberOfPitches") or st.get("pitchesThrown") or 0),
                    )
            out[int(p["id"])] = {"gs": gs, "ip": ip, "pitches": pitches, "name": p.get("fullName")}
    return out


def classify(
    season: int,
    queue_rows: list[dict],
    team_ids: dict[str, int] | None = None,
    min_pitches: int = MIN_PITCHES,
) -> list[dict]:
    """
    Annotate trackable pitchers with current team + GS-based role.

    Returns rows that exist in the statcast queue (i.e. are actually trackable)
    and clear the pitch floor. `role` is "SP" when gamesStarted > 0 else "RP".
    """
    team_ids = team_ids or all_teams(season)
    roster, status = roster_pitchers(team_ids, season)
    stats = pitching_stats(sorted(roster), season)

    by_id = {int(r["mlbam"]): r for r in queue_rows}
    rows: list[dict] = []
    for pid, abbr in roster.items():
        q = by_id.get(pid)
        if not q:
            continue  # not in statcast queue -> not trackable
        st = stats.get(pid) or {}
        n_pitches = int(q.get("n_pitches") or 0) or int(st.get("pitches") or 0)
        if n_pitches < min_pitches:
            continue
        gs = int(st.get("gs") or 0)
        rows.append(
            {
                **q,
                "team": abbr,
                "n_pitches": n_pitches,
                "games_started": gs,
                "innings": st.get("ip") or 0.0,
                "status": status.get(pid) or "Unknown",
                "role": "SP" if gs > 0 else "RP",
            }
        )
    return rows


def _rotation_key(r: dict) -> tuple:
    return (
        0 if is_available(r.get("status") or "") else 1,
        -int(r.get("games_started") or 0),
        -float(r.get("innings") or 0.0),
        -int(r.get("n_pitches") or 0),
    )


def rotation_by_team(
    rows: list[dict], teams: list[str], top_n: int = 6, min_gs: int = 3
) -> list[dict]:
    """
    Per-team rotation: starters ranked active-first, then games started.

    `min_gs` filters out spot-start / opener noise; `top_n` allows for rotation
    churn (IL replacements) rather than assuming a clean five.
    """
    out: list[dict] = []
    for t in teams:
        arms = [
            r
            for r in rows
            if r["team"] == t and r["role"] == "SP" and int(r.get("games_started") or 0) >= min_gs
        ]
        arms.sort(key=_rotation_key)
        out += arms[:top_n]
    return out


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")


def display_name(statcast_name: str) -> str:
    if "," in statcast_name:
        last, first = [x.strip() for x in statcast_name.split(",", 1)]
        return f"{first} {last}"
    return statcast_name


def has_report(runs: Path, name: str) -> bool:
    return (runs / f"{slug(display_name(name))}_poc" / "report.json").is_file()
