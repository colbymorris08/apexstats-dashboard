#!/usr/bin/env python3
"""Build Apex pitcher client pitch-metrics workbook (MLB / MiLB / College sheets)."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

APEX_ROOT = Path(__file__).resolve().parents[1]
KNCT_ROOT = Path("/Users/colbymorris/knctdashboard")
OUT_XLSX = APEX_ROOT / "client_lists" / "Apex_Pitcher_Pitch_Metrics.xlsx"
COLLEGE_CACHE_JSON = APEX_ROOT / "client_lists" / ".knct_college_pitch_cache.json"
DASHBOARD_JSON = APEX_ROOT / "apex_dashboard_data.json"

PITCH_COLS = [
    "FB Velo",
    "FB IVB",
    "FB HB",
    "CH Velo",
    "CH IVB",
    "CH HB",
    "SL Velo",
    "SL IVB",
    "SL HB",
    "CB Velo",
    "CB IVB",
    "CB HB",
]

BASE_COLS = ["Name", "Organization", "Level", "College Team", "Age", *PITCH_COLS]
PRO_COLS = ["Name", "Organization", "Level", "Age", *PITCH_COLS]
COLLEGE_COLS = ["Name", "Level", "College Team", "Age", *PITCH_COLS]

# Statcast window for MLB pitch averages (calendar-year season).
MLB_STATCAST_SEASON = 2026

# Statcast fastball codes (prefer FF; fall back to SI).
FB_TYPES = ("FF", "SI")
PITCH_MAP = {
    "FB": FB_TYPES,
    "CH": ("CH",),
    "SL": ("SL",),
    "CB": ("CU", "KC", "CS"),
}


def _norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


def _name_parts(name: str) -> tuple[str, str]:
    parts = [p for p in (name or "").strip().split() if p]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[-1]


def _school_slug(school: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (school or "").lower()).strip()


def _blank_pitch_row() -> dict[str, Any]:
    return {c: None for c in PITCH_COLS}


def _pitch_row_from_map(values: dict[str, Any]) -> dict[str, Any]:
    out = _blank_pitch_row()
    for k in PITCH_COLS:
        v = values.get(k)
        if v is not None and v != "":
            try:
                out[k] = round(float(v), 1)
            except (TypeError, ValueError):
                out[k] = v
    return out


def _pitch_row_from_statcast_types(by_type: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out = _blank_pitch_row()

    def pick(types: tuple[str, ...]) -> dict[str, Any] | None:
        best: dict[str, Any] | None = None
        best_cnt = -1
        for t in types:
            row = by_type.get(t)
            if not row:
                continue
            cnt = int(row.get("count") or 0)
            if cnt > best_cnt:
                best_cnt = cnt
                best = row
        return best

    for label, types in PITCH_MAP.items():
        row = pick(types)
        if not row:
            continue
        out[f"{label} Velo"] = row.get("velo")
        out[f"{label} IVB"] = row.get("z")
        out[f"{label} HB"] = row.get("x")
    return out


def _load_college_cache() -> dict[str, Any]:
    if not COLLEGE_CACHE_JSON.is_file():
        return {}
    try:
        return json.loads(COLLEGE_CACHE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _college_cache_key(season: int, school: str, name: str) -> str:
    first, last = _name_parts(name)
    if not last:
        last, first = _name_parts(name.replace(",", " "))
    return f"{season}|d1|{_school_slug(school)}|{last.lower()}|{first.lower()}"


def _college_from_json_cache(season: int, school: str, name: str, cache: dict[str, Any]) -> dict[str, Any]:
    key = _college_cache_key(season, school, name)
    hit = cache.get(key)
    if isinstance(hit, dict) and hit.get("ok") and isinstance(hit.get("pitches"), dict):
        return _pitch_row_from_map(hit["pitches"])
    return _blank_pitch_row()


def _resolve_trackman_school_label(school: str) -> str:
    school = (school or "").strip()
    if not school:
        return ""
    knct_schools = KNCT_ROOT / "data" / "trackman_college_schools.json"
    if knct_schools.is_file():
        try:
            doc = json.loads(knct_schools.read_text(encoding="utf-8"))
            labels: list[str] = []
            for lvl in ("D1", "D2", "D3", "JUCO", "NAIA"):
                labels.extend(doc.get("by_level", {}).get(lvl, []) or [])
            labels.extend(doc.get("schools", []) or [])
            school_l = school.lower()
            # Exact prefix match (e.g. Oregon -> Oregon Ducks)
            for lab in labels:
                if lab.lower().startswith(school_l) or school_l in lab.lower():
                    return lab
        except Exception:
            pass
    # Minimal mascot defaults when index lookup fails.
    mascots = {
        "oregon": "Oregon Ducks",
        "clemson": "Clemson Tigers",
        "louisville": "Louisville Cardinals",
        "florida gulf coast": "Florida Gulf Coast Eagles",
        "illinois": "Illinois Fighting Illini",
        "uc santa barbara": "UC Santa Barbara Gauchos",
        "arkansas": "Arkansas Razorbacks",
        "florida atlantic": "Florida Atlantic Owls",
        "ucla": "UCLA Bruins",
        "uc berkeley": "California Golden Bears",
        "cal poly": "Cal Poly Mustangs",
        "florida": "Florida Gators",
        "high point": "High Point Panthers",
        "georgia tech": "Georgia Tech Yellow Jackets",
    }
    school_l = school.lower()
    for key, label in mascots.items():
        if school_l == key or school_l.startswith(key):
            return label
    return school


def _college_from_knct_disk(season: int, school: str, name: str) -> dict[str, Any]:
    if not KNCT_ROOT.is_dir():
        return _blank_pitch_row()
    sys.path.insert(0, str(KNCT_ROOT))
    try:
        from app.college_pitch_cache import load_trackman_pitch_frame, pitches_from_report_summary
    except Exception:
        return _blank_pitch_row()

    label = _resolve_trackman_school_label(school)
    frame, meta = load_trackman_pitch_frame(
        season=season,
        level="D1",
        school_label=label,
        pitcher_name=name,
    )
    by_type: dict[str, dict[str, Any]] = {}
    if frame is not None and not frame.empty:
        for ptype, grp in frame.groupby("pitch_type"):
            by_type[str(ptype).upper()] = {
                "count": len(grp),
                "velo": round(float(grp["release_speed"].mean()), 1),
                "x": round(float(grp["pfx_x"].mean()) * 12.0, 1),
                "z": round(float(grp["pfx_z"].mean()) * 12.0, 1),
            }
    elif meta and meta.get("report_summary"):
        for row in pitches_from_report_summary(meta["report_summary"]):
            t = str(row.get("type") or "").upper()
            if t:
                by_type[t] = row
    if by_type:
        return _pitch_row_from_statcast_types(by_type)
    return _blank_pitch_row()


def _mlb_pitch_metrics(player_id: int, *, season: int = MLB_STATCAST_SEASON) -> dict[str, Any]:
    try:
        from pybaseball import statcast_pitcher
    except Exception:
        return _blank_pitch_row()
    start = f"{season}-01-01"
    end = min(date.today(), date(season, 12, 31)).isoformat()
    try:
        df = statcast_pitcher(start, end, player_id)
    except Exception:
        return _blank_pitch_row()
    if df is None or df.empty:
        return _blank_pitch_row()
    need = ["pitch_type", "release_speed", "pfx_x", "pfx_z"]
    if not all(c in df.columns for c in need):
        return _blank_pitch_row()
    d = df[need].copy()
    d["pitch_type"] = d["pitch_type"].fillna("UN").astype(str).str.upper()
    d["release_speed"] = pd.to_numeric(d["release_speed"], errors="coerce")
    d["pfx_x"] = pd.to_numeric(d["pfx_x"], errors="coerce") * 12.0
    d["pfx_z"] = pd.to_numeric(d["pfx_z"], errors="coerce") * 12.0
    d = d.dropna(subset=["release_speed", "pfx_x", "pfx_z"])
    if d.empty:
        return _blank_pitch_row()
    by_type: dict[str, dict[str, Any]] = {}
    for ptype, grp in d.groupby("pitch_type"):
        by_type[str(ptype)] = {
            "count": len(grp),
            "velo": round(float(grp["release_speed"].mean()), 1),
            "x": round(float(grp["pfx_x"].mean()), 1),
            "z": round(float(grp["pfx_z"].mean()), 1),
        }
    return _pitch_row_from_statcast_types(by_type)


def _player_age(player_id: int | None) -> float | None:
    if not player_id:
        return None
    sys.path.insert(0, str(APEX_ROOT))
    try:
        import apex_dashboard_builder as b

        js = b._req_json(f"{b.API}/people/{player_id}")
        p = (js.get("people") or [{}])[0]
        age = p.get("currentAge")
        if age is not None:
            return float(age)
        bd = str(p.get("birthDate") or "")[:10]
        if len(bd) == 10:
            y, m, d = [int(x) for x in bd.split("-")]
            today = date.today()
            age_y = today.year - y - ((today.month, today.day) < (m, d))
            return float(age_y)
    except Exception:
        return None
    return None


def _dashboard_index() -> dict[str, dict[str, Any]]:
    if not DASHBOARD_JSON.is_file():
        return {}
    try:
        data = json.loads(DASHBOARD_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for key in ("pro_clients", "amateur_clients"):
        for row in data.get(key, []) or []:
            nn = _norm_name(str(row.get("name") or ""))
            if nn:
                out[nn] = row
    return out


def _pro_bucket(team_level: str) -> str:
    lvl = (team_level or "").strip().upper()
    if lvl == "MLB":
        return "MLB"
    if lvl in {"NPB", "KBO", "CPBL"}:
        return "MLB"  # treat intl pro like MLB tab for metrics rules
    return "MiLB"


def build_pro_rows(*, fetch_mlb: bool = True, season: int = MLB_STATCAST_SEASON) -> dict[str, list[dict[str, Any]]]:
    sys.path.insert(0, str(APEX_ROOT))
    import apex_dashboard_builder as b

    dash = _dashboard_index()
    pro_clients = [c for c in b.load_clients(b.SOURCE_XLSX) if b.is_pitcher(c.position)]
    sheets: dict[str, list[dict[str, Any]]] = {"MLB": [], "MiLB": []}

    for c in pro_clients:
        nn = _norm_name(c.name)
        drow = dash.get(nn, {})
        team_level = str(drow.get("team_level") or drow.get("level") or c.level or "").strip()
        org = str(drow.get("organization") or c.major_affiliate or "").strip()
        if org.lower() == "nan":
            org = ""
        bucket = _pro_bucket(team_level)
        pid = b.resolve_player_id(c)
        age = _player_age(pid)
        pitches = _blank_pitch_row()
        if bucket == "MLB" and fetch_mlb and pid:
            pitches = _mlb_pitch_metrics(pid, season=season)
        row = {
            "Name": c.name,
            "Organization": org,
            "Level": team_level or c.level,
            "Age": age,
            **pitches,
        }
        sheets[bucket].append(row)

    for key in sheets:
        sheets[key].sort(key=lambda r: (str(r.get("Name") or "").lower()))
    return sheets


def build_college_rows(*, season: int | None = None) -> list[dict[str, Any]]:
    sys.path.insert(0, str(APEX_ROOT))
    import apex_dashboard_builder as b

    if season is None:
        season = b.SEASON
    dash = _dashboard_index()
    college_cache = _load_college_cache()
    amateur_clients = [
        c
        for c in b.load_amateur_clients(b.AMATEUR_SOURCE_XLSX)
        if b.college_is_pitcher(c)
    ]
    rows: list[dict[str, Any]] = []

    for c in amateur_clients:
        nn = _norm_name(c.name)
        drow = dash.get(nn, {})
        school = str(drow.get("school_or_team") or c.school_or_team or c.minor_affiliate or "").strip()
        pitches = _college_from_json_cache(season, school, c.name, college_cache)
        if not any(pitches.get(k) is not None for k in PITCH_COLS):
            pitches = _college_from_knct_disk(season, school, c.name)
        rows.append(
            {
                "Name": c.name,
                "Level": "College",
                "College Team": school,
                "Age": None,
                **pitches,
            }
        )

    rows.sort(key=lambda r: (str(r.get("Name") or "").lower()))
    return rows


def load_college_rows_from_workbook(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        df = pd.read_excel(path, sheet_name="College")
    except Exception:
        return []
    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        row: dict[str, Any] = {}
        for col in COLLEGE_COLS:
            val = r.get(col) if col in df.columns else None
            if pd.isna(val):
                val = None
            row[col] = val
        rows.append(row)
    return rows


def write_workbook(sheets: dict[str, list[dict[str, Any]]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(sheets.get("MLB", []), columns=PRO_COLS).to_excel(
            writer, sheet_name="MLB", index=False
        )
        pd.DataFrame(sheets.get("MiLB", []), columns=PRO_COLS).to_excel(
            writer, sheet_name="MiLB", index=False
        )
        pd.DataFrame(sheets.get("College", []), columns=COLLEGE_COLS).to_excel(
            writer, sheet_name="College", index=False
        )
        all_rows: list[dict[str, Any]] = []
        for sheet_name in ("MLB", "MiLB"):
            for r in sheets.get(sheet_name, []):
                all_rows.append({"Category": sheet_name, **r})
        for r in sheets.get("College", []):
            all_rows.append({"Category": "College", **r})
        if all_rows:
            pd.DataFrame(all_rows).to_excel(writer, sheet_name="All Pitchers", index=False)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build Apex pitcher pitch-metrics Excel.")
    parser.add_argument(
        "--no-mlb-fetch",
        action="store_true",
        help="Skip Statcast pulls for MLB arms (faster; keeps MiLB blank / college from KNCT cache).",
    )
    parser.add_argument(
        "--keep-college",
        action="store_true",
        help="Reuse College sheet from existing workbook (skip KNCT/college rebuild).",
    )
    parser.add_argument(
        "--mlb-season",
        type=int,
        default=MLB_STATCAST_SEASON,
        help=f"Calendar year for MLB Statcast window (default: {MLB_STATCAST_SEASON}).",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the workbook after building (macOS).",
    )
    args = parser.parse_args()

    pro = build_pro_rows(fetch_mlb=not args.no_mlb_fetch, season=args.mlb_season)
    if args.keep_college or OUT_XLSX.is_file():
        college = load_college_rows_from_workbook(OUT_XLSX)
        if not college:
            college = build_college_rows()
            college_src = "rebuilt"
        else:
            college_src = f"kept from {OUT_XLSX.name}"
    else:
        college = build_college_rows()
        college_src = "rebuilt"

    sheets = {**pro, "College": college}
    write_workbook(sheets, OUT_XLSX)
    print(f"Wrote {OUT_XLSX}")
    print(f"  MLB Statcast season: {args.mlb_season}")
    print(f"  MLB: {len(sheets.get('MLB', []))} pitchers")
    print(f"  MiLB: {len(sheets.get('MiLB', []))} pitchers")
    print(f"  College: {len(sheets.get('College', []))} pitchers ({college_src})")

    if args.open:
        import subprocess

        subprocess.run(["open", str(OUT_XLSX)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
