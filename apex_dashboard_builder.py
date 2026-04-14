#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
import urllib.parse

import pandas as pd
import requests

SOURCE_XLSX = Path("/Users/colbymorris/Downloads/Apex Client List July 2024.xlsx")
OUT_JSON = Path("/Users/colbymorris/apexstats/apex_dashboard_data.json")
SEASON = date.today().year
API = "https://statsapi.mlb.com/api/v1"

PITCHER_POS = {"RHP", "LHP", "SP", "RP", "P"}
AMATEUR_TOKENS = ("NCAA", "COLLEGE", "JUCO", "HS", "HIGH SCHOOL")
TEAM_CATALOG: list[dict[str, Any]] | None = None


@dataclass
class Client:
    name: str
    position: str
    level: str
    league: str
    minor_affiliate: str
    major_affiliate: str
    agent: str
    agent_last: str
    is_amateur: bool


def _req_json(url: str) -> dict[str, Any]:
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    return r.json()


def _safe_int(x: Any) -> int | None:
    try:
        return int(x)
    except Exception:
        return None


def _parse_name(name: str) -> str:
    # Spreadsheet mostly uses "Last, First"
    if "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
        return f"{first} {last}".strip()
    return name.strip()


def _agent_last(agent: str) -> str:
    s = (agent or "").strip()
    if not s:
        return ""
    if "," in s:
        return s.split(",", 1)[0].strip()
    parts = s.split()
    return parts[-1] if parts else ""


def get_team_catalog() -> list[dict[str, Any]]:
    global TEAM_CATALOG
    if TEAM_CATALOG is not None:
        return TEAM_CATALOG
    teams: list[dict[str, Any]] = []
    for sport_id in [1, 11, 12, 13, 14, 15, 16, 17]:
        url = f"{API}/teams?" + urllib.parse.urlencode({"sportId": sport_id, "season": SEASON})
        try:
            js = _req_json(url)
        except Exception:
            continue
        teams.extend(js.get("teams") or [])
    TEAM_CATALOG = teams
    return teams


def pick_current_team_name(c: Client) -> str:
    if c.level.upper() == "MLB":
        return c.major_affiliate or c.minor_affiliate or ""
    return c.minor_affiliate or c.major_affiliate or ""


def fallback_schedule_url(team_name: str, level: str) -> str:
    if not team_name:
        return ""
    if (level or "").upper() == "MLB":
        team_slug = _slug(team_name.replace("MLB", "").strip())
        return f"https://www.mlb.com/{team_slug}/schedule"
    return f"https://www.milb.com/{_slug(team_name)}/schedule"


def lookup_team_by_name(team_name: str) -> dict[str, Any] | None:
    q = (team_name or "").strip().lower()
    if not q:
        return None
    teams = get_team_catalog()
    exact = []
    contains = []
    for t in teams:
        name = str(t.get("name", "")).lower()
        tname = str(t.get("teamName", "")).lower()
        lname = str(t.get("locationName", "")).lower()
        full = f"{lname} {tname}".strip()
        if q == name or q == full:
            exact.append(t)
        elif q in name or q in full:
            contains.append(t)
    if exact:
        return exact[0]
    if contains:
        return contains[0]
    return None


def load_clients(path: Path) -> list[Client]:
    df = pd.read_excel(path, sheet_name="Sorted By League")
    out: list[Client] = []
    for _, r in df.iterrows():
        raw_name = str(r.get("Name", "")).strip()
        if not raw_name or raw_name.lower() == "nan":
            continue
        level = str(r.get("Level", "")).strip()
        league = str(r.get("League", "")).strip()
        position = str(r.get("Position", "")).strip().upper()
        raw_agent = r.get("Agent", "")
        agent = "" if pd.isna(raw_agent) else str(raw_agent).strip()
        level_upper = level.upper()
        league_upper = league.upper()
        is_amateur = any(t in level_upper for t in AMATEUR_TOKENS) or any(
            t in league_upper for t in AMATEUR_TOKENS
        )
        out.append(
            Client(
                name=_parse_name(raw_name),
                position=position,
                level=level,
                league=league,
                minor_affiliate=str(r.get("Minor League Affiliate", "")).strip(),
                major_affiliate=str(r.get("Major League Affiliate", "")).strip(),
                agent=agent,
                agent_last=_agent_last(agent),
                is_amateur=is_amateur,
            )
        )
    return out


def lookup_player(name: str) -> dict[str, Any] | None:
    url = f"{API}/people/search?" + urllib.parse.urlencode({"names": name})
    js = _req_json(url)
    people = js.get("people") or []
    return people[0] if people else None


def stat_group(position: str) -> str:
    return "pitching" if position.upper() in PITCHER_POS else "hitting"


def is_pitcher(position: str) -> bool:
    return position.upper() in PITCHER_POS


def sport_id_for_level(level: str) -> int:
    return 1 if (level or "").upper() == "MLB" else 11


def fetch_player_stats(
    player_id: int,
    group: str,
    stat_type: str,
    sport_id: int,
    start: date | None = None,
    end: date | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"stats": stat_type, "group": group, "season": SEASON, "sportId": sport_id}
    if sport_id == 1:
        params["gameType"] = "R"
    if start and end:
        params["startDate"] = start.isoformat()
        params["endDate"] = end.isoformat()
    url = f"{API}/people/{player_id}/stats?" + urllib.parse.urlencode(params)
    js = _req_json(url)
    splits = (js.get("stats") or [{}])[0].get("splits") or []
    return splits[0].get("stat", {}) if splits else {}


def fetch_latest_team_from_gamelog(player_id: int, group: str, sport_id: int) -> dict[str, Any]:
    params: dict[str, Any] = {"stats": "gameLog", "group": group, "season": SEASON, "sportId": sport_id}
    if sport_id == 1:
        params["gameType"] = "R"
    url = f"{API}/people/{player_id}/stats?" + urllib.parse.urlencode(params)
    js = _req_json(url)
    splits = (js.get("stats") or [{}])[0].get("splits") or []
    if not splits:
        return {}
    latest = sorted(splits, key=lambda s: s.get("date", ""), reverse=True)[0]
    team = latest.get("team") or {}
    return {
        "team_id": _safe_int(team.get("id")),
        "team_name": team.get("name", ""),
        "last_game_date": latest.get("date", ""),
    }


def fetch_last_night_from_gamelog(player_id: int, group: str, sport_id: int, target_day: date) -> dict[str, Any]:
    params: dict[str, Any] = {"stats": "gameLog", "group": group, "season": SEASON, "sportId": sport_id}
    if sport_id == 1:
        params["gameType"] = "R"
    url = f"{API}/people/{player_id}/stats?" + urllib.parse.urlencode(params)
    js = _req_json(url)
    splits = (js.get("stats") or [{}])[0].get("splits") or []
    day = target_day.isoformat()
    # If multiple games in one day, sum numeric fields.
    same_day = [s for s in splits if s.get("date") == day]
    if not same_day:
        return {}
    merged: dict[str, Any] = {}
    for s in same_day:
        st = s.get("stat") or {}
        for k, v in st.items():
            try:
                fv = float(v)
            except Exception:
                if k not in merged:
                    merged[k] = v
                continue
            merged[k] = float(merged.get(k, 0)) + fv
    return merged


def fetch_team_schedule(team_id: int, weeks: int = 4) -> list[dict[str, Any]]:
    start = date.today()
    end = start + timedelta(days=7 * weeks)
    games: list[dict[str, Any]] = []
    # Try MLB + MiLB sport IDs so each client pulls from their team context.
    for sport_id in [1, 11, 12, 13, 14, 15, 16, 17]:
        params = {
            "sportId": sport_id,
            "teamId": team_id,
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "hydrate": "venue(location),team",
        }
        url = f"{API}/schedule?" + urllib.parse.urlencode(params)
        try:
            js = _req_json(url)
        except Exception:
            continue
        for d in js.get("dates", []):
            for g in d.get("games", []):
                games.append(g)
        if games:
            break
    # Build next 4 series by contiguous opponent-homeaway
    series: list[dict[str, Any]] = []
    curr: dict[str, Any] | None = None
    for g in sorted(games, key=lambda x: x.get("gameDate", "")):
        teams = g.get("teams", {})
        home = teams.get("home", {}).get("team", {})
        away = teams.get("away", {}).get("team", {})
        is_home = _safe_int(home.get("id")) == team_id
        opp = away if is_home else home
        venue = g.get("venue", {})
        game_dt = g.get("gameDate", "")
        key = f"{opp.get('id')}|{'H' if is_home else 'A'}|{venue.get('id')}"
        if curr is None or curr["key"] != key:
            if curr is not None:
                series.append(curr)
            curr = {
                "key": key,
                "opponent": opp.get("name", ""),
                "home_away": "Home" if is_home else "Away",
                "venue": venue.get("name", ""),
                "location": (venue.get("location", {}) or {}).get("city", ""),
                "start_date": game_dt[:10],
                "end_date": game_dt[:10],
            }
        else:
            curr["end_date"] = game_dt[:10]
    if curr is not None:
        series.append(curr)
    for s in series:
        s.pop("key", None)
        code = guess_airport_code(s.get("location", ""))
        s["nearest_airport_code"] = code
    return series[:4]


AIRPORT_BY_CITY = {
    "Albuquerque": "ABQ",
    "Atlanta": "ATL",
    "Austin": "AUS",
    "Boston": "BOS",
    "Charlotte": "CLT",
    "Chicago": "ORD",
    "Cincinnati": "CVG",
    "Cleveland": "CLE",
    "Colorado Springs": "COS",
    "Dallas": "DFW",
    "Denver": "DEN",
    "Des Moines": "DSM",
    "Detroit": "DTW",
    "Houston": "IAH",
    "Indianapolis": "IND",
    "Jacksonville": "JAX",
    "Kansas City": "MCI",
    "Las Vegas": "LAS",
    "Los Angeles": "LAX",
    "Memphis": "MEM",
    "Miami": "MIA",
    "Minneapolis": "MSP",
    "Nashville": "BNA",
    "New York": "JFK",
    "Oklahoma City": "OKC",
    "Orlando": "MCO",
    "Philadelphia": "PHL",
    "Phoenix": "PHX",
    "Pittsburgh": "PIT",
    "Portland": "PDX",
    "Raleigh": "RDU",
    "Richmond": "RIC",
    "Sacramento": "SMF",
    "Salt Lake City": "SLC",
    "San Antonio": "SAT",
    "San Diego": "SAN",
    "San Francisco": "SFO",
    "Seattle": "SEA",
    "St. Louis": "STL",
    "Tampa": "TPA",
    "Toledo": "DTW",
    "Washington": "DCA",
}


def guess_airport_code(city: str) -> str:
    c = (city or "").strip()
    if not c:
        return ""
    # exact then prefix heuristics
    if c in AIRPORT_BY_CITY:
        return AIRPORT_BY_CITY[c]
    for k, v in AIRPORT_BY_CITY.items():
        if c.lower().startswith(k.lower()):
            return v
    return ""


def to_number(v: Any) -> float | int | None:
    try:
        if v is None or v == "":
            return None
        x = float(v)
        if x.is_integer():
            return int(x)
        return round(x, 3)
    except Exception:
        return None


def _slug(s: str) -> str:
    return (
        (s or "")
        .strip()
        .lower()
        .replace("&", "and")
        .replace(".", "")
        .replace("'", "")
        .replace(" ", "-")
    )


def get_team_context(team_id: int | None) -> dict[str, str]:
    if not team_id:
        return {"team_name": "", "team_location": "", "schedule_url": "", "team_level": ""}
    try:
        js = _req_json(f"{API}/teams/{team_id}")
    except Exception:
        return {"team_name": "", "team_location": "", "schedule_url": "", "team_level": ""}
    teams = js.get("teams") or []
    if not teams:
        return {"team_name": "", "team_location": "", "schedule_url": "", "team_level": ""}
    t = teams[0]
    sport_id = _safe_int((t.get("sport") or {}).get("id")) or 1
    league_name = str((t.get("league") or {}).get("name", "")).lower()
    if sport_id == 1:
        team_level = "MLB"
    elif "triple-a" in league_name:
        team_level = "AAA"
    elif "double-a" in league_name:
        team_level = "AA"
    elif "high-a" in league_name:
        team_level = "A+"
    elif "single-a" in league_name or "carolina league" in league_name:
        team_level = "A"
    elif "rookie" in league_name or "complex" in league_name or "dominican summer" in league_name:
        team_level = "Rk"
    else:
        team_level = ""
    location = t.get("locationName") or ((t.get("venue") or {}).get("location") or {}).get("city", "")
    team_name = t.get("name", "")
    if sport_id == 1:
        # MLB schedule page.
        team_slug = _slug(team_name.replace(location, "").strip() or team_name)
        schedule_url = f"https://www.mlb.com/{team_slug}/schedule"
    else:
        # MiLB schedule page.
        nickname = t.get("teamName") or team_name
        schedule_url = f"https://www.milb.com/{_slug(nickname)}/schedule"
    return {"team_name": team_name, "team_location": location or "", "schedule_url": schedule_url, "team_level": team_level}


def build_client_payload(c: Client) -> dict[str, Any]:
    base = {
        "name": c.name,
        "position": c.position,
        "level": c.level,
        "league": c.league,
        "minor_affiliate": c.minor_affiliate,
        "major_affiliate": c.major_affiliate,
        "agent": c.agent,
        "agent_last": c.agent_last,
        "is_pitcher": is_pitcher(c.position),
        "current_team": "",
        "current_team_location": "",
        "team_level": "",
        "team_schedule_url": "",
        "last_night_date": (date.today() - timedelta(days=1)).isoformat(),
        "last_night": {},
        "month_to_date": {},
        "season": {},
        "upcoming_series": [],
    }
    person = lookup_player(c.name)
    pid = _safe_int((person or {}).get("id"))
    if not pid:
        pid = None

    group = stat_group(c.position)
    sport_id = sport_id_for_level(c.level)
    latest_team = fetch_latest_team_from_gamelog(pid, group, sport_id) if pid else {}
    tid = _safe_int(latest_team.get("team_id"))
    team_name_guess = latest_team.get("team_name") or pick_current_team_name(c)
    if not tid:
        team_obj = lookup_team_by_name(team_name_guess)
        tid = _safe_int((team_obj or {}).get("id"))
    team_ctx = get_team_context(tid)
    base["current_team"] = team_ctx["team_name"] or team_name_guess
    base["current_team_location"] = team_ctx["team_location"]
    base["team_level"] = team_ctx["team_level"] or c.level
    base["team_schedule_url"] = team_ctx["schedule_url"] or fallback_schedule_url(base["current_team"], c.level)
    yday = date.today() - timedelta(days=1)
    mstart = date.today().replace(day=1)
    if pid:
        try:
            base["last_night"] = {
                k: to_number(v)
                for k, v in fetch_last_night_from_gamelog(pid, group, sport_id, yday).items()
            }
        except Exception:
            base["last_night"] = {}
        try:
            base["month_to_date"] = {
                k: to_number(v)
                for k, v in fetch_player_stats(pid, group, "byDateRange", sport_id, mstart, date.today()).items()
            }
        except Exception:
            base["month_to_date"] = {}
        try:
            base["season"] = {
                k: to_number(v) for k, v in fetch_player_stats(pid, group, "season", sport_id).items()
            }
        except Exception:
            base["season"] = {}

    if tid:
        try:
            base["upcoming_series"] = fetch_team_schedule(tid, weeks=4)
        except Exception:
            base["upcoming_series"] = []
    return base


def build_dashboard_data() -> dict[str, Any]:
    clients = load_clients(SOURCE_XLSX)
    pro = [c for c in clients if not c.is_amateur]
    amateur = [c for c in clients if c.is_amateur]

    pro_rows = [build_client_payload(c) for c in pro]
    # Amateur section keeps base roster metadata for now; NCAA scraping can be added
    # with a provider adapter without changing frontend contract.
    amateur_rows = [
        {
            "name": c.name,
            "position": c.position,
            "level": c.level,
            "league": c.league,
            "agent": c.agent,
            "agent_last": c.agent_last,
            "is_pitcher": is_pitcher(c.position),
            "school_or_team": c.minor_affiliate or c.major_affiliate,
            "team_schedule_url": "",
            "last_night_date": (date.today() - timedelta(days=1)).isoformat(),
            "last_night": {},
            "month_to_date": {},
            "season": {},
            "upcoming_series": [],
        }
        for c in amateur
    ]

    data = {
        "generated_at": datetime.now(UTC).isoformat(),
        "season": SEASON,
        "last_night_date": (date.today() - timedelta(days=1)).isoformat(),
        "pro_clients": pro_rows,
        "amateur_clients": amateur_rows,
    }
    return data


def write_dashboard_data(out: Path = OUT_JSON) -> Path:
    data = build_dashboard_data()
    out.write_text(json.dumps(data, separators=(",", ":")))
    return out


if __name__ == "__main__":
    path = write_dashboard_data()
    print(f"Wrote: {path}")
