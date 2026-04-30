#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any
import time
import urllib.parse
import re

import pandas as pd
import requests

SOURCE_XLSX = Path("/Users/colbymorris/apexstats/client_lists/Client List - 04-15-26.xlsx")
AMATEUR_SOURCE_XLSX = Path("/Users/colbymorris/apexstats/client_lists/AmateurList.xlsx")
HS_SOURCE_XLSX = Path("/Users/colbymorris/apexstats/client_lists/HSList.xlsx")
OUT_JSON = Path("/Users/colbymorris/apexstats/apex_dashboard_data.json")
SEASON = date.today().year
API = "https://statsapi.mlb.com/api/v1"
NCAA_GQL_BASE = "https://sdataprod.ncaa.com"
NCAA_SPORT_CODE = "MBA"  # NCAA baseball sport code used by ncaa.com
NCAA_DIVISION = 1
# NCAA GraphQL uses an academic/sport year that lags the calendar for spring baseball
# (e.g. April 2026 contests appear under seasonYear 2025).
NCAA_SEASON_YEAR = SEASON - 1
NCAA_CONTESTS_HASH = "6b26e5cda954c1302873c52835bfd223e169e2068b12511e92b3ef29fac779c2"
NCAA_CONTESTS_BY_DATE: dict[str, list[dict[str, Any]]] = {}
NCAA_BOX_BASEBALL_HASH = "5e92118b2f424040aa96067aba6d34e882165aaf02e9e73cb9d69317066c6ae8"
NCAA_BOX_BY_CONTEST_ID: dict[int, dict[str, Any] | None] = {}
D1_PLAYERS_SEARCH_JSON = "https://d1baseball.com/wp-content/themes/d1-staxx/data/2026-players.json"
D1_PLAYERS_INDEX: list[dict[str, Any]] | None = None
D1_PLAYER_STATS_CACHE: dict[str, dict[str, Any] | None] = {}
NCAA_SCHOOL_PAYLOAD_CACHE: dict[str, dict[str, Any]] = {}
MAXPREPS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ApexDashboard/1.0)",
    "Accept-Language": "en-US,en;q=0.9",
}
HS_MAXPREPS_URL_OVERRIDES: dict[str, str] = {
    "jensen hirschkorn": "https://www.maxpreps.com/ca/kingsburg/kingsburg-vikings/athletes/jensen-hirschkorn/baseball/stats/?careerid=nl0cjhntsf600&sportSeasonId=1278779e-84df-4e60-8d03-db0024535aa6",
}

PITCHER_POS = {"RHP", "LHP", "SP", "RP", "P"}
# Exclude from pro tab (still in workbook for records, but not shown on dashboard).
PRO_CLIENT_EXCLUDE_NAMES: frozenset[str] = frozenset(
    {"alyssa nakken", "jordan viars", "daulton jefferies", "adam wolf"}
)
# Normalized client name -> Stats API person id when search is ambiguous or returns no hits.
PRO_MLB_PLAYER_ID_OVERRIDES: dict[str, int] = {
    "alexander darby": 801592,  # listed as Zander Darby
    "zander darby": 801592,
    "matthew klein": 702600,  # listed as Matt Klein (Rockies)
    "matt klein": 702600,
    "carter mathison": 701296,
    "alexander barr": 828781,  # listed as Alex Barr
    "alex barr": 828781,
    "walter ford": 703609,
    "dale stanavich": 689359,
    # people/search "Ryan Harvey" returns an unrelated older player (458243); Tigers prospect:
    "ryan harvey": 687308,
    # Twins pitching prospect; people/search is unreliable for this entry.
    "ryan gallagher": 801594,
    # people/search often returns [] for Tookoian despite valid player endpoint.
    "samuel tookoian": 702494,
    "sam tookoian": 702494,
    "sarkis tookoian": 702494,
    # Fraizer/Frazier spellings in client sheets.
    "matthew frazier": 670208,
    "matt frazier": 670208,
    "matthew fraizer": 670208,
    "matt fraizer": 670208,
    "ruben ibarra": 702140,
}
# Normalized client name -> people/search query (API spelling differs from the roster sheet).
PRO_MLB_PEOPLE_SEARCH_ALIASES: dict[str, str] = {
    # MLB lists "Matt Fraizer" (670208); sheet often uses "Frazier"; Texas Rangers org per client.
    "matthew frazier": "Matt Fraizer",
    "matt frazier": "Matt Fraizer",
}
# Sheet quirks: treat as hitter for college stat tables / D1 scrape.
COLLEGE_FORCE_HITTER_NAMES: frozenset[str] = frozenset({"ethan surowiec"})
COLLEGE_TWO_WAY_NAMES: frozenset[str] = frozenset({"evan dempsey"})
AMATEUR_TOKENS = ("NCAA", "COLLEGE", "JUCO", "HS", "HIGH SCHOOL")
TEAM_CATALOG: list[dict[str, Any]] | None = None
# MLB + affiliated minors; used so call-ups and reassignments resolve from real game logs.
SPORT_IDS_PRO: tuple[int, ...] = (1, 11, 12, 13, 14, 15, 16, 17)
NCAA_SCHOOL_ALIASES: dict[str, tuple[str, ...]] = {
    # Common ncaa.com short-name variants
    "florida gulf coast": ("fgcu", "florida gulf coast"),
    "florida atlantic": ("fau", "florida atlantic", "fla atlantic"),
    "uc berkeley": ("cal", "california", "uc berkeley"),
}
FOREIGN_LEAGUES: frozenset[str] = frozenset({"NPB", "KBO", "CPBL"})
PRO_FOREIGN_BR_URLS: dict[str, str] = {
    # International pro stats on Baseball-Reference register pages.
    "spencer howard": "https://www.baseball-reference.com/register/player.fcgi?id=howard000spe",
    "jackson stephens": "https://www.baseball-reference.com/register/player.fcgi?id=stephe003jac",
    "mitch white": "https://www.baseball-reference.com/minors/player.cgi?id=white-000mit",
}
FOREIGN_BR_SEASON_CACHE: dict[tuple[str, bool], dict[str, Any] | None] = {}


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


_HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ApexDashboard/1.0; +https://github.com/colbymorris08/apexstats-dashboard)"}


def _req_json(url: str, *, timeout: int = 45, retries: int = 4) -> dict[str, Any]:
    """GET JSON with browser-like UA and short retries (MLB/NCAA can stall or reset connections)."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout, headers=_HTTP_HEADERS)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, OSError) as e:
            last = e
            if attempt + 1 >= retries:
                raise
            time.sleep(0.75 * (2**attempt))
    raise last  # pragma: no cover


def _req_json_with_headers(url: str) -> dict[str, Any]:
    return _req_json(url)


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


def _normalize_agent_initials(agent: str) -> str:
    """Map legacy workbook codes to display initials."""
    a = (agent or "").strip()
    if a.upper() == "S":
        return "SK"
    return a


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


def _norm_player_name(s: str) -> str:
    x = (s or "").strip().lower()
    x = x.replace(".", " ").replace(",", " ").replace("-", " ")
    parts = [p for p in x.split() if p not in {"jr", "sr", "ii", "iii", "iv"}]
    return " ".join(parts)


def _year_as_int(v: Any) -> int | None:
    try:
        return int(str(v).strip())
    except Exception:
        return None


def _to_str_num(v: Any) -> str:
    if pd.isna(v):
        return ""
    return str(v).strip()


def get_d1_players_index() -> list[dict[str, Any]]:
    global D1_PLAYERS_INDEX
    if D1_PLAYERS_INDEX is not None:
        return D1_PLAYERS_INDEX
    try:
        js = _req_json_with_headers(D1_PLAYERS_SEARCH_JSON)
        if isinstance(js, list):
            D1_PLAYERS_INDEX = js
            return D1_PLAYERS_INDEX
    except Exception:
        pass
    D1_PLAYERS_INDEX = []
    return D1_PLAYERS_INDEX


def resolve_d1_player_url(client_name: str, school: str = "") -> str:
    idx = get_d1_players_index()
    if not idx:
        return ""
    want_name = _norm_player_name(client_name)
    want_school = _norm_school(school)
    first, last = _name_parts(client_name)
    first_i = _norm_token(first[:1])
    last_n = _norm_token(last)

    best_url = ""
    best_score = -1
    for p in idx:
        pname = str(p.get("player_name") or "")
        pteam = str(p.get("team_name") or "")
        purl = str(p.get("player_url") or "")
        if not purl:
            continue
        score = 0
        pn = _norm_player_name(pname)
        if pn == want_name:
            score += 10
        elif want_name and (pn.startswith(want_name) or want_name.startswith(pn)):
            score += 6
        # Last name + first initial fallback
        pf, pl = _name_parts(pname)
        if _norm_token(pl) == last_n:
            score += 4
            if first_i and _norm_token(pf[:1]) == first_i:
                score += 2
        if want_school:
            pteam_n = _norm_school(pteam)
            if pteam_n and (pteam_n in want_school or want_school in pteam_n):
                score += 4
        if score > best_score:
            best_score = score
            best_url = purl
    if best_score <= 0:
        return ""
    if best_url.startswith("http://") or best_url.startswith("https://"):
        return best_url
    return f"https://d1baseball.com{best_url}"


def _d1_get(row: pd.Series, *candidates: str) -> Any:
    cmap = {str(c).strip().lower(): c for c in row.index}
    for cand in candidates:
        k = cand.lower()
        if k in cmap:
            return row[cmap[k]]
    return None


def _pick_d1_table(dfs: list[pd.DataFrame], is_pitcher_role: bool) -> pd.DataFrame | None:
    # Player pages include multiple tables; choose the basic seasonal one.
    for df in dfs:
        cols = {str(c).strip().upper() for c in df.columns}
        if "YEAR" not in cols:
            continue
        if is_pitcher_role and {"IP", "ERA", "APP"}.issubset(cols):
            return df
        if (not is_pitcher_role) and {"AB", "R", "H", "RBI", "OPS", "BA"}.issubset(cols):
            return df
    return None


def fetch_d1_player_stats(player_url: str, is_pitcher_role: bool) -> dict[str, Any]:
    if not player_url:
        return {}
    key = f"{player_url}|{'P' if is_pitcher_role else 'H'}"
    if key in D1_PLAYER_STATS_CACHE:
        return D1_PLAYER_STATS_CACHE[key] or {}
    try:
        html = requests.get(player_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"}).text
        dfs = pd.read_html(StringIO(html))
    except Exception:
        D1_PLAYER_STATS_CACHE[key] = None
        return {}
    table = _pick_d1_table(dfs, is_pitcher_role)
    if table is None or table.empty:
        D1_PLAYER_STATS_CACHE[key] = None
        return {}
    year_col = next((c for c in table.columns if str(c).strip().upper() == "YEAR"), None)
    if not year_col:
        D1_PLAYER_STATS_CACHE[key] = None
        return {}
    row = None
    for _, r in table.iterrows():
        y = _year_as_int(r.get(year_col))
        if y == SEASON:
            row = r
            break
    if row is None:
        # Fall back to latest numeric year.
        best_y = -1
        for _, r in table.iterrows():
            y = _year_as_int(r.get(year_col))
            if y is not None and y > best_y:
                best_y = y
                row = r
    if row is None:
        D1_PLAYER_STATS_CACHE[key] = None
        return {}

    if is_pitcher_role:
        ip_cell = _to_str_num(row.get("IP"))
        out = {
            "inningsPitched": json_stat_value("inningsPitched", ip_cell) if ip_cell else "0.0",
            "hits": to_number(row.get("H")),
            "runs": to_number(row.get("R")),
            "earnedRuns": to_number(row.get("ER")),
            "baseOnBalls": to_number(row.get("BB")),
            "strikeOuts": to_number(row.get("K")),
            "homeRuns": to_number(row.get("HR")),
            "era": to_number(row.get("ERA")),
        }
    else:
        out = {
            "atBats": to_number(_d1_get(row, "AB", "Ab")),
            "runs": to_number(_d1_get(row, "R")),
            "hits": to_number(_d1_get(row, "H")),
            "rbi": to_number(_d1_get(row, "RBI")),
            "baseOnBalls": to_number(_d1_get(row, "BB")),
            "strikeOuts": to_number(_d1_get(row, "K", "SO")),
            "avg": to_number(_d1_get(row, "BA", "AVG")),
            "ops": to_number(_d1_get(row, "OPS")),
            "homeRuns": to_number(_d1_get(row, "HR", "Home Runs")),
            "doubles": to_number(_d1_get(row, "2B", "2b", "Doubles")),
            "stolenBases": to_number(_d1_get(row, "SB", "Stolen Bases")),
            "outfieldAssists": to_number(_d1_get(row, "OFA", "OF A", "Outfield Assists")),
        }
    D1_PLAYER_STATS_CACHE[key] = out
    return out


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
    school_tokens = set(school_n.split())
    raw_words = [w.lower() for w in re.findall(r"[a-zA-Z]+", school or "")]
    acronym = "".join(w[0] for w in raw_words if w not in {"of", "the", "at"})
    school_keys = {school_n}
    for a in NCAA_SCHOOL_ALIASES.get(school_n, ()):
        aa = _norm_school(a)
        if aa:
            school_keys.add(aa)
    if acronym:
        school_keys.add(acronym)
    teams = _contest_team_entries(contest)
    if len(teams) != 2:
        return None
    for i, t in enumerate(teams):
        tn = _norm_school(t["name"])
        slug_n = _norm_school(t["slug"].replace("-", " "))
        team_keys = {tn, slug_n}
        # strict key match first (exact normalized or acronym like UCF/FGCU)
        if school_keys & team_keys:
            opp = teams[1 - i]
            return t, opp
        # conservative token overlap fallback (avoid broad "florida" collisions)
        for k in team_keys:
            k_tokens = set(k.split())
            if not school_tokens or not k_tokens:
                continue
            ov = school_tokens & k_tokens
            if len(ov) >= 2 and (ov == school_tokens or ov == k_tokens):
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
        raw_last = str(p.get("lastName") or "")
        raw_first = str(p.get("firstName") or "")
        p_last = _norm_token(raw_last)
        p_first = _norm_token(raw_first[:1])
        # NCAA can return full name in lastName with empty firstName.
        raw_combo = f"{raw_first} {raw_last}".strip()
        combo_tokens = {_norm_token(tok) for tok in raw_combo.replace(",", " ").split() if tok}
        combo_tokens.discard("")
        combo_first_i = _norm_token(raw_combo[:1]) if raw_combo else ""
        if ln and ln in combo_tokens and (not f0 or f0 == p_first or f0 == combo_first_i):
            return p
        if p_last and p_last == ln and (not f0 or p_first == f0):
            return p
    # fallback: last-name exact only
    for p in player_stats:
        raw_last = str(p.get("lastName") or "")
        raw_first = str(p.get("firstName") or "")
        p_last = _norm_token(raw_last)
        raw_combo = f"{raw_first} {raw_last}".strip()
        combo_tokens = {_norm_token(tok) for tok in raw_combo.replace(",", " ").split() if tok}
        combo_tokens.discard("")
        if ln and ln in combo_tokens:
            return p
        if p_last and p_last == ln:
            return p
    return None


def _ncaa_ip_value(ps: dict[str, Any]) -> float:
    return _to_float(_ncaa_dict_get_ci(ps, "inningsPitched", "ip", "innings"))


def _apply_ncaa_pitcher_k_fallback(
    selected_row: dict[str, Any] | None,
    team_rows: list[dict[str, Any]],
    opp_rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Fallback when NCAA feed reports 0 K for every pitcher in a game.

    Some NCAA box payloads zero out per-pitcher strikeouts while batter rows still
    include opponent team strikeout totals. In that case, assign team K total to
    the pitcher with the most IP so last-night dashboards don't show false zeros.
    """
    if not selected_row:
        return selected_row
    ps_sel = selected_row.get("pitcherStats") or {}
    if not ps_sel:
        return selected_row

    pitchers: list[dict[str, Any]] = []
    all_zero = True
    for r in team_rows:
        ps = r.get("pitcherStats") or {}
        if not ps:
            continue
        ip = _ncaa_ip_value(ps)
        if ip <= 0:
            continue
        k = _ncaa_stat_int(ps, "strikeouts", "strikeOuts", "battersStruckOut", "struckOut", "k", "so")
        pitchers.append({"row": r, "ip": ip, "k": k})
        if k > 0:
            all_zero = False
    if not pitchers or not all_zero:
        return selected_row

    team_opp_k = 0
    for r in opp_rows:
        bs = r.get("batterStats") or {}
        team_opp_k += _ncaa_stat_int(bs, "strikeouts", "strikeOuts", "struckOut", "k", "so")
    if team_opp_k <= 0:
        return selected_row

    by_ip = sorted(pitchers, key=lambda x: x["ip"], reverse=True)
    top_ip = by_ip[0]["ip"]
    top_count = sum(1 for p in by_ip if p["ip"] == top_ip)
    # If one pitcher clearly carried the bulk innings, attribute team Ks to that arm.
    if top_count == 1 and top_ip >= 2:
        starter = by_ip[0]["row"]
        if starter is not selected_row:
            return selected_row
        patched = dict(selected_row)
        patched_ps = dict(ps_sel)
        patched_ps["strikeouts"] = str(team_opp_k)
        patched["pitcherStats"] = patched_ps
        return patched

    # Otherwise estimate per-pitcher Ks by share of batters faced.
    sel_bf = _ncaa_stat_int(ps_sel, "battersFaced", "bf")
    total_bf = sum(max(0, _ncaa_stat_int((p["row"].get("pitcherStats") or {}), "battersFaced", "bf")) for p in pitchers)
    if sel_bf <= 0 or total_bf <= 0:
        return selected_row
    est = int(round((team_opp_k * sel_bf) / total_bf))
    if est <= 0 and team_opp_k > 0 and sel_bf >= 3:
        est = 1
    patched = dict(selected_row)
    patched_ps = dict(ps_sel)
    patched_ps["strikeouts"] = str(est)
    patched["pitcherStats"] = patched_ps
    return patched


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


def _to_float_or_none(v: Any) -> float | None:
    s = str(v or "").strip()
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _blank_individual_line(is_pitcher_role: bool) -> dict[str, Any]:
    if is_pitcher_role:
        return {"ip": 0.0, "h": 0, "r": 0, "er": 0, "bb": 0, "k": 0, "hr": 0, "bf": 0, "era": 0.0}
    return {"ab": 0, "h": 0, "r": 0, "rbi": 0, "bb": 0, "k": 0, "doubles": 0, "hr": 0, "sb": 0, "ofa": 0}


def _ncaa_stat_int(container: dict[str, Any], *keys: str) -> int:
    for k in keys:
        if k in container and container[k] is not None:
            return _to_int(container.get(k))
    return 0


def _ncaa_dict_get_ci(container: dict[str, Any], *candidates: str) -> Any:
    """Case-insensitive key lookup for NCAA GraphQL objects."""
    if not isinstance(container, dict):
        return None
    lower_map = {str(k).lower().replace(" ", ""): k for k in container}
    for cand in candidates:
        ck = cand.lower().replace(" ", "")
        k = lower_map.get(ck)
        if k is not None:
            return container.get(k)
    return None


def _is_ncaa_outfield_position(pos_raw: str) -> bool:
    """True if NCAA position string includes LF/CF/RF/OF (box-score defensive line)."""
    low = (pos_raw or "").strip().lower()
    if not low:
        return False
    if "outfield" in low:
        return True
    toks = [t.strip() for t in re.split(r"[/,\s]+", low) if t.strip()]
    of_set = {"lf", "cf", "rf", "of"}
    return any(t in of_set for t in toks)


def _ncaa_outfield_assists_from_row(player_row: dict[str, Any]) -> int:
    """
    NCAA.com boxscores expose defensive assists on fieldStats (not batterStats).
    For LF/CF/RF/OF, the box 'A' column is fieldStats.assists.
    """
    if not _is_ncaa_outfield_position(str(player_row.get("position") or "")):
        return 0
    fs = player_row.get("fieldStats")
    if isinstance(fs, dict):
        return _to_int(fs.get("assists"))
    return 0


def _ncaa_pitch_count_from_pitcher_row(player_row: dict[str, Any]) -> int:
    """
    NCAA GraphQL usually omits total pitch count; pitcherStats almost always
    includes 'strikes'. When 'balls' (or similar) is present, sum strikes+balls.
    Otherwise report strikes so the dashboard shows a real number (not zero).
    """
    ps = player_row.get("pitcherStats")
    if not isinstance(ps, dict):
        return 0
    for key in (
        "pitchesThrown",
        "numberOfPitches",
        "pitchCount",
        "totalPitches",
        "pitches",
        "npc",
        "totalPitchCount",
    ):
        v = _ncaa_dict_get_ci(ps, key)
        if v is not None and str(v).strip() != "":
            n = _to_int(v)
            if n > 0:
                return n
    strikes = _to_int(ps.get("strikes"))
    balls = 0
    for k, v in ps.items():
        if str(k) == "__typename":
            continue
        lk = str(k).lower().replace(" ", "")
        if lk in ("balls", "ballsthrown", "ballcount", "nonstrikes", "ballsseen"):
            balls = _to_int(v)
            break
    if strikes > 0 and balls > 0:
        return strikes + balls
    if strikes > 0:
        return strikes
    return 0


def _ncaa_batter_extra_counts(bs: dict[str, Any]) -> dict[str, int]:
    """When NCAA includes extra columns on BatterStat (varies by feed)."""
    out = {"doubles": 0, "hr": 0, "sb": 0}
    if not isinstance(bs, dict):
        return out
    for k, v in bs.items():
        if str(k) == "__typename":
            continue
        lk = str(k).lower().replace(" ", "").replace("_", "")
        if lk in ("doubles", "double", "twobasehits", "2b"):
            out["doubles"] = _to_int(v)
        elif lk in ("homeruns", "homerun", "hr"):
            out["hr"] = _to_int(v)
        elif lk in ("stolenbases", "stolenbase", "sb"):
            out["sb"] = _to_int(v)
    return out


def _extract_individual_line(player_row: dict[str, Any], is_pitcher_role: bool) -> dict[str, Any]:
    if is_pitcher_role:
        ps = player_row.get("pitcherStats") or {}
        pitches = _ncaa_pitch_count_from_pitcher_row(player_row)
        k_val = _ncaa_stat_int(
            ps,
            "strikeouts",
            "strikeOuts",
            "battersStruckOut",
            "struckOut",
            "k",
            "so",
        )
        return {
            "ip": round(_to_float(_ncaa_dict_get_ci(ps, "inningsPitched", "ip", "innings")), 1),
            "h": _ncaa_stat_int(ps, "hitsAllowed", "hits", "h"),
            "r": _ncaa_stat_int(ps, "runsAllowed", "runs", "r"),
            "er": _ncaa_stat_int(ps, "earnedRunsAllowed", "earnedRuns", "er"),
            "bb": _ncaa_stat_int(ps, "walksAllowed", "walks", "baseOnBalls", "bb"),
            "k": k_val,
            "hr": _ncaa_stat_int(ps, "homeRunsAllowed", "homeRuns", "hr"),
            "bf": _ncaa_stat_int(ps, "battersFaced", "bf"),
            "pitches": pitches,
        }
    bs = player_row.get("batterStats") or {}
    extra = _ncaa_batter_extra_counts(bs)
    ofa_field = _ncaa_outfield_assists_from_row(player_row)
    ofa_bat = _ncaa_stat_int(
        bs,
        "outfieldAssists",
        "outFieldAssists",
        "ofAssists",
        "assistsOutfield",
    )
    ofa = max(ofa_field, ofa_bat)
    return {
        "ab": _to_int(bs.get("atBats")),
        "h": _to_int(bs.get("hits")),
        "r": _to_int(bs.get("runsScored")),
        "rbi": _to_int(bs.get("runsBattedIn")),
        "bb": _to_int(bs.get("walks")),
        "k": _to_int(bs.get("strikeouts")),
        "doubles": max(
            extra["doubles"],
            _ncaa_stat_int(bs, "doubles", "double", "twoBaseHits"),
        ),
        "hr": max(extra["hr"], _ncaa_stat_int(bs, "homeRuns", "homeRun", "hr")),
        "sb": max(extra["sb"], _ncaa_stat_int(bs, "stolenBases", "stolenBase", "sb")),
        "ofa": ofa,
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
        if outs > 0:
            out["era"] = round((er * 27.0 / outs), 2)
        else:
            era_raw = _to_float_or_none(out.get("era"))
            out["era"] = round(era_raw, 2) if era_raw is not None else 0.0
    else:
        ab = _to_int(out.get("ab"))
        h = _to_int(out.get("h"))
        out["avg"] = round((h / ab), 3) if ab > 0 else 0.0
        if "ops" not in out:
            obp = _to_float_or_none(out.get("obp"))
            slg = _to_float_or_none(out.get("slg"))
            if obp is not None and slg is not None:
                out["ops"] = round(obp + slg, 3)
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


def get_cached_ncaa_school_payload(school: str, weeks: int = 4) -> dict[str, Any]:
    key = _norm_school(school)
    if not key:
        return {}
    if key not in NCAA_SCHOOL_PAYLOAD_CACHE:
        NCAA_SCHOOL_PAYLOAD_CACHE[key] = fetch_ncaa_school_payload(school, weeks=weeks)
    return NCAA_SCHOOL_PAYLOAD_CACHE[key]


def college_is_pitcher(c: Client) -> bool:
    if _norm_player_name(c.name) in COLLEGE_FORCE_HITTER_NAMES:
        return False
    return is_pitcher(c.position)


def _split_two_way_amateur(c: Client) -> list[Client]:
    nn = _norm_player_name(c.name)
    if nn not in COLLEGE_TWO_WAY_NAMES:
        return [c]
    pos_parts = [p.strip().upper() for p in re.split(r"[/,]", c.position or "") if p.strip()]
    if not pos_parts:
        pos_parts = [c.position or ""]
    out: list[Client] = []
    for p in pos_parts:
        out.append(
            Client(
                name=c.name,
                position=p,
                level=c.level,
                league=c.league,
                minor_affiliate=c.minor_affiliate,
                major_affiliate=c.major_affiliate,
                agent=c.agent,
                agent_last=c.agent_last,
                is_amateur=c.is_amateur,
                school_or_team=c.school_or_team,
            )
        )
    return out


def _amateur_line_to_pro_keys(raw: dict[str, Any], is_p: bool) -> dict[str, Any]:
    """Align NCAA line dicts with MLB Stats API-ish keys for the dashboard tables."""
    if is_p:
        ip_val = raw.get("ip")
        ip_s = json_stat_value("inningsPitched", ip_val) if ip_val not in (None, "") else None
        if not ip_s:
            ip_s = "0.0"
        out: dict[str, Any] = {
            "inningsPitched": ip_s,
            "hits": to_number(raw.get("h")),
            "runs": to_number(raw.get("r")),
            "earnedRuns": to_number(raw.get("er")),
            "baseOnBalls": to_number(raw.get("bb")),
            "strikeOuts": to_number(raw.get("k")),
            "homeRuns": to_number(raw.get("hr")),
            "era": to_number(raw.get("era")),
        }
        pt = to_number(raw.get("pitches"))
        if pt is not None:
            try:
                fv = float(pt)
                out["numberOfPitches"] = int(fv) if fv == int(fv) else int(round(fv))
            except (TypeError, ValueError):
                out["numberOfPitches"] = pt
        return out
    return {
        "atBats": to_number(raw.get("ab")),
        "runs": to_number(raw.get("r")),
        "hits": to_number(raw.get("h")),
        "rbi": to_number(raw.get("rbi")),
        "baseOnBalls": to_number(raw.get("bb")),
        "strikeOuts": to_number(raw.get("k")),
        "avg": to_number(raw.get("avg")),
        "ops": to_number(raw.get("ops")),
        "homeRuns": to_number(raw.get("hr")),
        "doubles": to_number(raw.get("doubles")),
        "stolenBases": to_number(raw.get("sb")),
        "outfieldAssists": to_number(raw.get("ofa")),
    }


def _player_row_from_ncaa_contest(
    g: dict[str, Any], school: str, client_name: str
) -> dict[str, Any] | None:
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
    school_n = _norm_school(school)
    if len(teams_meta) >= 2:
        for i, tm in enumerate(teams_meta[:2]):
            nm = str(tm.get("nameShort") or tm.get("name") or "")
            sn = _norm_school(nm)
            if sn and (sn == school_n or school_n in sn or sn in school_n):
                idx = i
                break
        else:
            want_home = bool((g.get("team") or {}).get("is_home"))
            idx = 0 if bool(teams_meta[0].get("isHome")) == want_home else 1
    player_stats = (team_box[idx] or {}).get("playerStats") or []
    selected = _pick_ncaa_player_row(player_stats, client_name)
    opp_stats = (team_box[1 - idx] or {}).get("playerStats") or []
    return _apply_ncaa_pitcher_k_fallback(selected, player_stats, opp_stats)


def ncaa_player_last_night_and_month(
    c: Client, school: str, is_p: bool, ncaa_payload: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Per-player lines from NCAA.com team schedule + boxscores (same source as team search)."""
    games: list[dict[str, Any]] = list(ncaa_payload.get("_games") or [])
    today = date.today()
    yday = today - timedelta(days=1)
    mstart = today.replace(day=1)

    def is_final(g: dict[str, Any]) -> bool:
        return g.get("status") == "final" or g.get("state") in {"C", "F", "3"}

    last_keys: dict[str, Any] = {}
    for g in games:
        if g.get("date") == yday and is_final(g):
            prow = _player_row_from_ncaa_contest(g, school, c.name)
            if prow:
                last_raw = _with_rate_stats(_extract_individual_line(prow, is_p), is_p)
                last_keys = _amateur_line_to_pro_keys(last_raw, is_p)
                break

    month_raw = _blank_individual_line(is_p)
    month_games = [
        g
        for g in games
        if isinstance(g.get("date"), date)
        and mstart <= g["date"] <= today
        and is_final(g)
    ]
    for g in month_games[:45]:
        prow = _player_row_from_ncaa_contest(g, school, c.name)
        if not prow:
            continue
        line = _extract_individual_line(prow, is_p)
        if is_p:
            line.pop("pitches", None)
        month_raw = _add_lines(month_raw, line)
    month_keys: dict[str, Any] = {}
    if month_raw != _blank_individual_line(is_p):
        month_merged = _with_rate_stats(month_raw, is_p)
        month_keys = _amateur_line_to_pro_keys(month_merged, is_p)

    return last_keys, month_keys


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
        agent = _normalize_agent_initials(notes_agent or fallback_agent)
        # Keep requested manual assignment for known client.
        if _parse_name(raw_name).strip().lower() == "brock burke":
            agent = "PC"
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
        agent_val = _normalize_agent_initials(_cell_str(r.get(agent_col, "")) if agent_col else "")
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
    nn = _norm_player_name(c.name)
    oid = PRO_MLB_PLAYER_ID_OVERRIDES.get(nn)
    if oid is not None:
        return oid
    alias_q = PRO_MLB_PEOPLE_SEARCH_ALIASES.get(nn)
    variants = _name_search_variants(c.name)
    if alias_q:
        seen_l = {v.casefold() for v in variants}
        if alias_q.casefold() not in seen_l:
            variants = [alias_q] + variants
        else:
            variants = [alias_q] + [v for v in variants if v.casefold() != alias_q.casefold()]
    people: list[dict[str, Any]] = []
    for variant in variants:
        people = search_people(variant)
        if people:
            break
    if not people:
        team_guess = pick_current_team_name(c)
        if team_guess:
            team_obj = lookup_team_by_name(team_guess, c.level)
            tid = _safe_int((team_obj or {}).get("id"))
            if tid:
                try:
                    rjs = _req_json(f"{API}/teams/{tid}/roster?" + urllib.parse.urlencode({"season": SEASON}))
                    target = _norm_player_name(c.name)
                    for row in rjs.get("roster") or []:
                        person = row.get("person") or {}
                        pid = _safe_int(person.get("id"))
                        nm = _norm_player_name(str(person.get("fullName", "")))
                        if pid and nm == target:
                            return pid
                except Exception:
                    pass
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
    *,
    season: int | None = None,
) -> dict[str, Any]:
    season_year = SEASON if season is None else season
    params: dict[str, Any] = {"stats": stat_type, "group": group, "season": season_year, "sportId": sport_id}
    if sport_id == 1:
        params["gameType"] = "R"
    if start and end:
        params["startDate"] = start.isoformat()
        params["endDate"] = end.isoformat()
    url = f"{API}/people/{player_id}/stats?" + urllib.parse.urlencode(params)
    js = _req_json(url)
    splits = (js.get("stats") or [{}])[0].get("splits") or []
    return splits[0].get("stat", {}) if splits else {}


def _stats_non_empty(st: dict[str, Any]) -> bool:
    return bool(st) and any(v not in (None, "", 0, 0.0) for v in st.values())


def fetch_player_stats_preferred_then_all_sports(
    player_id: int,
    group: str,
    stat_type: str,
    preferred_sport_id: int,
    start: date | None = None,
    end: date | None = None,
    *,
    season: int | None = None,
) -> dict[str, Any]:
    """Try preferred sport first, then scan other pro sport IDs for non-empty stats."""
    order = [preferred_sport_id] + [s for s in SPORT_IDS_PRO if s != preferred_sport_id]
    for sid in order:
        try:
            st = fetch_player_stats(player_id, group, stat_type, sid, start, end, season=season)
        except Exception:
            continue
        if _stats_non_empty(st):
            return st
    try:
        return fetch_player_stats(player_id, group, stat_type, preferred_sport_id, start, end, season=season)
    except Exception:
        return {}


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(str(p) for p in c if str(p) != "nan").strip() for c in df.columns]
    else:
        df.columns = [str(c).strip() for c in df.columns]
    return df


def _find_col(cols: list[str], names: tuple[str, ...]) -> str | None:
    low = {c.lower(): c for c in cols}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    for c in cols:
        cl = c.lower()
        if any(n.lower() in cl for n in names):
            return c
    return None


def fetch_foreign_br_season_stats(client_name: str, is_pitcher_role: bool) -> dict[str, Any]:
    nn = _norm_player_name(client_name)
    url = PRO_FOREIGN_BR_URLS.get(nn)
    if not url:
        return {}
    key = (nn, is_pitcher_role)
    if key in FOREIGN_BR_SEASON_CACHE:
        return FOREIGN_BR_SEASON_CACHE[key] or {}
    try:
        html = requests.get(url, timeout=35, headers={"User-Agent": "Mozilla/5.0"}).text
        dfs = pd.read_html(StringIO(html))
    except Exception:
        FOREIGN_BR_SEASON_CACHE[key] = None
        return {}

    best: tuple[int, dict[str, Any]] | None = None
    for raw_df in dfs:
        df = _flatten_columns(raw_df.copy())
        cols = list(df.columns)
        year_col = _find_col(cols, ("Year",))
        lg_col = _find_col(cols, ("Lg", "League"))
        lev_col = _find_col(cols, ("Lev", "Level"))
        if not year_col or not lg_col:
            continue
        tm_col = _find_col(cols, ("Tm", "Team"))
        ip_col = _find_col(cols, ("IP",))
        era_col = _find_col(cols, ("ERA",))
        so_col = _find_col(cols, ("SO", "K"))
        bb_col = _find_col(cols, ("BB",))
        h_col = _find_col(cols, ("H",))
        er_col = _find_col(cols, ("ER",))
        r_col = _find_col(cols, ("R",))
        hr_col = _find_col(cols, ("HR",))
        ab_col = _find_col(cols, ("AB",))
        hit_col = _find_col(cols, ("H",))
        rbi_col = _find_col(cols, ("RBI",))
        avg_col = _find_col(cols, ("AVG",))
        ops_col = _find_col(cols, ("OPS",))
        d2_col = _find_col(cols, ("2B", "Doubles"))
        sb_col = _find_col(cols, ("SB",))
        ofa_col = _find_col(cols, ("Outfield Assists", "OFA"))

        for _, row in df.iterrows():
            y = _year_as_int(row.get(year_col))
            if y is None:
                continue
            lg = str(row.get(lg_col) or "").strip().upper()
            lev = str(row.get(lev_col) or "").strip().upper() if lev_col else ""
            is_foreign = (
                lg in FOREIGN_LEAGUES
                or "KBO" in lg
                or "CPBL" in lg
                or lg.startswith("JP")
                or lev == "FGN"
            )
            if not is_foreign:
                continue
            if is_pitcher_role and not ip_col:
                continue
            season_line: dict[str, Any]
            if is_pitcher_role:
                season_line = {
                    "inningsPitched": json_stat_value("inningsPitched", row.get(ip_col)) if ip_col else None,
                    "hits": to_number(row.get(h_col)) if h_col else None,
                    "runs": to_number(row.get(r_col)) if r_col else None,
                    "earnedRuns": to_number(row.get(er_col)) if er_col else None,
                    "baseOnBalls": to_number(row.get(bb_col)) if bb_col else None,
                    "strikeOuts": to_number(row.get(so_col)) if so_col else None,
                    "homeRuns": to_number(row.get(hr_col)) if hr_col else None,
                    "era": to_number(row.get(era_col)) if era_col else None,
                }
            else:
                season_line = {
                    "atBats": to_number(row.get(ab_col)) if ab_col else None,
                    "hits": to_number(row.get(hit_col)) if hit_col else None,
                    "runs": to_number(row.get(r_col)) if r_col else None,
                    "rbi": to_number(row.get(rbi_col)) if rbi_col else None,
                    "avg": to_number(row.get(avg_col)) if avg_col else None,
                    "ops": to_number(row.get(ops_col)) if ops_col else None,
                    "homeRuns": to_number(row.get(hr_col)) if hr_col else None,
                    "doubles": to_number(row.get(d2_col)) if d2_col else None,
                    "stolenBases": to_number(row.get(sb_col)) if sb_col else None,
                    "outfieldAssists": to_number(row.get(ofa_col)) if ofa_col else None,
                }
            if best is None or y > best[0]:
                if tm_col:
                    season_line["_foreign_team"] = str(row.get(tm_col) or "").strip()
                season_line["_foreign_league"] = lg
                season_line["_foreign_year"] = y
                best = (y, season_line)

    if best is None:
        FOREIGN_BR_SEASON_CACHE[key] = None
        return {}
    out = {k: v for k, v in best[1].items() if v is not None}
    FOREIGN_BR_SEASON_CACHE[key] = out
    return out


def _gamelog_splits_for_sport(player_id: int, group: str, sport_id: int) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"stats": "gameLog", "group": group, "season": SEASON, "sportId": sport_id}
    if sport_id == 1:
        params["gameType"] = "R"
    url = f"{API}/people/{player_id}/stats?" + urllib.parse.urlencode(params)
    js = _req_json(url)
    return (js.get("stats") or [{}])[0].get("splits") or []


def fetch_last_night_outfield_assists_all_sports(player_id: int, target_day: date) -> int:
    """Sum outfield assists (LF/CF/RF) from fielding game logs for one calendar day."""
    day = target_day.isoformat()
    total = 0
    for sport_id in SPORT_IDS_PRO:
        try:
            splits = _gamelog_splits_for_sport(player_id, "fielding", sport_id)
        except Exception:
            continue
        for sp in splits:
            if sp.get("date") != day:
                continue
            pos = (sp.get("position") or {}).get("abbreviation") or ""
            if pos not in ("LF", "CF", "RF"):
                continue
            st = sp.get("stat") or {}
            total += _to_int(st.get("assists"))
    return total


def _strip_pitch_count_fields(st: dict[str, Any]) -> dict[str, Any]:
    """Pitch counts belong in last-game lines only, not month/season tables."""
    if not st:
        return st
    out = {k: v for k, v in st.items() if k not in ("numberOfPitches", "strikes", "balls")}
    return out


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


def fetch_last_night_boxscore_url_all_sports(player_id: int, group: str, target_day: date) -> str:
    day = target_day.isoformat()
    best_game_pk: int | None = None
    for sport_id in SPORT_IDS_PRO:
        try:
            splits = _gamelog_splits_for_sport(player_id, group, sport_id)
        except Exception:
            continue
        for s in splits:
            if s.get("date") != day:
                continue
            game = s.get("game") or {}
            game_pk = _safe_int(game.get("gamePk") or s.get("gamePk"))
            if game_pk is not None and (best_game_pk is None or game_pk > best_game_pk):
                best_game_pk = game_pk
    if best_game_pk is None:
        return ""
    return f"https://www.mlb.com/gameday/{best_game_pk}/final/box"


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


def json_stat_value(stat_key: str, v: Any) -> float | int | str | None:
    """JSON-safe stat values. MLB inningsPitched uses baseball strings (4.0, 4.1, 4.2); never coerce to int."""
    if stat_key != "inningsPitched":
        return to_number(v)
    if v is None or v == "":
        return None
    s = str(v).strip()
    if not s:
        return None
    if re.fullmatch(r"\d+\.\d", s):
        return s
    try:
        x = float(s)
    except ValueError:
        return s
    outs = int(round(x * 3))
    whole, rem = divmod(max(0, outs), 3)
    return f"{whole}.{rem}"


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
        "last_night_boxscore_url": "",
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
                k: json_stat_value(k, v)
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
                        ln = {k: json_stat_value(k, v) for k, v in day_stats.items()}
                        break
            base["last_night"] = ln
            base["last_night_boxscore_url"] = fetch_last_night_boxscore_url_all_sports(pid, group, yday)
            if base["last_night"]:
                if base["is_pitcher"]:
                    pass  # keep numberOfPitches for last game only
                else:
                    base["last_night"].pop("numberOfPitches", None)
                    try:
                        base["last_night"]["outfieldAssists"] = json_stat_value(
                            "outfieldAssists",
                            fetch_last_night_outfield_assists_all_sports(pid, yday),
                        )
                    except Exception:
                        base["last_night"]["outfieldAssists"] = 0
        except Exception:
            base["last_night"] = {}
        try:
            mtd_raw = fetch_player_stats_preferred_then_all_sports(
                pid, group, "byDateRange", stat_sport_id, mstart, date.today()
            )
            base["month_to_date"] = _strip_pitch_count_fields(
                {k: json_stat_value(k, v) for k, v in mtd_raw.items()}
            )
        except Exception:
            base["month_to_date"] = {}
        try:
            st_season = fetch_player_stats_preferred_then_all_sports(pid, group, "season", stat_sport_id)
            base["season"] = _strip_pitch_count_fields(
                {k: json_stat_value(k, v) for k, v in st_season.items()}
            )
        except Exception:
            base["season"] = {}

    if tid:
        try:
            base["upcoming_series"] = fetch_team_schedule(tid, weeks=4)
        except Exception:
            base["upcoming_series"] = []

    # Foreign league preference for known clients (NPB/KBO/CPBL) from Baseball-Reference.
    nn = _norm_player_name(c.name)
    if nn in PRO_FOREIGN_BR_URLS:
        foreign_season = fetch_foreign_br_season_stats(c.name, base["is_pitcher"])
        if foreign_season:
            base["season"] = _strip_pitch_count_fields(
                {k: v for k, v in foreign_season.items() if not str(k).startswith("_")}
            )
            f_team = str(foreign_season.get("_foreign_team", "")).strip()
            f_lg = str(foreign_season.get("_foreign_league", "")).strip()
            if f_team:
                base["current_team"] = f_team
                base["organization"] = f_team
            if f_lg:
                base["team_level"] = f_lg
    return base


def build_amateur_payload(c: Client) -> dict[str, Any]:
    """
    College clients: D1Baseball season table + NCAA.com team schedule/boxscores for last night & MTD.
    (No MLB Stats API for school-based amateurs — avoids wrong-player matches and bad P/pos splits.)
    """
    school = (c.school_or_team or c.minor_affiliate or "").strip()
    is_p = college_is_pitcher(c)
    base = {
        "name": c.name,
        "position": c.position,
        "level": c.level or "NCAA",
        "league": c.league or "Amateur",
        "minor_affiliate": c.minor_affiliate,
        "major_affiliate": c.major_affiliate,
        "agent": c.agent,
        "agent_last": c.agent_last,
        "is_pitcher": is_p,
        "organization": c.school_or_team,
        "school_or_team": c.school_or_team,
        "current_team": c.school_or_team,
        "current_team_location": "",
        "team_level": c.level or "NCAA",
        "team_schedule_url": school_schedule_url(c.school_or_team),
        "last_night_boxscore_url": "",
        "last_night_date": (date.today() - timedelta(days=1)).isoformat(),
        "last_night": {},
        "month_to_date": {},
        "season": {},
        "upcoming_series": [],
    }

    # Season totals from D1 player page (search index + 2026 table).
    d1_url = resolve_d1_player_url(c.name, school)
    d1_season = fetch_d1_player_stats(d1_url, is_p) if d1_url else {}
    if d1_url:
        base["team_schedule_url"] = d1_url
    if d1_season:
        base["season"] = d1_season

    if school:
        try:
            ncaa_payload = get_cached_ncaa_school_payload(school, weeks=4)
            base["upcoming_series"] = ncaa_payload.get("upcoming_series") or []

            ln_ind, mtd_ind = ncaa_player_last_night_and_month(c, school, is_p, ncaa_payload)
            yday = date.today() - timedelta(days=1)
            for g in list(ncaa_payload.get("_games") or []):
                if g.get("date") == yday and (g.get("status") == "final" or g.get("state") in {"C", "F", "3"}):
                    cid = _safe_int(g.get("contest_id"))
                    if cid:
                        base["last_night_boxscore_url"] = f"https://www.ncaa.com/game/{cid}/boxscore"
                    break
            if ln_ind:
                base["last_night"] = {
                    k: json_stat_value(k, v) for k, v in ln_ind.items() if v is not None
                }
            if mtd_ind:
                base["month_to_date"] = {
                    k: json_stat_value(k, v) for k, v in mtd_ind.items() if v is not None
                }

            # Team-level fallbacks (W/L, runs) if boxscore did not resolve the player row.
            if not base["last_night"]:
                base["last_night"] = ncaa_payload.get("last_night") or {}
            if not base["month_to_date"]:
                base["month_to_date"] = ncaa_payload.get("month_to_date") or {}
            if not base["season"]:
                base["season"] = ncaa_payload.get("season") or {}
        except Exception:
            pass
    return base


def _maxpreps_get(url: str, timeout: int = 30) -> str:
    r = requests.get(url, timeout=timeout, headers=MAXPREPS_HEADERS)
    r.raise_for_status()
    return r.text


def _maxpreps_link_for_day(html: str, day: date) -> str:
    mm = day.strftime("%m").lstrip("0")
    dd = day.strftime("%d").lstrip("0")
    patterns = [
        rf'href="([^"]*?/games/{mm}-{dd}-{day.year}/[^"]+)"',
        rf'href="([^"]*?/games/{int(mm)}-{int(dd)}-{day.year}/[^"]+)"',
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            href = m.group(1)
            if href.startswith("http"):
                return href
            return f"https://www.maxpreps.com{href}"
    return ""


def _maxpreps_next_data(html: str) -> dict[str, Any] | None:
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def _maxpreps_stat_map(stats: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for s in stats or []:
        name = str(s.get("name") or "").strip()
        if name:
            out[name] = s.get("value")
    return out


def _maxpreps_pitching_rows(next_data: dict[str, Any] | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not next_data:
        return [], {}
    try:
        groups = next_data["props"]["pageProps"]["statsCardProps"]["careerGameLogs"]["groups"]
    except Exception:
        return [], {}
    pitching_group = None
    for g in groups:
        if str(g.get("name", "")).strip().lower() == "pitching":
            pitching_group = g
            break
    if not pitching_group:
        return [], {}
    subgroups = list(pitching_group.get("subgroups") or [])
    if len(subgroups) < 2:
        return [], {}
    sg0 = subgroups[0]  # includes ERA
    sg1 = subgroups[1]  # includes IP/H/R/ER/BB/K/HR
    era_by_key: dict[tuple[str, str], Any] = {}
    for r in sg0.get("stats") or []:
        sm = _maxpreps_stat_map(r.get("stats") or [])
        key = (str(r.get("date") or ""), str(r.get("contestUrl") or ""))
        era_by_key[key] = sm.get("EarnedRunAverage")
    rows: list[dict[str, Any]] = []
    for r in sg1.get("stats") or []:
        sm = _maxpreps_stat_map(r.get("stats") or [])
        key = (str(r.get("date") or ""), str(r.get("contestUrl") or ""))
        rows.append(
            {
                "date": key[0],
                "contest_url": key[1],
                "ip": sm.get("InningsPitchedDecimal"),
                "h": sm.get("HitsAgainst"),
                "r": sm.get("RunsAgainst"),
                "er": sm.get("EarnedRuns"),
                "bb": sm.get("BaseOnBallsAgainst"),
                "k": sm.get("BattersStruckOut"),
                "hr": sm.get("HomeRunsAgainst"),
                "era": era_by_key.get(key),
            }
        )
    t0 = _maxpreps_stat_map((sg0.get("totalStats") or {}).get("stats") or [])
    t1 = _maxpreps_stat_map((sg1.get("totalStats") or {}).get("stats") or [])
    season = {
        "ip": t1.get("InningsPitchedDecimal"),
        "h": t1.get("HitsAgainst"),
        "r": t1.get("RunsAgainst"),
        "er": t1.get("EarnedRuns"),
        "bb": t1.get("BaseOnBallsAgainst"),
        "k": t1.get("BattersStruckOut"),
        "hr": t1.get("HomeRunsAgainst"),
        "era": t0.get("EarnedRunAverage"),
    }
    return rows, season


def _pick_maxpreps_tables(tables: list[pd.DataFrame]) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    batting: pd.DataFrame | None = None
    pitching: pd.DataFrame | None = None
    for t in tables:
        cols = {str(c).strip().lower(): c for c in t.columns}
        if "date" not in cols:
            continue
        if batting is None and "ab" in cols and "h" in cols:
            batting = t.copy()
        if pitching is None and "ip" in cols and ("er" in cols or "h" in cols or "k" in cols):
            pitching = t.copy()
    return batting, pitching


def _hs_position_flags(position: str) -> tuple[bool, bool]:
    """Return (is_pitcher, is_hitter) from HS sheet position text."""
    raw = (position or "").upper().strip()
    if not raw:
        return False, True
    toks = [t for t in re.split(r"[/,\\s]+", raw) if t]
    if not toks:
        toks = [raw]
    is_p = any(("HP" in t) or (t in PITCHER_POS) or (t == "P") for t in toks)
    is_h = any(not (("HP" in t) or (t in PITCHER_POS) or (t == "P")) for t in toks)
    if is_p and not is_h:
        return True, False
    if is_h and not is_p:
        return False, True
    if is_p and is_h:
        return True, True
    return False, True


def build_high_school_payloads(entry: dict[str, str]) -> list[dict[str, Any]]:
    today = date.today()
    yday = today - timedelta(days=1)
    base_hitter: dict[str, Any] = {
        "name": entry.get("name", ""),
        "position": entry.get("position", ""),
        "level": "HS",
        "league": "High School",
        "minor_affiliate": entry.get("school", ""),
        "major_affiliate": "",
        "agent": entry.get("agent", ""),
        "agent_last": _agent_last(entry.get("agent", "")),
        "is_pitcher": False,
        "organization": entry.get("school", ""),
        "school_or_team": entry.get("school", ""),
        "current_team": entry.get("school", ""),
        "current_team_location": "",
        "team_level": "HS",
        "team_schedule_url": entry.get("stats_url", ""),
        "last_night_boxscore_url": "",
        "last_night_date": yday.isoformat(),
        "last_night": {},
        "month_to_date": {},
        "season": {},
        "upcoming_series": [],
    }
    base_pitcher = dict(base_hitter)
    base_pitcher["position"] = "P"
    base_pitcher["is_pitcher"] = True
    wants_pitcher = bool(entry.get("hs_is_pitcher"))
    wants_hitter = bool(entry.get("hs_is_hitter"))
    if not wants_pitcher and not wants_hitter:
        wants_hitter = True
    url = entry.get("stats_url", "").strip()
    if not url:
        out_no_url: list[dict[str, Any]] = []
        if wants_hitter:
            out_no_url.append(base_hitter)
        if wants_pitcher:
            out_no_url.append(base_pitcher)
        return out_no_url
    try:
        html = _maxpreps_get(url)
        tables = pd.read_html(StringIO(html))
    except Exception:
        out_err: list[dict[str, Any]] = []
        if wants_hitter:
            out_err.append(base_hitter)
        if wants_pitcher:
            out_err.append(base_pitcher)
        return out_err
    batting, pitching = _pick_maxpreps_tables(tables)
    if wants_hitter and batting is not None:
        batting.columns = [str(c).strip() for c in batting.columns]
        if "Date" in batting.columns:
            last_row = None
            month_rows: list[pd.Series] = []
            for _, row in batting.iterrows():
                ds = str(row.get("Date", "")).strip()
                if not ds:
                    continue
                if ds.lower().startswith("season total"):
                    base_hitter["season"] = _amateur_line_to_pro_keys(
                        {
                            "ab": row.get("AB"),
                            "r": row.get("R"),
                            "h": row.get("H"),
                            "rbi": row.get("RBI"),
                            "bb": row.get("BB"),
                            "k": row.get("K"),
                            "hr": row.get("HR"),
                            "doubles": row.get("2B"),
                            "avg": row.get("Avg"),
                            "ops": row.get("OPS"),
                        },
                        False,
                    )
                    continue
                try:
                    mm_s, dd_s = ds.split("/", 1)
                    gd = date(today.year, int(mm_s), int(dd_s))
                except Exception:
                    continue
                if gd == yday:
                    last_row = row
                if gd.month == today.month and gd <= today:
                    month_rows.append(row)
            if last_row is not None:
                base_hitter["last_night"] = _amateur_line_to_pro_keys(
                    {
                        "ab": last_row.get("AB"),
                        "r": last_row.get("R"),
                        "h": last_row.get("H"),
                        "rbi": last_row.get("RBI"),
                        "bb": last_row.get("BB"),
                        "k": last_row.get("K"),
                        "hr": last_row.get("HR"),
                        "doubles": last_row.get("2B"),
                        "avg": last_row.get("Avg"),
                        "ops": last_row.get("OPS"),
                    },
                    False,
                )
            if month_rows:
                agg = {"ab": 0, "r": 0, "h": 0, "rbi": 0, "bb": 0, "k": 0, "hr": 0, "doubles": 0}
                for r in month_rows:
                    for k, c in (
                        ("ab", "AB"),
                        ("r", "R"),
                        ("h", "H"),
                        ("rbi", "RBI"),
                        ("bb", "BB"),
                        ("k", "K"),
                        ("hr", "HR"),
                        ("doubles", "2B"),
                    ):
                        agg[k] += int(to_number(r.get(c)) or 0)
                agg["avg"] = round((agg["h"] / agg["ab"]), 3) if agg["ab"] else 0.0
                base_hitter["month_to_date"] = _amateur_line_to_pro_keys(agg, False)
    box_link = _maxpreps_link_for_day(html, yday)
    base_hitter["last_night_boxscore_url"] = box_link

    out: list[dict[str, Any]] = []
    if wants_hitter:
        out.append(base_hitter)
    next_data = _maxpreps_next_data(html)
    p_rows, p_season = _maxpreps_pitching_rows(next_data)
    if wants_pitcher and p_season:
        base_pitcher["season"] = _amateur_line_to_pro_keys(p_season, True)
    p_last_row = None
    p_month_rows: list[dict[str, Any]] = []
    for row in p_rows:
        ds = str(row.get("date", "")).strip()
        if not ds:
            continue
        try:
            mm_s, dd_s = ds.split("/", 1)
            gd = date(today.year, int(mm_s), int(dd_s))
        except Exception:
            continue
        if gd == yday:
            p_last_row = row
            if not box_link:
                cu = str(row.get("contest_url") or "")
                if cu:
                    box_link = cu if cu.startswith("http") else f"https://www.maxpreps.com{cu}"
        if gd.month == today.month and gd <= today:
            p_month_rows.append(row)
    if wants_pitcher and p_last_row is not None:
        base_pitcher["last_night"] = _amateur_line_to_pro_keys(p_last_row, True)
    if wants_pitcher and p_month_rows:
        p_month = _blank_individual_line(True)
        for r in p_month_rows:
            p_month = _add_lines(
                p_month,
                {
                    "ip": r.get("ip"),
                    "h": int(to_number(r.get("h")) or 0),
                    "r": int(to_number(r.get("r")) or 0),
                    "er": int(to_number(r.get("er")) or 0),
                    "bb": int(to_number(r.get("bb")) or 0),
                    "k": int(to_number(r.get("k")) or 0),
                    "hr": int(to_number(r.get("hr")) or 0),
                },
            )
        p_month = _with_rate_stats(p_month, True)
        base_pitcher["month_to_date"] = _amateur_line_to_pro_keys(p_month, True)
    base_pitcher["last_night_boxscore_url"] = box_link
    if wants_pitcher and (base_pitcher["season"] or base_pitcher["month_to_date"] or base_pitcher["last_night"] or not wants_hitter):
        out.append(base_pitcher)
    return out


def load_high_school_clients(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    df = pd.read_excel(path)
    lower = {str(c).strip().lower(): c for c in df.columns}

    def pick_col(cands: list[str]) -> str | None:
        for c in cands:
            if c.lower() in lower:
                return str(lower[c.lower()])
        return None

    name_col = pick_col(["Name", "Player", "Player Name"])
    pos_col = pick_col(["Position", "Pos"])
    school_col = pick_col(["School", "Team", "High School"])
    agent_col = pick_col(["Agent", "Agent Initials", "Agt"])
    url_col = pick_col(["MaxPreps URL", "Stats URL", "URL", "Profile URL", "Link"])
    if not name_col:
        return []

    out: list[dict[str, str]] = []
    for _, r in df.iterrows():
        raw_name = _cell_str(r.get(name_col, ""))
        if not raw_name:
            continue
        name = _parse_name(raw_name)
        norm = _norm_player_name(name)
        stats_url = _cell_str(r.get(url_col, "")) if url_col else ""
        if not stats_url:
            stats_url = HS_MAXPREPS_URL_OVERRIDES.get(norm, "")
        out.append(
            {
                "name": name,
                "position": _cell_str(r.get(pos_col, "")) if pos_col else "",
                "school": _cell_str(r.get(school_col, "")) if school_col else "",
                "agent": _normalize_agent_initials(_cell_str(r.get(agent_col, "")) if agent_col else ""),
                "stats_url": stats_url,
                "hs_is_pitcher": _hs_position_flags(_cell_str(r.get(pos_col, "")) if pos_col else "")[0],
                "hs_is_hitter": _hs_position_flags(_cell_str(r.get(pos_col, "")) if pos_col else "")[1],
            }
        )
    return out


def build_dashboard_data() -> dict[str, Any]:
    NCAA_SCHOOL_PAYLOAD_CACHE.clear()
    FOREIGN_BR_SEASON_CACHE.clear()
    clients = load_clients(SOURCE_XLSX)
    pro = [c for c in clients if not c.is_amateur]
    pro = [c for c in pro if _norm_player_name(c.name) not in PRO_CLIENT_EXCLUDE_NAMES]
    amateur = [c for c in clients if c.is_amateur]
    # Primary amateur source now comes from the dedicated Desktop list.
    # Merge with legacy workbook rows so dedicated list doesn't drop anyone.
    dedicated_amateur = load_amateur_clients(AMATEUR_SOURCE_XLSX)
    if dedicated_amateur:
        merged: dict[str, Client] = {}
        for c in amateur:
            merged[_norm_player_name(c.name)] = c
        for c in dedicated_amateur:
            merged[_norm_player_name(c.name)] = c
        amateur = list(merged.values())
    # Expand configured two-way amateurs into separate hitter/pitcher rows.
    amateur_expanded: list[Client] = []
    for c in amateur:
        amateur_expanded.extend(_split_two_way_amateur(c))
    amateur = amateur_expanded

    # Same roster + stats resolution for every pro row (no per-player exceptions).
    pro_rows = [build_client_payload(c) for c in pro]
    amateur_rows = [build_amateur_payload(c) for c in amateur]
    high_school_rows: list[dict[str, Any]] = []
    for p in load_high_school_clients(HS_SOURCE_XLSX):
        high_school_rows.extend(build_high_school_payloads(p))

    data = {
        "generated_at": datetime.now(UTC).isoformat(),
        "season": SEASON,
        "last_night_date": (date.today() - timedelta(days=1)).isoformat(),
        "pro_clients": pro_rows,
        "amateur_clients": amateur_rows,
        "high_school_clients": high_school_rows,
    }
    return data


def write_dashboard_data(out: Path = OUT_JSON) -> Path:
    data = build_dashboard_data()
    out.write_text(json.dumps(data, separators=(",", ":")))
    return out


if __name__ == "__main__":
    path = write_dashboard_data()
    print(f"Wrote: {path}")
