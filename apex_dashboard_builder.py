#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
import urllib.parse
import re

import pandas as pd
import requests

SOURCE_XLSX = Path("/Users/colbymorris/Downloads/Client List - 04-15-26.xlsx")
AMATEUR_SOURCE_XLSX = Path("/Users/colbymorris/Desktop/AmateurList.xlsx")
OUT_JSON = Path("/Users/colbymorris/apexstats/apex_dashboard_data.json")
SEASON = date.today().year
API = "https://statsapi.mlb.com/api/v1"
NCAA_GQL_BASE = "https://sdataprod.ncaa.com"
NCAA_SPORT_CODE = "MBA"  # NCAA baseball sport code used by ncaa.com
NCAA_DIVISION = 1
NCAA_SEASON_YEAR = 2025
NCAA_CONTESTS_HASH = "6b26e5cda954c1302873c52835bfd223e169e2068b12511e92b3ef29fac779c2"
NCAA_CONTESTS_BY_DATE: dict[str, list[dict[str, Any]]] = {}
NCAA_BOX_BASEBALL_HASH = "5e92118b2f424040aa96067aba6d34e882165aaf02e9e73cb9d69317066c6ae8"
NCAA_BOX_BY_CONTEST_ID: dict[int, dict[str, Any] | None] = {}

PITCHER_POS = {"RHP", "LHP", "SP", "RP", "P"}
AMATEUR_TOKENS = ("NCAA", "COLLEGE", "JUCO", "HS", "HIGH SCHOOL")
TEAM_CATALOG: list[dict[str, Any]] | None = None
# MLB + affiliated minors; used so call-ups and reassignments resolve from real game logs.
SPORT_IDS_PRO: tuple[int, ...] = (1, 11, 12, 13, 14, 15, 16, 17)


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
    school_or_team: str = ""


def _req_json(url: str) -> dict[str, Any]:
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    return r.json()


def _req_json_with_headers(url: str) -> dict[str, Any]:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, timeout=25, headers=headers)
    r.raise_for_status()
    return r.json()


def _safe_int(x: Any) -> int | None:
    try:
        return int(x)
    except Exception:
        return None


def _parse_name(name: str) -> str:
    # Fix known spreadsheet abbreviations / aliases.
    # Keep this very small and explicit so we don't accidentally rename real players.
    n0 = (name or "").strip()
    if n0.lower() == "rj green":
        n0 = "Rodney Green"
    # Spreadsheet mostly uses "Last, First"
    if "," in n0:
        last, first = [p.strip() for p in n0.split(",", 1)]
        return f"{first} {last}".strip()
    return n0.strip()


def _agent_last(agent: str) -> str:
    s = (agent or "").strip()
    if not s:
        return ""
    if "," in s:
        return s.split(",", 1)[0].strip()
    parts = s.split()
    return parts[-1] if parts else ""


def _cell_str(v: Any) -> str:
    if pd.isna(v):
        return ""
    return str(v).strip()


def _norm_school(s: str) -> str:
    x = (s or "").lower()
    x = re.sub(r"[^a-z0-9 ]+", " ", x)
    stop = {"university", "college", "of", "the", "at", "state"}
    parts = [p for p in x.split() if p and p not in stop]
    return " ".join(parts)


def _norm_token(s: str) -> str:
    x = (s or "").lower().strip()
    x = re.sub(r"[^a-z0-9]+", "", x)
    return x


def _ncaa_graphql_url(meta: str, sha: str, variables: dict[str, Any]) -> str:
    ext = json.dumps({"persistedQuery": {"version": 1, "sha256Hash": sha}}, separators=(",", ":"))
    var = json.dumps(variables, separators=(",", ":"))
    return (
        f"{NCAA_GQL_BASE}?meta={meta}"
        f"&extensions={urllib.parse.quote(ext, safe='')}"
        f"&variables={urllib.parse.quote(var, safe='')}"
    )


def fetch_ncaa_contests_for_date(contest_date: date) -> list[dict[str, Any]]:
    key = contest_date.isoformat()
    if key in NCAA_CONTESTS_BY_DATE:
        return NCAA_CONTESTS_BY_DATE[key]
    vars_ = {
        "sportCode": NCAA_SPORT_CODE,
        "division": NCAA_DIVISION,
        "seasonYear": NCAA_SEASON_YEAR,
        "contestDate": contest_date.strftime("%m/%d/%Y"),
        "conferenceFilter": None,
        "showAllContests": True,
        "week": None,
    }
    try:
        url = _ncaa_graphql_url("GetContests_web", NCAA_CONTESTS_HASH, vars_)
        js = _req_json_with_headers(url)
        contests = ((js.get("data") or {}).get("contests") or [])
    except Exception:
        contests = []
    NCAA_CONTESTS_BY_DATE[key] = contests
    return contests


def fetch_ncaa_boxscore_baseball(contest_id: int) -> dict[str, Any] | None:
    if contest_id in NCAA_BOX_BY_CONTEST_ID:
        return NCAA_BOX_BY_CONTEST_ID[contest_id]
    vars_ = {"contestId": int(contest_id)}
    try:
        url = _ncaa_graphql_url(
            "NCAA_GetGamecenterBoxscoreBaseballById_web",
            NCAA_BOX_BASEBALL_HASH,
            vars_,
        )
        js = _req_json_with_headers(url)
        box = (js.get("data") or {}).get("boxscore")
    except Exception:
        box = None
    NCAA_BOX_BY_CONTEST_ID[contest_id] = box
    return box


def _contest_team_entries(contest: dict[str, Any]) -> list[dict[str, Any]]:
    teams = contest.get("teams") or []
    out: list[dict[str, Any]] = []
    for t in teams:
        out.append(
            {
                "name": str(t.get("nameShort") or ""),
                "slug": str(t.get("seoname") or ""),
                "is_home": bool(t.get("isHome")),
                "score": _safe_int(t.get("score")),
            }
        )
    return out


def _contest_for_school(contest: dict[str, Any], school: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
    school_n = _norm_school(school)
    teams = _contest_team_entries(contest)
    if len(teams) != 2:
        return None
    for i, t in enumerate(teams):
        tn = _norm_school(t["name"])
        slug_n = _norm_school(t["slug"].replace("-", " "))
        if (
            school_n == tn
            or school_n in tn
            or tn in school_n
            or school_n == slug_n
            or school_n in slug_n
            or slug_n in school_n
        ):
            opp = teams[1 - i]
            return t, opp
    return None


def _name_parts(full_name: str) -> tuple[str, str]:
    parts = [p for p in (full_name or "").strip().split() if p]
    if not parts:
        return "", ""
    first = parts[0]
    last = parts[-1]
    # Keep apostrophes/hyphens handling loose for matching.
    return first, last


def _pick_ncaa_player_row(player_stats: list[dict[str, Any]], client_name: str) -> dict[str, Any] | None:
    first, last = _name_parts(client_name)
    f0 = _norm_token(first[:1])
    ln = _norm_token(last)
    # last-name exact + first initial best
    for p in player_stats:
        p_last = _norm_token(str(p.get("lastName") or ""))
        p_first = _norm_token(str(p.get("firstName") or "")[:1])
        if p_last and p_last == ln and (not f0 or p_first == f0):
            return p
    # fallback: last-name exact only
    for p in player_stats:
        p_last = _norm_token(str(p.get("lastName") or ""))
        if p_last and p_last == ln:
            return p
    return None


def _to_int(v: Any) -> int:
    try:
        return int(float(str(v).strip()))
    except Exception:
        return 0


def _to_float(v: Any) -> float:
    try:
        return float(str(v).strip())
    except Exception:
        return 0.0


def _blank_individual_line(is_pitcher_role: bool) -> dict[str, Any]:
    if is_pitcher_role:
        return {"ip": 0.0, "h": 0, "r": 0, "er": 0, "bb": 0, "k": 0, "hr": 0, "bf": 0, "era": 0.0}
    return {"ab": 0, "h": 0, "r": 0, "rbi": 0, "bb": 0, "k": 0}


def _extract_individual_line(player_row: dict[str, Any], is_pitcher_role: bool) -> dict[str, Any]:
    if is_pitcher_role:
        ps = player_row.get("pitcherStats") or {}
        return {
            "ip": round(_to_float(ps.get("inningsPitched")), 1),
            "h": _to_int(ps.get("hitsAllowed")),
            "r": _to_int(ps.get("runsAllowed")),
            "er": _to_int(ps.get("earnedRunsAllowed")),
            "bb": _to_int(ps.get("walksAllowed")),
            "k": _to_int(ps.get("strikeouts")),
            "hr": _to_int(ps.get("homeRunsAllowed")),
            "bf": _to_int(ps.get("battersFaced")),
        }
    bs = player_row.get("batterStats") or {}
    return {
        "ab": _to_int(bs.get("atBats")),
        "h": _to_int(bs.get("hits")),
        "r": _to_int(bs.get("runsScored")),
        "rbi": _to_int(bs.get("runsBattedIn")),
        "bb": _to_int(bs.get("walks")),
        "k": _to_int(bs.get("strikeouts")),
    }


def _ip_to_outs(ip: Any) -> int:
    s = str(ip or "0").strip()
    if not s:
        return 0
    if "." in s:
        whole, frac = s.split(".", 1)
        try:
            w = int(whole)
        except Exception:
            w = 0
        f = frac[:1]
        o = 0
        if f in {"1", "2"}:
            o = int(f)
        return max(0, w * 3 + o)
    try:
        return max(0, int(round(float(s) * 3)))
    except Exception:
        return 0


def _outs_to_ip(outs: int) -> float:
    whole = max(0, outs) // 3
    rem = max(0, outs) % 3
    return float(f"{whole}.{rem}")


def _with_rate_stats(line: dict[str, Any], is_pitcher_role: bool) -> dict[str, Any]:
    out = dict(line)
    if is_pitcher_role:
        outs = _ip_to_outs(out.get("ip"))
        er = _to_int(out.get("er"))
        out["era"] = round((er * 27.0 / outs), 2) if outs > 0 else 0.0
    else:
        ab = _to_int(out.get("ab"))
        h = _to_int(out.get("h"))
        out["avg"] = round((h / ab), 3) if ab > 0 else 0.0
    return out


def _add_lines(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k in set(a.keys()) | set(b.keys()):
        av = a.get(k, 0)
        bv = b.get(k, 0)
        if k == "ip":
            out[k] = _outs_to_ip(_ip_to_outs(av) + _ip_to_outs(bv))
            continue
        if isinstance(av, float) or isinstance(bv, float):
            out[k] = round(float(av) + float(bv), 1)
        else:
            out[k] = int(av) + int(bv)
    return out


def fetch_ncaa_school_payload(school: str, weeks: int = 4) -> dict[str, Any]:
    today = date.today()
    yday = today - timedelta(days=1)
    # Keep NCAA pulls fast: enough history for recent form + month/season summaries.
    # Full-season backfills are expensive and can stall dashboard refresh.
    start = max(date(today.year, 2, 1), today - timedelta(days=21))
    end = today + timedelta(days=7 * weeks)
    contests_all: list[dict[str, Any]] = []
    d = start
    while d <= end:
        contests_all.extend(fetch_ncaa_contests_for_date(d))
        d += timedelta(days=1)

    school_games: list[dict[str, Any]] = []
    for c in contests_all:
        match = _contest_for_school(c, school)
        if not match:
            continue
        team, opp = match
        sd = c.get("startDate") or ""
        # NCAA startDate is MM/DD/YYYY
        try:
            gd = datetime.strptime(sd, "%m/%d/%Y").date()
        except Exception:
            continue
        school_games.append(
            {
                "contest_id": _safe_int(c.get("contestId")),
                "date": gd,
                "team": team,
                "opp": opp,
                "state": str(c.get("gameState") or ""),
                "status": str(c.get("statusCodeDisplay") or ""),
            }
        )
    school_games.sort(key=lambda g: g["date"])

    def mk_series(g: dict[str, Any]) -> dict[str, Any]:
        return {
            "opponent": g["opp"]["name"],
            "home_away": "Home" if g["team"]["is_home"] else "Away",
            "venue": "",
            "location": "",
            "start_date": g["date"].isoformat(),
            "end_date": g["date"].isoformat(),
            "nearest_airport_code": "",
        }

    upcoming = [mk_series(g) for g in school_games if g["date"] >= today][:4]

    def is_final(g: dict[str, Any]) -> bool:
        return g.get("status") == "final" or g.get("state") in {"C", "F", "3"}

    def score_pair(g: dict[str, Any]) -> tuple[int, int] | None:
        a = g["team"]["score"]
        b = g["opp"]["score"]
        if a is None or b is None:
            return None
        return int(a), int(b)

    last_night = {}
    for g in school_games:
        if g["date"] == yday and is_final(g):
            sc = score_pair(g)
            if sc:
                rs, ra = sc
                last_night = {
                    "result": "W" if rs > ra else "L" if rs < ra else "T",
                    "runs_for": rs,
                    "runs_against": ra,
                    "opponent": g["opp"]["name"],
                }
            break

    month_games = [g for g in school_games if g["date"].year == today.year and g["date"].month == today.month and g["date"] <= today]
    season_games = [g for g in school_games if g["date"] <= today]

    def agg(games: list[dict[str, Any]]) -> dict[str, Any]:
        w = l = t = rf = ra = 0
        for g in games:
            if not is_final(g):
                continue
            sc = score_pair(g)
            if not sc:
                continue
            a, b = sc
            rf += a
            ra += b
            if a > b:
                w += 1
            elif a < b:
                l += 1
            else:
                t += 1
        out: dict[str, Any] = {"wins": w, "losses": l, "runs_for": rf, "runs_against": ra}
        if t:
            out["ties"] = t
        return out

    return {
        "upcoming_series": upcoming,
        "last_night": last_night,
        "month_to_date": agg(month_games),
        "season": agg(season_games),
        "_games": school_games,
    }


def get_team_catalog() -> list[dict[str, Any]]:
    global TEAM_CATALOG
    if TEAM_CATALOG is not None:
        return TEAM_CATALOG
    teams: list[dict[str, Any]] = []
    for sport_id in SPORT_IDS_PRO:
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


def lookup_team_by_name(team_name: str, level_hint: str = "") -> dict[str, Any] | None:
    q = (team_name or "").strip().lower()
    if not q:
        return None
    teams = get_team_catalog()
    hint = (level_hint or "").upper().strip()
    want_mlb = hint == "MLB"
    exact = []
    contains = []
    for t in teams:
        name = str(t.get("name", "")).lower()
        tname = str(t.get("teamName", "")).lower()
        lname = str(t.get("locationName", "")).lower()
        full = f"{lname} {tname}".strip()
        sport_id = _safe_int((t.get("sport") or {}).get("id")) or 0
        if q == name or q == full:
            exact.append((t, sport_id))
        elif q in name or q in full:
            contains.append((t, sport_id))

    def pick(cands: list[tuple[dict[str, Any], int]]) -> dict[str, Any] | None:
        if not cands:
            return None
        # Respect hint first: MLB -> sport 1, otherwise prefer non-MLB clubs.
        if want_mlb:
            mlb = [t for t, sid in cands if sid == 1]
            if mlb:
                return mlb[0]
        else:
            milb = [t for t, sid in cands if sid != 1]
            if milb:
                return milb[0]
        return cands[0][0]

    picked = pick(exact) or pick(contains)
    if picked:
        return picked
    return None


def load_clients(path: Path) -> list[Client]:
    xl = pd.ExcelFile(path)
    sheet = "Sorted By League" if "Sorted By League" in xl.sheet_names else xl.sheet_names[0]
    df = pd.read_excel(path, sheet_name=sheet)
    out: list[Client] = []
    for _, r in df.iterrows():
        raw_name = _cell_str(r.get("Name", ""))
        if not raw_name or raw_name.lower() == "nan":
            continue
        level = _cell_str(r.get("Level", ""))
        league = _cell_str(r.get("League", ""))
        position = _cell_str(r.get("Position", "")).upper()
        # Pro workbook now stores agent initials in Notes.
        raw_notes = r.get("Notes", "")
        notes_agent = "" if pd.isna(raw_notes) else str(raw_notes).strip()
        raw_agent = r.get("Agent", "")
        fallback_agent = "" if pd.isna(raw_agent) else str(raw_agent).strip()
        agent = notes_agent or fallback_agent
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


def load_amateur_clients(path: Path) -> list[Client]:
    """
    Load amateur-only client list.
    Expected columns include Name, Position, School and optionally agent initials.
    """
    if not path.is_file():
        return []
    df = pd.read_excel(path)

    def pick_col(cands: list[str]) -> str | None:
        lower = {str(c).strip().lower(): c for c in df.columns}
        for c in cands:
            if c.lower() in lower:
                return str(lower[c.lower()])
        return None

    name_col = pick_col(["Name", "Player", "Player Name"])
    pos_col = pick_col(["Position", "Pos"])
    school_col = pick_col(["School", "College", "Team"])
    agent_col = pick_col(
        [
            "Agent Initials",
            "Agent",
            "Agent Init",
            "Agt",
            "Agent Name",
        ]
    )

    if not name_col:
        return []

    out: list[Client] = []
    for _, r in df.iterrows():
        raw_name = _cell_str(r.get(name_col, ""))
        if not raw_name:
            continue
        position = _cell_str(r.get(pos_col, "")).upper() if pos_col else ""
        school = _cell_str(r.get(school_col, "")) if school_col else ""
        agent_val = _cell_str(r.get(agent_col, "")) if agent_col else ""
        out.append(
            Client(
                name=_parse_name(raw_name),
                position=position,
                level="NCAA",
                league="Amateur",
                minor_affiliate=school,
                major_affiliate="",
                agent=agent_val,
                agent_last=_agent_last(agent_val) if agent_val else "",
                is_amateur=True,
                school_or_team=school,
            )
        )
    return out


def _normalize_org_token(s: str) -> str:
    """Loose match for 'Major League Affiliate' vs API parentOrgName / team name."""
    x = (s or "").lower()
    for w in ("mlb", "milb", "baseball", "club", "the "):
        x = x.replace(w, " ")
    parts = [p for p in "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in x).split() if len(p) > 2]
    return " ".join(parts)


def _org_match_score(major_affiliate: str, team: dict[str, Any]) -> int:
    maj = _normalize_org_token(major_affiliate)
    if not maj:
        return 0
    parent = _normalize_org_token(str(team.get("parentOrgName", "")))
    name = _normalize_org_token(str(team.get("name", "")))
    score = 0
    for token in maj.split():
        if len(token) < 3:
            continue
        if token in parent:
            score += 4
        if token in name:
            score += 2
    return score


def search_people(name: str) -> list[dict[str, Any]]:
    url = f"{API}/people/search?" + urllib.parse.urlencode({"names": name})
    js = _req_json(url)
    return js.get("people") or []


def _name_search_variants(name: str) -> list[str]:
    """Try alternate strings so roster lookup works for every row (e.g. Jr. on MLB.com but not in sheet)."""
    n = (name or "").strip()
    if not n:
        return []
    variants = [n]
    for suffix in (" Jr.", " Jr", " Sr.", " Sr", " III", " II", " IV"):
        if n.endswith(suffix):
            variants.append(n[: -len(suffix)].strip())
    # If no suffix, also try common generational suffix (API often uses Jr.)
    if " jr" not in n.lower() and " sr" not in n.lower() and " iii" not in n.lower():
        variants.append(f"{n} Jr.")
    seen: set[str] = set()
    out: list[str] = []
    for v in variants:
        key = v.lower()
        if v and key not in seen:
            seen.add(key)
            out.append(v)
    return out


def resolve_player_id(c: Client) -> int | None:
    """Resolve Stats API person id; disambiguate when search returns multiple players."""
    people: list[dict[str, Any]] = []
    for variant in _name_search_variants(c.name):
        people = search_people(variant)
        if people:
            break
    if not people:
        return None
    if len(people) == 1:
        return _safe_int(people[0].get("id"))

    best_id: int | None = None
    best_score = -1
    client_pos = (c.position or "").upper().strip()
    for p in people:
        pid = _safe_int(p.get("id"))
        if not pid:
            continue
        try:
            js = _req_json(f"{API}/people/{pid}?hydrate=currentTeam")
        except Exception:
            continue
        p2 = (js.get("people") or [{}])[0]
        ct = p2.get("currentTeam") or {}
        tid = _safe_int(ct.get("id"))
        score = _org_match_score(c.major_affiliate, {"name": ct.get("name", ""), "parentOrgName": ""})
        if tid:
            try:
                tjs = _req_json(f"{API}/teams/{tid}")
                team = (tjs.get("teams") or [{}])[0]
                score = max(score, _org_match_score(c.major_affiliate, team))
            except Exception:
                pass
        api_pos = str((p.get("primaryPosition") or {}).get("abbreviation", "")).upper()
        if client_pos and api_pos:
            if client_pos in PITCHER_POS and api_pos == "P":
                score += 3
            elif client_pos == api_pos:
                score += 2
            elif client_pos in ("OF", "IF", "DH") and api_pos in ("OF", "IF", "DH"):
                score += 1
        if score > best_score:
            best_score = score
            best_id = pid
    return best_id if best_id is not None else _safe_int(people[0].get("id"))


def fetch_current_team_from_person(player_id: int) -> dict[str, Any]:
    """Official roster assignment (preferred over last game played for level/stats context)."""
    try:
        js = _req_json(f"{API}/people/{player_id}?hydrate=currentTeam")
    except Exception:
        return {}
    p = (js.get("people") or [{}])[0]
    ct = p.get("currentTeam") or {}
    tid = _safe_int(ct.get("id"))
    return {
        "team_id": tid,
        "team_name": str(ct.get("name", "") or ""),
    }


def stat_group(position: str) -> str:
    pos = (position or "").upper()
    tokens = [t for t in pos.replace("/", " ").replace(",", " ").split() if t]
    is_p = any(t in PITCHER_POS for t in tokens) or pos in PITCHER_POS
    return "pitching" if is_p else "hitting"


def is_pitcher(position: str) -> bool:
    pos = (position or "").upper()
    tokens = [t for t in pos.replace("/", " ").replace(",", " ").split() if t]
    return any(t in PITCHER_POS for t in tokens) or pos in PITCHER_POS


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


def _gamelog_splits_for_sport(player_id: int, group: str, sport_id: int) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"stats": "gameLog", "group": group, "season": SEASON, "sportId": sport_id}
    if sport_id == 1:
        params["gameType"] = "R"
    url = f"{API}/people/{player_id}/stats?" + urllib.parse.urlencode(params)
    js = _req_json(url)
    return (js.get("stats") or [{}])[0].get("splits") or []


def fetch_latest_team_from_gamelog_all_sports(player_id: int, group: str) -> dict[str, Any]:
    """Most recent regular-season appearance across MLB and MiLB sport IDs."""
    best_date = ""
    best: dict[str, Any] = {}
    for sport_id in SPORT_IDS_PRO:
        try:
            splits = _gamelog_splits_for_sport(player_id, group, sport_id)
        except Exception:
            continue
        for sp in splits:
            d = sp.get("date") or ""
            if not d:
                continue
            if d > best_date:
                best_date = d
                team = sp.get("team") or {}
                best = {
                    "team_id": _safe_int(team.get("id")),
                    "team_name": team.get("name", ""),
                    "last_game_date": d,
                }
    return best


def fetch_last_night_from_gamelog_all_sports(player_id: int, group: str, target_day: date) -> dict[str, Any]:
    """Yesterday's line if they played at any level (handles late-season MLB call-ups)."""
    day = target_day.isoformat()
    merged: dict[str, Any] = {}
    for sport_id in SPORT_IDS_PRO:
        try:
            splits = _gamelog_splits_for_sport(player_id, group, sport_id)
        except Exception:
            continue
        same_day = [s for s in splits if s.get("date") == day]
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
    for sport_id in SPORT_IDS_PRO:
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


def school_schedule_url(school_or_team: str) -> str:
    q = (school_or_team or "").strip()
    if not q:
        return ""
    params = urllib.parse.urlencode({"s": f"{q} baseball"})
    return f"https://d1baseball.com/?{params}"


def get_team_context(team_id: int | None) -> dict[str, Any]:
    empty: dict[str, Any] = {
        "team_name": "",
        "team_location": "",
        "schedule_url": "",
        "team_level": "",
        "sport_id": None,
        "organization": "",
    }
    if not team_id:
        return empty
    try:
        js = _req_json(f"{API}/teams/{team_id}")
    except Exception:
        return empty
    teams = js.get("teams") or []
    if not teams:
        return empty
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
        # Stats API sport ids are stable per classification when league name strings vary.
        sport_level = {11: "AAA", 12: "AA", 13: "A+", 14: "A", 15: "Rk", 16: "Rk", 17: "Rk"}
        team_level = sport_level.get(sport_id, "")
    location = t.get("locationName") or ((t.get("venue") or {}).get("location") or {}).get("city", "")
    team_name = t.get("name", "")
    if sport_id == 1:
        # MLB schedule page.
        team_slug = _slug(team_name.replace(location, "").strip() or team_name)
        schedule_url = f"https://www.mlb.com/{team_slug}/schedule"
        organization = team_name
    else:
        # MiLB schedule page.
        nickname = t.get("teamName") or team_name
        schedule_url = f"https://www.milb.com/{_slug(nickname)}/schedule"
        organization = str(t.get("parentOrgName", "") or "").strip() or team_name
    return {
        "team_name": team_name,
        "team_location": location or "",
        "schedule_url": schedule_url,
        "team_level": team_level,
        "sport_id": sport_id,
        "organization": organization,
    }


def build_client_payload(c: Client) -> dict[str, Any]:
    """One code path for every pro client: Stats API roster (currentTeam) drives team, level, org, and stat sportId."""
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
        "organization": "",
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
    pid = resolve_player_id(c) if c.name else None

    group = stat_group(c.position)
    fallback_sport_id = sport_id_for_level(c.level)
    roster_team = fetch_current_team_from_person(pid) if pid else {}
    latest_team = fetch_latest_team_from_gamelog_all_sports(pid, group) if pid else {}
    tid = _safe_int(roster_team.get("team_id"))
    team_name_guess = roster_team.get("team_name") or latest_team.get("team_name") or pick_current_team_name(c)
    if not tid:
        tid = _safe_int(latest_team.get("team_id"))
    if not tid:
        team_obj = lookup_team_by_name(team_name_guess, c.level)
        tid = _safe_int((team_obj or {}).get("id"))
    team_ctx = get_team_context(tid)
    stat_sport_id = team_ctx.get("sport_id")
    if stat_sport_id is None:
        stat_sport_id = fallback_sport_id
    base["organization"] = team_ctx.get("organization") or (c.major_affiliate if (c.major_affiliate or "").lower() != "nan" else "")
    base["current_team"] = team_ctx["team_name"] or team_name_guess
    base["current_team_location"] = team_ctx["team_location"]
    base["team_level"] = team_ctx["team_level"] or c.level
    base["team_schedule_url"] = team_ctx["schedule_url"] or fallback_schedule_url(
        base["current_team"], base["team_level"]
    )
    yday = date.today() - timedelta(days=1)
    mstart = date.today().replace(day=1)
    if pid:
        try:
            ln = {
                k: to_number(v)
                for k, v in fetch_last_night_from_gamelog_all_sports(pid, group, yday).items()
            }
            # Fallback for environments where gameLog is sparse for that day.
            if not any(v is not None for v in ln.values()):
                ln = {}
                for sid in SPORT_IDS_PRO:
                    try:
                        day_stats = fetch_player_stats(pid, group, "byDateRange", sid, yday, yday)
                    except Exception:
                        continue
                    if any(v not in (None, "", 0, 0.0) for v in day_stats.values()):
                        ln = {k: to_number(v) for k, v in day_stats.items()}
                        break
            base["last_night"] = ln
        except Exception:
            base["last_night"] = {}
        try:
            base["month_to_date"] = {
                k: to_number(v)
                for k, v in fetch_player_stats(pid, group, "byDateRange", stat_sport_id, mstart, date.today()).items()
            }
        except Exception:
            base["month_to_date"] = {}
        try:
            base["season"] = {
                k: to_number(v) for k, v in fetch_player_stats(pid, group, "season", stat_sport_id).items()
            }
        except Exception:
            base["season"] = {}

    if tid:
        try:
            base["upcoming_series"] = fetch_team_schedule(tid, weeks=4)
        except Exception:
            base["upcoming_series"] = []
    return base


def build_amateur_payload(c: Client) -> dict[str, Any]:
    """
    Build amateur client payload.
    Tries StatsAPI resolution first; otherwise keeps school/team metadata and schedule link.
    """
    base = {
        "name": c.name,
        "position": c.position,
        "level": c.level or "NCAA",
        "league": c.league or "Amateur",
        "minor_affiliate": c.minor_affiliate,
        "major_affiliate": c.major_affiliate,
        "agent": c.agent,
        "agent_last": c.agent_last,
        "is_pitcher": is_pitcher(c.position),
        "organization": c.school_or_team,
        "school_or_team": c.school_or_team,
        "current_team": c.school_or_team,
        "current_team_location": "",
        "team_level": c.level or "NCAA",
        "team_schedule_url": school_schedule_url(c.school_or_team),
        "last_night_date": (date.today() - timedelta(days=1)).isoformat(),
        "last_night": {},
        "month_to_date": {},
        "season": {},
        "upcoming_series": [],
    }
    pid = resolve_player_id(c) if c.name else None
    group = stat_group(c.position)
    yday = date.today() - timedelta(days=1)
    mstart = date.today().replace(day=1)

    if pid:
        roster_team = fetch_current_team_from_person(pid)
        latest_team = fetch_latest_team_from_gamelog_all_sports(pid, group)
        tid = _safe_int(roster_team.get("team_id")) or _safe_int(latest_team.get("team_id"))
        if tid:
            team_ctx = get_team_context(tid)
            stat_sport_id = team_ctx.get("sport_id") or 11
            base["organization"] = team_ctx.get("organization") or base["organization"]
            base["current_team"] = team_ctx.get("team_name") or base["current_team"]
            base["current_team_location"] = team_ctx.get("team_location", "")
            base["team_level"] = team_ctx.get("team_level") or base["team_level"]
            base["team_schedule_url"] = team_ctx.get("schedule_url") or base["team_schedule_url"]
            try:
                base["last_night"] = {
                    k: to_number(v) for k, v in fetch_last_night_from_gamelog_all_sports(pid, group, yday).items()
                }
            except Exception:
                base["last_night"] = {}
            try:
                base["month_to_date"] = {
                    k: to_number(v)
                    for k, v in fetch_player_stats(pid, group, "byDateRange", stat_sport_id, mstart, date.today()).items()
                }
            except Exception:
                base["month_to_date"] = {}
            try:
                base["season"] = {
                    k: to_number(v) for k, v in fetch_player_stats(pid, group, "season", stat_sport_id).items()
                }
            except Exception:
                base["season"] = {}
            try:
                base["upcoming_series"] = fetch_team_schedule(tid, weeks=4)
            except Exception:
                base["upcoming_series"] = []
    # Backfill amateur stats/schedules from NCAA feed when pro/miLB APIs are incomplete.
    needs_ncaa = (
        not base["upcoming_series"]
        or not base["season"]
        or not base["month_to_date"]
        or not base["last_night"]
    )
    if needs_ncaa:
        try:
            ncaa_payload = fetch_ncaa_school_payload(c.school_or_team or c.minor_affiliate, weeks=4)
            if not base["last_night"]:
                base["last_night"] = ncaa_payload.get("last_night") or {}
            if not base["month_to_date"]:
                base["month_to_date"] = ncaa_payload.get("month_to_date") or {}
            if not base["season"]:
                base["season"] = ncaa_payload.get("season") or {}
            base["upcoming_series"] = ncaa_payload.get("upcoming_series") or []

            # Upgrade from team summaries to individual player lines when NCAA boxscore data resolves.
            games = ncaa_payload.get("_games") or []
            if games:
                today = date.today()
                yday = today - timedelta(days=1)
                is_p = is_pitcher(c.position)
                month_line = _blank_individual_line(is_p)
                season_line = _blank_individual_line(is_p)
                last_line: dict[str, Any] = {}

                def player_row_for_game(g: dict[str, Any]) -> dict[str, Any] | None:
                    cid = _safe_int(g.get("contest_id"))
                    if not cid:
                        return None
                    box = fetch_ncaa_boxscore_baseball(cid)
                    if not box:
                        return None
                    team_box = box.get("teamBoxscore") or []
                    if len(team_box) != 2:
                        return None
                    teams_meta = box.get("teams") or []
                    idx = 0
                    if len(teams_meta) >= 2:
                        want_home = bool((g.get("team") or {}).get("is_home"))
                        idx = 0 if bool(teams_meta[0].get("isHome")) == want_home else 1
                    player_stats = (team_box[idx] or {}).get("playerStats") or []
                    return _pick_ncaa_player_row(player_stats, c.name)

                # Last-night individual line (if played)
                yday_games = [g for g in games if g.get("date") == yday]
                for g in yday_games:
                    prow = player_row_for_game(g)
                    if prow:
                        last_line = _extract_individual_line(prow, is_p)
                        break

                # Season line from most recent appearance's season-to-date counters
                recent_games = sorted(
                    [g for g in games if isinstance(g.get("date"), date) and g.get("date") <= today],
                    key=lambda x: x.get("date"),
                    reverse=True,
                )
                for g in recent_games:
                    prow = player_row_for_game(g)
                    if not prow:
                        continue
                    if is_p:
                        ps = prow.get("pitcherStats") or {}
                        season_line = {
                            "ip": round(_to_float(ps.get("inningsPitched")), 1),
                            "h": _to_int(ps.get("hitsAllowed")),
                            "er": _to_int(ps.get("earnedRunsAllowed")),
                            "bb": _to_int(ps.get("walksAllowed")),
                            "k": _to_int(ps.get("strikeouts")),
                            "bf": _to_int(ps.get("battersFaced")),
                        }
                    else:
                        hs = prow.get("hittingSeason") or prow.get("batterStats") or {}
                        season_line = {
                            "ab": _to_int(hs.get("atBats")),
                            "h": _to_int(hs.get("hits")),
                            "r": _to_int(hs.get("runsScored")),
                            "rbi": _to_int(hs.get("runsBattedIn")),
                            "bb": _to_int(hs.get("walks")),
                            "k": _to_int(hs.get("strikeouts")),
                        }
                    break

                # Month-to-date: aggregate up to the last 5 games this month where player appeared.
                month_games = [
                    g for g in recent_games
                    if isinstance(g.get("date"), date) and g["date"].year == today.year and g["date"].month == today.month
                ][:5]
                for g in month_games:
                    prow = player_row_for_game(g)
                    if not prow:
                        continue
                    line = _extract_individual_line(prow, is_p)
                    month_line = _add_lines(month_line, line)

                if season_line != _blank_individual_line(is_p):
                    base["season"] = _with_rate_stats(season_line, is_p)
                if month_line != _blank_individual_line(is_p):
                    base["month_to_date"] = _with_rate_stats(month_line, is_p)
                if last_line:
                    base["last_night"] = _with_rate_stats(last_line, is_p)
        except Exception:
            pass
    return base


def build_dashboard_data() -> dict[str, Any]:
    clients = load_clients(SOURCE_XLSX)
    pro = [c for c in clients if not c.is_amateur]
    amateur = [c for c in clients if c.is_amateur]
    # Primary amateur source now comes from the dedicated Desktop list.
    # Fallback to legacy amateur rows from the main client workbook if needed.
    dedicated_amateur = load_amateur_clients(AMATEUR_SOURCE_XLSX)
    if dedicated_amateur:
        amateur = dedicated_amateur

    # Same roster + stats resolution for every pro row (no per-player exceptions).
    pro_rows = [build_client_payload(c) for c in pro]
    amateur_rows = [build_amateur_payload(c) for c in amateur]

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
