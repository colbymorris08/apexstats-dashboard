#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any
import time
import unicodedata
import urllib.parse
import re
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from gamechanger_api import (
    GCPlayerRef,
    GameChangerIndex,
    GameChangerClient,
    _merge_hit_lines,
    _merge_pitch_lines,
    _player_season_lines,
    _team_schedule_url,
    fetch_public_roster,
    gc_player_game_lines,
    get_gamechanger_client,
    match_gc_roster_player,
    public_player_season_lines,
    search_gc_teams,
)

APEX_ROOT = Path(__file__).resolve().parent
SOURCE_XLSX = APEX_ROOT / "client_lists" / "Client List - 04-15-26.xlsx"
AMATEUR_SOURCE_XLSX = APEX_ROOT / "client_lists" / "AmateurList.xlsx"
HS_SOURCE_XLSX = APEX_ROOT / "client_lists" / "HSList.xlsx"


# Arb / FA / JF / AR watch lists — edit these in client_lists/ (used by site + GitHub Actions).
JF_FOLLOW_SOURCE_XLSX = APEX_ROOT / "client_lists" / "FurmaniakFollow.xlsx"
AR_FOLLOW_SOURCE_XLSX = APEX_ROOT / "client_lists" / "ARFollow.xlsx"

# GameChanger public/internal IDs for summer travel teams (program key = lowercased Program column).
# Each program may list multiple teams; the first roster match wins.
GC_SUMMER_TEAMS: dict[str, list[dict[str, str]]] = {
    "2027 alpha prime": [{"public_id": "VpbE6SBAdU1f", "internal_id": "f888a449-3ccc-4e0a-91d5-343c6d68056e", "grad_year": "2027"}],
    "2027 usa prime/detroit tigers scout": [
        {"public_id": "6tCCUYwkmmmN", "internal_id": "b814ce2f-a465-4d3d-b5da-7424ba1e48df", "grad_year": "2027"},
        {"public_id": "C9sGCQlZudsm"},
    ],
    "2027 canes national": [{"public_id": "loGFljSxDTEQ", "internal_id": "587e7568-49db-4906-8e59-6cf8788009c2"}],
    "2027 norcal": [
        {"public_id": "YoqTPc30UqAO", "internal_id": "133975fa-5df3-4c86-82b8-9786a5a1c147", "grad_year": "2027"},
        {"public_id": "2YBxQncoeiot"},
    ],
    "2027 top tier": [{"public_id": "TQfPUw2mqDvg", "grad_year": "2027"}],
    "2028 alpha prime": [
        {
            "public_id": "oT4InPq8VLP9",
            "internal_id": "4dff7977-3db9-4a7f-80df-969463e4d197",
            "grad_year": "2028",
        },
    ],
    "2028 norcal": [
        {"public_id": "LSOi1bVQrjUn", "internal_id": "22fb6d25-beba-4663-9db9-90f88ae49dae", "grad_year": "2028"},
        {"public_id": "4mQOcP6qSVUV", "internal_id": "576fc145-296f-41dd-bad4-0874c7f485af", "grad_year": "2028"},
        {"public_id": "7DXVnYPadY77", "internal_id": "b261b87f-2a7a-45b9-a213-fbb918af0b41", "grad_year": "2028"},
    ],
    "2028 canes national": [
        {"public_id": "pbcVpMwOqaDB", "internal_id": "7910c0e1-f5c7-4d78-bb22-deab3a0cc761", "grad_year": "2028"},
    ],
    "2028 franklin scout": [
        {"public_id": "hKiMjlr2Fy1v", "internal_id": "ab6ea9bf-2606-4986-aeb3-43d3805ffbc1", "grad_year": "2028"},
        {"public_id": "99GjKMKbVHGq", "internal_id": "8419b177-b119-416f-8a31-40df6872989c", "grad_year": "2028"},
        {"public_id": "XLBwEZq31n1w", "internal_id": "4ce74011-6388-480c-98a0-d561ba9c2a6e"},
    ],
    "2029 alpha prime": [
        {
            "public_id": "KdR6FtG9xzKl",
            "internal_id": "695b3946-d84e-4213-9ad8-82017509bf09",
            "grad_year": "2029",
        },
    ],
    "2029 norcal": [
        {"public_id": "id7ybiSJagA9", "internal_id": "cf85520d-ee97-4b8c-8704-f785971eaafc", "grad_year": "2029"},
    ],
    "2029 usa prime national": [
        {"public_id": "OidOhT3aGNFh", "internal_id": "5a005da8-ca7e-4e3c-93f5-44d2323390f4", "grad_year": "2029"},
        {"public_id": "5XqWs7hjR3mI", "internal_id": "6266b2b2-99fc-4e60-9930-61ec51500bd8", "grad_year": "2029"},
        {"public_id": "0FBXtZpQyaGl", "internal_id": "95696c70-d710-4efa-af23-9981a1835668", "grad_year": "2029"},
    ],
    "2030 usa prime national": [
        {"public_id": "qmGs6H3kV0XX", "internal_id": "aee5c3e3-76b0-4fe1-800f-35c0160a5528"},
        {"public_id": "bMc0qGma2n7C", "internal_id": "f82c9972-3bc5-4845-a0f2-725940f1225b", "grad_year": "2030"},
    ],
}
GC_PROGRAM_SEARCH_QUERIES: dict[str, list[str]] = {
    "2027 alpha prime": ["Alpha Prime 2027", "2027 Alpha Prime"],
    "2027 usa prime/detroit tigers scout": ["USA Prime Detroit Tigers", "Detroit Tigers Scout 2027"],
    "2027 canes national": ["Canes National 2027", "2027 Canes National"],
    "2027 norcal": ["NorCal 2027", "2027 NorCal"],
    "2027 top tier": ["Top Tier 2027", "2027 Top Tier"],
    "2028 alpha prime": ["Alpha Prime 2028", "2028 Alpha Prime"],
    "2028 norcal": ["NorCal 2028", "2028 NorCal"],
    "2028 canes national": ["Canes National 2028", "2028 Canes National"],
    "2028 franklin scout": ["Franklin Scout 2028", "2028 Franklin Scout"],
    "2028 mlb breakthrough": ["MLB Breakthrough 2028", "2028 MLB Breakthrough"],
    "2029 alpha prime": ["Alpha Prime 2029", "2029 Alpha Prime"],
    "2029 norcal": ["NorCal 2029", "2029 NorCal"],
    "2029 usa prime national": ["USA Prime National 2029", "USA Prime 2029 National"],
    "2030 usa prime national": ["USA Prime National 2030", "USA Prime 2030 National"],
}
_GC_DISCOVERED_TEAMS_CACHE: dict[str, list[dict[str, str]]] = {}
# HS clients without a Program column: map to AR-style summer program labels.
HS_SUMMER_PROGRAM_OVERRIDES: dict[str, str] = {
    "cooper vais": "2027 USA Prime/Detroit Tigers Scout",
    "enzi otieku": "2029 NorCal",
    "gavin mcmillan": "2027 Canes National",
    "jack leeper": "2027 Alpha Prime",
    "jaxxon tweedt": "2028 Alpha Prime",
}
ARB_TRACKER_SOURCE_XLSX = APEX_ROOT / "client_lists" / "DashboardArb.xlsx"
FA_TRACKER_SOURCE_XLSX = APEX_ROOT / "client_lists" / "DashboardFA.xlsx"
OUT_JSON = APEX_ROOT / "apex_dashboard_data.json"
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


def dashboard_date() -> date:
    """Calendar day in US Pacific; matches how we think about MLB/college night games."""
    return datetime.now(PACIFIC_TZ).date()


def last_night_date() -> date:
    """Report anchor day: yesterday in Pacific (never today's games)."""
    return dashboard_date() - timedelta(days=1)


def report_anchor_date() -> date:
    """Dashboard/PDF report day; override with APEX_REPORT_DATE=YYYY-MM-DD for backfills/previews."""
    raw = os.environ.get("APEX_REPORT_DATE", "").strip()
    if raw:
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            pass
    return last_night_date()


def gc_report_anchor_date() -> date:
    """Last-night anchor for GameChanger summer line pulls."""
    return report_anchor_date()


SEASON = dashboard_date().year
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
# TASBS boxes (data.{school}.com linked from athletics schedules) carry correct fractional IP;
# NCAA GraphQL often truncates (e.g. 1.2 -> 1.0).
TASBS_SCHEDULE_GAME_PATHS: dict[tuple[str, int], list[str]] = {}
TASBS_BOX_HTML_BY_URL: dict[str, str] = {}
# Norm school -> athletics baseball schedule when AmateurList Link column is empty.
COLLEGE_ATHLETICS_SCHEDULE_BY_SCHOOL: dict[str, str] = {
    "clemson": "https://clemsontigers.com/sports/baseball/schedule",
    "oregon": "https://goducks.com/sports/baseball/schedule",
}
D1_PLAYERS_SEARCH_JSON = "https://d1baseball.com/wp-content/themes/d1-staxx/data/2026-players.json"
D1_PLAYERS_INDEX: list[dict[str, Any]] | None = None
D1_PLAYER_STATS_CACHE: dict[str, dict[str, Any] | None] = {}
NCAA_SCHOOL_PAYLOAD_CACHE: dict[str, dict[str, Any]] = {}
NCAA_COLLEGE_LOCATION_CACHE: dict[str, str] = {}
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
    {
        "alyssa nakken",
        "jordan viars",
        "daulton jefferies",
        "adam wolf",
        "scott alexander",
        "colin barber",
    }
)
# Hidden from dashboard, PDF email, and site (all levels).
DASHBOARD_EXCLUDE_NAMES: frozenset[str] = frozenset(
    {
        "parker clubb",
        *PRO_CLIENT_EXCLUDE_NAMES,
    }
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
    # Tracker sheets often omit accents; Stats API search requires them.
    "huascar brazoban": "Huascar Brazobán",
    "adolis garcia": "Adolis García",
    "ramon urias": "Ramón Urías",
    "mauricio dubon": "Mauricio Dubón",
    "jose azocar": "José Azócar",
    "wenceel perez": "Wenceel Pérez",
    "dedniel nunez": "Dedniel Núñez",
}
# Sheet quirks: treat as hitter for college stat tables / D1 scrape.
COLLEGE_FORCE_HITTER_NAMES: frozenset[str] = frozenset({"ethan surowiec"})
COLLEGE_TWO_WAY_NAMES: frozenset[str] = frozenset({"evan dempsey", "talan bell"})
# HS sheet may list only RHP/LHP while the athlete also hits (MaxPreps has both game logs).
HS_TWO_WAY_NAMES: frozenset[str] = frozenset(
    {"jensen hirschkorn", "cooper vais", "enzi otieku"}
)
# Pitcher-only: do not add a hitter row when MaxPreps also has batting logs.
HS_PITCHER_ONLY_NAMES: frozenset[str] = frozenset(
    {
        "gavin mcmillan",
        "miles cornell",
        "austin rider",
        "chase cotton",
        "luke shoemaker",
    }
)
AMATEUR_TOKENS = ("NCAA", "COLLEGE", "JUCO", "HS", "HIGH SCHOOL")
TEAM_CATALOG: list[dict[str, Any]] | None = None
# (team_id, season) -> [(person_id, fullName), ...] for org roster scans when people/search fails.
ROSTER_CACHE: dict[tuple[int, int], list[tuple[int, str]]] = {}
# MLB + affiliated minors; used so call-ups and reassignments resolve from real game logs.
SPORT_IDS_PRO: tuple[int, ...] = (1, 11, 12, 13, 14, 15, 16, 17)
NCAA_SCHOOL_ALIASES: dict[str, tuple[str, ...]] = {
    # Common ncaa.com short-name variants
    "florida gulf coast": ("fgcu", "florida gulf coast"),
    "florida atlantic": ("fau", "florida atlantic", "fla atlantic"),
    "uc berkeley": ("cal", "california", "uc berkeley"),
}
# Big West teamstats.aspx `school=` slug -> official NCAA conference cumulative JSON (ERA/IP/ER
# agree with NCAA; D1Baseball scraping can drift — e.g. one extra earned run on the seasonal row).
BIG_WEST_TEAMSTATS_SLUG_BY_NORM_SCHOOL: dict[str, str] = {
    "cal poly": "calpoly",
    "cal poly san luis obispo": "calpoly",
}
BIG_WEST_TEAM_STATS_JSON_CACHE: dict[str, dict[str, Any] | None] = {}
FOREIGN_LEAGUES: frozenset[str] = frozenset({"NPB", "KBO", "CPBL"})
PRO_FOREIGN_BR_URLS: dict[str, str] = {
    # International pro stats on Baseball-Reference register pages.
    "spencer howard": "https://www.baseball-reference.com/register/player.fcgi?id=howard000spe",
    "jackson stephens": "https://www.baseball-reference.com/register/player.fcgi?id=stephe003jac",
    "mitch white": "https://www.baseball-reference.com/register/player.fcgi?id=white-000mit",
}
# Roster/Excel spelling -> key in PRO_FOREIGN_BR_URLS (same register player).
PRO_FOREIGN_BR_NAME_ALIASES: dict[str, str] = {
    "mitchell white": "mitch white",
}
FOREIGN_BR_SEASON_CACHE: dict[tuple[str, bool], dict[str, Any] | None] = {}
TRACKER_BREF_WAR_CACHE: dict[str, dict[str, Any]] = {}
TRACKER_PYB_SEASON_CACHE: dict[tuple[int, bool, str], pd.DataFrame | None] = {}
TRACKER_DEBUT_DATE_CACHE: dict[int, str] = {}


def _foreign_br_primary_norm(nn: str) -> str | None:
    """Canonical PRO_FOREIGN_BR_URLS key for a normalized client name, or None."""
    if nn in PRO_FOREIGN_BR_URLS:
        return nn
    primary = PRO_FOREIGN_BR_NAME_ALIASES.get(nn)
    if primary and primary in PRO_FOREIGN_BR_URLS:
        return primary
    return None


def _foreign_br_register_url(nn: str) -> str | None:
    k = _foreign_br_primary_norm(nn)
    return PRO_FOREIGN_BR_URLS.get(k) if k else None


def _is_foreign_br_register_client_norm(nn: str) -> bool:
    return _foreign_br_register_url(nn) is not None


def _foreign_league_schedule_url(league: str) -> str:
    """Official-ish schedule hub when a client is on KBO/NPB/CPBL (not in MLB Stats API)."""
    u = (league or "").strip().upper()
    if "KBO" in u:
        return "https://eng.koreabaseball.com/Schedule/DailySchedule.aspx"
    if "CPBL" in u:
        return "https://www.cpbl.com.tw/"
    if u.startswith("JP") or "NPB" in u:
        return "https://npb.jp/eng/"
    return ""
MANUAL_PRO_CLIENTS: list[dict[str, str]] = [
    {
        "name": "Aaron Shortridge",
        "position": "RHP",
        "level": "Rk",
        "league": "Florida Complex League",
        "minor_affiliate": "FCL Nationals",
        "major_affiliate": "Washington Nationals",
        "agent": "",
    }
]

# Rows missing from AmateurList.xlsx but tracked on the dashboard (Oregon, etc.).
MANUAL_AMATEUR_CLIENTS: list[dict[str, str]] = [
    {
        "name": "Jake Gregor",
        "position": "RHP",
        "school": "Oregon",
        "league": "Amateur",
        "agent": "",
        "schedule_link": "https://goducks.com/sports/baseball/schedule",
    },
    {
        "name": "LJ Edwards",
        "position": "OF",
        "school": "",
        "league": "Amateur",
        "agent": "",
        "schedule_link": "",
    },
]

# College summer assignments tracked on the amateur tab (Stats API sportId 22).
SUMMER_AMATEUR_OVERRIDES: dict[str, dict[str, Any]] = {
    "elai iwanaga": {
        "summer_team": "Orleans Firebirds",
        "summer_league": "Cape Cod Baseball League",
        "team_level": "CCL",
        "team_id": 6102,
        "league_id": 565,
        "schedule_url": "https://www.capecodleague.com/scores",
        "player_id": 828233,
    },
    "rowan kelly": {
        "summer_team": "Orleans Firebirds",
        "summer_league": "Cape Cod Baseball League",
        "team_level": "CCL",
        "team_id": 6102,
        "league_id": 565,
        "schedule_url": "https://www.capecodleague.com/scores",
    },
    "ray olivas": {
        "summer_team": "Hyannis Harbor Hawks",
        "summer_league": "Cape Cod Baseball League",
        "team_level": "CCL",
        "team_id": 6101,
        "league_id": 565,
        "schedule_url": "https://www.capecodleague.com/scores",
        "player_id": 842080,
        "name_aliases": ["Raymond Olivas"],
    },
    "raymond olivas": {
        "summer_team": "Hyannis Harbor Hawks",
        "summer_league": "Cape Cod Baseball League",
        "team_level": "CCL",
        "team_id": 6101,
        "league_id": 565,
        "schedule_url": "https://www.capecodleague.com/scores",
        "player_id": 842080,
    },
    "lj edwards": {
        "summer_team": "Burlington Sock Puppets",
        "summer_league": "MLB Draft League",
        "team_level": "MBDL",
        "team_id": 483,
        "league_id": 120,
        "schedule_url": "https://www.mlbdraftleague.com/scores",
        "player_id": 815817,
    },
    "sean mcgrath": {
        "summer_team": "Wenatchee AppleSox",
        "summer_league": "West Coast League",
        "team_level": "WCL",
        "schedule_url": "https://wclstats.com/sports/bsb/2026/teams/wenatcheeapplesox",
        "stats_source": "wcl",
        "wcl_team_id": "xjbohafz57d8cauh",
    },
    "jackson flora": {
        "summer_team": "Marion Berries",
        "summer_league": "West Coast League",
        "team_level": "WCL",
        "schedule_url": "https://wclstats.com/sports/bsb/2026/teams/marionberries",
        "stats_source": "wcl",
        "wcl_team_id": "txq616nqlxf0lsiv",
        "name_aliases": ["Hudson Flora"],
    },
    "brayden jaksa": {
        "summer_team": "Harwich Mariners",
        "summer_league": "Cape Cod Baseball League",
        "team_level": "CCL",
        "team_id": 6100,
        "league_id": 565,
        "schedule_url": "https://www.capecodleague.com/scores",
        "player_id": 815984,
    },
    "wade walton": {
        "summer_team": "Wareham Gatemen",
        "summer_league": "Cape Cod Baseball League",
        "team_level": "CCL",
        "team_id": 6103,
        "league_id": 565,
        "schedule_url": "https://www.capecodleague.com/scores",
        "player_id": 816132,
    },
}
WCL_PLAYERS_DATA_URL = (
    "https://prestosports-downloads.s3.us-west-2.amazonaws.com/playersData/oc90tg1ho5rh9ixu.json"
)
_WCL_PLAYERS_CACHE: list[dict[str, Any]] | None = None
SPORT_ID_COLLEGE = 22


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
    schedule_link: str = ""


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


def _college_home_location(name: str) -> str:
    key = (name or "").strip()
    if not key:
        return ""
    if key in NCAA_COLLEGE_LOCATION_CACHE:
        return NCAA_COLLEGE_LOCATION_CACHE[key]
    try:
        url = (
            "https://geocoding-api.open-meteo.com/v1/search?"
            + urllib.parse.urlencode({"name": f"{key} university", "count": 1, "language": "en", "format": "json"})
        )
        js = _req_json(url, timeout=15, retries=2)
        row = (js.get("results") or [{}])[0]
        city = str(row.get("name") or "").strip()
        admin = str(row.get("admin1") or "").strip()
        loc = f"{city}, {admin}".strip(", ") if city else ""
    except Exception:
        loc = ""
    NCAA_COLLEGE_LOCATION_CACHE[key] = loc
    return loc


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
    x = unicodedata.normalize("NFD", x)
    x = "".join(ch for ch in x if unicodedata.category(ch) != "Mn")
    x = re.sub(r"[^a-z0-9]+", "", x)
    return x


def _norm_player_name(s: str) -> str:
    x = (s or "").strip().lower()
    x = unicodedata.normalize("NFD", x)
    x = "".join(ch for ch in x if unicodedata.category(ch) != "Mn")
    x = x.replace(".", " ").replace(",", " ").replace("-", " ")
    parts = [p for p in x.split() if p not in {"jr", "sr", "ii", "iii", "iv"}]
    return " ".join(parts)


TRACKER_PINNED_ARB: tuple[str, ...] = (
    "Lucas Erceg",
    "Bryan Woo",
    "James Outman",
    "Riley Greene",
    "Matt Vierling",
    "Kyle Tucker",
    "Franmil Reyes",
)
TRACKER_PINNED_FA: tuple[str, ...] = ("Brock Burke", "Kris Bubic", "Ryan Mountcastle")
TRACKER_BREF_URLS: dict[str, str] = {
    "bryan woo": "https://www.baseball-reference.com/players/w/woobr01.shtml",
    "lucas erceg": "https://www.baseball-reference.com/players/e/erceglu01.shtml",
    "james outman": "https://www.baseball-reference.com/players/o/outmaja01.shtml",
    "riley greene": "https://www.baseball-reference.com/players/g/greenri03.shtml",
    "matt vierling": "https://www.baseball-reference.com/players/v/vierlma01.shtml",
    "kyle tucker": "https://www.baseball-reference.com/players/t/tuckeky01.shtml",
    "franmil reyes": "https://www.baseball-reference.com/players/r/reyesfr01.shtml",
    "brock burke": "https://www.baseball-reference.com/players/b/burkebr01.shtml",
    "kris bubic": "https://www.baseball-reference.com/players/b/bubickr01.shtml",
    "ryan mountcastle": "https://www.baseball-reference.com/players/m/mountry01.shtml",
}

# Extra arbitration rows (2026 OF comps by service-time tier) merged into DashboardArb.
TRACKER_ARB_SUPPLEMENT: tuple[dict[str, Any], ...] = (
    # ~3.1 years MLS (Riley Greene cohort)
    {"name": "Riley Greene", "primary_position": "LF", "mls": 3.110, "age": 25, "debut_year": 2022, "year": 2026},
    {"name": "Jarren Duran", "primary_position": "CF", "mls": 3.155, "age": 29, "debut_year": 2022, "year": 2026},
    {"name": "Oneil Cruz", "primary_position": "CF", "mls": 3.110, "age": 27, "debut_year": 2022, "year": 2026},
    {"name": "Kerry Carpenter", "primary_position": "RF", "mls": 3.057, "age": 28, "debut_year": 2022, "year": 2026},
    {"name": "Josh Lowe", "primary_position": "LF", "mls": 3.093, "age": 28, "debut_year": 2022, "year": 2026},
    {"name": "Alek Thomas", "primary_position": "CF", "mls": 3.103, "age": 26, "debut_year": 2022, "year": 2026},
    {"name": "Jake McCarthy", "primary_position": "LF", "mls": 3.124, "age": 28, "debut_year": 2022, "year": 2026},
    {"name": "Derek Hill", "primary_position": "CF", "mls": 3.040, "age": 30, "debut_year": 2021, "year": 2026},
    {"name": "Eli White", "primary_position": "OF", "mls": 3.140, "age": 32, "debut_year": 2022, "year": 2026},
    {"name": "Nolan Jones", "primary_position": "RF", "mls": 3.007, "age": 28, "debut_year": 2022, "year": 2026},
    {"name": "Will Benson", "primary_position": "RF", "mls": 3.003, "age": 28, "debut_year": 2022, "year": 2026},
    # Precedent comps at ~3.1 MLS (stats from their first-arb seasons)
    {
        "name": "Kyle Tucker",
        "primary_position": "RF",
        "mls": 3.079,
        "age": 26,
        "debut_year": 2018,
        "year": 2023,
        "tracker_stat_years": [2022, 2021, 2020],
        "tracker_career_through": 2022,
        "yearly_salary_3": 5_000_000,
        "comp_note": "2023 1st arb",
        "comp_kind": "precedent",
    },
    {
        "name": "Franmil Reyes",
        "primary_position": "RF",
        "mls": 3.115,
        "age": 26,
        "debut_year": 2018,
        "year": 2022,
        "tracker_stat_years": [2021, 2020, 2019],
        "tracker_career_through": 2021,
        "yearly_salary_3": 4_550_000,
        "comp_note": "2022 1st arb",
        "comp_kind": "precedent",
    },
    # ~4.0 years MLS (Matt Vierling cohort)
    {"name": "Matt Vierling", "primary_position": "OF", "mls": 4.026, "age": 29, "debut_year": 2021, "year": 2026},
    {"name": "Steven Kwan", "primary_position": "LF", "mls": 4.000, "age": 28, "debut_year": 2021, "year": 2026},
    {"name": "Lars Nootbaar", "primary_position": "LF", "mls": 4.076, "age": 28, "debut_year": 2021, "year": 2026},
    {"name": "Brandon Marsh", "primary_position": "LF", "mls": 4.078, "age": 28, "debut_year": 2021, "year": 2026},
    {"name": "Jo Adell", "primary_position": "RF", "mls": 4.085, "age": 27, "debut_year": 2020, "year": 2026},
    {"name": "Jesus Sanchez", "primary_position": "LF", "mls": 4.118, "age": 28, "debut_year": 2020, "year": 2026},
    {"name": "Kyle Isbel", "primary_position": "CF", "mls": 4.043, "age": 29, "debut_year": 2021, "year": 2026},
    {"name": "Jake Meyers", "primary_position": "CF", "mls": 4.044, "age": 30, "debut_year": 2021, "year": 2026},
)

TRACKER_BASE_FIELDS = (
    "name",
    "age",
    "year",
    "debut_year",
    "primary_position",
    "mls",
    "awards",
    "award_votes",
    "il_stints_sheet",
    "yearly_salary_3",
    "yearly_salary_4",
)


def _tracker_json_num(v: Any) -> int | float | str | None:
    n = to_number(v)
    if n is not None:
        return n
    s = str(v or "").strip()
    return s or None


def _tracker_col(row: pd.Series, cols: dict[str, str], name: str) -> Any:
    c = cols.get(name.lower())
    return row.get(c) if c else None


def _find_tracker_header_row(df: pd.DataFrame) -> int | None:
    for i, row in df.iterrows():
        v0 = str(row.iloc[0] or "").strip().lower()
        if "player" in v0 and "(1)" in v0:
            return int(i)
    return None


def _load_tracker_sheet(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    raw = pd.read_excel(path)
    hi = _find_tracker_header_row(raw)
    if hi is None:
        return []
    header = [str(v).strip() for v in raw.iloc[hi].tolist()]
    body = raw.iloc[hi + 1 :].copy()
    body.columns = header
    out: list[dict[str, Any]] = []
    cols = {str(c).strip().lower(): str(c) for c in body.columns}
    for _, row in body.iterrows():
        name_raw = _tracker_col(row, cols, "player(1)")
        if pd.isna(name_raw):
            continue
        name = _parse_name(_clean_text(name_raw))
        if not name:
            continue
        age = _tracker_json_num(_tracker_col(row, cols, "age(1)"))
        debut = _tracker_json_num(_tracker_col(row, cols, "debut year(1)"))
        year = _tracker_json_num(_tracker_col(row, cols, "year(1)"))
        primary_position = _clean_text(_tracker_col(row, cols, "primary position(1)")).upper()
        if not primary_position:
            continue
        out.append(
            {
                "name": name,
                "name_norm": _norm_player_name(name),
                "age": age,
                "year": year,
                "debut_year": debut,
                "primary_position": primary_position,
                "mls": _tracker_json_num(_tracker_col(row, cols, "mls(2)")),
                "awards": [_clean_text(_tracker_col(row, cols, k)) for k in ("awards(1)", "awards(3)", "awards(4)") if _clean_text(_tracker_col(row, cols, k))],
                "award_votes": [_clean_text(_tracker_col(row, cols, k)) for k in ("award votes(1)", "award votes(3)", "award votes(4)") if _clean_text(_tracker_col(row, cols, k))],
                "il_stints_sheet": _clean_text(_tracker_col(row, cols, "il(2)")),
                "yearly_salary_3": _tracker_json_num(_tracker_col(row, cols, "yearly salary(3)")),
                "yearly_salary_4": _tracker_json_num(_tracker_col(row, cols, "yearly salary(4)")),
            }
        )
    return out


def _tracker_base_row(row: dict[str, Any]) -> dict[str, Any]:
    awards = row.get("awards") if isinstance(row.get("awards"), list) else []
    votes = row.get("award_votes") if isinstance(row.get("award_votes"), list) else []
    base = {
        "name": row.get("name", ""),
        "name_norm": _norm_player_name(row.get("name", "")),
        "age": row.get("age"),
        "year": row.get("year") or SEASON,
        "debut_year": row.get("debut_year"),
        "primary_position": str(row.get("primary_position", "")).upper(),
        "mls": row.get("mls"),
        "awards": awards,
        "award_votes": votes,
        "il_stints_sheet": row.get("il_stints_sheet", ""),
        "yearly_salary_3": row.get("yearly_salary_3"),
        "yearly_salary_4": row.get("yearly_salary_4"),
    }
    for extra in ("tracker_stat_years", "tracker_career_through", "comp_note", "comp_kind"):
        if row.get(extra) not in (None, ""):
            base[extra] = row.get(extra)
    return base


def _sum_tracker_hitting_lines(lines: list[dict[str, Any]]) -> dict[str, Any]:
    if not lines:
        return {}
    int_keys = (
        "atBats",
        "runs",
        "hits",
        "rbi",
        "homeRuns",
        "doubles",
        "stolenBases",
        "strikeOuts",
        "baseOnBalls",
        "hr",
        "sb",
        "k",
        "bb",
        "gamesStarted",
        "games_started",
    )
    out: dict[str, Any] = {k: 0 for k in int_keys}
    war = 0.0
    saw_war = False
    for line in lines:
        for k in int_keys:
            out[k] = int(out[k]) + int(_safe_int(line.get(k)) or 0)
        if line.get("war") not in (None, ""):
            war += _to_float(line.get("war"))
            saw_war = True
    if saw_war:
        out["war"] = round(war, 1)
    ab = _to_float(out.get("atBats"))
    h = _to_float(out.get("hits"))
    if ab > 0:
        out["avg"] = round(h / ab, 3)
    return out


def _sum_tracker_pitching_lines(lines: list[dict[str, Any]]) -> dict[str, Any]:
    if not lines:
        return {}
    int_keys = (
        "wins",
        "saves",
        "hits",
        "runs",
        "earnedRuns",
        "baseOnBalls",
        "strikeOuts",
        "homeRuns",
        "gamesStarted",
        "battersFaced",
        "w",
        "k",
        "bb",
        "hr",
        "qs",
    )
    out: dict[str, Any] = {k: 0 for k in int_keys}
    ip_total = 0.0
    war = 0.0
    saw_war = False
    for line in lines:
        for k in int_keys:
            out[k] = int(out[k]) + int(_safe_int(line.get(k)) or 0)
        ip_total += _to_float(line.get("inningsPitched") or line.get("ip"))
        if line.get("war") not in (None, ""):
            war += _to_float(line.get("war"))
            saw_war = True
    if ip_total > 0:
        out["inningsPitched"] = round(ip_total, 1)
        out["ip"] = out["inningsPitched"]
    if saw_war:
        out["war"] = round(war, 1)
    return out


def _merge_tracker_supplements(rows: list[dict[str, Any]], supplements: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    by_norm = {_norm_player_name(r.get("name", "")): r for r in rows if r.get("name")}
    for item in supplements:
        base = _tracker_base_row(item)
        if not base.get("name") or not base.get("primary_position"):
            continue
        by_norm[base["name_norm"]] = base
    return list(by_norm.values())


def _load_tracker_rows(path: Path, fallback_rows: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows = _load_tracker_sheet(path)
    if rows:
        return rows
    if not fallback_rows:
        return []
    return [_tracker_base_row(r) for r in fallback_rows if r.get("name")]


def _mlb_stat_line_for_year(player_id: int, group: str, season_year: int) -> dict[str, Any]:
    try:
        return fetch_player_stats_preferred_then_all_sports(player_id, group, "season", 1, season=season_year)
    except Exception:
        return {}


def _mlb_stat_line_career(player_id: int, group: str) -> dict[str, Any]:
    try:
        return fetch_player_stats_preferred_then_all_sports(player_id, group, "career", 1)
    except Exception:
        return {}


def _tracker_pitching_line(raw: dict[str, Any]) -> dict[str, Any]:
    bf = _to_float(raw.get("battersFaced"))
    bb = _to_float(raw.get("baseOnBalls"))
    kk = _to_float(raw.get("strikeOuts"))
    out = {
        "inningsPitched": json_stat_value("inningsPitched", raw.get("inningsPitched")),
        "wins": _tracker_json_num(raw.get("wins")),
        "saves": _tracker_json_num(raw.get("saves")),
        "hits": _tracker_json_num(raw.get("hits")),
        "runs": _tracker_json_num(raw.get("runs")),
        "earnedRuns": _tracker_json_num(raw.get("earnedRuns")),
        "baseOnBalls": _tracker_json_num(raw.get("baseOnBalls")),
        "strikeOuts": _tracker_json_num(raw.get("strikeOuts")),
        "homeRuns": _tracker_json_num(raw.get("homeRuns")),
        "gamesStarted": _tracker_json_num(raw.get("gamesStarted")),
        "battersFaced": _tracker_json_num(raw.get("battersFaced")),
        "ip": json_stat_value("inningsPitched", raw.get("inningsPitched")),
        "w": _tracker_json_num(raw.get("wins")),
        "k": _tracker_json_num(raw.get("strikeOuts")),
        "bb": _tracker_json_num(raw.get("baseOnBalls")),
        "qs": _tracker_json_num(raw.get("qualityStarts")),
        "bb_pct": round((bb / bf) * 100, 1) if bf > 0 else None,
        "k_pct": round((kk / bf) * 100, 1) if bf > 0 else None,
        "whip": _tracker_json_num(raw.get("whip")),
        "era": _tracker_json_num(raw.get("era")),
    }
    return out


def _tracker_hitting_line(raw: dict[str, Any]) -> dict[str, Any]:
    pa = _to_float(raw.get("plateAppearances"))
    bb = _to_float(raw.get("baseOnBalls"))
    kk = _to_float(raw.get("strikeOuts"))
    out = {
        "atBats": _tracker_json_num(raw.get("atBats")),
        "runs": _tracker_json_num(raw.get("runs")),
        "hits": _tracker_json_num(raw.get("hits")),
        "rbi": _tracker_json_num(raw.get("rbi")),
        "baseOnBalls": _tracker_json_num(raw.get("baseOnBalls")),
        "homeRuns": _tracker_json_num(raw.get("homeRuns")),
        "doubles": _tracker_json_num(raw.get("doubles")),
        "stolenBases": _tracker_json_num(raw.get("stolenBases")),
        "strikeOuts": _tracker_json_num(raw.get("strikeOuts")),
        "obp": _tracker_json_num(raw.get("obp")),
        "hr": _tracker_json_num(raw.get("homeRuns")),
        "sb": _tracker_json_num(raw.get("stolenBases")),
        "avg": _tracker_json_num(raw.get("avg")),
        "slg": _tracker_json_num(raw.get("slg")),
        "ops": _tracker_json_num(raw.get("ops")),
        "k": _tracker_json_num(raw.get("strikeOuts")),
        "bb": _tracker_json_num(raw.get("baseOnBalls")),
        "k_pct": round((kk / pa) * 100, 1) if pa > 0 else None,
        "bb_pct": round((bb / pa) * 100, 1) if pa > 0 else None,
        "gamesStarted": _tracker_json_num(raw.get("gamesStarted")),
        "games_started": _tracker_json_num(raw.get("gamesStarted")),
    }
    if out.get("ops") in (None, ""):
        obp = _to_float(raw.get("obp"))
        slg = _to_float(raw.get("slg"))
        if obp > 0 or slg > 0:
            out["ops"] = round(obp + slg, 3)
    return out


def _ensure_ops_from_obp_slg(st: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(st, dict):
        return st
    if st.get("ops") not in (None, ""):
        return st
    obp = _to_float(st.get("obp"))
    slg = _to_float(st.get("slg"))
    if obp > 0 or slg > 0:
        st["ops"] = round(obp + slg, 3)
    return st


def _fetch_bref_war_by_year(player_name: str, is_pitcher_role: bool) -> dict[str, Any]:
    nn = _norm_player_name(player_name)
    if nn in TRACKER_BREF_WAR_CACHE:
        return TRACKER_BREF_WAR_CACHE[nn]
    url = TRACKER_BREF_URLS.get(nn, "")
    if not url:
        TRACKER_BREF_WAR_CACHE[nn] = {"war_by_year": {}, "teams_by_year": {}}
        return TRACKER_BREF_WAR_CACHE[nn]
    war_by_year: dict[str, Any] = {}
    teams_by_year: dict[str, str] = {}
    try:
        html = requests.get(url, timeout=35, headers=_HTTP_HEADERS).text
        blobs = [html]
        # Baseball-Reference keeps key tables in HTML comments.
        blobs.extend(re.findall(r"<!--(.*?)-->", html, flags=re.S))
        dfs: list[pd.DataFrame] = []
        for blob in blobs:
            if "WAR" not in blob or "Year" not in blob:
                continue
            try:
                dfs.extend(pd.read_html(StringIO(blob)))
            except Exception:
                continue
        for raw in dfs:
            df = _flatten_columns(raw.copy())
            cols = [str(c) for c in df.columns]
            year_col = _find_col(cols, ("Year",))
            team_col = _find_col(cols, ("Tm", "Team"))
            war_col = _find_col(cols, ("WAR",))
            if not year_col or not war_col:
                continue
            for _, row in df.iterrows():
                y = _year_as_int(row.get(year_col))
                if y is None:
                    continue
                war_val = to_number(row.get(war_col))
                if war_val is not None:
                    war_by_year[str(y)] = war_val
                if team_col:
                    tm = str(row.get(team_col) or "").strip()
                    if tm and tm not in {"TOT", "Team"}:
                        teams_by_year[str(y)] = tm
            if war_by_year:
                break
    except Exception:
        pass
    TRACKER_BREF_WAR_CACHE[nn] = {"war_by_year": war_by_year, "teams_by_year": teams_by_year}
    return TRACKER_BREF_WAR_CACHE[nn]


def _pyb_season_war_table(year: int, is_pitcher_role: bool) -> pd.DataFrame | None:
    key = (int(year), bool(is_pitcher_role), "legacy")
    if key in TRACKER_PYB_SEASON_CACHE:
        return TRACKER_PYB_SEASON_CACHE[key]
    try:
        from pybaseball import bwar_bat, bwar_pitch

        df = bwar_pitch() if is_pitcher_role else bwar_bat()
    except Exception:
        TRACKER_PYB_SEASON_CACHE[key] = None
        return None
    TRACKER_PYB_SEASON_CACHE[key] = df if isinstance(df, pd.DataFrame) else None
    return TRACKER_PYB_SEASON_CACHE[key]


def _bwar_career_total(player_name: str, is_pitcher_role: bool) -> float | None:
    """Full career Baseball-Reference WAR total from pybaseball bWAR tables (all seasons)."""
    df = _pyb_season_war_table(SEASON, is_pitcher_role)
    if df is None or df.empty or "name_common" not in df.columns or "WAR" not in df.columns:
        return None
    nn = _norm_player_name(player_name)
    mask = df["name_common"].astype(str).map(_norm_player_name) == nn
    hit = df[mask]
    if hit.empty:
        return None
    total = sum(_to_float(x) for x in hit["WAR"].tolist())
    return round(total, 1)


def _fetch_war_by_year(player_name: str, is_pitcher_role: bool) -> dict[str, Any]:
    out: dict[str, Any] = {}
    df = _pyb_season_war_table(SEASON, is_pitcher_role)
    if df is not None and not df.empty and "name_common" in df.columns and "year_ID" in df.columns:
        mask = df["name_common"].astype(str).map(_norm_player_name) == _norm_player_name(player_name)
        hit = df[mask]
        if not hit.empty:
            for y in (SEASON, SEASON - 1, SEASON - 2):
                yr = hit[hit["year_ID"] == y]
                if yr.empty:
                    continue
                war_sum = yr["WAR"].apply(_to_float).sum() if "WAR" in yr.columns else 0.0
                out[str(y)] = round(war_sum, 2)
    if out:
        return out
    # Fallback to Baseball-Reference scrape when pybaseball lookup fails.
    return _fetch_bref_war_by_year(player_name, is_pitcher_role).get("war_by_year", {})


def _bulk_war_maps() -> dict[str, dict[str, Any]]:
    """
    Build normalized-name -> {year: WAR} maps for all rows from bWAR tables.
    Returns dict with keys: pitcher, hitter.
    """
    out: dict[str, dict[str, dict[str, Any]]] = {"pitcher": {}, "hitter": {}}
    for role_key, is_pitcher_role in (("pitcher", True), ("hitter", False)):
        df = _pyb_season_war_table(SEASON, is_pitcher_role)
        if df is None or df.empty or "name_common" not in df.columns or "year_ID" not in df.columns:
            continue
        for _, row in df.iterrows():
            y = _year_as_int(row.get("year_ID"))
            if y is None or y not in {SEASON, SEASON - 1, SEASON - 2}:
                continue
            nn = _norm_player_name(str(row.get("name_common") or ""))
            if not nn:
                continue
            war = to_number(row.get("WAR"))
            if war is None:
                continue
            cur = out[role_key].setdefault(nn, {})
            cur[str(y)] = round(_to_float(cur.get(str(y))) + _to_float(war), 2)
    return out


def _fetch_player_transactions_summary(player_id: int, debut_year: int | None) -> dict[str, Any]:
    start = f"{max(2018, int(debut_year or SEASON - 7))}-01-01"
    end = dashboard_date().isoformat()
    out = {"il_stints_live": 0, "minor_league_moves": 0}
    try:
        url = f"{API}/transactions?" + urllib.parse.urlencode({"playerId": player_id, "startDate": start, "endDate": end})
        js = _req_json(url, timeout=35, retries=2)
        txs = js.get("transactions") or []
        for tx in txs:
            desc = str(tx.get("description") or "").lower()
            typ = str(tx.get("typeCode") or "").lower()
            if "injured list" in desc or typ in {"udl", "d60", "d15", "d10", "d7"}:
                out["il_stints_live"] += 1
            # Tightened "broken service" signal:
            # count only clear MLB<->minors service breaks and ignore rehab/admin moves.
            if "rehab assignment" in desc or "rehabilitation assignment" in desc:
                continue
            minor_move = (
                ("optioned to" in desc and "optioned to mlb" not in desc)
                or ("outrighted to" in desc)
                or ("sent outright to minors" in desc)
                or ("assigned to" in desc and "triple-a" in desc)
                or ("assigned to" in desc and "double-a" in desc)
                or ("assigned to" in desc and "high-a" in desc)
                or ("assigned to" in desc and "single-a" in desc)
                or ("assigned to" in desc and "rookie" in desc)
            )
            if minor_move:
                out["minor_league_moves"] += 1
    except Exception:
        pass
    return out


def _fetch_player_debut_date(player_id: int) -> str:
    if player_id in TRACKER_DEBUT_DATE_CACHE:
        return TRACKER_DEBUT_DATE_CACHE[player_id]
    val = ""
    try:
        js = _req_json(f"{API}/people/{player_id}", timeout=25, retries=2)
        p = (js.get("people") or [{}])[0]
        val = str(p.get("mlbDebutDate") or "").strip()
    except Exception:
        val = ""
    TRACKER_DEBUT_DATE_CACHE[player_id] = val
    return val


def _service_time_to_days(mls: Any) -> int | None:
    s = _clean_text(mls)
    if not s:
        return None
    m = re.fullmatch(r"(\d+)(?:\.(\d{1,3}))?", s)
    if m:
        years = int(m.group(1))
        days_s = (m.group(2) or "0").ljust(3, "0")[:3]
        days = int(days_s)
        return years * 172 + days
    try:
        f = float(s)
        years = int(f)
        days = int(round((f - years) * 1000))
        return years * 172 + max(0, days)
    except Exception:
        return None


def _estimated_max_service_days_entering_season(debut_date_iso: str, fallback_debut_year: int | None) -> int | None:
    """
    Approx max service days entering current season based on promotion/debut date.
    Uses MLB season-day envelope (max 187 service days in debut season) and
    caps each full subsequent season to 172 for one full service year.
    """
    debut_y = fallback_debut_year
    md = ""
    if debut_date_iso:
        try:
            d = datetime.strptime(debut_date_iso, "%Y-%m-%d").date()
            debut_y = d.year
            md = d.strftime("%m-%d")
        except Exception:
            pass
    if not debut_y or debut_y >= SEASON:
        return None
    # Approx opening day anchor for debut-season remaining service days.
    # Conservative envelope to avoid false positives.
    season_start = date(debut_y, 3, 20)
    season_days = 187
    debut_days = 172
    if md:
        try:
            d0 = datetime.strptime(f"{debut_y}-{md}", "%Y-%m-%d").date()
            offset = max(0, (d0 - season_start).days)
            rem = max(0, season_days - offset)
            debut_days = min(172, rem)
        except Exception:
            debut_days = 172
    full_years_after = max(0, SEASON - debut_y - 1)
    return debut_days + (172 * full_years_after)


def _enrich_tracker_player(row: dict[str, Any]) -> dict[str, Any]:
    name = row.get("name", "")
    pos = str(row.get("primary_position", "")).upper()
    is_pitcher_role = pos in PITCHER_POS or pos in {"SP", "RP"}
    c = Client(
        name=name,
        position="P" if is_pitcher_role else "OF",
        level="MLB",
        league="MLB",
        minor_affiliate="",
        major_affiliate="",
        agent="",
        agent_last="",
        is_amateur=False,
    )
    pid = resolve_player_id(c)
    stat_years_raw = row.get("tracker_stat_years")
    if isinstance(stat_years_raw, (list, tuple)) and stat_years_raw:
        years = [int(y) for y in stat_years_raw]
    else:
        years = [SEASON, SEASON - 1, SEASON - 2]
    group = "pitching" if is_pitcher_role else "hitting"
    by_year: dict[str, Any] = {}
    for y in years:
        raw = _mlb_stat_line_for_year(pid, group, y) if pid else {}
        by_year[str(y)] = _tracker_pitching_line(raw) if is_pitcher_role else _tracker_hitting_line(raw)
    career_through = _safe_int(row.get("tracker_career_through"))
    if career_through and pid:
        debut_y = _safe_int(row.get("debut_year")) or career_through
        career_years = list(range(debut_y, career_through + 1))
        career_lines = []
        for y in career_years:
            raw = _mlb_stat_line_for_year(pid, group, y)
            career_lines.append(
                _tracker_pitching_line(raw) if is_pitcher_role else _tracker_hitting_line(raw)
            )
        career = (
            _sum_tracker_pitching_lines(career_lines)
            if is_pitcher_role
            else _sum_tracker_hitting_lines(career_lines)
        )
    else:
        raw_career = _mlb_stat_line_career(pid, group) if pid else {}
        career = _tracker_pitching_line(raw_career) if is_pitcher_role else _tracker_hitting_line(raw_career)
    bref = _fetch_bref_war_by_year(name, is_pitcher_role)
    war_by_year = _fetch_war_by_year(name, is_pitcher_role)
    teams_by_year = bref.get("teams_by_year", {})
    debut_year_i = _safe_int(row.get("debut_year"))
    tx = _fetch_player_transactions_summary(pid, debut_year_i) if pid else {"il_stints_live": 0, "minor_league_moves": 0}
    for y in list(by_year.keys()):
        yr_key = str(y)
        by_year[yr_key]["war"] = war_by_year.get(yr_key)
        if by_year[yr_key]["war"] is None:
            by_year[yr_key]["war"] = bref.get("war_by_year", {}).get(yr_key)
    if career_through:
        partial_war = 0.0
        saw_partial = False
        for yr_s, wv in (bref.get("war_by_year") or {}).items():
            yr_i = _year_as_int(yr_s)
            if yr_i is None or yr_i > career_through:
                continue
            partial_war += _to_float(wv)
            saw_partial = True
        career_bwar = round(partial_war, 1) if saw_partial else None
    else:
        career_bwar = _bwar_career_total(name, is_pitcher_role)
    if career_bwar is None:
        bref_wars = bref.get("war_by_year") or {}
        partial = 0.0
        saw = False
        for yr_s, wv in bref_wars.items():
            if _year_as_int(yr_s) is None:
                continue
            if career_through and _year_as_int(yr_s) > career_through:
                continue
            partial += _to_float(wv)
            saw = True
        if saw:
            career_bwar = round(partial, 1)
    if career_bwar is None and war_by_year:
        vals = []
        for yr_s, wv in war_by_year.items():
            yr_i = _year_as_int(yr_s)
            if career_through and yr_i is not None and yr_i > career_through:
                continue
            vals.append(_to_float(wv))
        if vals:
            career_bwar = round(sum(vals), 1)
    career["war"] = career_bwar
    row["career_bwar"] = career_bwar
    row["stats_by_year"] = by_year
    row["stats_career"] = career
    row["teams_by_year"] = teams_by_year
    row["il_stints_live"] = tx.get("il_stints_live", 0)
    row["minor_league_moves"] = tx.get("minor_league_moves", 0)
    if row.get("comp_kind") == "precedent":
        row["broken_service"] = "No"
    else:
        debut_date = _fetch_player_debut_date(pid) if pid else ""
        service_days = _service_time_to_days(row.get("mls"))
        max_days = _estimated_max_service_days_entering_season(debut_date, debut_year_i)
        service_gap_broken = bool(
            service_days is not None and max_days is not None and service_days + 20 < max_days
        )
        row["broken_service"] = "Yes" if (tx.get("minor_league_moves", 0) > 0 or service_gap_broken) else "No"
    row["position_group"] = "SP" if pos == "SP" else "RP" if pos == "RP" else "OF" if pos in {"LF", "RF", "CF"} else pos
    return row


def build_tracker_data(
    path: Path,
    pinned_names: tuple[str, ...],
    *,
    fallback_rows: list[dict[str, Any]] | None = None,
    supplements: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    rows = _load_tracker_rows(path, fallback_rows)
    if supplements:
        rows = _merge_tracker_supplements(rows, supplements)
    if not rows:
        return {"rows": [], "pinned": [], "year_options": [str(SEASON), str(SEASON - 1), str(SEASON - 2), "career"]}
    pinned_norm = {_norm_player_name(n) for n in pinned_names}
    war_maps = _bulk_war_maps()
    # Populate WAR for every row so wide tables can show it globally.
    for i, r in enumerate(rows):
        pos = str(r.get("primary_position", "")).upper()
        is_pitcher_role = pos in PITCHER_POS or pos in {"SP", "RP"}
        role_key = "pitcher" if is_pitcher_role else "hitter"
        wn = war_maps.get(role_key, {}).get(r.get("name_norm", ""), {})
        row_years: dict[str, Any] = {
            str(SEASON): {"war": wn.get(str(SEASON))},
            str(SEASON - 1): {"war": wn.get(str(SEASON - 1))},
            str(SEASON - 2): {"war": wn.get(str(SEASON - 2))},
        }
        row_career_war = round(sum(_to_float(v) for v in wn.values()), 1) if wn else None
        r["stats_by_year"] = row_years
        r["stats_career"] = {"war": row_career_war}
        r["broken_service"] = r.get("broken_service", "No")
        rows[i] = r
    rows = [
        r
        for r in _parallel_map(rows, _enrich_tracker_player, max_workers=8)
        if isinstance(r, dict)
    ]
    # Remove players with negative career bWAR from tracker lists.
    filtered_rows: list[dict[str, Any]] = []
    for r in rows:
        if r.get("name_norm") in DASHBOARD_EXCLUDE_NAMES:
            continue
        cbwar = r.get("career_bwar")
        if cbwar is not None and float(cbwar) < 0 and r.get("comp_kind") != "precedent":
            continue
        filtered_rows.append(r)
    rows = filtered_rows
    pinned = [r for r in rows if r.get("name_norm") in pinned_norm]
    pinned.sort(key=lambda r: list(pinned_names).index(r.get("name", "")) if r.get("name", "") in pinned_names else 999)
    return {
        "rows": rows,
        "pinned": pinned,
        "year_options": [str(SEASON), str(SEASON - 1), str(SEASON - 2), "career"],
    }


def _year_as_int(v: Any) -> int | None:
    try:
        return int(str(v).strip())
    except Exception:
        return None


def _to_str_num(v: Any) -> str:
    if pd.isna(v):
        return ""
    return str(v).strip()


def _clean_text(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    s = str(v).strip()
    return "" if s.lower() in {"nan", "none", "nat"} else s


def _cache_bust_url(url: str) -> str:
    """Append a daily cache-buster so CDN/browser caches don't serve stale HTML/JSON."""
    day = dashboard_date().isoformat()
    sep = "&" if ("?" in url) else "?"
    return f"{url}{sep}_apexcb={day}"


def get_d1_players_index() -> list[dict[str, Any]]:
    global D1_PLAYERS_INDEX
    if D1_PLAYERS_INDEX is not None:
        return D1_PLAYERS_INDEX
    try:
        js = _req_json_with_headers(_cache_bust_url(D1_PLAYERS_SEARCH_JSON))
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


def _individual_college_season_nonempty(season: dict[str, Any]) -> bool:
    if not season or _is_ncaa_team_season_stub(season):
        return False
    return any(
        v not in (None, "", 0, 0.0) for k, v in season.items() if k not in ("wins", "losses", "runs_for", "runs_against")
    )


def fetch_d1_player_stats(player_url: str, is_pitcher_role: bool) -> dict[str, Any]:
    if not player_url:
        return {}
    key = f"{player_url}|{'P' if is_pitcher_role else 'H'}|{dashboard_date().isoformat()}"
    cached = D1_PLAYER_STATS_CACHE.get(key)
    if cached is not None:
        return cached
    table = None
    for attempt in range(4):
        try:
            html = requests.get(
                _cache_bust_url(player_url), timeout=30, headers={"User-Agent": "Mozilla/5.0"}
            ).text
            dfs = pd.read_html(StringIO(html))
            table = _pick_d1_table(dfs, is_pitcher_role)
            if table is not None and not table.empty:
                break
        except Exception:
            table = None
        if attempt + 1 < 4:
            time.sleep(0.6 * (attempt + 1))
    if table is None or table.empty:
        return {}
    year_col = next((c for c in table.columns if str(c).strip().upper() == "YEAR"), None)
    if not year_col:
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


def _bigwest_teamstats_slug(school: str) -> str | None:
    return BIG_WEST_TEAMSTATS_SLUG_BY_NORM_SCHOOL.get(_norm_school(school))


def _bigwest_team_stats_payload(slug: str) -> dict[str, Any] | None:
    key = f"{slug}|{SEASON}"
    if key in BIG_WEST_TEAM_STATS_JSON_CACHE:
        return BIG_WEST_TEAM_STATS_JSON_CACHE[key]
    page_url = "https://bigwest.org/teamstats.aspx?" + urllib.parse.urlencode(
        {"path": "baseball", "school": slug, "year": str(SEASON)}
    )
    try:
        html = requests.get(page_url, timeout=35, headers=_HTTP_HEADERS).text
        m = re.search(r"team_id:\s*'(\d+)'", html)
        if not m:
            BIG_WEST_TEAM_STATS_JSON_CACHE[key] = None
            return None
        api_url = "https://bigwest.org/services/conf_stats.ashx?" + urllib.parse.urlencode(
            {
                "method": "get_team_stats",
                "team_id": m.group(1),
                "sport": "baseball",
                "year": str(SEASON),
                "conf": "False",
                "postseason": "False",
            }
        )
        js = _req_json(api_url, timeout=45, retries=2)
    except Exception:
        BIG_WEST_TEAM_STATS_JSON_CACHE[key] = None
        return None
    BIG_WEST_TEAM_STATS_JSON_CACHE[key] = js if isinstance(js, dict) else None
    return BIG_WEST_TEAM_STATS_JSON_CACHE[key]


def _pitching_line_from_big_west_pitching_stats(ps: dict[str, Any]) -> dict[str, Any]:
    """Map Sidearm pitching_stats blob to MLB-ish keys used by the dashboard."""
    ip_raw = ps.get("innings_pitched")
    ip_s = json_stat_value("inningsPitched", ip_raw) if ip_raw not in (None, "") else None
    if not ip_s:
        ip_s = "0.0"
    out: dict[str, Any] = {
        "inningsPitched": ip_s,
        "hits": to_number(ps.get("hits_allowed")),
        "runs": to_number(ps.get("runs_allowed")),
        "earnedRuns": to_number(ps.get("earned_runs_allowed")),
        "baseOnBalls": to_number(ps.get("walks_allowed")),
        "strikeOuts": to_number(ps.get("strikeouts")),
        "homeRuns": to_number(ps.get("home_runs_allowed")),
        "era": to_number(ps.get("earned_run_average")),
    }
    return {k: v for k, v in out.items() if v not in (None, "")}


def fetch_big_west_pitching_season_line(school: str, client_full_name: str) -> dict[str, Any]:
    """Official Big West pitcher season line when the school plays in that conference."""
    slug = _bigwest_teamstats_slug(school)
    if not slug:
        return {}
    js = _bigwest_team_stats_payload(slug)
    if not js:
        return {}
    want = _norm_player_name(_parse_name(client_full_name))
    for p in js.get("players") or []:
        if not isinstance(p, dict):
            continue
        nm = str(p.get("name") or "").strip()
        if not nm:
            continue
        if _norm_player_name(_parse_name(nm)) != want:
            continue
        ps = p.get("pitching_stats")
        if not isinstance(ps, dict):
            continue
        return _pitching_line_from_big_west_pitching_stats(ps)
    return {}


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


def _pick_ncaa_player_row(
    player_stats: list[dict[str, Any]], client_name: str, is_pitcher_role: bool | None = None
) -> dict[str, Any] | None:
    def role_ok(p: dict[str, Any]) -> bool:
        if is_pitcher_role is None:
            return True
        if is_pitcher_role:
            return bool(p.get("pitcherStats"))
        return bool(p.get("batterStats"))

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
            if not role_ok(p):
                continue
            return p
        if p_last and p_last == ln and (not f0 or p_first == f0):
            if not role_ok(p):
                continue
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
            if not role_ok(p):
                continue
            return p
        if p_last and p_last == ln:
            if not role_ok(p):
                continue
            return p
    return None


def _ncaa_ip_value(ps: dict[str, Any]) -> float:
    return _to_float(_ncaa_dict_get_ci(ps, "inningsPitched", "ip", "innings"))


def _apply_ncaa_pitcher_k_fallback(
    selected_row: dict[str, Any] | None,
    team_rows: list[dict[str, Any]],
    opp_rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Deliberately does nothing.

    We previously inferred pitcher strikeouts when NCAA fed per-pitcher zeros.
    Product requirement: never synthesize stats — use NCAA/Sidearm values only,
    or leave zeros/missing and rely on the AmateurList schedule Link fallback.
    """
    return selected_row


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


def _is_valid_hitter_last_night_line(line: dict[str, Any]) -> bool:
    """
    Reject obvious non-player aggregate lines accidentally attributed to a hitter.
    A single player's AB in one game should never approach full-team totals.
    """
    if not isinstance(line, dict):
        return True
    ab = _to_int(line.get("atBats"))
    # Defensive cap: protects two-way hitter rows from occasional team/opponent
    # aggregate stat lines (e.g., 19 AB).
    if ab > 12:
        return False
    if ab > 0:
        return True
    # Walk-only / DH lines can be 0 AB with runs, RBI, or walks.
    if _to_int(line.get("runs")) > 0 or _to_int(line.get("rbi")) > 0:
        return True
    if _to_int(line.get("baseOnBalls")) > 0:
        return True
    return False


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


def _is_ncaa_team_season_stub(season: dict[str, Any]) -> bool:
    """NCAA school payload season is team W/L when individual lines are unavailable."""
    if not season:
        return False
    keys = {str(k) for k in season.keys()}
    return keys.issubset({"wins", "losses", "runs_for", "runs_against"})


def _fetch_college_amateur_season(c: Client, school: str, is_p: bool) -> dict[str, Any]:
    """D1Baseball (or Big West JSON for conference pitchers) college season line."""
    d1_url = resolve_d1_player_url(c.name, school)
    d1_season = fetch_d1_player_stats(d1_url, is_p) if d1_url else {}
    bw_season = fetch_big_west_pitching_season_line(school, c.name) if is_p else {}
    return bw_season or d1_season or {}


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


def _ncaa_pitcher_ip_baseball_string(ps: dict[str, Any]) -> str:
    """
    NCAA IP in baseball form (1.2 = 1⅔ IP). Never ``round(float(...), 1)`` on inningsPitched.
    """
    if not isinstance(ps, dict):
        return "0.0"
    for outs_key in (
        "outsRecorded",
        "outs",
        "outsPitched",
        "pitcherOuts",
        "totalOuts",
        "ipOuts",
    ):
        v = _ncaa_dict_get_ci(ps, outs_key)
        if v is not None and str(v).strip() != "":
            o = _to_int(v)
            if o > 0:
                w, r = divmod(max(0, o), 3)
                return f"{w}.{r}"
    raw = _ncaa_dict_get_ci(ps, "inningsPitched", "ip", "innings", "inningsPitchedDisplay")
    if raw is None or raw == "":
        return "0.0"
    s = str(raw).strip()
    if re.fullmatch(r"\d+\.[012]", s):
        return s
    if re.fullmatch(r"\d+", s):
        return f"{int(s)}.0"
    try:
        x = float(s)
    except ValueError:
        return "0.0"
    if x <= 0:
        return "0.0"
    outs = int(round(x * 3))
    w, r = divmod(max(0, outs), 3)
    if abs(x * 3 - outs) < 0.051:
        return f"{w}.{r}"
    o2 = _ip_to_outs(s)
    w2, r2 = divmod(max(0, o2), 3)
    return f"{w2}.{r2}"


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
        # NCAA sometimes files pitcher K under batterStats (e.g. Gaeckle 9 K with 0 AB).
        if k_val == 0:
            bs = player_row.get("batterStats") or {}
            if _to_int(bs.get("atBats")) == 0:
                k_val = _ncaa_stat_int(
                    bs,
                    "strikeouts",
                    "strikeOuts",
                    "battersStruckOut",
                    "struckOut",
                    "k",
                    "so",
                )
        return {
            "ip": _ncaa_pitcher_ip_baseball_string(ps),
            "h": _ncaa_stat_int(ps, "hitsAllowed", "hits", "h"),
            "r": _ncaa_stat_int(ps, "runsAllowed", "runs", "r"),
            "er": _ncaa_stat_int(ps, "earnedRunsAllowed", "earnedRuns", "er"),
            "bb": _ncaa_stat_int(ps, "walksAllowed", "walks", "baseOnBalls", "bb"),
            "k": k_val,
            "hr": _ncaa_stat_int(ps, "homeRunsAllowed", "homeRuns", "hr"),
            "bf": _ncaa_stat_int(ps, "battersFaced", "bf"),
            "pitches": pitches,
            "w": _ncaa_stat_int(ps, "win", "wins"),
            "l": _ncaa_stat_int(ps, "loss", "losses"),
            "sv": _ncaa_stat_int(ps, "save", "saves"),
            "bs": _ncaa_stat_int(ps, "blownSave", "blownSaves"),
            "hld": _ncaa_stat_int(ps, "hold", "holds"),
            "wp": _ncaa_stat_int(ps, "wildPitches", "wildPitch"),
            "hb": _ncaa_stat_int(ps, "hitBatsmen", "hitByPitch"),
            "bk": _ncaa_stat_int(ps, "balks", "balk"),
        }
    bs = player_row.get("batterStats") or {}
    # NCAA GraphQL often omits XBH / HR in `batterStats` while still exposing them
    # on the sibling `hittingSeason` object for that game row (see Molony example).
    hs = player_row.get("hittingSeason") if isinstance(player_row.get("hittingSeason"), dict) else {}
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
    doubles_bs = max(extra["doubles"], _ncaa_stat_int(bs, "doubles", "double", "twoBaseHits"))
    hr_bs = max(extra["hr"], _ncaa_stat_int(bs, "homeRuns", "homeRun", "hr"))
    doubles_hs = _ncaa_stat_int(hs, "doubles", "double", "twoBaseHits") if hs else 0
    triples_hs = _ncaa_stat_int(hs, "triples", "triple", "threeBaseHits") if hs else 0
    hr_hs = _ncaa_stat_int(hs, "homeRuns", "homeRun", "hr") if hs else 0
    return {
        "ab": _to_int(bs.get("atBats")),
        "h": _to_int(bs.get("hits")),
        "r": _to_int(bs.get("runsScored")),
        "rbi": _to_int(bs.get("runsBattedIn")),
        "bb": _to_int(bs.get("walks")),
        "k": _to_int(bs.get("strikeouts")),
        "doubles": max(doubles_bs, doubles_hs, triples_hs),
        "hr": max(hr_bs, hr_hs),
        "sb": max(extra["sb"], _ncaa_stat_int(bs, "stolenBases", "stolenBase", "sb")),
        "hbp": _ncaa_stat_int(bs, "hitByPitch", "hitByPitch"),
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
    today = dashboard_date()
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
        home_name = g["team"]["name"] if g["team"]["is_home"] else g["opp"]["name"]
        loc = _college_home_location(home_name) or home_name
        return {
            "opponent": g["opp"]["name"],
            "home_away": "Home" if g["team"]["is_home"] else "Away",
            "venue": "",
            "location": loc,
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
                schedule_link=c.schedule_link,
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
        for rk, ok in (
            ("w", "wins"),
            ("l", "losses"),
            ("sv", "saves"),
            ("bs", "blownSaves"),
            ("hld", "holds"),
            ("wp", "wildPitches"),
            ("hb", "hitBatsmen"),
            ("bk", "balks"),
            ("hbp", "hitByPitch"),
        ):
            n = to_number(raw.get(rk))
            if n:
                out[ok] = n
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
        "triples": to_number(raw.get("triples")),
        "doubles": to_number(raw.get("doubles")),
        "stolenBases": to_number(raw.get("sb")),
        "hitByPitch": to_number(raw.get("hbp")),
        "outfieldAssists": to_number(raw.get("ofa")),
    }


def _player_row_from_ncaa_contest(
    g: dict[str, Any], school: str, client_name: str, is_pitcher_role: bool | None = None
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
    selected = _pick_ncaa_player_row(player_stats, client_name, is_pitcher_role=is_pitcher_role)
    opp_stats = (team_box[1 - idx] or {}).get("playerStats") or []
    return _apply_ncaa_pitcher_k_fallback(selected, player_stats, opp_stats)


def _college_ncaa_last_night_accept_dates(
    yday: date, games: list[dict[str, Any]]
) -> set[date]:
    """Calendar days to treat as last night on NCAA team schedules.

    When there is no final game on ``yday``, also allow ``yday + 1`` (common for
  late West Coast games filed on the next NCAA calendar day, e.g. Oregon).
    """
    def is_final(g: dict[str, Any]) -> bool:
        return g.get("status") == "final" or g.get("state") in {"C", "F", "3"}

    out = {yday}
    if not any(g.get("date") == yday and is_final(g) for g in games):
        out.add(yday + timedelta(days=1))
    return out


def ncaa_player_last_night_and_month(
    c: Client, school: str, is_p: bool, ncaa_payload: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Per-player lines from NCAA.com team schedule + boxscores (same source as team search)."""
    games: list[dict[str, Any]] = list(ncaa_payload.get("_games") or [])
    today = dashboard_date()
    yday = last_night_date()
    accept_days = _college_ncaa_last_night_accept_dates(yday, games)
    mstart = today.replace(day=1)

    def is_final(g: dict[str, Any]) -> bool:
        return g.get("status") == "final" or g.get("state") in {"C", "F", "3"}

    last_keys: dict[str, Any] = {}
    for day in (yday, yday + timedelta(days=1)):
        if day not in accept_days:
            continue
        for g in games:
            if g.get("date") == day and is_final(g):
                prow = _player_row_from_ncaa_contest(g, school, c.name, is_pitcher_role=is_p)
                if prow:
                    last_raw = _with_rate_stats(_extract_individual_line(prow, is_p), is_p)
                    last_keys = _amateur_line_to_pro_keys(last_raw, is_p)
                    break
        if last_keys:
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
        prow = _player_row_from_ncaa_contest(g, school, c.name, is_pitcher_role=is_p)
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


def _college_athletics_schedule_urls(c: Client, school: str) -> list[str]:
    """School athletics schedule pages (Sidearm / TASBS links), in priority order."""
    out: list[str] = []
    sl = (c.schedule_link or "").strip()
    if sl:
        out.append(sl)
    override = COLLEGE_ATHLETICS_SCHEDULE_BY_SCHOOL.get(_norm_school(school), "")
    if override and override not in out:
        out.append(override)
    return out


def _college_tasbs_team_labels(school: str) -> list[str]:
    """Header tokens for TASBS <pre> pitching tables (e.g. 'Clemson IP H R...')."""
    ns = _norm_school(school)
    if not ns:
        return []
    labels: list[str] = []
    for cand in (ns.title(), " ".join(w.title() for w in ns.split())):
        if cand and cand not in labels:
            labels.append(cand)
    parts = ns.split()
    if parts:
        last = parts[-1].title()
        if last and last not in labels:
            labels.append(last)
    return labels


def _tasbs_data_title_game_date(html: str) -> date | None:
    m = re.search(r"<title>\s*.*?\(([^)]+)\)\s*</title>", html, flags=re.I | re.S)
    if not m:
        return None
    inner = m.group(1).strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(inner, fmt).date()
        except ValueError:
            continue
    return None


def _tasbs_pitching_header_for_team(line: str, team_labels: list[str]) -> bool:
    if not team_labels:
        return False
    for lab in team_labels:
        if re.search(
            rf"{re.escape(lab)}\s+IP\s+H\s+R\s+ER\s+BB\s+SO(?:\s+AB\s+BF)?",
            line,
            re.I,
        ):
            return True
    return False


def _tasbs_raw_pitching_line(
    html: str, client_name: str, team_labels: list[str]
) -> dict[str, Any] | None:
    first, last = _name_parts(client_name)
    last_n = _norm_token(last)
    first_i = _norm_token(first[:1]) if first else ""
    if not last_n or not team_labels:
        return None
    in_section = False
    for line in html.splitlines():
        if _tasbs_pitching_header_for_team(line, team_labels):
            in_section = True
            continue
        if not in_section:
            continue
        st = line.rstrip()
        if not st.strip() or set(st.replace(" ", "")) <= {"-", "_"}:
            continue
        if re.search(r"\bIP\b.*\bH\b.*\bR\b.*\bER\b.*\bBB\b.*\bSO\b", st) and not any(
            re.search(re.escape(lab), st, re.I) for lab in team_labels
        ):
            break
        m = re.match(
            r"^\s*([A-Za-z][A-Za-z '\-]+?)\s*\.+\s+(\d+\.\d)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
            st,
        )
        if not m:
            continue
        pitch_name = m.group(1).strip()
        parts = pitch_name.split()
        if not parts or _norm_token(parts[-1]) != last_n:
            continue
        if first_i and _norm_token(parts[0][:1]) != first_i:
            continue
        return {
            "ip": m.group(2),
            "h": int(m.group(3)),
            "r": int(m.group(4)),
            "er": int(m.group(5)),
            "bb": int(m.group(6)),
            "k": int(m.group(7)),
            "hr": 0,
        }
    return None


def _tasbs_data_hosts_from_html(html: str) -> list[str]:
    hosts: list[str] = []
    seen: set[str] = set()
    for mm in re.finditer(r"(https?://data\.[a-z0-9.-]+)", html, flags=re.I):
        host = mm.group(1).rstrip("/")
        key = host.lower()
        if key not in seen:
            seen.add(key)
            hosts.append(host)
    return hosts


def _tasbs_game_paths_from_schedule(html: str, data_host: str, year: int) -> list[str]:
    cache_key = (data_host.lower(), year)
    cached = TASBS_SCHEDULE_GAME_PATHS.get(cache_key)
    if cached is not None:
        return cached
    paths: list[str] = []
    seen: set[str] = set()
    for mm in re.finditer(rf"Stats/Baseball/{year}/([a-z0-9]+\.htm)", html, flags=re.I):
        fn = mm.group(1)
        if "teamstat" in fn.lower():
            continue
        if fn not in seen:
            seen.add(fn)
            paths.append(fn)

    def _path_num(fn: str) -> int:
        m2 = re.search(r"(\d+)", fn)
        return int(m2.group(1)) if m2 else 0

    paths.sort(key=_path_num, reverse=True)
    TASBS_SCHEDULE_GAME_PATHS[cache_key] = paths
    return paths


def _tasbs_box_html(full_url: str) -> str:
    if full_url in TASBS_BOX_HTML_BY_URL:
        return TASBS_BOX_HTML_BY_URL[full_url]
    try:
        txt = requests.get(full_url, timeout=20, headers=_HTTP_HEADERS).text
    except Exception:
        txt = ""
    TASBS_BOX_HTML_BY_URL[full_url] = txt
    return txt


def _tasbs_amateur_pitching_last_night(
    schedule_urls: list[str],
    team_labels: list[str],
    client_name: str,
    target_day: date,
) -> tuple[dict[str, Any] | None, str]:
    year = target_day.year
    for sched_url in schedule_urls:
        try:
            sched_html = requests.get(sched_url, timeout=25, headers=_HTTP_HEADERS).text
        except Exception:
            continue
        for data_host in _tasbs_data_hosts_from_html(sched_html):
            prefix = f"{data_host}/Stats/Baseball/{year}/"
            for fn in _tasbs_game_paths_from_schedule(sched_html, data_host, year)[:70]:
                full = prefix + fn
                html = _tasbs_box_html(full)
                if not html:
                    continue
                if _tasbs_data_title_game_date(html) != target_day:
                    continue
                raw = _tasbs_raw_pitching_line(html, client_name, team_labels)
                if raw and _to_float(raw.get("ip")) > 0:
                    return raw, full
    return None, ""


def _college_pitcher_last_night_pro_keys(
    c: Client,
    school: str,
    yday: date,
    ncaa_ln_keys: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """
    Prefer school athletics box scores (TASBS data.* hosts, Sidearm) over NCAA GraphQL when
    fractional IP or strikeouts differ (e.g. Talan Bell 1.2 IP, Oregon K totals).
    """
    sched_urls = _college_athletics_schedule_urls(c, school)
    team_labels = _college_tasbs_team_labels(school)

    if sched_urls and team_labels:
        raw_tasbs, tasbs_url = _tasbs_amateur_pitching_last_night(
            sched_urls, team_labels, c.name, yday
        )
        if raw_tasbs:
            keys = _amateur_line_to_pro_keys(raw_tasbs, True)
            return (
                {k: json_stat_value(k, v) for k, v in keys.items() if v is not None},
                tasbs_url,
            )

    accept_days = _college_ncaa_last_night_accept_dates(
        yday, list(get_cached_ncaa_school_payload(school, weeks=4).get("_games") or [])
    )
    for su in sched_urls:
        side = _sidearm_player_last_night_from_schedule_link(
            su, c.name, True, yday, accept_days=accept_days
        )
        if side and _to_float(side.get("inningsPitched")) > 0:
            cu = str(side.pop("contest_url", "") or "")
            side.pop("game_date", None)
            keys = {k: json_stat_value(k, v) for k, v in side.items() if v is not None}
            if keys:
                return keys, cu if cu.startswith("http") else ""

    if ncaa_ln_keys:
        return dict(ncaa_ln_keys), ""

    return {}, ""


def _merge_manual_amateur_clients(clients: list[Client]) -> list[Client]:
    merged: dict[str, Client] = {_norm_player_name(c.name): c for c in clients}
    for m in MANUAL_AMATEUR_CLIENTS:
        name = (m.get("name") or "").strip()
        if not name:
            continue
        nn = _norm_player_name(name)
        school = (m.get("school") or "").strip()
        merged[nn] = Client(
            name=name,
            position=(m.get("position") or "RHP").upper(),
            level="NCAA",
            league=m.get("league") or "Amateur",
            minor_affiliate=school,
            major_affiliate="",
            agent=(m.get("agent") or "").strip(),
            agent_last=_agent_last(m.get("agent") or ""),
            is_amateur=True,
            school_or_team=school,
            schedule_link=(m.get("schedule_link") or "").strip(),
        )
    return list(merged.values())


def _sidearm_player_last_night_from_schedule_link(
    schedule_url: str,
    player_name: str,
    is_p: bool,
    target_day: date,
    accept_days: set[date] | None = None,
) -> dict[str, Any]:
    """Best-effort fallback from Sidearm schedule link -> boxscore tables."""
    url = (schedule_url or "").strip()
    if not url:
        return {}
    try:
        html = requests.get(url, timeout=25, headers=_HTTP_HEADERS).text
    except Exception:
        return {}
    cand_urls: list[str] = []
    seen: set[str] = set()
    for h in re.findall(r'href="([^"]+)"', html, flags=re.I):
        hl = h.lower()
        if "boxscore" not in hl or "sidearm-icons" in hl:
            continue
        full = urllib.parse.urljoin(url, h)
        if full in seen:
            continue
        seen.add(full)
        cand_urls.append(full)
    if not cand_urls:
        return {}
    first, last = _name_parts(player_name)
    first_i = _norm_token(first[:1])
    last_n = _norm_token(last)

    def _day_tokens(d: date) -> set[str]:
        return {
            d.isoformat(),
            d.strftime("%m/%d/%Y"),
            d.strftime("%-m/%-d/%Y"),
            d.strftime("%b %-d, %Y"),
        }

    def _scan_boxscores(accept_days: set[date]) -> dict[str, Any]:
        tokens: set[str] = set()
        for d in accept_days:
            tokens |= _day_tokens(d)
        recent_urls = list(reversed(cand_urls))[:60]
        for bu in recent_urls:
            try:
                bhtml = requests.get(bu, timeout=20, headers=_HTTP_HEADERS).text
            except Exception:
                continue
            actual_game_day: date | None = None
            for m in re.finditer(r"\bon\s+(\d{1,2}/\d{1,2}/\d{4})\b", bhtml, flags=re.I):
                try:
                    actual_game_day = datetime.strptime(m.group(1), "%m/%d/%Y").date()
                    break
                except Exception:
                    continue
            if actual_game_day is not None and actual_game_day not in accept_days:
                continue
            if actual_game_day is None and not any(tok in bhtml for tok in tokens):
                continue
            try:
                tables = pd.read_html(StringIO(bhtml))
            except Exception:
                continue
            for t in tables:
                df = _flatten_columns(t.copy())
                cols_l = [str(c).strip().lower() for c in df.columns]
                if is_p and "ip" not in cols_l:
                    continue
                if (not is_p) and not any(c in cols_l for c in ("ab", "h", "rbi")):
                    continue
                for _, row in df.iterrows():
                    row_vals = [str(v) for v in row.tolist()]
                    row_text = " ".join(row_vals).lower()
                    if last_n and last_n not in _norm_token(row_text):
                        continue
                    if is_p:
                        out = _amateur_line_to_pro_keys(
                            {
                                "ip": row.get(_find_col(list(df.columns), ("IP", "Innings"))),
                                "h": row.get(_find_col(list(df.columns), ("H", "Hits"))),
                                "r": row.get(_find_col(list(df.columns), ("R", "Runs"))),
                                "er": row.get(_find_col(list(df.columns), ("ER", "Earned"))),
                                "bb": row.get(_find_col(list(df.columns), ("BB", "Walks"))),
                                "k": row.get(_find_col(list(df.columns), ("SO", "K", "Strikeouts"))),
                                "hr": row.get(_find_col(list(df.columns), ("HR", "Home Runs"))),
                            },
                            True,
                        )
                        out["contest_url"] = bu
                        if actual_game_day:
                            out["game_date"] = actual_game_day.isoformat()
                        return out
                    out = _amateur_line_to_pro_keys(
                        {
                            "ab": row.get(_find_col(list(df.columns), ("AB", "At Bats"))),
                            "r": row.get(_find_col(list(df.columns), ("R", "Runs"))),
                            "h": row.get(_find_col(list(df.columns), ("H", "Hits"))),
                            "rbi": row.get(_find_col(list(df.columns), ("RBI",))),
                            "bb": row.get(_find_col(list(df.columns), ("BB", "Walks"))),
                            "k": row.get(_find_col(list(df.columns), ("SO", "K", "Strikeouts"))),
                            "hr": row.get(_find_col(list(df.columns), ("HR", "Home Runs"))),
                        },
                        False,
                    )
                    out["contest_url"] = bu
                    if actual_game_day:
                        out["game_date"] = actual_game_day.isoformat()
                    return out
        return {}

    days = accept_days if accept_days else {target_day}
    return _scan_boxscores(days)


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
        if _norm_player_name(_parse_name(raw_name)) in DASHBOARD_EXCLUDE_NAMES:
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
                schedule_link="",
            )
        )
    existing = {_norm_player_name(c.name) for c in out}
    for m in MANUAL_PRO_CLIENTS:
        nm = _norm_player_name(m.get("name", ""))
        if not nm or nm in existing:
            continue
        agent = _normalize_agent_initials(m.get("agent", ""))
        out.append(
            Client(
                name=m.get("name", ""),
                position=m.get("position", ""),
                level=m.get("level", ""),
                league=m.get("league", ""),
                minor_affiliate=m.get("minor_affiliate", ""),
                major_affiliate=m.get("major_affiliate", ""),
                agent=agent,
                agent_last=_agent_last(agent),
                is_amateur=False,
                school_or_team="",
                schedule_link="",
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
    link_col = pick_col(["Link", "Schedule Link", "Stats Link", "URL"])

    if not name_col:
        return []

    out: list[Client] = []
    for _, r in df.iterrows():
        raw_name = _cell_str(r.get(name_col, ""))
        if not raw_name:
            continue
        if _norm_player_name(_parse_name(raw_name)) in DASHBOARD_EXCLUDE_NAMES:
            continue
        position = _cell_str(r.get(pos_col, "")).upper() if pos_col else ""
        school = _cell_str(r.get(school_col, "")) if school_col else ""
        agent_val = _normalize_agent_initials(_cell_str(r.get(agent_col, "")) if agent_col else "")
        schedule_link = _cell_str(r.get(link_col, "")) if link_col else ""
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
                schedule_link=schedule_link,
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


def _person_matches_client_name(api_name: str, client_name: str) -> bool:
    """Last name + first initial (Stats API fullName vs spreadsheet)."""
    if not api_name or not client_name:
        return False
    if _norm_player_name(api_name) == _norm_player_name(client_name):
        return True
    t_first, t_last = _name_parts(client_name)
    a_first, a_last = _name_parts(api_name)
    if not t_last or not a_last or _norm_token(t_last) != _norm_token(a_last):
        return False
    if t_first and a_first:
        return _norm_token(t_first[:1]) == _norm_token(a_first[:1])
    return True


def _roster_name_rows(team_id: int) -> list[tuple[int, str]]:
    key = (team_id, SEASON)
    cached = ROSTER_CACHE.get(key)
    if cached is not None:
        return cached
    rows: list[tuple[int, str]] = []
    try:
        rjs = _req_json(f"{API}/teams/{team_id}/roster?" + urllib.parse.urlencode({"season": SEASON}))
    except Exception:
        ROSTER_CACHE[key] = rows
        return rows
    for row in rjs.get("roster") or []:
        person = row.get("person") or {}
        pid = _safe_int(person.get("id"))
        fn = str(person.get("fullName", "") or "").strip()
        if pid and fn:
            rows.append((pid, fn))
    ROSTER_CACHE[key] = rows
    return rows


def _find_player_id_on_team_roster(client_name: str, team_id: int) -> int | None:
    for pid, fn in _roster_name_rows(team_id):
        if _person_matches_client_name(fn, client_name):
            return pid
    return None


def _teams_for_client_org(c: Client) -> list[int]:
    """All affiliate team ids for the client's MLB org (parentOrg), for roster scans."""
    maj = (c.major_affiliate or "").strip()
    if not maj or maj.lower() == "nan":
        return []
    teams = get_team_catalog()
    ranked: list[tuple[int, int, int]] = []
    for t in teams:
        tid = _safe_int(t.get("id"))
        if not tid:
            continue
        parent_score = _org_match_score(maj, t)
        if parent_score < 4:
            continue
        sport_id = _safe_int((t.get("sport") or {}).get("id")) or 99
        ranked.append((-parent_score, sport_id, tid))
    ranked.sort()
    return [tid for _, _, tid in ranked]


def _find_player_id_via_org_rosters(c: Client) -> int | None:
    """
    people/search often misses active MiLB/rehab players; scan affiliate rosters
    (sheet affiliate first, then every club under major_affiliate).
    """
    seen: set[int] = set()
    for label in (c.minor_affiliate, c.major_affiliate):
        lab = (label or "").strip()
        if not lab or lab.lower() == "nan":
            continue
        team_obj = lookup_team_by_name(lab, c.level)
        tid = _safe_int((team_obj or {}).get("id"))
        if tid and tid not in seen:
            seen.add(tid)
            pid = _find_player_id_on_team_roster(c.name, tid)
            if pid:
                return pid
    for tid in _teams_for_client_org(c):
        if tid in seen:
            continue
        seen.add(tid)
        pid = _find_player_id_on_team_roster(c.name, tid)
        if pid:
            return pid
    return None


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
        hits = search_people(variant)
        if hits:
            people = [
                p
                for p in hits
                if _person_matches_client_name(str(p.get("fullName", "")), c.name)
            ]
        if people:
            break
    if not people:
        return _find_player_id_via_org_rosters(c)
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
    url = _foreign_br_register_url(nn)
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


def fetch_team_from_gamelog_on_date(player_id: int, group: str, target_day: date) -> dict[str, Any]:
    """Club from the most recent game on a calendar day (any pro sportId)."""
    day = target_day.isoformat()
    best_game_pk: int | None = None
    best: dict[str, Any] = {}
    for sport_id in SPORT_IDS_PRO:
        try:
            splits = _gamelog_splits_for_sport(player_id, group, sport_id)
        except Exception:
            continue
        for sp in splits:
            if sp.get("date") != day:
                continue
            game = sp.get("game") or {}
            game_pk = _safe_int(game.get("gamePk") or sp.get("gamePk"))
            if game_pk is None:
                continue
            if best_game_pk is None or game_pk > best_game_pk:
                best_game_pk = game_pk
                team = sp.get("team") or {}
                best = {
                    "team_id": _safe_int(team.get("id")),
                    "team_name": team.get("name", ""),
                    "sport_id": sport_id,
                }
    return best


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
                    "sport_id": sport_id,
                }
    return best


def _resolve_pro_client_team(
    pid: int | None,
    group: str,
    yday: date,
    roster_team: dict[str, Any],
    latest_team: dict[str, Any],
    team_name_guess: str,
    level_hint: str,
) -> tuple[int | None, dict[str, Any], int | None]:
    """
  Pick team context for display, schedule, and stat sportId.

  Roster currentTeam can lag rehab/reassignment; game logs reflect where the player
  actually appeared (e.g. High-A roster, Low-A rehab start -> Tampa Tarpons stats).
    """
    tid = _safe_int(roster_team.get("team_id"))
    latest_tid = _safe_int(latest_team.get("team_id"))
    if not tid:
        tid = latest_tid
    if not tid:
        team_obj = lookup_team_by_name(team_name_guess, level_hint)
        tid = _safe_int((team_obj or {}).get("id"))
    team_ctx = get_team_context(tid)
    stat_sport_id = team_ctx.get("sport_id")

    yday_team = fetch_team_from_gamelog_on_date(pid, group, yday) if pid else {}
    yday_tid = _safe_int(yday_team.get("team_id"))
    if yday_tid:
        tid = yday_tid
        team_ctx = get_team_context(tid)
        stat_sport_id = yday_team.get("sport_id") or team_ctx.get("sport_id")
        return tid, team_ctx, stat_sport_id

    roster_tid = _safe_int(roster_team.get("team_id"))
    if latest_tid and roster_tid and latest_tid != roster_tid:
        latest_ctx = get_team_context(latest_tid)
        tid = latest_tid
        team_ctx = latest_ctx
        stat_sport_id = latest_team.get("sport_id") or latest_ctx.get("sport_id")
    elif latest_tid and not roster_tid:
        latest_ctx = get_team_context(latest_tid)
        tid = latest_tid
        team_ctx = latest_ctx
        stat_sport_id = latest_team.get("sport_id") or latest_ctx.get("sport_id")

    return tid, team_ctx, stat_sport_id


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
    start = dashboard_date()
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
        # MiLB schedule page (use full Stats API club name slug — matches milb.com paths;
        # nickname-only slugs like "dust-devils" redirect but are easy to confuse with wrong clubs).
        schedule_url = f"https://www.milb.com/{_slug(team_name)}/schedule"
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
    """
    Pro client: resolve player id (search + org roster scan), then team/stats from game logs
    when assignments change (rehab, call-up, new affiliate).
    """
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
        "last_night_date": report_anchor_date().isoformat(),
        "last_night": {},
        "month_to_date": {},
        "season": {},
        "upcoming_series": [],
    }
    nn = _norm_player_name(c.name or "")
    # Stats API name collisions (e.g. another "Mitch White" still listed on a MiLB affiliate) are wrong
    # for KBO/NPB/CPBL; use Baseball-Reference register URLs only (no MLB person id).
    pid = None if _is_foreign_br_register_client_norm(nn) else (resolve_player_id(c) if c.name else None)

    group = stat_group(c.position)
    fallback_sport_id = sport_id_for_level(c.level)
    roster_team = fetch_current_team_from_person(pid) if pid else {}
    latest_team = fetch_latest_team_from_gamelog_all_sports(pid, group) if pid else {}
    team_name_guess = roster_team.get("team_name") or latest_team.get("team_name") or pick_current_team_name(c)
    yday = last_night_date()
    tid, team_ctx, stat_sport_id = _resolve_pro_client_team(
        pid, group, yday, roster_team, latest_team, team_name_guess, c.level
    )
    if stat_sport_id is None:
        stat_sport_id = fallback_sport_id
    base["organization"] = team_ctx.get("organization") or (c.major_affiliate if (c.major_affiliate or "").lower() != "nan" else "")
    resolved_team = team_ctx["team_name"] or team_name_guess
    base["current_team"] = resolved_team
    base["current_team_location"] = team_ctx["team_location"]
    base["team_level"] = team_ctx["team_level"] or c.level
    if team_ctx.get("team_level"):
        base["level"] = team_ctx["team_level"]
    # Sheet affiliate can lag rehab/reassignment; show and bucket stats by actual club.
    if resolved_team and _normalize_org_token(c.minor_affiliate) != _normalize_org_token(resolved_team):
        base["minor_affiliate"] = resolved_team
    base["team_schedule_url"] = team_ctx["schedule_url"] or fallback_schedule_url(
        base["current_team"], base["team_level"]
    )
    mstart = dashboard_date().replace(day=1)
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
            mtd_raw = fetch_player_stats(
                pid, group, "byDateRange", stat_sport_id, mstart, dashboard_date()
            )
            if not _stats_non_empty(mtd_raw):
                mtd_raw = fetch_player_stats_preferred_then_all_sports(
                    pid, group, "byDateRange", stat_sport_id, mstart, dashboard_date()
                )
            base["month_to_date"] = _strip_pitch_count_fields(
                {k: json_stat_value(k, v) for k, v in mtd_raw.items()}
            )
        except Exception:
            base["month_to_date"] = {}
        try:
            st_season = fetch_player_stats(pid, group, "season", stat_sport_id)
            if not _stats_non_empty(st_season):
                st_season = fetch_player_stats_preferred_then_all_sports(
                    pid, group, "season", stat_sport_id
                )
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

    # Foreign league: season/team/schedule from Baseball-Reference register (authoritative vs MiLB roster noise).
    if _is_foreign_br_register_client_norm(nn):
        foreign_season = fetch_foreign_br_season_stats(c.name, True)
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
            # Stats API still lists org affiliates (e.g. MiLB); drop MLB/MiLB schedule rows.
            base["upcoming_series"] = []
            sched = _foreign_league_schedule_url(f_lg)
            if sched:
                base["team_schedule_url"] = sched
    return base


def _summer_amateur_config(c: Client) -> dict[str, Any] | None:
    return SUMMER_AMATEUR_OVERRIDES.get(_norm_player_name(c.name or ""))


def _wcl_individuals() -> list[dict[str, Any]]:
    global _WCL_PLAYERS_CACHE
    if _WCL_PLAYERS_CACHE is None:
        try:
            js = _req_json(WCL_PLAYERS_DATA_URL, timeout=30)
            _WCL_PLAYERS_CACHE = list(js.get("individuals") or [])
        except Exception:
            _WCL_PLAYERS_CACHE = []
    return _WCL_PLAYERS_CACHE


def _wcl_player_full_name(p: dict[str, Any]) -> str:
    fn = str(p.get("firstName") or "").strip()
    ln = str(p.get("lastName") or "").strip()
    return _norm_player_name(f"{fn} {ln}")


def _parse_wcl_gpgs(gpgs: Any) -> tuple[int | None, int | None]:
    m = re.match(r"^(\d+)-(\d+)$", str(gpgs or "").strip())
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def _find_wcl_player(c: Client, cfg: dict[str, Any]) -> dict[str, Any] | None:
    names = {_norm_player_name(c.name or "")}
    for alias in cfg.get("name_aliases") or []:
        names.add(_norm_player_name(str(alias)))
    team_id = str(cfg.get("wcl_team_id") or "").strip()
    team_filter = str(cfg.get("summer_team") or "").strip().lower()
    for p in _wcl_individuals():
        if _wcl_player_full_name(p) not in names:
            continue
        if team_id and str(p.get("teamId") or "") != team_id:
            continue
        if team_filter and team_filter not in str(p.get("team") or "").lower():
            continue
        return p
    return None


def _wcl_stats_to_season(p: dict[str, Any], is_pitcher: bool) -> dict[str, Any]:
    st = p.get("stats") or p.get("statsConference") or {}
    ip = _to_float(st.get("ip")) or 0.0
    ab = _to_float(st.get("ab")) or 0.0
    use_pitcher = ip > 0 if (ip > 0 or ab > 0) else is_pitcher
    out: dict[str, Any] = {}
    gp, gs = _parse_wcl_gpgs(st.get("gpgs"))
    if gp is None:
        gp = _safe_int(st.get("gp"))
    if gs is None:
        gs = _safe_int(st.get("gs")) or _safe_int(st.get("pgs"))
    out["gamesPlayed"] = gp
    if gs is not None:
        out["gamesStarted"] = gs
    if use_pitcher:
        for wcl_k, dst_k in (
            ("ip", "inningsPitched"),
            ("era", "era"),
            ("whip", "whip"),
            ("pk", "strikeOuts"),
            ("ph", "hits"),
            ("pbb", "baseOnBalls"),
            ("er", "earnedRuns"),
        ):
            if st.get(wcl_k) not in (None, ""):
                out[dst_k] = json_stat_value(dst_k, st.get(wcl_k))
    else:
        for wcl_k, dst_k in (
            ("ab", "atBats"),
            ("avg", "avg"),
            ("obp", "obp"),
            ("slg", "slg"),
            ("ops", "ops"),
            ("h", "hits"),
            ("r", "runs"),
            ("rbi", "rbi"),
            ("k", "strikeOuts"),
            ("bb", "baseOnBalls"),
            ("sb", "stolenBases"),
            ("hd", "doubles"),
            ("hr", "homeRuns"),
        ):
            if st.get(wcl_k) not in (None, ""):
                out[dst_k] = json_stat_value(dst_k, st.get(wcl_k))
    return _strip_pitch_count_fields(out)


def _resolve_summer_amateur_player_id(c: Client, cfg: dict[str, Any]) -> int | None:
    pid = _safe_int(cfg.get("player_id"))
    if pid:
        return pid
    team_id = _safe_int(cfg.get("team_id"))
    if not team_id:
        return None
    pid = _find_player_id_on_team_roster(c.name, team_id)
    if pid:
        return pid
    for alias in cfg.get("name_aliases") or []:
        pid = _find_player_id_on_team_roster(str(alias), team_id)
        if pid:
            return pid
    return None


def _college_gamelog_splits(player_id: int, group: str) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "stats": "gameLog",
        "group": group,
        "season": SEASON,
        "sportId": SPORT_ID_COLLEGE,
    }
    url = f"{API}/people/{player_id}/stats?" + urllib.parse.urlencode(params)
    js = _req_json(url)
    return (js.get("stats") or [{}])[0].get("splits") or []


def _fetch_summer_league_stats(
    player_id: int,
    group: str,
    league_id: int,
    stat_type: str,
    start: date | None = None,
    end: date | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "stats": stat_type,
        "group": group,
        "season": SEASON,
        "leagueId": league_id,
    }
    if start and end:
        params["startDate"] = start.isoformat()
        params["endDate"] = end.isoformat()
    url = f"{API}/people/{player_id}/stats?" + urllib.parse.urlencode(params)
    js = _req_json(url)
    splits = (js.get("stats") or [{}])[0].get("splits") or []
    return splits[0].get("stat", {}) if splits else {}


def _summer_team_gamelog_splits(
    player_id: int, group: str, team_id: int
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for sp in _college_gamelog_splits(player_id, group):
        tid = _safe_int((sp.get("team") or {}).get("id"))
        if tid == team_id:
            out.append(sp)
    return out


def _summer_last_night_line(
    player_id: int, group: str, team_id: int, target_day: date
) -> dict[str, Any]:
    day = target_day.isoformat()
    merged: dict[str, Any] = {}
    for sp in _summer_team_gamelog_splits(player_id, group, team_id):
        if sp.get("date") != day:
            continue
        st = sp.get("stat") or {}
        for k, v in st.items():
            try:
                fv = float(v)
            except Exception:
                if k not in merged:
                    merged[k] = v
                continue
            merged[k] = float(merged.get(k, 0)) + fv
    return merged


def _summer_last_night_boxscore_url(
    player_id: int, group: str, team_id: int, target_day: date
) -> str:
    day = target_day.isoformat()
    best_game_pk: int | None = None
    for sp in _summer_team_gamelog_splits(player_id, group, team_id):
        if sp.get("date") != day:
            continue
        game = sp.get("game") or {}
        game_pk = _safe_int(game.get("gamePk") or sp.get("gamePk"))
        if game_pk is not None and (best_game_pk is None or game_pk > best_game_pk):
            best_game_pk = game_pk
    if best_game_pk is None:
        return ""
    return f"https://www.mlb.com/gameday/{best_game_pk}/final/box"


def _summer_month_to_date_stats(
    player_id: int, group: str, team_id: int, month_start: date, month_end: date
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "stats": "byDateRange",
        "group": group,
        "season": SEASON,
        "sportId": SPORT_ID_COLLEGE,
        "startDate": month_start.isoformat(),
        "endDate": month_end.isoformat(),
    }
    url = f"{API}/people/{player_id}/stats?" + urllib.parse.urlencode(params)
    js = _req_json(url)
    splits = (js.get("stats") or [{}])[0].get("splits") or []
    for sp in splits:
        if _safe_int((sp.get("team") or {}).get("id")) == team_id:
            return sp.get("stat") or {}
    return {}


def _fetch_summer_team_schedule(team_id: int, weeks: int = 4) -> list[dict[str, Any]]:
    start = dashboard_date()
    end = start + timedelta(days=7 * weeks)
    params = {
        "sportId": SPORT_ID_COLLEGE,
        "teamId": team_id,
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "hydrate": "venue(location),team",
    }
    url = f"{API}/schedule?" + urllib.parse.urlencode(params)
    try:
        js = _req_json(url)
    except Exception:
        return []
    games: list[dict[str, Any]] = []
    for d in js.get("dates", []):
        for g in d.get("games", []):
            games.append(g)
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
    return series[:4]


def build_summer_amateur_payload(c: Client, cfg: dict[str, Any]) -> dict[str, Any]:
    """Summer-ball amateur row: college org + summer team stats via MLB Stats API (sportId 22)."""
    school = (c.school_or_team or c.minor_affiliate or "").strip()
    is_p = college_is_pitcher(c)
    group = stat_group(c.position)
    team_id = _safe_int(cfg.get("team_id")) or 0
    league_id = _safe_int(cfg.get("league_id")) or 0
    summer_team = str(cfg.get("summer_team") or "").strip()
    summer_league = str(cfg.get("summer_league") or "").strip()
    team_level = str(cfg.get("team_level") or summer_league).strip()
    schedule_url = str(cfg.get("schedule_url") or "").strip()
    base: dict[str, Any] = {
        "name": c.name,
        "position": c.position,
        "level": team_level,
        "league": summer_league or "Summer",
        "minor_affiliate": school,
        "major_affiliate": "",
        "agent": c.agent,
        "agent_last": c.agent_last,
        "is_pitcher": is_p,
        "organization": school,
        "school_or_team": school,
        "current_team": summer_team,
        "summer_team": summer_team,
        "current_team_location": "",
        "team_level": team_level,
        "team_schedule_url": schedule_url,
        "stats_context": "summer",
        "last_night_boxscore_url": "",
        "last_night_date": report_anchor_date().isoformat(),
        "last_night": {},
        "month_to_date": {},
        "season": {},
        "summer_season": {},
        "upcoming_series": [],
    }
    college_season = _fetch_college_amateur_season(c, school, is_p)
    if college_season:
        base["season"] = college_season
    if str(cfg.get("stats_source") or "").lower() == "wcl":
        wcl_p = _find_wcl_player(c, cfg)
        if wcl_p:
            base["summer_season"] = _wcl_stats_to_season(wcl_p, is_p)
        return base
    if team_id:
        try:
            base["upcoming_series"] = _fetch_summer_team_schedule(team_id)
        except Exception:
            pass
    pid = _resolve_summer_amateur_player_id(c, cfg)
    if not pid or not league_id or not team_id:
        return base
    yday = last_night_date()
    mstart = dashboard_date().replace(day=1)
    try:
        ln = {
            k: json_stat_value(k, v)
            for k, v in _summer_last_night_line(pid, group, team_id, yday).items()
        }
        if ln:
            base["last_night"] = ln
            base["last_night_boxscore_url"] = _summer_last_night_boxscore_url(
                pid, group, team_id, yday
            )
        if (not is_p) and ln and not _is_valid_hitter_last_night_line(ln):
            base["last_night"] = {}
    except Exception:
        pass
    try:
        mtd_raw = _summer_month_to_date_stats(pid, group, team_id, mstart, dashboard_date())
        base["month_to_date"] = _strip_pitch_count_fields(
            {k: json_stat_value(k, v) for k, v in mtd_raw.items()}
        )
    except Exception:
        pass
    try:
        st_season = _fetch_summer_league_stats(pid, group, league_id, "season")
        base["summer_season"] = _strip_pitch_count_fields(
            {k: json_stat_value(k, v) for k, v in st_season.items()}
        )
    except Exception:
        pass
    return base


def build_amateur_payload(c: Client) -> dict[str, Any]:
    """
    College clients: D1Baseball season table + NCAA.com team schedule/boxscores for last night & MTD.
    Summer assignments (Cape Cod, MBDL, etc.) use MLB Stats API on sportId 22 when configured.
    """
    summer_cfg = _summer_amateur_config(c)
    if summer_cfg:
        return build_summer_amateur_payload(c, summer_cfg)
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
        "team_schedule_url": (
            c.schedule_link
            or COLLEGE_ATHLETICS_SCHEDULE_BY_SCHOOL.get(_norm_school(school), "")
            or school_schedule_url(c.school_or_team)
        ),
        "last_night_boxscore_url": "",
            "last_night_date": report_anchor_date().isoformat(),
            "last_night": {},
            "month_to_date": {},
            "season": {},
            "upcoming_series": [],
        }

    # Season totals: Big West conference JSON (NCAA-aligned) when available; else D1Baseball scrape.
    d1_url = resolve_d1_player_url(c.name, school)
    if d1_url and not c.schedule_link:
        base["team_schedule_url"] = d1_url
    season_preferred = _fetch_college_amateur_season(c, school, is_p)
    if season_preferred:
        base["season"] = season_preferred

    if school:
        try:
            ncaa_payload = get_cached_ncaa_school_payload(school, weeks=4)
            base["upcoming_series"] = ncaa_payload.get("upcoming_series") or []

            ln_ind, mtd_ind = ncaa_player_last_night_and_month(c, school, is_p, ncaa_payload)
            yday = last_night_date()
            accept_days = _college_ncaa_last_night_accept_dates(
                yday, list(ncaa_payload.get("_games") or [])
            )
            ncaa_box_url = ""
            for day in (yday, yday + timedelta(days=1)):
                if day not in accept_days:
                    continue
                for g in list(ncaa_payload.get("_games") or []):
                    if g.get("date") == day and (
                        g.get("status") == "final" or g.get("state") in {"C", "F", "3"}
                    ):
                        cid = _safe_int(g.get("contest_id"))
                        if cid:
                            ncaa_box_url = f"https://www.ncaa.com/game/{cid}/boxscore"
                        break
                if ncaa_box_url:
                    break
            ncaa_ln_fmt: dict[str, Any] = {}
            if ln_ind:
                ncaa_ln_fmt = {k: json_stat_value(k, v) for k, v in ln_ind.items() if v is not None}
            if is_p:
                ln_best, box_best = _college_pitcher_last_night_pro_keys(c, school, yday, ncaa_ln_fmt)
                if ln_best:
                    base["last_night"] = ln_best
                if box_best:
                    base["last_night_boxscore_url"] = box_best
                elif ncaa_box_url:
                    base["last_night_boxscore_url"] = ncaa_box_url
            elif ncaa_ln_fmt:
                base["last_night"] = ncaa_ln_fmt
                if ncaa_box_url:
                    base["last_night_boxscore_url"] = ncaa_box_url
            if (not is_p) and base["last_night"] and not _is_valid_hitter_last_night_line(base["last_night"]):
                base["last_night"] = {}
            if mtd_ind:
                base["month_to_date"] = {
                    k: json_stat_value(k, v) for k, v in mtd_ind.items() if v is not None
                }

            # Team-level fallbacks for hitters only (W/L + runs). Never attach that stub to pitchers.
            if not base["last_night"] and not is_p:
                base["last_night"] = ncaa_payload.get("last_night") or {}
            if not base["month_to_date"]:
                base["month_to_date"] = ncaa_payload.get("month_to_date") or {}
            if not base["season"]:
                ncaa_season = ncaa_payload.get("season") or {}
                if not _is_ncaa_team_season_stub(ncaa_season):
                    base["season"] = ncaa_season
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
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
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


def _maxpreps_pitching_subgroup(subgroups: list[dict[str, Any]], *stat_names: str) -> dict[str, Any] | None:
    for sg in subgroups:
        sm = _maxpreps_stat_map((sg.get("totalStats") or {}).get("stats") or [])
        if any(sm.get(name) not in (None, "", "0", 0) for name in stat_names):
            return sg
    return None


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
    if not subgroups:
        return [], {}
    sg0 = _maxpreps_pitching_subgroup(subgroups, "EarnedRunAverage", "Win", "Appearances") or subgroups[0]
    sg1 = _maxpreps_pitching_subgroup(
        subgroups, "InningsPitchedDecimal", "HitsAgainst", "BattersStruckOut"
    ) or (subgroups[1] if len(subgroups) > 1 else subgroups[0])
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


def _maxpreps_md_to_date(ds: Any, year: int) -> date | None:
    s = str(ds).strip()
    if not s:
        return None
    try:
        mm_s, dd_s = s.split("/", 1)
        return date(year, int(mm_s), int(dd_s))
    except Exception:
        return None


def _maxpreps_career_game_log_groups(next_data: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not next_data:
        return []
    try:
        return list(next_data["props"]["pageProps"]["statsCardProps"]["careerGameLogs"]["groups"] or [])
    except Exception:
        return []


def _maxpreps_next_has_batting_season(next_data: dict[str, Any] | None) -> bool:
    for g in _maxpreps_career_game_log_groups(next_data):
        if str(g.get("name", "")).strip().lower() != "batting":
            continue
        sg0 = (g.get("subgroups") or [{}])[0]
        t0 = _maxpreps_stat_map((sg0.get("totalStats") or {}).get("stats") or [])
        if _to_int(t0.get("AtBats")) > 0 or _to_int(t0.get("PlateAppearances")) > 0:
            return True
    return False


def _maxpreps_next_has_pitching_season(next_data: dict[str, Any] | None) -> bool:
    _, season = _maxpreps_pitching_rows(next_data)
    if not season:
        return False
    return _to_float(season.get("ip")) > 0


def _maxpreps_hs_hitter_stats_from_next(
    next_data: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Batting game logs from MaxPreps ``__NEXT_DATA__`` (BB/K live on a second batting subgroup)."""
    groups = _maxpreps_career_game_log_groups(next_data)
    if not groups:
        return [], {}
    by_lower = {str(g.get("name", "")).strip().lower(): g for g in groups}
    bg = by_lower.get("batting")
    if not bg:
        return [], {}
    subgroups = list(bg.get("subgroups") or [])
    if len(subgroups) < 2:
        return [], {}
    sg0, sg1 = subgroups[0], subgroups[1]

    sb_by_key: dict[tuple[str, str], int] = {}
    br_g = by_lower.get("baserunning")
    if br_g:
        sg_br = (br_g.get("subgroups") or [{}])[0]
        for r in sg_br.get("stats") or []:
            key = (str(r.get("date") or ""), str(r.get("contestUrl") or ""))
            sm = _maxpreps_stat_map(r.get("stats") or [])
            sb_by_key[key] = _to_int(sm.get("StolenBase"))

    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for r in sg0.get("stats") or []:
        key = (str(r.get("date") or ""), str(r.get("contestUrl") or ""))
        sm = _maxpreps_stat_map(r.get("stats") or [])
        by_key[key] = {
            "date": key[0],
            "contest_url": key[1],
            "ab": sm.get("AtBats"),
            "r": sm.get("Runs"),
            "h": sm.get("Hits"),
            "rbi": sm.get("RunsBattedIn"),
            "doubles": sm.get("Doubles"),
            "triples": sm.get("Triples"),
            "hr": sm.get("HomeRuns"),
            "avg": sm.get("BattingAverage"),
            "sb": sb_by_key.get(key, 0),
        }
    for r in sg1.get("stats") or []:
        key = (str(r.get("date") or ""), str(r.get("contestUrl") or ""))
        sm = _maxpreps_stat_map(r.get("stats") or [])
        row = by_key.get(key)
        if row is None:
            row = {"date": key[0], "contest_url": key[1], "sb": sb_by_key.get(key, 0)}
            by_key[key] = row
        row["bb"] = sm.get("BaseOnBalls")
        row["k"] = sm.get("StruckOut")
        row["ops"] = sm.get("OnBasePlusSluggingPercentage")

    rows = list(by_key.values())
    t0 = _maxpreps_stat_map((sg0.get("totalStats") or {}).get("stats") or [])
    t1 = _maxpreps_stat_map((sg1.get("totalStats") or {}).get("stats") or [])
    sb_season = 0
    if br_g:
        sg_br = (br_g.get("subgroups") or [{}])[0]
        tbr = _maxpreps_stat_map((sg_br.get("totalStats") or {}).get("stats") or [])
        sb_season = _to_int(tbr.get("StolenBase"))
    season = {
        "ab": t0.get("AtBats"),
        "r": t0.get("Runs"),
        "h": t0.get("Hits"),
        "rbi": t0.get("RunsBattedIn"),
        "doubles": t0.get("Doubles"),
        "triples": t0.get("Triples"),
        "hr": t0.get("HomeRuns"),
        "bb": t1.get("BaseOnBalls"),
        "k": t1.get("StruckOut"),
        "avg": t0.get("BattingAverage"),
        "ops": t1.get("OnBasePlusSluggingPercentage"),
        "sb": sb_season,
    }
    return rows, season


def _hs_apply_two_way_roles(
    entry: dict[str, str], next_data: dict[str, Any] | None, wants_pitcher: bool, wants_hitter: bool
) -> tuple[bool, bool]:
    """Ensure two-way HS athletes get separate hitter + pitcher dashboard/PDF rows."""
    nn = _norm_player_name(entry.get("name", ""))
    if nn in HS_PITCHER_ONLY_NAMES:
        return True, False
    if nn in HS_TWO_WAY_NAMES:
        return True, True
    if _maxpreps_next_has_batting_season(next_data):
        wants_hitter = True
    if _maxpreps_next_has_pitching_season(next_data):
        wants_pitcher = True
    return wants_pitcher, wants_hitter


def _apex_hs_client_name_set() -> frozenset[str]:
    return frozenset(_norm_player_name(c.get("name", "")) for c in load_high_school_clients(HS_SOURCE_XLSX))


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


def _hs_row_has_positive_stats(row: dict[str, Any]) -> bool:
    for section in ("last_night", "month_to_date", "season"):
        st = row.get(section) or {}
        if not isinstance(st, dict):
            continue
        for v in st.values():
            if _to_float(v) > 0:
                return True
    return False


def _apply_gc_lines_to_hs_row(
    row: dict[str, Any],
    *,
    season_line: dict[str, Any] | None,
    last_line: dict[str, Any] | None,
    month_line: dict[str, Any] | None,
    schedule_url: str,
    is_pitcher: bool,
) -> None:
    if schedule_url and not row.get("team_schedule_url"):
        row["team_schedule_url"] = schedule_url
    if season_line and not _hs_row_has_positive_stats({**row, "last_night": {}, "month_to_date": {}}):
        row["season"] = _amateur_line_to_pro_keys(season_line, is_pitcher)
    elif season_line and not row.get("season"):
        row["season"] = _amateur_line_to_pro_keys(season_line, is_pitcher)
    if last_line:
        mapped = _amateur_line_to_pro_keys(last_line, is_pitcher)
        if is_pitcher or _is_valid_hitter_last_night_line(mapped):
            row["last_night"] = mapped
    if month_line:
        if is_pitcher:
            month_merged = _with_rate_stats(month_line, True)
            row["month_to_date"] = _amateur_line_to_pro_keys(month_merged, True)
        else:
            row["month_to_date"] = _amateur_line_to_pro_keys(month_line, False)
    if _hs_row_has_positive_stats(row):
        row["stats_unavailable_reason"] = ""


def enrich_high_school_from_gamechanger(
    rows: list[dict[str, Any]],
    entry: dict[str, str],
    gc_index: GameChangerIndex,
) -> None:
    """Fill HS rows from GameChanger when MaxPreps is missing or empty."""
    if not rows:
        return
    needs = any(not _hs_row_has_positive_stats(r) for r in rows)
    if not needs:
        return
    ref = gc_index.match_player(
        entry.get("name", ""),
        entry.get("school", ""),
        _norm_player_name,
        _norm_token,
        _name_parts,
    )
    if not ref:
        return
    today = dashboard_date()
    yday = today - timedelta(days=1)
    month_start = today.replace(day=1)
    try:
        season_payload = gc_index.season_stats(ref.team_id)
        season_hit, season_pitch = _player_season_lines(season_payload, ref.player_id)
        last_hit, month_hit, last_pitch, month_pitch = gc_player_game_lines(
            gc_index, ref, yday, month_start, today
        )
    except Exception:
        return
    wants_pitcher = bool(entry.get("hs_is_pitcher"))
    wants_hitter = bool(entry.get("hs_is_hitter"))
    if not wants_pitcher and not wants_hitter:
        wants_hitter = True
    for row in rows:
        is_pitcher = bool(row.get("is_pitcher"))
        if is_pitcher and not wants_pitcher:
            continue
        if not is_pitcher and not wants_hitter:
            continue
        if _hs_row_has_positive_stats(row):
            continue
        if is_pitcher:
            _apply_gc_lines_to_hs_row(
                row,
                season_line=season_pitch,
                last_line=last_pitch,
                month_line=month_pitch,
                schedule_url=ref.schedule_url,
                is_pitcher=True,
            )
        else:
            _apply_gc_lines_to_hs_row(
                row,
                season_line=season_hit,
                last_line=last_hit,
                month_line=month_hit,
                schedule_url=ref.schedule_url,
                is_pitcher=False,
            )
        if ref.schedule_url:
            row["last_night_boxscore_url"] = ref.schedule_url


def build_high_school_payloads(entry: dict[str, str]) -> list[dict[str, Any]]:
    today = dashboard_date()
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
        "summer_season": {},
        "summer_last_night": {},
        "summer_month_to_date": {},
        "upcoming_series": [],
        "stats_unavailable_reason": "",
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
            base_hitter["stats_unavailable_reason"] = "MaxPreps statistics not available"
            out_no_url.append(base_hitter)
        if wants_pitcher:
            base_pitcher["stats_unavailable_reason"] = "MaxPreps statistics not available"
            out_no_url.append(base_pitcher)
        return out_no_url
    try:
        html = _maxpreps_get(url)
        tables = pd.read_html(StringIO(html))
    except Exception:
        out_err: list[dict[str, Any]] = []
        if wants_hitter:
            base_hitter["stats_unavailable_reason"] = "MaxPreps statistics not available"
            out_err.append(base_hitter)
        if wants_pitcher:
            base_pitcher["stats_unavailable_reason"] = "MaxPreps statistics not available"
            out_err.append(base_pitcher)
        return out_err
    next_data = _maxpreps_next_data(html)
    wants_pitcher, wants_hitter = _hs_apply_two_way_roles(entry, next_data, wants_pitcher, wants_hitter)
    batting, pitching = _pick_maxpreps_tables(tables)
    mp_b_rows, mp_b_season = _maxpreps_hs_hitter_stats_from_next(next_data)
    if wants_hitter and mp_b_rows:
        last_bd: dict[str, Any] | None = None
        month_bds: list[dict[str, Any]] = []
        for row in mp_b_rows:
            gd = _maxpreps_md_to_date(row.get("date"), today.year)
            if gd is None:
                continue
            if gd == yday:
                last_bd = row
            if gd.month == today.month and gd <= today:
                month_bds.append(row)
        if last_bd is not None:
            base_hitter["last_night"] = _amateur_line_to_pro_keys(
                {
                    "ab": last_bd.get("ab"),
                    "r": last_bd.get("r"),
                    "h": last_bd.get("h"),
                    "rbi": last_bd.get("rbi"),
                    "bb": last_bd.get("bb"),
                    "k": last_bd.get("k"),
                    "hr": last_bd.get("hr"),
                    "triples": last_bd.get("triples"),
                    "doubles": last_bd.get("doubles"),
                    "sb": last_bd.get("sb"),
                    "avg": last_bd.get("avg"),
                    "ops": last_bd.get("ops"),
                },
                False,
            )
            if not _is_valid_hitter_last_night_line(base_hitter["last_night"]):
                base_hitter["last_night"] = {}
        if month_bds:
            agg = {"ab": 0, "r": 0, "h": 0, "rbi": 0, "bb": 0, "k": 0, "hr": 0, "triples": 0, "doubles": 0, "sb": 0}
            for r in month_bds:
                agg["ab"] += int(to_number(r.get("ab")) or 0)
                agg["r"] += int(to_number(r.get("r")) or 0)
                agg["h"] += int(to_number(r.get("h")) or 0)
                agg["rbi"] += int(to_number(r.get("rbi")) or 0)
                agg["bb"] += int(to_number(r.get("bb")) or 0)
                agg["k"] += int(to_number(r.get("k")) or 0)
                agg["hr"] += int(to_number(r.get("hr")) or 0)
                agg["triples"] += int(to_number(r.get("triples")) or 0)
                agg["doubles"] += int(to_number(r.get("doubles")) or 0)
                agg["sb"] += int(to_number(r.get("sb")) or 0)
            agg["avg"] = round((agg["h"] / agg["ab"]), 3) if agg["ab"] else 0.0
            base_hitter["month_to_date"] = _amateur_line_to_pro_keys(agg, False)
        if mp_b_season:
            base_hitter["season"] = _amateur_line_to_pro_keys(mp_b_season, False)
    elif wants_hitter and batting is not None:
        batting.columns = [str(c).strip() for c in batting.columns]
        col_l = {str(c).strip().lower(): c for c in batting.columns}

        def _bat_col(*names: str) -> str | None:
            for n in names:
                c = col_l.get(n.lower())
                if c:
                    return c
            return None

        c_bb = _bat_col("bb", "walks", "base on balls")
        c_k = _bat_col("k", "so", "strikeouts", "strike outs")
        c_sb = _bat_col("sb", "stolen bases", "stolen base")
        c_3b = _bat_col("3b", "triples", "triple")
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
                            "bb": row.get(c_bb) if c_bb else row.get("BB"),
                            "k": row.get(c_k) if c_k else row.get("K"),
                            "hr": row.get("HR"),
                            "triples": row.get(c_3b) if c_3b else row.get("3B"),
                            "doubles": row.get("2B"),
                            "sb": row.get(c_sb) if c_sb else row.get("SB"),
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
                        "bb": last_row.get(c_bb) if c_bb else last_row.get("BB"),
                        "k": last_row.get(c_k) if c_k else last_row.get("K"),
                        "hr": last_row.get("HR"),
                        "triples": last_row.get(c_3b) if c_3b else last_row.get("3B"),
                        "doubles": last_row.get("2B"),
                        "sb": last_row.get(c_sb) if c_sb else last_row.get("SB"),
                        "avg": last_row.get("Avg"),
                        "ops": last_row.get("OPS"),
                    },
                    False,
                )
                if not _is_valid_hitter_last_night_line(base_hitter["last_night"]):
                    base_hitter["last_night"] = {}
            if month_rows:
                agg = {"ab": 0, "r": 0, "h": 0, "rbi": 0, "bb": 0, "k": 0, "hr": 0, "triples": 0, "doubles": 0, "sb": 0}
                for r in month_rows:
                    for k, c in (
                        ("ab", "AB"),
                        ("r", "R"),
                        ("h", "H"),
                        ("rbi", "RBI"),
                        ("bb", c_bb or "BB"),
                        ("k", c_k or "K"),
                        ("hr", "HR"),
                        ("triples", c_3b or "3B"),
                        ("doubles", "2B"),
                        ("sb", c_sb or "SB"),
                    ):
                        agg[k] += int(to_number(r.get(c)) or 0)
                agg["avg"] = round((agg["h"] / agg["ab"]), 3) if agg["ab"] else 0.0
                base_hitter["month_to_date"] = _amateur_line_to_pro_keys(agg, False)
    box_link = _maxpreps_link_for_day(html, yday)
    base_hitter["last_night_boxscore_url"] = box_link

    out: list[dict[str, Any]] = []
    if wants_hitter:
        out.append(base_hitter)
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
    if wants_pitcher:
        out.append(base_pitcher)
    # Flag rows with only empty/zero numeric output so UI can show explicit unavailability text.
    for row in out:
        is_hs = str(row.get("team_level", "")).upper() == "HS"
        if not is_hs:
            continue
        has_positive = False
        for section in ("last_night", "month_to_date", "season"):
            st = row.get(section) or {}
            if not isinstance(st, dict):
                continue
            for v in st.values():
                n = _to_float(v)
                if n > 0:
                    has_positive = True
                    break
            if has_positive:
                break
        if not has_positive:
            row["stats_unavailable_reason"] = "MaxPreps statistics not available"
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
    year_col = pick_col(["Year", "Grad Year", "Graduation Year"])
    url_col = pick_col(["MaxPreps URL", "Stats URL", "URL", "Profile URL", "Link"])
    program_col = pick_col(["Program", "Summer Program", "Travel Team", "Club"])
    if not name_col:
        return []

    out: list[dict[str, str]] = []
    for _, r in df.iterrows():
        raw_name = _cell_str(r.get(name_col, ""))
        if not raw_name:
            continue
        name = _parse_name(raw_name)
        norm = _norm_player_name(name)
        if norm in DASHBOARD_EXCLUDE_NAMES:
            continue
        stats_url = _cell_str(r.get(url_col, "")) if url_col else ""
        # Force known overrides when sheet links are stale/wrong sport pages.
        override_url = HS_MAXPREPS_URL_OVERRIDES.get(norm, "")
        if override_url:
            stats_url = override_url
        elif not stats_url:
            stats_url = ""
        program = _cell_str(r.get(program_col, "")) if program_col else ""
        if not program:
            program = HS_SUMMER_PROGRAM_OVERRIDES.get(norm, "")
        out.append(
            {
                "name": name,
                "position": _cell_str(r.get(pos_col, "")) if pos_col else "",
                "school": _cell_str(r.get(school_col, "")) if school_col else "",
                "agent": _normalize_agent_initials(_cell_str(r.get(agent_col, "")) if agent_col else ""),
                "grad_year": _cell_str(r.get(year_col, "")) if year_col else "",
                "stats_url": stats_url,
                "program": program,
                "hs_is_pitcher": _hs_position_flags(_cell_str(r.get(pos_col, "")) if pos_col else "")[0],
                "hs_is_hitter": _hs_position_flags(_cell_str(r.get(pos_col, "")) if pos_col else "")[1],
            }
        )
    return out


def load_jf_follow_clients(path: Path) -> list[dict[str, str]]:
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
    year_col = pick_col(["Year", "Grad Year", "Graduation Year"])
    city_col = pick_col(["City"])
    state_col = pick_col(["State"])
    commit_col = pick_col(["Commitment", "Commit"])
    url_col = pick_col(["MaxPreps URL", "Stats URL", "URL", "Profile URL", "Link"])
    if not name_col:
        return []
    out: list[dict[str, str]] = []
    for _, r in df.iterrows():
        name = _parse_name(_cell_str(r.get(name_col, "")))
        if not name:
            continue
        pos = _cell_str(r.get(pos_col, "")) if pos_col else ""
        school = _cell_str(r.get(school_col, "")) if school_col else ""
        city = _cell_str(r.get(city_col, "")) if city_col else ""
        state = _cell_str(r.get(state_col, "")) if state_col else ""
        loc = ", ".join([x for x in [city, state] if x])
        school_full = f"{school}, {loc}".strip(", ") if loc else school
        stats_url = _cell_str(r.get(url_col, "")) if url_col else ""
        out.append(
            {
                "name": name,
                "position": pos,
                "school": school_full,
                "commitment": _cell_str(r.get(commit_col, "")) if commit_col else "",
                "grad_year": _cell_str(r.get(year_col, "")) if year_col else "",
                "agent": "JF",
                "stats_url": stats_url,
                "hs_is_pitcher": _hs_position_flags(pos)[0],
                "hs_is_hitter": _hs_position_flags(pos)[1],
            }
        )
    return out


def _norm_program_key(program: str) -> str:
    return re.sub(r"\s+", " ", (program or "").strip().lower())


def _gc_discover_program_team_configs(program: str) -> list[dict[str, str]]:
    """Search GameChanger for teams matching a travel program label (cached)."""
    key = _norm_program_key(program)
    if not key:
        return []
    if key in _GC_DISCOVERED_TEAMS_CACHE:
        return _GC_DISCOVERED_TEAMS_CACHE[key]
    client = get_gamechanger_client()
    if not client:
        _GC_DISCOVERED_TEAMS_CACHE[key] = []
        return []
    queries = GC_PROGRAM_SEARCH_QUERIES.get(key) or [program.strip(), key.title()]
    teams: list[dict[str, str]] = []
    seen: set[str] = set()
    for q in queries:
        if not q:
            continue
        try:
            hits = search_gc_teams(client, q)
        except Exception:
            continue
        for t in hits:
            public_id = str(t.get("public_id") or "").strip()
            if not public_id or public_id in seen:
                continue
            seen.add(public_id)
            team_year = _grad_year_from_text(str(t.get("name") or "")) or ""
            cfg: dict[str, str] = {"public_id": public_id}
            internal_id = str(t.get("id") or "").strip()
            if internal_id:
                cfg["internal_id"] = internal_id
            if team_year:
                cfg["grad_year"] = team_year
            teams.append(cfg)
    _GC_DISCOVERED_TEAMS_CACHE[key] = teams
    return teams


def _gc_summer_team_configs(program: str, *, discover: bool = True) -> list[dict[str, str]]:
    key = _norm_program_key(program)
    static: list[dict[str, str]] = []
    cfg = GC_SUMMER_TEAMS.get(key)
    if cfg:
        static = list(cfg) if isinstance(cfg, list) else [cfg]
    discovered = _gc_discover_program_team_configs(program) if discover else []
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in static + discovered:
        public_id = str(item.get("public_id") or "").strip()
        if not public_id or public_id in seen:
            continue
        seen.add(public_id)
        out.append(item)
    return out


def _truthy_private_flag(v: Any) -> bool:
    s = str(v or "").strip().lower()
    return s in {"y", "yes", "true", "1", "*"}


def _ar_display_school(program: str, hs_school: str) -> str:
    prog = (program or "").strip()
    hs = (hs_school or "").strip()
    if prog and hs:
        return f"{prog} - {hs}"
    return prog or hs


def load_ar_follow_clients(path: Path) -> list[dict[str, str]]:
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
    program_col = pick_col(["Program", "Summer Program", "Travel Team", "Club"])
    year_col = pick_col(["Year", "Grad Year", "Graduation Year"])
    city_col = pick_col(["City"])
    state_col = pick_col(["State"])
    commit_col = pick_col(["Commitment", "Commit"])
    url_col = pick_col(["MaxPreps URL", "Stats URL", "URL", "Profile URL", "Link"])
    private_col = pick_col(["Private", "Private Email", "Email Private", "Star"])
    if not name_col:
        return []
    out: list[dict[str, str]] = []
    for _, r in df.iterrows():
        name = _parse_name(_cell_str(r.get(name_col, "")))
        if not name:
            continue
        pos = _cell_str(r.get(pos_col, "")) if pos_col else ""
        school = _cell_str(r.get(school_col, "")) if school_col else ""
        program = _cell_str(r.get(program_col, "")) if program_col else ""
        city = _cell_str(r.get(city_col, "")) if city_col else ""
        state = _cell_str(r.get(state_col, "")) if state_col else ""
        loc = ", ".join([x for x in [city, state] if x])
        school_full = f"{school}, {loc}".strip(", ") if loc else school
        stats_url = _cell_str(r.get(url_col, "")) if url_col else ""
        private = _truthy_private_flag(r.get(private_col, "")) if private_col else False
        out.append(
            {
                "name": name,
                "position": pos,
                "school": school_full,
                "program": program,
                "commitment": _cell_str(r.get(commit_col, "")) if commit_col else "",
                "grad_year": _cell_str(r.get(year_col, "")) if year_col else "",
                "agent": "AR",
                "stats_url": stats_url,
                "private_email": private,
                "hs_is_pitcher": _hs_position_flags(pos)[0],
                "hs_is_hitter": _hs_position_flags(pos)[1],
            }
        )
    return out


def _grad_year_from_text(text: str) -> str | None:
    m = re.search(r"\b(20\d{2})\b", str(text or ""))
    return m.group(1) if m else None


def _gc_summer_grad_year_ok(entry: dict[str, str], team_name: str, team_cfg: dict[str, str]) -> bool:
    """Skip cross-class roster matches (e.g. Jack Leeper 2027 vs Tommy Leeper 2029)."""
    player_year = str(entry.get("grad_year") or "").strip()
    if not player_year:
        return True
    team_year = str(team_cfg.get("grad_year") or "").strip() or _grad_year_from_text(team_name)
    if not team_year:
        return True
    return player_year == team_year


def _gc_summer_lines_for_team(
    entry: dict[str, str],
    gc_client: GameChangerClient,
    gc_index: GameChangerIndex | None,
    team_cfg: dict[str, str],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, str, str]:
    """Return season_hit, season_pitch, last_hit, last_pitch, schedule_url, team_name."""
    program = entry.get("program", "")
    public_id = str(team_cfg.get("public_id") or "").strip()
    internal_id = str(team_cfg.get("internal_id") or "").strip()
    if not public_id:
        return None, None, None, None, "", ""
    team_name = ""
    try:
        team_meta = gc_client.get(f"/public/teams/{public_id}")
        if isinstance(team_meta, dict):
            team_name = str(team_meta.get("name") or "")
    except Exception:
        pass
    if not _gc_summer_grad_year_ok(entry, team_name, team_cfg):
        return None, None, None, None, "", team_name
    try:
        roster = fetch_public_roster(gc_client, public_id)
    except Exception:
        return None, None, None, None, "", team_name
    player = match_gc_roster_player(
        roster, entry.get("name", ""), _norm_player_name, _norm_token, _name_parts
    )
    if not player:
        return None, None, None, None, "", team_name
    player_id = str(player.get("id") or "")
    if not player_id:
        return None, None, None, None, "", team_name
    schedule_url = ""
    if gc_index and internal_id:
        team_meta = gc_index._team_meta.get(internal_id) or {}
        schedule_url = str(team_meta.get("schedule_url") or "")
        if not schedule_url:
            schedule_url = _team_schedule_url(team_meta)
    season_hit: dict[str, Any] | None = None
    season_pitch: dict[str, Any] | None = None
    last_hit: dict[str, Any] | None = None
    last_pitch: dict[str, Any] | None = None
    if gc_index and internal_id:
        try:
            season_payload = gc_index.season_stats(internal_id)
            season_hit, season_pitch = _player_season_lines(season_payload, player_id)
            ref = GCPlayerRef(
                team_id=internal_id,
                team_name=program,
                player_id=player_id,
                first_name=str(player.get("first_name") or ""),
                last_name=str(player.get("last_name") or ""),
                schedule_url=schedule_url,
            )
            today = dashboard_date()
            yday = gc_report_anchor_date()
            month_start = yday.replace(day=1)
            last_hit, _, last_pitch, _ = gc_player_game_lines(
                gc_index, ref, yday, month_start, today
            )
        except Exception:
            season_hit, season_pitch = None, None
    if season_hit is None and season_pitch is None:
        season_hit, season_pitch = public_player_season_lines(gc_client, public_id, player_id)
    if season_hit is None and season_pitch is None and gc_index and internal_id:
        try:
            season_payload = gc_index.season_stats(internal_id)
            season_hit, season_pitch = _player_season_lines(season_payload, player_id)
        except Exception:
            pass
    return season_hit, season_pitch, last_hit, last_pitch, schedule_url, team_name


def _gc_summer_candidate_score(
    season_hit: dict[str, Any] | None,
    season_pitch: dict[str, Any] | None,
    last_hit: dict[str, Any] | None,
    last_pitch: dict[str, Any] | None,
    *,
    wants_pitcher: bool,
    wants_hitter: bool,
) -> float:
    """Prefer last-night lines, then the squad with the most season volume."""
    if last_hit or last_pitch:
        return 100_000.0
    score = 0.0
    if wants_pitcher and season_pitch:
        try:
            score += float(season_pitch.get("ip") or 0) * 100.0
        except (TypeError, ValueError):
            pass
    if wants_hitter and season_hit:
        try:
            score += float(season_hit.get("ab") or 0)
        except (TypeError, ValueError):
            pass
    if not wants_pitcher and not wants_hitter:
        if season_pitch:
            try:
                score += float(season_pitch.get("ip") or 0) * 100.0
            except (TypeError, ValueError):
                pass
        if season_hit:
            try:
                score += float(season_hit.get("ab") or 0)
            except (TypeError, ValueError):
                pass
    return score


def _gc_summer_team_display_name(team_rows: list[tuple[str, str, float, float]]) -> tuple[str, str]:
    """Pick primary team label/schedule URL when a player appears on multiple summer squads."""
    if not team_rows:
        return "", ""
    ranked = sorted(team_rows, key=lambda row: (row[2], row[3]), reverse=True)
    primary_name, primary_url, _, _ = ranked[0]
    extra = len(ranked) - 1
    if extra <= 0:
        return primary_name, primary_url
    suffix = f" (+{extra} team{'s' if extra != 1 else ''})"
    return f"{primary_name}{suffix}", primary_url


def _gc_summer_lines_for_player(
    entry: dict[str, str],
    gc_client: GameChangerClient,
    gc_index: GameChangerIndex | None,
    *,
    discover: bool = True,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, str, str]:
    """Return season_hit, season_pitch, last_hit, last_pitch, schedule_url, team_name."""
    wants_pitcher = bool(entry.get("hs_is_pitcher"))
    wants_hitter = bool(entry.get("hs_is_hitter"))
    if not wants_pitcher and not wants_hitter:
        wants_hitter = True
    program_key = _norm_program_key(entry.get("program", ""))
    use_discover = discover

    season_hits: list[dict[str, Any]] = []
    season_pitches: list[dict[str, Any]] = []
    last_hits: list[dict[str, Any]] = []
    last_pitches: list[dict[str, Any]] = []
    team_rows: list[tuple[str, str, float, float]] = []

    for team_cfg in _gc_summer_team_configs(entry.get("program", ""), discover=use_discover):
        season_hit, season_pitch, last_hit, last_pitch, schedule_url, team_name = _gc_summer_lines_for_team(
            entry, gc_client, gc_index, team_cfg
        )
        if not (season_hit or season_pitch or last_hit or last_pitch):
            continue
        if season_hit:
            season_hits.append(season_hit)
        if season_pitch:
            season_pitches.append(season_pitch)
        if last_hit:
            last_hits.append(last_hit)
        if last_pitch:
            last_pitches.append(last_pitch)
        pitch_ip = 0.0
        hit_ab = 0.0
        try:
            if season_pitch:
                pitch_ip = float(season_pitch.get("ip") or 0)
        except (TypeError, ValueError):
            pass
        try:
            if season_hit:
                hit_ab = float(season_hit.get("ab") or 0)
        except (TypeError, ValueError):
            pass
        team_rows.append((team_name or "", schedule_url or "", pitch_ip, hit_ab))

    if not team_rows:
        return None, None, None, None, "", ""

    team_label, schedule_url = _gc_summer_team_display_name(team_rows)
    season_hit = _merge_hit_lines(season_hits) if season_hits else None
    season_pitch = _merge_pitch_lines(season_pitches) if season_pitches else None
    last_hit = _merge_hit_lines(last_hits) if last_hits else None
    last_pitch = _merge_pitch_lines(last_pitches) if last_pitches else None
    return season_hit, season_pitch, last_hit, last_pitch, schedule_url, team_label


def _gc_summer_lines_any_program(
    entry: dict[str, str],
    gc_client: GameChangerClient | None,
    gc_index: GameChangerIndex | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, str, str]:
    """Match a player on any mapped summer travel team when program is unknown."""
    if not gc_client:
        return None, None, None, None, "", ""
    program = str(entry.get("program") or "").strip()
    if program:
        return _gc_summer_lines_for_player(entry, gc_client, gc_index, discover=True)
    for program_key in GC_SUMMER_TEAMS:
        probe = {**entry, "program": program_key}
        season_hit, season_pitch, last_hit, last_pitch, schedule_url, team_name = _gc_summer_lines_for_player(
            probe, gc_client, gc_index, discover=False
        )
        if season_hit or season_pitch or last_hit or last_pitch:
            return season_hit, season_pitch, last_hit, last_pitch, schedule_url, team_name
    return None, None, None, None, "", ""


def _apply_gc_lines_to_summer_row(
    row: dict[str, Any],
    *,
    season_line: dict[str, Any] | None,
    last_line: dict[str, Any] | None,
    month_line: dict[str, Any] | None,
    schedule_url: str,
    is_pitcher: bool,
) -> None:
    if schedule_url and not row.get("team_schedule_url"):
        row["team_schedule_url"] = schedule_url
    if season_line:
        row["summer_season"] = _ensure_ops_from_obp_slg(
            _amateur_line_to_pro_keys(season_line, is_pitcher)
        )
    if last_line:
        mapped = _amateur_line_to_pro_keys(last_line, is_pitcher)
        if is_pitcher or _is_valid_hitter_last_night_line(mapped):
            row["summer_last_night"] = _ensure_ops_from_obp_slg(mapped)
    if month_line:
        if is_pitcher:
            month_merged = _with_rate_stats(month_line, True)
            row["summer_month_to_date"] = _ensure_ops_from_obp_slg(
                _amateur_line_to_pro_keys(month_merged, True)
            )
        else:
            row["summer_month_to_date"] = _ensure_ops_from_obp_slg(
                _amateur_line_to_pro_keys(month_line, False)
            )


def attach_summer_travel_stats(
    rows: list[dict[str, Any]],
    entry: dict[str, str],
    gc_client: GameChangerClient | None,
    gc_index: GameChangerIndex | None,
) -> None:
    """Fill summer_* fields from mapped GameChanger travel teams."""
    if not rows or not gc_client:
        return
    season_hit, season_pitch, last_hit, last_pitch, schedule_url, summer_team = _gc_summer_lines_any_program(
        entry, gc_client, gc_index
    )
    if not (season_hit or season_pitch or last_hit or last_pitch):
        return
    wants_pitcher = bool(entry.get("hs_is_pitcher"))
    wants_hitter = bool(entry.get("hs_is_hitter"))
    if not wants_pitcher and not wants_hitter:
        wants_hitter = True
    for row in rows:
        is_pitcher = bool(row.get("is_pitcher"))
        if is_pitcher and not wants_pitcher:
            continue
        if not is_pitcher and not wants_hitter:
            continue
        if is_pitcher:
            _apply_gc_lines_to_summer_row(
                row,
                season_line=season_pitch,
                last_line=last_pitch,
                month_line=None,
                schedule_url=schedule_url,
                is_pitcher=True,
            )
        else:
            _apply_gc_lines_to_summer_row(
                row,
                season_line=season_hit,
                last_line=last_hit,
                month_line=None,
                schedule_url=schedule_url,
                is_pitcher=False,
            )
        if summer_team:
            row["summer_team"] = summer_team


def _append_ar_watch_row(
    out: list[dict[str, Any]],
    entry: dict[str, str],
    *,
    is_pitcher: bool,
    season: dict[str, Any],
    month_to_date: dict[str, Any],
    last_night: dict[str, Any],
    summer_season: dict[str, Any] | None = None,
    summer_month_to_date: dict[str, Any] | None = None,
    summer_last_night: dict[str, Any] | None = None,
    summer_team: str = "",
    stats_url: str,
    stats_unavailable_reason: str,
    summer_stats_unavailable_reason: str = "",
) -> None:
    pos = entry.get("position", "") or ("P" if is_pitcher else "")
    out.append(
        {
            "agent": "AR",
            "name": entry.get("name", ""),
            "position": pos,
            "is_pitcher": is_pitcher,
            "grad_year": entry.get("grad_year", ""),
            "school": _ar_display_school(entry.get("program", ""), entry.get("school", "")),
            "program": entry.get("program", ""),
            "commitment": entry.get("commitment", ""),
            "stats_url": stats_url,
            "private_email": bool(entry.get("private_email")),
            "season": _ensure_ops_from_obp_slg(season or {}),
            "month_to_date": _ensure_ops_from_obp_slg(month_to_date or {}),
            "last_night": _ensure_ops_from_obp_slg(last_night or {}),
            "summer_season": _ensure_ops_from_obp_slg(summer_season or {}),
            "summer_month_to_date": _ensure_ops_from_obp_slg(summer_month_to_date or {}),
            "summer_last_night": _ensure_ops_from_obp_slg(summer_last_night or {}),
            "summer_team": str(summer_team or "").strip(),
            "stats_unavailable_reason": stats_unavailable_reason,
            "summer_stats_unavailable_reason": summer_stats_unavailable_reason,
        }
    )


def build_ar_follow_rows(
    path: Path,
    gc_client: GameChangerClient | None = None,
    gc_index: GameChangerIndex | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    client = gc_client or get_gamechanger_client()
    index = gc_index
    if client and index is None:
        index = GameChangerIndex.build(client, _norm_player_name, _norm_token)
    hs_client_names = _apex_hs_client_name_set()
    for entry in load_ar_follow_clients(path):
        if _norm_player_name(entry.get("name", "")) in hs_client_names:
            continue
        season_hit, season_pitch, last_hit, last_pitch, gc_url, gc_team = (None, None, None, None, "", "")
        if client:
            season_hit, season_pitch, last_hit, last_pitch, gc_url, gc_team = _gc_summer_lines_for_player(
                entry, client, index
            )
        maxpreps_url = (entry.get("stats_url") or "").strip()
        wants_pitcher = bool(entry.get("hs_is_pitcher"))
        wants_hitter = bool(entry.get("hs_is_hitter"))
        if not wants_pitcher and not wants_hitter:
            wants_hitter = True
        built_rows = build_high_school_payloads({**entry, "agent": "AR", "stats_url": maxpreps_url})
        hs_hitter = next((br for br in built_rows if not br.get("is_pitcher")), None)
        hs_pitcher = next((br for br in built_rows if br.get("is_pitcher")), None)
        summer_hit = _ensure_ops_from_obp_slg(_amateur_line_to_pro_keys(season_hit or {}, False))
        summer_pitch = _ensure_ops_from_obp_slg(_amateur_line_to_pro_keys(season_pitch or {}, True))
        summer_ln_hit = _ensure_ops_from_obp_slg(_amateur_line_to_pro_keys(last_hit or {}, False))
        summer_ln_pitch = _ensure_ops_from_obp_slg(_amateur_line_to_pro_keys(last_pitch or {}, True))
        has_summer = bool(season_hit or season_pitch or last_hit or last_pitch)
        display_url = maxpreps_url or gc_url or ""
        if wants_hitter:
            hs = hs_hitter or {}
            hs_season = hs.get("season", {}) or {}
            hs_ln = hs.get("last_night", {}) or {}
            hs_mtd = hs.get("month_to_date", {}) or {}
            hs_reason = ""
            if maxpreps_url and not hs_season and not hs_ln:
                hs_reason = str(hs.get("stats_unavailable_reason") or "").strip()
            summer_reason = ""
            if not has_summer and not (summer_hit or summer_ln_hit):
                summer_reason = "Summer statistics not available"
            _append_ar_watch_row(
                out,
                entry,
                is_pitcher=False,
                season=hs_season,
                month_to_date=hs_mtd,
                last_night=hs_ln,
                summer_season=summer_hit,
                summer_last_night=summer_ln_hit,
                summer_team=gc_team,
                stats_url=display_url,
                stats_unavailable_reason=hs_reason,
                summer_stats_unavailable_reason=summer_reason,
            )
        if wants_pitcher:
            hs = hs_pitcher or {}
            hs_season = hs.get("season", {}) or {}
            hs_ln = hs.get("last_night", {}) or {}
            hs_mtd = hs.get("month_to_date", {}) or {}
            hs_reason = ""
            if maxpreps_url and not hs_season and not hs_ln:
                hs_reason = str(hs.get("stats_unavailable_reason") or "").strip()
            summer_reason = ""
            if not has_summer and not (summer_pitch or summer_ln_pitch):
                summer_reason = "Summer statistics not available"
            _append_ar_watch_row(
                out,
                entry,
                is_pitcher=True,
                season=hs_season,
                month_to_date=hs_mtd,
                last_night=hs_ln,
                summer_season=summer_pitch,
                summer_last_night=summer_ln_pitch,
                summer_team=gc_team,
                stats_url=display_url,
                stats_unavailable_reason=hs_reason,
                summer_stats_unavailable_reason=summer_reason,
            )
    return out


def build_jf_follow_rows(
    path: Path,
    gc_client: GameChangerClient | None = None,
    gc_index: GameChangerIndex | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    client = gc_client or get_gamechanger_client()
    index = gc_index
    if client and index is None:
        index = GameChangerIndex.build(client, _norm_player_name, _norm_token)
    for p in load_jf_follow_clients(path):
        built_rows = build_high_school_payloads(p)
        attach_summer_travel_stats(built_rows, p, client, index)
        has_hitter_row = any(not br.get("is_pitcher") for br in built_rows)
        has_pitcher_row = any(br.get("is_pitcher") for br in built_rows)
        if p.get("hs_is_pitcher") and not has_hitter_row:
            p2 = dict(p)
            p2["hs_is_hitter"] = True
            extra = [br for br in build_high_school_payloads(p2) if not br.get("is_pitcher")]
            attach_summer_travel_stats(extra, p2, client, index)
            built_rows.extend(extra)
        if p.get("hs_is_hitter") and not has_pitcher_row:
            p3 = dict(p)
            p3["hs_is_pitcher"] = True
            extra = [br for br in build_high_school_payloads(p3) if br.get("is_pitcher")]
            attach_summer_travel_stats(extra, p3, client, index)
            built_rows.extend(extra)
        for br in built_rows:
            season = _ensure_ops_from_obp_slg(br.get("season", {}) or {})
            month_to_date = _ensure_ops_from_obp_slg(br.get("month_to_date", {}) or {})
            last_night = _ensure_ops_from_obp_slg(br.get("last_night", {}) or {})
            summer_season = _ensure_ops_from_obp_slg(br.get("summer_season", {}) or {})
            summer_month_to_date = _ensure_ops_from_obp_slg(br.get("summer_month_to_date", {}) or {})
            summer_last_night = _ensure_ops_from_obp_slg(br.get("summer_last_night", {}) or {})
            summer_reason = ""
            if not summer_season and not summer_last_night:
                summer_reason = "Summer statistics not available"
            out.append(
                {
                    "agent": "JF",
                    "name": br.get("name", p.get("name", "")),
                    "position": br.get("position", p.get("position", "")),
                    "grad_year": p.get("grad_year", ""),
                    "school": p.get("school", ""),
                    "commitment": p.get("commitment", ""),
                    "stats_url": p.get("stats_url", ""),
                    "season": season,
                    "month_to_date": month_to_date,
                    "last_night": last_night,
                    "summer_season": summer_season,
                    "summer_month_to_date": summer_month_to_date,
                    "summer_last_night": summer_last_night,
                    "stats_unavailable_reason": br.get("stats_unavailable_reason", ""),
                    "summer_stats_unavailable_reason": summer_reason,
                }
            )
    return out


def _reset_dashboard_build_caches() -> None:
    """Fresh MLB/MiLB team catalog and scraper caches each sync (rehab teams, schedules)."""
    global TEAM_CATALOG, D1_PLAYERS_INDEX
    TEAM_CATALOG = None
    D1_PLAYERS_INDEX = None
    NCAA_SCHOOL_PAYLOAD_CACHE.clear()
    FOREIGN_BR_SEASON_CACHE.clear()
    D1_PLAYER_STATS_CACHE.clear()
    TASBS_SCHEDULE_GAME_PATHS.clear()
    TASBS_BOX_HTML_BY_URL.clear()
    NCAA_CONTESTS_BY_DATE.clear()
    NCAA_BOX_BY_CONTEST_ID.clear()
    ROSTER_CACHE.clear()
    _GC_DISCOVERED_TEAMS_CACHE.clear()


def _load_pro_clients_for_dashboard() -> list[Client]:
    clients = load_clients(SOURCE_XLSX)
    pro = [c for c in clients if not c.is_amateur]
    pro = [c for c in pro if _norm_player_name(c.name) not in DASHBOARD_EXCLUDE_NAMES]
    return [
        c
        for c in pro
        if "MEXIC"
        not in f"{c.league} {c.level} {c.minor_affiliate} {c.major_affiliate}".upper()
    ]


def _parallel_map(items: list[Any], fn, max_workers: int = 12) -> list[Any]:
    if not items:
        return []
    out: list[Any] = [None] * len(items)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        fut_map = {ex.submit(fn, item): i for i, item in enumerate(items)}
        for fut in as_completed(fut_map):
            idx = fut_map[fut]
            try:
                out[idx] = fut.result()
            except Exception:
                out[idx] = None
    return out


def refresh_pro_teams_in_dashboard(out: Path = OUT_JSON) -> Path:
    """
    Re-resolve pro team assignment from game logs (rehab, call-up, reassignment) and
    refresh pro last night / MTD / season without rebuilding amateur, HS, or trackers.
    """
    _reset_dashboard_build_caches()
    get_team_catalog()
    existing: dict[str, Any] = {}
    if out.is_file():
        existing = json.loads(out.read_text())
    pro_rows = [
        r
        for r in _parallel_map(_load_pro_clients_for_dashboard(), build_client_payload, max_workers=10)
        if isinstance(r, dict)
    ]
    existing["pro_clients"] = pro_rows
    existing["generated_at"] = datetime.now(UTC).isoformat()
    existing["last_night_date"] = report_anchor_date().isoformat()
    existing["season"] = existing.get("season") or SEASON

    def _json_safe(v: Any) -> Any:
        if isinstance(v, float):
            return v if math.isfinite(v) else None
        if isinstance(v, dict):
            return {k: _json_safe(x) for k, x in v.items()}
        if isinstance(v, list):
            return [_json_safe(x) for x in v]
        return v

    out.write_text(json.dumps(_json_safe(existing), separators=(",", ":"), allow_nan=False))
    return out


def refresh_trackers_in_dashboard(out: Path = OUT_JSON) -> Path:
    """Refresh arbitration + free agency tracker stats without rebuilding pro/amateur tabs."""
    _reset_dashboard_build_caches()
    get_team_catalog()
    existing: dict[str, Any] = {}
    if out.is_file():
        existing = json.loads(out.read_text())
    existing["arbitration_tracker"] = build_tracker_data(
        ARB_TRACKER_SOURCE_XLSX,
        TRACKER_PINNED_ARB,
        fallback_rows=(existing.get("arbitration_tracker") or {}).get("rows"),
        supplements=TRACKER_ARB_SUPPLEMENT,
    )
    existing["free_agency_tracker"] = build_tracker_data(
        FA_TRACKER_SOURCE_XLSX,
        TRACKER_PINNED_FA,
        fallback_rows=(existing.get("free_agency_tracker") or {}).get("rows"),
    )
    gc_client = get_gamechanger_client()
    gc_index = GameChangerIndex.build(gc_client, _norm_player_name, _norm_token) if gc_client else None
    existing["watch_list"] = {
        "JF": build_jf_follow_rows(JF_FOLLOW_SOURCE_XLSX, gc_client=gc_client, gc_index=gc_index),
        "AR": build_ar_follow_rows(AR_FOLLOW_SOURCE_XLSX, gc_client=gc_client, gc_index=gc_index),
    }
    existing["generated_at"] = datetime.now(UTC).isoformat()
    existing["season"] = existing.get("season") or SEASON

    def _json_safe(v: Any) -> Any:
        if isinstance(v, float):
            return v if math.isfinite(v) else None
        if isinstance(v, dict):
            return {k: _json_safe(x) for k, x in v.items()}
        if isinstance(v, list):
            return [_json_safe(x) for x in v]
        return v

    out.write_text(json.dumps(_json_safe(existing), separators=(",", ":"), allow_nan=False))
    return out


def _load_amateur_clients_for_dashboard() -> list[Client]:
    clients = load_clients(SOURCE_XLSX)
    amateur = [c for c in clients if c.is_amateur]
    dedicated_amateur = load_amateur_clients(AMATEUR_SOURCE_XLSX)
    if dedicated_amateur:
        merged: dict[str, Client] = {}
        for c in amateur:
            merged[_norm_player_name(c.name)] = c
        for c in dedicated_amateur:
            merged[_norm_player_name(c.name)] = c
        amateur = list(merged.values())
    amateur = _merge_manual_amateur_clients(amateur)
    amateur_expanded: list[Client] = []
    for c in amateur:
        amateur_expanded.extend(_split_two_way_amateur(c))
    return amateur_expanded


def _build_amateur_rows(clients: list[Client]) -> list[dict[str, Any]]:
    built = _parallel_map(clients, build_amateur_payload, max_workers=4)
    rows: list[dict[str, Any]] = []
    for i, item in enumerate(built):
        if isinstance(item, dict):
            rows.append(item)
        else:
            rows.append(build_amateur_payload(clients[i]))
    for i, row in enumerate(rows):
        if _individual_college_season_nonempty(row.get("season") or {}):
            continue
        time.sleep(0.35)
        rebuilt = build_amateur_payload(clients[i])
        if isinstance(rebuilt, dict):
            rows[i] = rebuilt
    return rows


def refresh_amateur_in_dashboard(out: Path = OUT_JSON) -> Path:
    """Refresh amateur tab (college + summer-ball) without rebuilding pro or trackers."""
    _reset_dashboard_build_caches()
    get_team_catalog()
    existing: dict[str, Any] = {}
    if out.is_file():
        existing = json.loads(out.read_text())
    amateur = _load_amateur_clients_for_dashboard()
    amateur_rows = _build_amateur_rows(amateur)
    existing["amateur_clients"] = amateur_rows
    existing["generated_at"] = datetime.now(UTC).isoformat()
    existing["last_night_date"] = report_anchor_date().isoformat()
    existing["season"] = existing.get("season") or SEASON

    def _json_safe(v: Any) -> Any:
        if isinstance(v, float):
            return v if math.isfinite(v) else None
        if isinstance(v, dict):
            return {k: _json_safe(x) for k, x in v.items()}
        if isinstance(v, list):
            return [_json_safe(x) for x in v]
        return v

    out.write_text(json.dumps(_json_safe(existing), separators=(",", ":"), allow_nan=False))
    return out


def build_dashboard_data() -> dict[str, Any]:
    _reset_dashboard_build_caches()
    get_team_catalog()
    clients = load_clients(SOURCE_XLSX)
    pro = _load_pro_clients_for_dashboard()
    amateur = _load_amateur_clients_for_dashboard()

    # Same roster + stats resolution for every pro row (no per-player exceptions).
    pro_rows = [r for r in _parallel_map(pro, build_client_payload, max_workers=10) if isinstance(r, dict)]
    amateur_rows = _build_amateur_rows(amateur)
    high_school_rows: list[dict[str, Any]] = []
    hs_clients = load_high_school_clients(HS_SOURCE_XLSX)
    gc_client = get_gamechanger_client()
    gc_index = GameChangerIndex.build(gc_client, _norm_player_name, _norm_token) if gc_client else None
    hs_built = _parallel_map(hs_clients, build_high_school_payloads, max_workers=8)
    for entry, rows in zip(hs_clients, hs_built):
        if isinstance(rows, list):
            if gc_index is not None:
                enrich_high_school_from_gamechanger(rows, entry, gc_index)
            attach_summer_travel_stats(rows, entry, gc_client, gc_index)
            high_school_rows.extend(rows)
    jf_watch_rows: list[dict[str, Any]] = build_jf_follow_rows(
        JF_FOLLOW_SOURCE_XLSX, gc_client=gc_client, gc_index=gc_index
    )
    ar_watch_rows: list[dict[str, Any]] = build_ar_follow_rows(
        AR_FOLLOW_SOURCE_XLSX, gc_client=gc_client, gc_index=gc_index
    )

    data = {
        "generated_at": datetime.now(UTC).isoformat(),
        "season": SEASON,
        "last_night_date": report_anchor_date().isoformat(),
        "pro_clients": pro_rows,
        "amateur_clients": amateur_rows,
        "high_school_clients": high_school_rows,
        "watch_list": {"JF": jf_watch_rows, "AR": ar_watch_rows},
        "arbitration_tracker": build_tracker_data(
            ARB_TRACKER_SOURCE_XLSX,
            TRACKER_PINNED_ARB,
            supplements=TRACKER_ARB_SUPPLEMENT,
        ),
        "free_agency_tracker": build_tracker_data(FA_TRACKER_SOURCE_XLSX, TRACKER_PINNED_FA),
    }
    return data


def _watch_list_nonempty(watch: Any) -> bool:
    if not isinstance(watch, dict):
        return False
    return any(isinstance(v, list) and len(v) > 0 for v in watch.values())


def _preserve_tracker_sections(new_data: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    """Keep prior tracker/watch data when a build cannot read the Excel sources (e.g. CI)."""
    if not existing:
        return new_data
    wl_new = new_data.get("watch_list")
    wl_old = existing.get("watch_list")
    if not _watch_list_nonempty(wl_new) and _watch_list_nonempty(wl_old):
        new_data["watch_list"] = wl_old
    for key in ("arbitration_tracker", "free_agency_tracker"):
        sec_new = new_data.get(key) if isinstance(new_data.get(key), dict) else {}
        sec_old = existing.get(key) if isinstance(existing.get(key), dict) else {}
        if not (sec_new.get("rows") or []) and (sec_old.get("rows") or []):
            new_data[key] = sec_old
    return new_data


def write_dashboard_data(out: Path = OUT_JSON) -> Path:
    def _json_safe(v: Any) -> Any:
        if isinstance(v, float):
            return v if math.isfinite(v) else None
        if isinstance(v, dict):
            return {k: _json_safe(x) for k, x in v.items()}
        if isinstance(v, list):
            return [_json_safe(x) for x in v]
        return v

    existing: dict[str, Any] = {}
    if out.is_file():
        try:
            existing = json.loads(out.read_text())
        except Exception:
            existing = {}
    data = _preserve_tracker_sections(build_dashboard_data(), existing)
    # Strict JSON for browser parsing: prevent NaN/Infinity tokens.
    out.write_text(json.dumps(_json_safe(data), separators=(",", ":"), allow_nan=False))
    return out


if __name__ == "__main__":
    import sys

    if "--pro-teams-only" in sys.argv:
        path = refresh_pro_teams_in_dashboard()
    elif "--trackers-only" in sys.argv:
        path = refresh_trackers_in_dashboard()
    elif "--amateur-only" in sys.argv:
        path = refresh_amateur_in_dashboard()
    else:
        path = write_dashboard_data()
    print(f"Wrote: {path}")
