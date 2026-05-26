#!/usr/bin/env python3
"""
Build a styled PDF from apex_dashboard_data.json: last-night + season columns.

Batting tables never show pitch count. Pitching tables include a **Pitches** column = last outing
pitch total (``numberOfPitches`` / ``pitchesThrown`` / similar from the pitcher line only).

PDF rows (pro, NCAA, HS): only if the row's last_night_date matches the JSON
last_night_date (the report anchor day) AND last_night has real counting stats.
Pitchers/hitters with only a team game stub (W/L + runs, no IP / no AB) are omitted.

Probable starters: schedule for the day after last_night_date (override with
APEX_PROBABLE_DATE). Pulled from the MLB Stats API ``/api/v1/schedule`` with
``sportIds`` 1,11,12,13,14,15,16,17 (MLB + all standard MiLB classes)—the same
calendar as https://www.mlb.com/milb/schedule/{date} (no HTML scraping). Only
probables that match exactly one Apex pro client by name + current team/org are listed.

Environment (optional email - omit APEX_PDF_EMAIL_TO to only write PDF):
  APEX_PDF_EMAIL_TO, APEX_PDF_EMAIL_FROM, APEX_SMTP_HOST, APEX_SMTP_PORT,
  APEX_SMTP_USER, APEX_SMTP_PASSWORD, APEX_SMTP_USE_SSL (1 for implicit TLS, e.g. port 465),
  APEX_PDF_OUT_DIR, APEX_PROBABLE_DATE

Input: ``apex_dashboard_data.json`` (run ``apex_dashboard_builder.py`` first).

Email-only (reuse current JSON; overwrites the PDF for that JSON's ``last_night_date`` and sends SMTP)::

    cd /path/to/apexstats && source ~/.apexstats_morning_email.env && python3 apex_last_night_pdf_email.py

Use a different env file for ``apex_daily_manual.sh`` by exporting ``APEX_EMAIL_ENV`` before running the script.
"""
from __future__ import annotations

import json
import os
import re
import smtplib
import sys
from datetime import date, datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import requests

OUT_JSON = Path(__file__).resolve().parent / "apex_dashboard_data.json"
API = "https://statsapi.mlb.com/api/v1"

HDR_FILL = (31, 73, 125)
HDR_TEXT = (255, 255, 255)
SEC_FILL = (230, 230, 230)
SEC_TEXT = (0, 0, 0)
ROW_ALT = (248, 248, 248)

PRO_LEVEL_ORDER = (
    "Majors",
    "International",
    "Triple-A",
    "Double-A",
    "High-A",
    "Single-A",
    "Rookie Leagues",
)

PROBABLE_LEVEL_ORDER = (
    "MLB",
    "Triple-A",
    "Double-A",
    "High-A",
    "Single-A",
    "Rookie Leagues",
)


def _truthy_stat(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, (int, float)):
        return v != 0
    s = str(v).strip().lower()
    if s in {"", "nan", "none", "null", "0", "0.0"}:
        return False
    return True


def last_night_nonempty(row: dict[str, Any]) -> bool:
    ln = row.get("last_night")
    if not isinstance(ln, dict) or not ln:
        return False
    for k, v in ln.items():
        if k == "summary" and v:
            return True
        if k != "summary" and _truthy_stat(v):
            return True
    return False


def _norm_report_date(s: Any) -> str:
    """YYYY-MM-DD for comparison."""
    t = str(s or "").strip().replace("/", "-")
    if len(t) >= 10 and t[4] == "-" and t[7] == "-":
        return t[:10]
    return t


def _next_calendar_day_iso(iso: Any) -> str:
    d = _norm_report_date(iso)
    if len(d) >= 10:
        try:
            return (date.fromisoformat(d[:10]) + timedelta(days=1)).isoformat()
        except ValueError:
            pass
    return str(iso or "").strip()


def _pdf_pitcher_line_is_individual(ln: Any) -> bool:
    """False for school team stubs (result/runs) with no pitching line."""
    if not isinstance(ln, dict) or not ln:
        return False
    if "result" in ln and "runs_for" in ln and "inningsPitched" not in ln:
        return False
    return True


def _pdf_hitter_line_is_individual(ln: Any) -> bool:
    """False for NCAA school last_night stub (W/L + runs, no batter box keys)."""
    if not isinstance(ln, dict) or not ln:
        return False
    keys = {str(k) for k in ln}
    if {"result", "runs_for"}.issubset(keys) and "atBats" not in keys and "plateAppearances" not in keys:
        return False
    return True


def pdf_row_for_last_night_email(row: dict[str, Any], report_last_night_iso: str) -> bool:
    """
    PDF-only: row appears only if stats are for the same calendar day as the
    dashboard last_night_date and look like an individual line, not a team stub.
    """
    if not isinstance(row, dict) or not last_night_nonempty(row):
        return False
    rd = _norm_report_date(report_last_night_iso)
    if not rd:
        return False
    row_d = _norm_report_date(row.get("last_night_date"))
    if row_d and row_d != rd:
        return False
    if not row_d:
        return False
    ln = row.get("last_night") or {}
    if row.get("is_pitcher"):
        return _pdf_pitcher_line_is_individual(ln)
    return _pdf_hitter_line_is_individual(ln)


def _pos_short(pos: str) -> str:
    p = (pos or "").strip().upper().replace("/", " ").replace(",", " ")
    toks = [t for t in p.split() if t]
    if not toks:
        return ""
    if len(toks) <= 2:
        return "-".join(toks)[:12]
    return "-".join(toks[:3])[:14]


def _org_cell(row: dict[str, Any]) -> str:
    o = str(row.get("organization") or "").strip()
    if o:
        return o
    return str(row.get("current_team") or "").strip()


def _player_cell(row: dict[str, Any]) -> str:
    return str(row.get("name") or "").strip()


def _pro_level_bucket(row: dict[str, Any]) -> str:
    tl = str(row.get("team_level") or "").strip().upper()
    lg = f"{row.get('league', '')} {row.get('minor_affiliate', '')} {row.get('current_team', '')}".upper()
    if tl == "MLB":
        return "Majors"
    if any(x in lg for x in ("KBO", "NPB", "CPBL", "LIDOM", "LVBP", "MEXICAN", "AUSTRALIAN")):
        return "International"
    if tl == "AAA" or "TRIPLE-A" in lg or "TRIPLE A" in lg:
        return "Triple-A"
    if tl == "AA" and "AAA" not in tl:
        return "Double-A"
    if tl in {"A+", "HIGH-A", "HIGH A"} or "HIGH-A" in lg:
        return "High-A"
    if tl == "A" or ("SINGLE-A" in lg and "HIGH" not in lg):
        return "Single-A"
    if tl in {"RK", "R", "ROOKIE"} or any(
        x in lg for x in ("ACL ", "FCL ", "DSL ", "COMPLEX", "ROOKIE", "RK ")
    ):
        return "Rookie Leagues"
    if tl:
        return "Single-A"
    return "Rookie Leagues"


def _fmt_num(v: Any, dec: int | None = None) -> str:
    if v is None or v == "":
        return ""
    if isinstance(v, float) and dec is not None:
        return f"{v:.{dec}f}".rstrip("0").rstrip(".")
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return str(v)
    return str(v)


def _fmt_avg(v: Any) -> str:
    if v in (None, ""):
        return ""
    try:
        n = float(v)
    except Exception:
        return str(v)
    x = n / 1000 if n > 1.5 else n
    s = f"{x:.3f}"
    return s[1:] if s.startswith("0.") else s


def _fmt_ops(v: Any) -> str:
    if v in (None, ""):
        return ""
    try:
        n = float(v)
    except Exception:
        return str(v)
    x = n / 1000 if n > 4 else n
    return f"{x:.3f}"


def _fmt_era(v: Any) -> str:
    if v in (None, ""):
        return ""
    try:
        return f"{float(v):.2f}"
    except Exception:
        return str(v)


def _pitcher_last_game_pitch_count(ln: dict[str, Any]) -> str:
    """Pitchers only: total pitches from the last outing line (never used for hitting rows)."""
    for k in ("numberOfPitches", "pitchesThrown", "pitchCount", "pitches", "npc"):
        v = ln.get(k)
        if v is None or v == "":
            continue
        if isinstance(v, (int, float)) and v > 0:
            return _fmt_num(v)
        s = str(v).strip().lower()
        if s and s not in ("0", "0.0", "null", "none"):
            return _fmt_num(v)
    return ""


def _sport_bucket_from_team(team: dict[str, Any]) -> str:
    sp = team.get("sport") or {}
    sid = int(sp.get("id") or 0)
    if sid == 1:
        return "MLB"
    if sid == 11:
        return "Triple-A"
    if sid == 12:
        return "Double-A"
    if sid == 13:
        return "High-A"
    if sid == 14:
        return "Single-A"
    if sid in (15, 16, 17):
        return "Rookie Leagues"
    ln = str((team.get("league") or {}).get("name", "")).lower()
    abbr = str((team.get("league") or {}).get("abbreviation", "")).upper()
    if (
        "triple" in ln
        or "international league" in ln
        or "pacific coast" in ln
        or abbr in ("IL", "PCL")
    ):
        return "Triple-A"
    if (
        any(x in ln for x in ("eastern league", "southern league", "texas league"))
        or abbr in ("EL", "SL", "TEX")
    ):
        return "Double-A"
    if "high" in ln:
        return "High-A"
    if "single" in ln or "carolina" in ln:
        return "Single-A"
    return "Rookie Leagues"


def _fetch_pitcher_wl_era(
    pid: int, sport_id: int, season: int, cache: dict[tuple[int, int], tuple[str, str, str]]
) -> tuple[str, str, str]:
    key = (pid, int(sport_id or 1))
    if key in cache:
        return cache[key]
    try:
        import apex_dashboard_builder as adb

        st = adb.fetch_player_stats_preferred_then_all_sports(
            pid, "pitching", "season", sport_id or 1, season=season
        )
    except Exception:
        st = {}
    w = _fmt_num(st.get("wins"), None) or "0"
    el = _fmt_num(st.get("losses"), None) or "0"
    era = _fmt_era(st.get("era"))
    cache[key] = (w, el, era)
    return cache[key]


def _game_matchup_line(game: dict[str, Any]) -> str:
    away = (game.get("teams") or {}).get("away", {}).get("team", {}).get("name", "") or ""
    home = (game.get("teams") or {}).get("home", {}).get("team", {}).get("name", "") or ""
    return f"{away} @ {home}"


def _game_time_et(game: dict[str, Any]) -> str:
    raw = str(game.get("gameDate") or "")
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        et = dt.astimezone(ZoneInfo("America/New_York"))
        s = et.strftime("%I:%M%p").lstrip("0")
        return f"{s} ET"
    except Exception:
        return ""


def _normalize_name_key(s: str) -> str:
    return re.sub(r"[^a-z]+", "", (s or "").lower())


_NAME_SUFFIX = frozenset({"jr", "sr", "ii", "iii", "iv", "v"})


def _first_last_lower(name: str) -> tuple[str, str] | None:
    parts = [p.strip(".,") for p in (name or "").lower().split() if p.strip(".,")]
    while len(parts) >= 2 and parts[-1] in _NAME_SUFFIX:
        parts.pop()
    if len(parts) < 2:
        return None
    return parts[0], parts[-1]


def _names_match_strict(api_name: str, roster_name: str) -> bool:
    a = (api_name or "").strip()
    r = (roster_name or "").strip()
    if not a or not r:
        return False
    if _normalize_name_key(a) == _normalize_name_key(r):
        return True
    fl_a = _first_last_lower(a)
    fl_r = _first_last_lower(r)
    if fl_a and fl_r and fl_a == fl_r:
        return True
    return False


def _norm_team_compact(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _schedule_team_name_variants(team: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    if not isinstance(team, dict):
        return out
    for k in ("name", "teamName", "abbreviation", "fileCode", "shortName"):
        v = team.get(k)
        if isinstance(v, str) and v.strip():
            out.add(_norm_team_compact(v))
    return {x for x in out if x}


def _client_team_variants(row: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    if not isinstance(row, dict):
        return out
    for k in ("current_team", "organization", "affiliates"):
        v = row.get(k)
        if isinstance(v, str) and v.strip():
            out.add(_norm_team_compact(v))
    return {x for x in out if x}


def _probable_team_matches_client(sched_team: dict[str, Any], row: dict[str, Any]) -> bool:
    sched_v = _schedule_team_name_variants(sched_team)
    cli_v = _client_team_variants(row)
    if not sched_v or not cli_v:
        return False
    for a in sched_v:
        for b in cli_v:
            if a == b or (len(a) >= 4 and (a in b or b in a)):
                return True
    return False


def _find_apex_client_for_probable(
    api_name: str, sched_team: dict[str, Any], apex_rows: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if not api_name or not isinstance(sched_team, dict):
        return None
    matches: list[dict[str, Any]] = []
    for r in apex_rows:
        if not isinstance(r, dict):
            continue
        nm = str(r.get("name") or "").strip()
        if not nm or not _names_match_strict(api_name, nm):
            continue
        if not _probable_team_matches_client(sched_team, r):
            continue
        matches.append(r)
    if len(matches) != 1:
        return None
    return matches[0]


def fetch_probable_starters_by_level(
    schedule_date: str, season: int, apex_pro_clients: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """Probables for ``schedule_date``: Apex-matched pitchers only.

    Uses ``GET /api/v1/schedule`` with ``sportIds=1,11,12,13,14,15,16,17`` and
    ``hydrate=probablePitcher,team(league)`` — same game calendar as the MiLB
    schedule page (e.g. https://www.mlb.com/milb/schedule/2026-05-13 for
    ``schedule_date=2026-05-13``), including MLB + MiLB. No scraping of mlb.com HTML.
    """
    out: dict[str, list[str]] = {k: [] for k in PROBABLE_LEVEL_ORDER}
    apex = [r for r in apex_pro_clients if isinstance(r, dict)]
    url = f"{API}/schedule?" + urlencode(
        {
            "sportIds": "1,11,12,13,14,15,16,17",
            "date": schedule_date,
            "hydrate": "probablePitcher,team(league)",
        }
    )
    try:
        js = requests.get(url, timeout=40).json()
    except Exception:
        return out

    cache: dict[tuple[int, int], tuple[str, str, str]] = {}
    for d in js.get("dates") or []:
        for game in d.get("games") or []:
            gt = str(game.get("gameType") or "").upper()
            if gt and gt != "R":
                continue
            for side in ("away", "home"):
                side_o = (game.get("teams") or {}).get(side) or {}
                pp = side_o.get("probablePitcher") or {}
                pid = int(pp.get("id") or 0)
                if not pid:
                    continue
                api_name = str(pp.get("fullName") or "").strip()
                team = side_o.get("team") or {}
                if not _find_apex_client_for_probable(api_name, team, apex):
                    continue
                bucket = _sport_bucket_from_team(team)
                if bucket not in out:
                    continue
                spid = int((team.get("sport") or {}).get("id") or 1)
                w, l, era = _fetch_pitcher_wl_era(pid, spid, season, cache)
                wl = f"{w}-{l}"
                era_s = era if era else "-"
                line = f"{api_name} ({wl}, {era_s} ERA): {_game_matchup_line(game)}, {_game_time_et(game)}"
                out[bucket].append(line)
    for k in out:
        out[k].sort()
    return out


def _draw_header_row(pdf: Any, headers: list[str], col_widths: list[float]) -> None:
    pdf.set_font("Helvetica", "B", 6.0)
    pdf.set_fill_color(*HDR_FILL)
    pdf.set_text_color(*HDR_TEXT)
    for h, w in zip(headers, col_widths):
        pdf.cell(w, 5.5, _cell_fit(h, w, 6.0, pdf=pdf), border=1, align="C", fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)


def _draw_level_bar(pdf: Any, title: str, width: float) -> None:
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*SEC_FILL)
    pdf.set_text_color(*SEC_TEXT)
    pdf.cell(width, 6, title, border=0, fill=True, new_x="LMARGIN", new_y="NEXT")


def _name_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    """Last name, then first name (stable alphabetical within each level)."""
    name = str(row.get("name") or "").strip().lower()
    name = re.sub(r"[^a-z0-9 '\-]", " ", name)
    parts = [p for p in name.split() if p and p not in {"jr", "sr", "ii", "iii", "iv"}]
    if len(parts) >= 2:
        return (parts[-1], " ".join(parts[:-1]))
    return (name, "")


def _sort_rows_by_name(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=_name_sort_key)


def _pdf_usable_width(pdf: Any) -> float:
    return float(pdf.w - pdf.l_margin - pdf.r_margin)


def _scale_cols(base: list[float], total: float) -> list[float]:
    s = sum(base)
    return [w * total / s for w in base] if s else base


def _cell_fit(text: str, width_mm: float, font_size: float = 6.0, pdf: Any = None) -> str:
    t = str(text or "")
    if not t:
        return ""
    avail = max(2.0, width_mm - 1.2)
    if pdf is not None:
        style = getattr(pdf, "font_style", "") or ""
        family = getattr(pdf, "font_family", "Helvetica") or "Helvetica"
        pdf.set_font(family, style, font_size)
        try:
            if pdf.get_string_width(t) <= avail:
                return t
            lo, hi = 0, len(t)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if pdf.get_string_width(t[:mid]) <= avail:
                    lo = mid
                else:
                    hi = mid - 1
            return t[:lo] if lo else ""
        except Exception:
            pass
    max_chars = max(2, int(avail / (font_size * 0.32)))
    return t if len(t) <= max_chars else t[:max_chars]


def _stat_val(d: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def _draw_data_row(
    pdf: Any,
    cells: list[str],
    col_widths: list[float],
    zebra: bool,
    aligns: list[str] | None = None,
    font_size: float = 6.0,
) -> None:
    pdf.set_font("Helvetica", "", font_size)
    if zebra:
        pdf.set_fill_color(*ROW_ALT)
    else:
        pdf.set_fill_color(255, 255, 255)
    pdf.set_text_color(0, 0, 0)
    al = aligns or (["C"] * len(cells))
    if len(al) < len(cells):
        al = al + ["C"] * (len(cells) - len(al))
    for c, w, a in zip(cells, col_widths, al):
        pdf.cell(w, 5.2, _cell_fit(c, w, font_size, pdf=pdf), border=1, align=a, fill=True)
    pdf.ln()


def _slash_mdy(iso: str) -> str:
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
        return f"{d.month}/{d.day}"
    except Exception:
        return iso


def write_last_night_pdf(data: dict[str, Any], out_path: Path) -> None:
    try:
        from fpdf import FPDF
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "Missing fpdf2. Install: pip install fpdf2\n"
            "Or: pip install -r apex_dashboard_requirements.txt"
        ) from e

    report_anchor = _norm_report_date(str(data.get("last_night_date") or ""))
    last_date = report_anchor or str(data.get("last_night_date") or "").strip() or "unknown-date"
    season_y = int(data.get("season") or datetime.now().year)
    generated = str(data.get("generated_at") or "")[:19]
    probable_date = (os.environ.get("APEX_PROBABLE_DATE") or "").strip() or _next_calendar_day_iso(
        report_anchor
    )

    pro = [r for r in (data.get("pro_clients") or []) if isinstance(r, dict)]
    pro_ln = [r for r in pro if pdf_row_for_last_night_email(r, report_anchor)]
    amateur = [
        r
        for r in (data.get("amateur_clients") or [])
        if isinstance(r, dict) and pdf_row_for_last_night_email(r, report_anchor)
    ]
    hs = [
        r
        for r in (data.get("high_school_clients") or [])
        if isinstance(r, dict) and pdf_row_for_last_night_email(r, report_anchor)
    ]

    # Legal landscape (~356mm wide) so wide pitching tables are not clipped.
    pdf = FPDF(orientation="L", unit="mm", format="Legal")
    pdf.set_margins(4, 8, 4)
    pdf.set_auto_page_break(auto=True, margin=8)
    pdf.add_page()
    usable_w = _pdf_usable_width(pdf)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, f"Apex last night / season ({last_date})", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(
        0,
        5,
        f"Generated {generated}   |   Probables: {probable_date} (default day after last night; APEX_PROBABLE_DATE overrides)",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(2)

    # Game cols then season cols; scaled to full page width so OPS is not clipped.
    b_headers = [
        "Player",
        "Org",
        "Pos",
        "AB",
        "R",
        "H",
        "RBI",
        "BB",
        "K",
        "HR",
        "3B",
        "2B",
        "SB",
        "HBP",
        "AVG",
        "OPS",
        "sHBP",
    ]
    b_base = [24, 28, 8, 7, 6, 6, 7, 6, 6, 6, 6, 6, 6, 7, 8, 8, 7]
    b_w = _scale_cols(b_base, usable_w)
    b_align = ["L", "L", "C"] + ["C"] * (len(b_headers) - 3)

    p_headers = [
        "Player",
        "Org",
        "Pos",
        "IP",
        "H",
        "R",
        "ER",
        "BB",
        "SO",
        "HR",
        "Pit",
        "WP",
        "HB",
        "BK",
        "W",
        "L",
        "SV",
        "BS",
        "Hld",
        "ERA",
        "sW",
        "sL",
        "sSV",
        "sBS",
        "sH",
        "sWP",
        "sHB",
        "sBK",
    ]
    # Extra weight on Player/Org; many game + season pitching columns.
    p_base = [34, 40, 9] + [7] * 16 + [8] * 9
    p_w = _scale_cols(p_base, usable_w)
    p_align = ["L", "L", "C"] + ["C"] * (len(p_headers) - 3)

    def season_ops(se: dict[str, Any]) -> Any:
        obp, slg, ops = se.get("obp"), se.get("slg"), se.get("ops")
        if (ops in (None, "", 0)) and obp not in (None, "") and slg not in (None, ""):
            try:
                return float(obp) + float(slg)
            except Exception:
                return ops
        return ops

    def batter_pdf_cells(r: dict[str, Any]) -> list[str]:
        ln = r.get("last_night") or {}
        se = r.get("season") or {}
        return [
            _player_cell(r),
            _org_cell(r),
            _pos_short(str(r.get("position") or "")),
            _fmt_num(_stat_val(ln, "atBats")),
            _fmt_num(_stat_val(ln, "runs")),
            _fmt_num(_stat_val(ln, "hits")),
            _fmt_num(_stat_val(ln, "rbi")),
            _fmt_num(_stat_val(ln, "baseOnBalls")),
            _fmt_num(_stat_val(ln, "strikeOuts")),
            _fmt_num(_stat_val(ln, "homeRuns")),
            _fmt_num(_stat_val(ln, "triples")),
            _fmt_num(_stat_val(ln, "doubles")),
            _fmt_num(_stat_val(ln, "stolenBases")),
            _fmt_num(_stat_val(ln, "hitByPitch")),
            _fmt_avg(se.get("avg")),
            _fmt_ops(season_ops(se)),
            _fmt_num(_stat_val(se, "hitByPitch")),
        ]

    def pitcher_pdf_cells(r: dict[str, Any]) -> list[str]:
        ln = r.get("last_night") or {}
        se = r.get("season") or {}
        return [
            _player_cell(r),
            _org_cell(r),
            _pos_short(str(r.get("position") or "")),
            _fmt_num(_stat_val(ln, "inningsPitched")),
            _fmt_num(_stat_val(ln, "hits")),
            _fmt_num(_stat_val(ln, "runs")),
            _fmt_num(_stat_val(ln, "earnedRuns")),
            _fmt_num(_stat_val(ln, "baseOnBalls")),
            _fmt_num(_stat_val(ln, "strikeOuts")),
            _fmt_num(_stat_val(ln, "homeRuns")),
            _pitcher_last_game_pitch_count(ln),
            _fmt_num(_stat_val(ln, "wildPitches")),
            _fmt_num(_stat_val(ln, "hitBatsmen", "hitByPitch")),
            _fmt_num(_stat_val(ln, "balks")),
            _fmt_num(_stat_val(ln, "wins")),
            _fmt_num(_stat_val(ln, "losses")),
            _fmt_num(_stat_val(ln, "saves")),
            _fmt_num(_stat_val(ln, "blownSaves")),
            _fmt_num(_stat_val(ln, "holds")),
            _fmt_era(se.get("era")),
            _fmt_num(_stat_val(se, "wins")),
            _fmt_num(_stat_val(se, "losses")),
            _fmt_num(_stat_val(se, "saves")),
            _fmt_num(_stat_val(se, "blownSaves")),
            _fmt_num(_stat_val(se, "holds")),
            _fmt_num(_stat_val(se, "wildPitches")),
            _fmt_num(_stat_val(se, "hitBatsmen", "hitByPitch")),
            _fmt_num(_stat_val(se, "balks")),
        ]

    row_zebra = 0

    batters = [r for r in pro_ln if not r.get("is_pitcher")]
    if batters:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Batting", new_x="LMARGIN", new_y="NEXT")
        _draw_header_row(pdf, b_headers, b_w)
        groups: dict[str, list[dict[str, Any]]] = {k: [] for k in PRO_LEVEL_ORDER}
        for r in batters:
            groups.setdefault(_pro_level_bucket(r), []).append(r)
        for lvl in PRO_LEVEL_ORDER:
            rows = groups.get(lvl) or []
            if not rows:
                continue
            _draw_level_bar(pdf, f"{lvl}:", usable_w)
            for r in _sort_rows_by_name(rows):
                _draw_data_row(pdf, batter_pdf_cells(r), b_w, bool(row_zebra % 2), b_align)
                row_zebra += 1
        pdf.ln(3)

    pitchers = [r for r in pro_ln if r.get("is_pitcher")]
    if pitchers:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Pitching", new_x="LMARGIN", new_y="NEXT")
        _draw_header_row(pdf, p_headers, p_w)
        pg: dict[str, list[dict[str, Any]]] = {k: [] for k in PRO_LEVEL_ORDER}
        for r in pitchers:
            pg.setdefault(_pro_level_bucket(r), []).append(r)
        for lvl in PRO_LEVEL_ORDER:
            rows = pg.get(lvl) or []
            if not rows:
                continue
            _draw_level_bar(pdf, f"{lvl}:", usable_w)
            for r in _sort_rows_by_name(rows):
                _draw_data_row(pdf, pitcher_pdf_cells(r), p_w, bool(row_zebra % 2), p_align)
                row_zebra += 1
        pdf.ln(3)

    if amateur:
        am_h = [r for r in amateur if not r.get("is_pitcher")]
        am_p = [r for r in amateur if r.get("is_pitcher")]
        if am_h:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "NCAA - Batting", new_x="LMARGIN", new_y="NEXT")
            _draw_header_row(pdf, b_headers, b_w)
            for r in _sort_rows_by_name(am_h):
                _draw_data_row(pdf, batter_pdf_cells(r), b_w, bool(row_zebra % 2), b_align)
                row_zebra += 1
            pdf.ln(2)
        if am_p:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "NCAA - Pitching", new_x="LMARGIN", new_y="NEXT")
            _draw_header_row(pdf, p_headers, p_w)
            for r in _sort_rows_by_name(am_p):
                _draw_data_row(pdf, pitcher_pdf_cells(r), p_w, bool(row_zebra % 2), p_align)
                row_zebra += 1
            pdf.ln(2)

    if hs:
        hs_h = [r for r in hs if not r.get("is_pitcher")]
        hs_p = [r for r in hs if r.get("is_pitcher")]
        if hs_h:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "High School - Batting", new_x="LMARGIN", new_y="NEXT")
            _draw_header_row(pdf, b_headers, b_w)
            for r in _sort_rows_by_name(hs_h):
                _draw_data_row(pdf, batter_pdf_cells(r), b_w, bool(row_zebra % 2), b_align)
                row_zebra += 1
            pdf.ln(2)
        if hs_p:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "High School - Pitching", new_x="LMARGIN", new_y="NEXT")
            _draw_header_row(pdf, p_headers, p_w)
            for r in _sort_rows_by_name(hs_p):
                _draw_data_row(pdf, pitcher_pdf_cells(r), p_w, bool(row_zebra % 2), p_align)
                row_zebra += 1
            pdf.ln(2)

    prob_map = fetch_probable_starters_by_level(probable_date, season_y, pro)
    if any(prob_map.get(lvl) for lvl in PROBABLE_LEVEL_ORDER):
        pdf.set_font("Helvetica", "B", 11)
        prob_lbl = _slash_mdy(probable_date)
        pdf.cell(0, 7, f"{prob_lbl} Probable Starters:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        for lvl in PROBABLE_LEVEL_ORDER:
            lines = prob_map.get(lvl) or []
            if not lines:
                continue
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, f"{lvl}:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 8)
            for pl in lines:
                pdf.multi_cell(0, 4.5, f"- {pl}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))


def _send_pdf_smtp(pdf_path: Path, subject: str, body_text: str) -> None:
    to_raw = os.environ.get("APEX_PDF_EMAIL_TO", "").strip()
    if not to_raw:
        print("APEX_PDF_EMAIL_TO not set - PDF written, not emailed.")
        return

    recipients = [x.strip() for x in to_raw.split(",") if x.strip()]
    if not recipients:
        return

    host = os.environ.get("APEX_SMTP_HOST", "").strip()
    user = os.environ.get("APEX_SMTP_USER", "").strip()
    password = os.environ.get("APEX_SMTP_PASSWORD", "").strip()
    if not host or not user or not password:
        raise SystemExit("Email requested but set APEX_SMTP_HOST, APEX_SMTP_USER, APEX_SMTP_PASSWORD.")

    port = int(os.environ.get("APEX_SMTP_PORT", "587"))
    use_ssl = os.environ.get("APEX_SMTP_USE_SSL", "").strip().lower() in ("1", "true", "yes") or port == 465
    from_addr = os.environ.get("APEX_PDF_EMAIL_FROM", "").strip() or recipients[0]

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(body_text, "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEApplication(f.read(), Name=pdf_path.name)
    part["Content-Disposition"] = f'attachment; filename="{pdf_path.name}"'
    msg.attach(part)

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=60) as smtp:
                smtp.login(user, password)
                smtp.sendmail(from_addr, recipients, msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=60) as smtp:
                smtp.starttls()
                smtp.login(user, password)
                smtp.sendmail(from_addr, recipients, msg.as_string())
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError(
            "SMTP login rejected. For Gmail use a 16-character App Password (Account → Security → "
            "2-Step Verification → App passwords), not your normal password; APEX_SMTP_USER must be that Gmail. "
            f"Server: {e}"
        ) from e
    print(f"Emailed {pdf_path.name} to {len(recipients)} recipient(s): {', '.join(recipients)}")


def main() -> int:
    if not OUT_JSON.is_file():
        print(f"Missing {OUT_JSON}", file=sys.stderr)
        return 1

    with open(OUT_JSON, encoding="utf-8") as f:
        data = json.load(f)

    last_date = str(data.get("last_night_date") or "unknown").replace("/", "-")
    out_dir = Path(os.environ.get("APEX_PDF_OUT_DIR", str(OUT_JSON.parent))).resolve()
    pdf_path = out_dir / f"apex_last_night_{last_date}.pdf"

    write_last_night_pdf(data, pdf_path)
    print(f"Wrote {pdf_path}")

    subject = f"Apex last-night stats ({last_date})"
    body = (
        f"Last night date in JSON: {data.get('last_night_date')}\n"
        f"Data generated_at: {data.get('generated_at')}\n\n"
        f"PDF attached: {pdf_path.name}\n"
    )
    try:
        _send_pdf_smtp(pdf_path, subject, body)
    except Exception as e:
        print(f"Email failed: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
