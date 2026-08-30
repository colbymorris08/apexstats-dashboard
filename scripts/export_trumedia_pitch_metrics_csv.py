#!/usr/bin/env python3
"""Export Apex pro pitcher pitch metrics from TruMedia (Giants site) to CSV."""

from __future__ import annotations

import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import browser_cookie3
import requests

APEX_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APEX_ROOT))

OUT_CSV = APEX_ROOT / "client_lists" / "Apex_Pro_Pitch_Metrics_2026.csv"

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

BASE_COLS = ["Name", "Organization", "Level", "Age", *PITCH_COLS]

# From Apex pro pitcher metrics template (2026).
PLAYERS: list[dict[str, str]] = [
    {"Name": "Aaron Shortridge", "Organization": "Washington Nationals", "Level": "A+"},
    {"Name": "Alex Barr", "Organization": "Athletics", "Level": "A"},
    {"Name": "Avery Short", "Organization": "Arizona Diamondbacks", "Level": "AA"},
    {"Name": "Ben Abeldt", "Organization": "Texas Rangers", "Level": "Rk"},
    {"Name": "Bryce Warrecker", "Organization": "New York Yankees", "Level": "A+"},
    {"Name": "Caden Monke", "Organization": "Kansas City Royals", "Level": "AA"},
    {"Name": "Cam Millar", "Organization": "Kansas City Royals", "Level": "Rk"},
    {"Name": "Carson Palmquist", "Organization": "Washington Nationals", "Level": "AAA"},
    {"Name": "Dale Stanavich", "Organization": "San Francisco Giants", "Level": "AA"},
    {"Name": "Derek True", "Organization": "Houston Astros", "Level": "AA"},
    {"Name": "Dom Reid", "Organization": "Chicago Cubs", "Level": "A"},
    {"Name": "Eric Adler", "Organization": "Chicago White Sox", "Level": "AA"},
    {"Name": "Evan Phillips", "Organization": "Los Angeles Dodgers", "Level": "AAA"},
    {"Name": "Franco Aleman", "Organization": "Cleveland Guardians", "Level": "AAA"},
    {"Name": "Garrett Baumann", "Organization": "Atlanta Braves", "Level": "AA"},
    {"Name": "Grayson Moore", "Organization": "Chicago Cubs", "Level": "A+"},
    {"Name": "Gunner Mayer", "Organization": "Seattle Mariners", "Level": "AAA"},
    {"Name": "Hayden Juenger", "Organization": "Toronto Blue Jays", "Level": "AAA"},
    {"Name": "Jason Alexander", "Organization": "Houston Astros", "Level": "AAA"},
    {"Name": "John Michael Bertrand", "Organization": "San Francisco Giants", "Level": "AAA"},
    {"Name": "Kris Bubic", "Organization": "Kansas City Royals", "Level": "AAA"},
    {"Name": "Matt Ager", "Organization": "Pittsburgh Pirates", "Level": "AA"},
    {"Name": "Matt Krook", "Organization": "Athletics", "Level": "AAA"},
    {"Name": "Nick Burdi", "Organization": "New York Mets", "Level": "AAA"},
    {"Name": "Noah Song", "Organization": "Boston Red Sox", "Level": "AAA"},
    {"Name": "Ryan Gallagher", "Organization": "Minnesota Twins", "Level": "AAA"},
    {"Name": "Ryan Harvey", "Organization": "Detroit Tigers", "Level": "A+"},
    {"Name": "Ryan Vanderhei", "Organization": "San Francisco Giants", "Level": "AA"},
    {"Name": "Sam Tookoian", "Organization": "Los Angeles Angels", "Level": "A+"},
    {"Name": "Seth Johnson", "Organization": "Philadelphia Phillies", "Level": "AAA"},
    {"Name": "Steven Brooks", "Organization": "Boston Red Sox", "Level": "A+"},
    {"Name": "Thatcher Hurd", "Organization": "New York Yankees", "Level": "A"},
    {"Name": "Tyler Schweitzer", "Organization": "Chicago White Sox", "Level": "AAA"},
    {"Name": "Walter Ford", "Organization": "Seattle Mariners", "Level": "A+"},
]

# TruMedia / MLBAM ids when not resolved from Apex client list.
PLAYER_ID_OVERRIDES: dict[str, int] = {
    "Derek True": 689223,
    "Dom Reid": 805255,
}

TRUMEDIA_BASE = "https://giants.trumedianetworks.com"
SEASON = 2026
SPLIT_KEYS = {
    "FB": ["FastSink^19", "Fastball (4S)^0", "Sinker^18", "Fastball (2S) / Sinker^1"],
    "CH": ["Change^5"],
    "SL": ["Sweepers and Sliders^9", "Sweeper^8", "Slider^3"],
    "CB": ["Curveball^4"],
}


def _chrome_cookies() -> dict[str, str]:
    jar = browser_cookie3.chrome(domain_name="trumedianetworks.com")
    return {c.name: c.value for c in jar}


def _raw_val(cell: Any) -> float | None:
    if cell is None:
        return None
    if isinstance(cell, (int, float)):
        return float(cell)
    if isinstance(cell, list) and len(cell) >= 2:
        try:
            return float(cell[1])
        except (TypeError, ValueError):
            return None
    s = str(cell).strip()
    if not s or s == "-":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _round1(v: float | None) -> float | None:
    if v is None:
        return None
    return round(v, 1)


class TruMediaClient:
    def __init__(self, cookies: dict[str, str]) -> None:
        self.session = requests.Session()
        self.session.cookies.update(cookies)
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )
        self._splits_clause: str | None = None

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        r = self.session.post(f"{TRUMEDIA_BASE}{path}", json=payload, timeout=90)
        r.raise_for_status()
        return r.json()

    def splits_clause(self) -> str:
        if self._splits_clause:
            return self._splits_clause
        meta = self._post(
            "/combined-splits",
            {
                "table": {
                    "staticStats": [],
                    "stats": [],
                    "orderBy": {},
                    "dpData": None,
                    "selectedReport": {
                        "selectedReportName": "Notable Pitching Metrics",
                        "selectedReportId": 226,
                    },
                },
                "descriptor": {
                    "namespaces": ["f", "pc"],
                    "sport": "BASEBALL",
                    "teamId": 137,
                    "siteName": "giants",
                    "f": {"bseason": [str(SEASON)], "bgt": ["reg"], "bpitchType": []},
                    "pc": {"bsst": "standard", "butp": "none"},
                },
                "entityData": {
                    "entityId": 1,
                    "modalIdClause": "'1' as playerId",
                    "entityClause": "playerId='1'",
                    "entityTable": "player p",
                },
                "filters": ["filterBaseballPitchType"],
                "groupByClauses": {},
                "additionalWhere": "",
            },
        )
        self._splits_clause = str(meta["splitsClause"])
        return self._splits_clause

    def pitch_splits(self, player_id: int) -> dict[str, dict[str, float | None]]:
        pid = int(player_id)
        descriptor = {
            "namespaces": ["f", "pc"],
            "sport": "BASEBALL",
            "teamId": 137,
            "siteName": "giants",
            "f": {"bseason": [str(SEASON)], "bgt": ["reg"], "bpitchType": []},
            "pc": {"bsst": "standard", "butp": "none"},
            "restrictiveEventCheck": True,
        }
        entity = {
            "entityId": pid,
            "modalIdClause": f"'{pid}' as playerId",
            "entityClause": f"playerId='{pid}'",
            "entityTable": "player p",
        }
        statement = (
            f"SELECT '{pid}' as playerId, SplitBy, [Vel], [TMIndVertBrk], [TMHrzBrk], [P|PIT] "
            f"FROM player p WHERE playerId='{pid}' SPLIT BY {self.splits_clause()}"
        )
        js = self._post(
            "/dp-proxy",
            {
                "format": "MIXED",
                "statement": statement,
                "descriptor": json.dumps(descriptor),
                "entityData": entity,
            },
        )
        by_split: dict[str, dict[str, float | None]] = {}
        for row in js.get("rows") or []:
            if not row or len(row) < 7:
                continue
            label = str(row[0]).split("^")[0]
            pitches = _raw_val(row[6]) or 0
            if pitches <= 0:
                continue
            by_split[str(row[0])] = {
                "label": label,
                "pitches": pitches,
                "velo": _raw_val(row[3]),
                "ivb": _raw_val(row[4]),
                "hb": _raw_val(row[5]),
            }
        return by_split


def _pick_split(by_split: dict[str, dict[str, float | None]], keys: list[str]) -> dict[str, float | None] | None:
    for key in keys:
        hit = by_split.get(key)
        if hit and (hit.get("pitches") or 0) > 0:
            return hit
    return None


def _pitch_row(by_split: dict[str, dict[str, float | None]]) -> dict[str, float | None]:
    out: dict[str, float | None] = {c: None for c in PITCH_COLS}
    for label, keys in SPLIT_KEYS.items():
        hit = _pick_split(by_split, keys)
        if not hit:
            continue
        out[f"{label} Velo"] = _round1(hit.get("velo"))
        out[f"{label} IVB"] = _round1(hit.get("ivb"))
        out[f"{label} HB"] = _round1(hit.get("hb"))
    return out


def main() -> int:
    import apex_dashboard_builder as b

    cookies = _chrome_cookies()
    if not cookies.get("accessToken"):
        print("No TruMedia session in Chrome — log in at giants.trumedianetworks.com first.", file=sys.stderr)
        return 1

    tm = TruMediaClient(cookies)
    tm.splits_clause()

    clients = {c.name: c for c in b.load_clients(b.SOURCE_XLSX)}
    rows_out: list[dict[str, Any]] = []

    for spec in PLAYERS:
        name = spec["Name"]
        row: dict[str, Any] = {
            "Name": name,
            "Organization": spec["Organization"],
            "Level": spec["Level"],
            "Age": None,
            **{c: None for c in PITCH_COLS},
        }
        client = clients.get(name)
        pid = b.resolve_player_id(client) if client else None
        if not pid:
            pid = PLAYER_ID_OVERRIDES.get(name)
        if pid:
            try:
                age_js = b._req_json(f"{b.API}/people/{pid}")
                age = (age_js.get("people") or [{}])[0].get("currentAge")
                if age is not None:
                    row["Age"] = float(age)
            except Exception:
                pass
            try:
                splits = tm.pitch_splits(pid)
                row.update(_pitch_row(splits))
            except Exception as exc:
                print(f"WARN {name} ({pid}): {exc}", file=sys.stderr)
        else:
            print(f"WARN no MLBAM id: {name}", file=sys.stderr)
        rows_out.append(row)
        time.sleep(0.15)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=BASE_COLS)
        w.writeheader()
        w.writerows(rows_out)

    filled = sum(1 for r in rows_out if any(r.get(c) is not None for c in PITCH_COLS))
    print(f"Wrote {OUT_CSV}")
    print(f"  Players: {len(rows_out)} | with pitch data: {filled}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
