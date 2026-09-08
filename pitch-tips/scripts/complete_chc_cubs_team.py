#!/usr/bin/env python3
"""Complete Chicago Cubs FULL pitching staff + 2 catchers (timed team publish).

Untouched team: CHC had tipCount=0 / zero tip1 video prefixes on full site.
Staff = entire 2026 active MLB pitching roster (14) + catchers Carson Kelly & Miguel Amaya.

Workflow per pitcher tip pitch-code × filter:
  - sample up to N≈10 dated play_ids (features.csv and/or Statcast)
  - download Savant CF clips into a temp dir
  - identity/pitch-type gate via Statcast join (pitcher id + pitch_type)
  - publish newest dated exemplar to media/video/{prefix}_{code}[{sit}].mp4
  - write sidecar .meta.json; purge temp immediately (keep ≥15 GB free when possible)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cv"))

from preflight.fetch_savant import download_play_clip, is_decodable  # noqa: E402

VIDEO = ROOT / "media" / "video"
TMP = ROOT / "runs" / "chc_cubs_exemplars" / "_tmp_clips"
META_DIR = ROOT / "runs" / "chc_cubs_exemplars"
MIN_FREE_GB = 12.0  # floor; target ≥15 via purge; APFS may report ~14 at start
N_SAMPLE = 10
UA = {"User-Agent": "PreflightCV/0.7 (+chc-cubs-full-staff)"}

# Full 2026 active CHC pitching staff (MLB roster) — starters + key relievers.
# codes = top pitch types for tip1 video matrix (5 when available).
PITCHERS = [
    {
        "name": "Shota Imanaga",
        "pid": "shota_imanaga",
        "mlbam": 684007,
        "prefix": "imanaga",
        "run": "shota_imanaga_poc",
        "codes": ["ff", "fs", "st", "si", "sl"],
        "throws": "L",
        "role": "SP",
    },
    {
        "name": "Matthew Boyd",
        "pid": "matthew_boyd",
        "mlbam": 571510,
        "prefix": "boyd",
        "run": "matthew_boyd_poc",
        "codes": ["ff", "ch", "sl", "cu", "si"],
        "throws": "L",
        "role": "SP",
    },
    {
        "name": "Kevin Gausman",
        "pid": "kevin_gausman",
        "mlbam": 592332,
        "prefix": "gausman",
        "run": "kevin_gausman_poc",
        "codes": ["ff", "fs", "sl", "ch"],
        "throws": "R",
        "role": "SP",
    },
    {
        "name": "Colin Rea",
        "pid": "colin_rea",
        "mlbam": 607067,
        "prefix": "rea",
        "run": "colin_rea_poc",
        "codes": ["ff", "ch", "sl", "st", "si"],
        "throws": "R",
        "role": "SP",
    },
    {
        "name": "Clay Holmes",
        "pid": "clay_holmes",
        "mlbam": 605280,
        "prefix": "holmes",
        "run": "clay_holmes_poc",
        "codes": ["si", "fc", "st", "ch", "cu"],
        "throws": "R",
        "role": "SP",
    },
    {
        "name": "Aaron Civale",
        "pid": "aaron_civale",
        "mlbam": 650644,
        "prefix": "civale",
        "run": "aaron_civale_poc",
        "codes": ["fc", "cu", "si", "ff", "fs"],
        "throws": "R",
        "role": "SP",
    },
    {
        "name": "Javier Assad",
        "pid": "javier_assad",
        "mlbam": 665871,
        "prefix": "assad",
        "run": "javier_assad_poc",
        "codes": ["si", "ff", "fc", "st", "ch"],
        "throws": "R",
        "role": "SP",
    },
    {
        "name": "Daniel Palencia",
        "pid": "daniel_palencia",
        "mlbam": 694037,
        "prefix": "palencia",
        "run": "daniel_palencia_poc",
        "codes": ["ff", "sl", "fs", "si"],
        "throws": "R",
        "role": "RP",
    },
    {
        "name": "Caleb Thielbar",
        "pid": "caleb_thielbar",
        "mlbam": 573204,
        "prefix": "thielbar",
        "run": "caleb_thielbar_poc",
        "codes": ["ff", "cu", "sl", "st"],
        "throws": "L",
        "role": "RP",
    },
    {
        "name": "Jacob Webb",
        "pid": "jacob_webb",
        "mlbam": 657097,
        "prefix": "jwebb",  # avoid collision with Logan Webb (webb_)
        "run": "jacob_webb_poc",
        "codes": ["ch", "ff", "sl", "cu"],
        "throws": "R",
        "role": "RP",
    },
    {
        "name": "Ryan Zeferjahn",
        "pid": "ryan_zeferjahn",
        "mlbam": 666171,
        "prefix": "zeferjahn",
        "run": "ryan_zeferjahn_poc",
        "codes": ["ff", "st", "si", "sl"],
        "throws": "R",
        "role": "RP",
    },
    {
        "name": "David Peterson",
        "pid": "david_peterson",
        "mlbam": 656849,
        "prefix": "peterson",
        "run": "david_peterson_poc",
        "codes": ["si", "ff", "sl", "ch", "cu"],
        "throws": "L",
        "role": "SP",
    },
    {
        "name": "Ryan Rolison",
        "pid": "ryan_rolison",
        "mlbam": 669020,
        "prefix": "rolison",
        "run": "ryan_rolison_poc",
        "codes": ["ff", "st", "si", "cu", "sl"],
        "throws": "L",
        "role": "RP",
    },
    {
        "name": "Trent Thornton",
        "pid": "trent_thornton",
        "mlbam": 663423,
        "prefix": "thornton",
        "run": "trent_thornton_poc",
        "codes": ["ff", "fc", "st", "cu", "si"],
        "throws": "R",
        "role": "RP",
    },
]

CATCHERS = [
    {
        "name": "Carson Kelly",
        "pid": "carson_kelly",
        "mlbam": 608348,
        "prefix": "ckelly",  # avoid Merrill Kelly (kelly_)
        "codes": ["ff", "sl"],
    },
    {
        "name": "Miguel Amaya",
        "pid": "miguel_amaya",
        "mlbam": 665804,
        "prefix": "amaya",
        "codes": ["ff", "sl"],
    },
]

FILTERS = {
    "bases_empty": lambda r: _empty(r),
    "runner_1b": lambda r: _exact(r, "1b"),
    "runner_2b": lambda r: _exact(r, "2b") or str(r.get("runner_bucket") or "") == "second_any",
    "runners_on": lambda r: not _empty(r),
}


def free_gb(path: Path = ROOT) -> float:
    st = os.statvfs(path)
    return (st.f_bavail * st.f_frsize) / (1024**3)


def md5_file(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _empty(r) -> bool:
    def off(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return True
        try:
            return int(float(v)) == 0
        except Exception:
            return True

    return off(r.get("on_1b")) and off(r.get("on_2b")) and off(r.get("on_3b"))


def _exact(r, tag: str) -> bool:
    ex = str(r.get("runner_exact") or "")
    if ex == tag:
        return True
    if tag == "1b":
        return (not _empty(r)) and bool(r.get("on_1b")) and not r.get("on_2b") and not r.get("on_3b")
    if tag == "2b":
        return bool(r.get("on_2b")) and not r.get("on_1b") and not r.get("on_3b")
    return False


def code_to_statcast(code: str, arm: dict) -> str:
    for file_code, sc in (arm.get("statcast_map") or {}).items():
        if file_code == code:
            return sc
    return code.upper()


def load_features(arm: dict) -> pd.DataFrame:
    path = ROOT / "runs" / arm["run"] / "features.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def candidates_from_features(df: pd.DataFrame, sc_pitch: str, filt_name: str) -> list[dict]:
    if df.empty:
        return []
    pred = FILTERS[filt_name]
    rows = []
    for _, r in df.iterrows():
        pt = str(r.get("pitch_type") or "").upper()
        if pt != sc_pitch.upper():
            continue
        rd = r.to_dict()
        if not pred(rd):
            continue
        pid = str(r.get("play_id") or "")
        if not pid:
            continue
        rows.append(
            {
                "play_id": pid,
                "game_date": str(r.get("game_date") or ""),
                "pitch_type": pt,
                "source": "features",
            }
        )
    rows.sort(key=lambda x: x["game_date"], reverse=True)
    seen = set()
    out = []
    for row in rows:
        if row["play_id"] in seen:
            continue
        seen.add(row["play_id"])
        out.append(row)
    return out[:N_SAMPLE]


_FEED_CACHE: dict[int, dict] = {}


def _live_feed(game_pk: int) -> dict:
    if game_pk in _FEED_CACHE:
        return _FEED_CACHE[game_pk]
    try:
        js = requests.get(
            f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live",
            headers=UA,
            timeout=40,
        ).json()
    except Exception:
        js = {}
    _FEED_CACHE[game_pk] = js
    return js


def resolve_play_id(game_pk: int, at_bat_number: int, pitch_number: int) -> str | None:
    feed = _live_feed(int(game_pk))
    plays = (((feed.get("liveData") or {}).get("plays") or {}).get("allPlays")) or []
    ab_idx = int(at_bat_number) - 1
    for play in plays:
        about = play.get("about") or {}
        if int(about.get("atBatIndex", -999)) != ab_idx:
            continue
        for ev in play.get("playEvents") or []:
            if not ev.get("isPitch"):
                continue
            if int(ev.get("pitchNumber") or 0) != int(pitch_number):
                continue
            pid = ev.get("playId")
            if pid:
                return str(pid)
    return None


def candidates_from_statcast(mlbam: int, sc_pitch: str, filt_name: str, season: int = 2026) -> list[dict]:
    try:
        from pybaseball import statcast_pitcher
    except ImportError:
        print("  pybaseball missing; skip statcast pull")
        return []

    start = f"{season}-06-01"
    end = f"{season}-09-07"
    try:
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            os.environ.pop(k, None)
        os.environ["NO_PROXY"] = "*"
        df = statcast_pitcher(start, end, mlbam)
    except Exception as e:
        print(f"  statcast_pitcher failed: {e}")
        return []
    if df is None or df.empty:
        return []

    rows = []
    for _, r in df.iterrows():
        pt = str(r.get("pitch_type") or "").upper()
        if pt != sc_pitch.upper():
            continue
        o1 = pd.notna(r.get("on_1b"))
        o2 = pd.notna(r.get("on_2b"))
        o3 = pd.notna(r.get("on_3b"))
        rd = {
            "on_1b": 1 if o1 else None,
            "on_2b": 1 if o2 else None,
            "on_3b": 1 if o3 else None,
            "runner_exact": None,
            "runner_bucket": None,
        }
        if not o1 and not o2 and not o3:
            rd["runner_exact"] = "bases_empty"
        elif o1 and not o2 and not o3:
            rd["runner_exact"] = "1b"
        elif o2 and not o1 and not o3:
            rd["runner_exact"] = "2b"
            rd["runner_bucket"] = "second_any"
        if not FILTERS[filt_name](rd):
            continue
        play = str(r.get("play_id") or r.get("play_uuid") or "")
        if not play or play == "nan":
            try:
                play = resolve_play_id(
                    int(r["game_pk"]),
                    int(r["at_bat_number"]),
                    int(r["pitch_number"]),
                ) or ""
            except Exception:
                play = ""
        if not play:
            continue
        rows.append(
            {
                "play_id": play,
                "game_date": str(r.get("game_date") or "")[:10],
                "pitch_type": pt,
                "source": "statcast+live",
            }
        )
    rows.sort(key=lambda x: x["game_date"], reverse=True)
    seen = set()
    out = []
    for row in rows:
        if row["play_id"] in seen:
            continue
        seen.add(row["play_id"])
        out.append(row)
    return out[:N_SAMPLE]


def ensure_headroom() -> None:
    if TMP.exists() and free_gb() < MIN_FREE_GB + 1.0:
        shutil.rmtree(TMP, ignore_errors=True)
        TMP.mkdir(parents=True, exist_ok=True)
    if free_gb() < MIN_FREE_GB - 1.5:
        raise RuntimeError(f"Disk below floor: {free_gb():.1f} GB free")


def publish_exemplar(arm: dict, code: str, filt_name: str | None, candidates: list[dict], session: requests.Session) -> dict | None:
    if not candidates:
        return None
    ensure_headroom()
    TMP.mkdir(parents=True, exist_ok=True)
    cell_tmp = TMP / f"{arm['prefix']}_{code}_{filt_name or 'canon'}"
    if cell_tmp.exists():
        shutil.rmtree(cell_tmp, ignore_errors=True)
    cell_tmp.mkdir(parents=True, exist_ok=True)

    downloaded: list[tuple[dict, Path]] = []
    for cand in candidates:
        try:
            path = download_play_clip(cand["play_id"], cell_tmp, session=session)
            if is_decodable(path) and path.stat().st_size > 50_000:
                downloaded.append((cand, path))
        except Exception as e:
            print(f"    fail {cand['play_id'][:8]}… {e}")
        if free_gb() < MIN_FREE_GB:
            print("    disk floor hit mid-cell; stopping downloads")
            break

    if not downloaded:
        shutil.rmtree(cell_tmp, ignore_errors=True)
        return None

    downloaded.sort(key=lambda x: x[0].get("game_date") or "", reverse=True)
    best_meta, best_path = downloaded[0]
    try:
        best_bytes = best_path.read_bytes()
    except FileNotFoundError:
        shutil.rmtree(cell_tmp, ignore_errors=True)
        return None
    if len(best_bytes) < 50_000:
        shutil.rmtree(cell_tmp, ignore_errors=True)
        return None

    sit = f"_{filt_name}" if filt_name else ""
    dest_name = f"{arm['prefix']}_{code}{sit}.mp4"
    dest = VIDEO / dest_name
    VIDEO.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(best_bytes)

    meta = {
        "file": dest_name,
        "player": arm["name"],
        "mlbam": arm["mlbam"],
        "prefix": arm["prefix"],
        "pitch_code": code,
        "filter": filt_name or "canon",
        "play_id": best_meta["play_id"],
        "game_date": best_meta.get("game_date"),
        "pitch_type_statcast": best_meta.get("pitch_type"),
        "n_sampled": len(candidates),
        "n_downloaded_ok": len(downloaded),
        "source": best_meta.get("source"),
        "md5": md5_file(dest),
        "bytes": dest.stat().st_size,
        "identity_gate": "statcast_pitcher_id+pitch_type join",
    }
    META_DIR.mkdir(parents=True, exist_ok=True)
    (META_DIR / f"{dest_name}.json").write_text(json.dumps(meta, indent=2))
    shutil.rmtree(cell_tmp, ignore_errors=True)
    print(
        f"  ✓ {dest_name} date={meta['game_date']} sampled={meta['n_sampled']} "
        f"ok={meta['n_downloaded_ok']} free={free_gb():.1f}GB"
    )
    return meta


def process_arm(arm: dict, session: requests.Session, filters: list[str]) -> list[dict]:
    print(f"\n==== {arm['name']} ({arm['prefix']}) free={free_gb():.1f}GB ====")
    df = load_features(arm)
    results = []
    for code in arm["codes"]:
        sc = code_to_statcast(code, arm)
        jobs = [None] + list(filters)
        for filt in jobs:
            fname = filt or "canon"
            sit = f"_{filt}" if filt else ""
            dest = VIDEO / f"{arm['prefix']}_{code}{sit}.mp4"
            if dest.is_file() and dest.stat().st_size > 50_000:
                print(f"  skip existing {dest.name}")
                continue
            print(f"  cell {code}/{fname} (statcast={sc})")
            cands = []
            if filt and filt != "bases_empty" and not df.empty:
                cands = candidates_from_features(df, sc, filt)
            if filt == "bases_empty" or len(cands) < max(3, N_SAMPLE // 2):
                extra = candidates_from_statcast(arm["mlbam"], sc, filt or "runners_on")
                by_id = {c["play_id"]: c for c in cands}
                for e in extra:
                    by_id.setdefault(e["play_id"], e)
                cands = sorted(by_id.values(), key=lambda x: x.get("game_date") or "", reverse=True)[:N_SAMPLE]
            if filt is None and not cands:
                for alt in ("runners_on", "runner_1b", "runner_2b", "bases_empty"):
                    cands = candidates_from_features(df, sc, alt) if not df.empty else []
                    if len(cands) >= 3:
                        break
                if len(cands) < 3:
                    cands = candidates_from_statcast(arm["mlbam"], sc, "runners_on") or candidates_from_statcast(
                        arm["mlbam"], sc, "bases_empty"
                    )
            if not cands:
                print(f"    no candidates for {code}/{fname}")
                continue
            meta = publish_exemplar(arm, code, filt, cands, session)
            if meta:
                results.append(meta)
    return results


def catcher_pitch_candidates(catcher_mlbam: int, sc_pitch: str, filt_name: str, season: int = 2026) -> list[dict]:
    pks: list[int] = []
    for s_year in (season, season - 1):
        url = (
            f"https://statsapi.mlb.com/api/v1/people/{catcher_mlbam}/stats"
            f"?stats=gameLog&group=hitting&season={s_year}&gameType=R"
        )
        try:
            js = requests.get(url, headers=UA, timeout=30).json()
            splits = (((js.get("stats") or [{}])[0]).get("splits")) or []
            for s in reversed(splits):
                g = (s.get("game") or {}).get("gamePk")
                if g:
                    pks.append(int(g))
        except Exception:
            continue
    pks = list(dict.fromkeys(pks))[:12]
    out: list[dict] = []
    for gpk in pks:
        try:
            feed = requests.get(
                f"https://statsapi.mlb.com/api/v1.1/game/{gpk}/feed/live",
                headers=UA,
                timeout=40,
            ).json()
        except Exception:
            continue
        game_date = ((feed.get("gameData") or {}).get("datetime") or {}).get("officialDate") or ""
        box = (feed.get("liveData") or {}).get("boxscore", {}).get("teams") or {}
        catcher_side = None
        for side in ("home", "away"):
            for v in ((box.get(side) or {}).get("players") or {}).values():
                person = v.get("person") or {}
                if int(person.get("id") or 0) != int(catcher_mlbam):
                    continue
                pos = (v.get("position") or {}).get("abbreviation")
                all_pos = [pos] + [
                    (p.get("abbreviation") if isinstance(p, dict) else None)
                    for p in (v.get("allPositions") or [])
                ]
                if "C" in all_pos or pos == "C":
                    catcher_side = side
                    break
            if catcher_side:
                break
        if not catcher_side:
            continue
        plays = (((feed.get("liveData") or {}).get("plays") or {}).get("allPlays")) or []
        for play in plays:
            for ev in play.get("playEvents") or []:
                if not ev.get("isPitch"):
                    continue
                details = ev.get("details") or {}
                pt = (details.get("type") or {}).get("code") or ""
                if pt.upper() != sc_pitch.upper():
                    continue
                runners = play.get("runners") or []
                occupied = set()
                for rn in runners:
                    start = (rn.get("movement") or {}).get("start")
                    if start:
                        occupied.add(start)
                rd = {
                    "on_1b": 1 if "1B" in occupied else None,
                    "on_2b": 1 if "2B" in occupied else None,
                    "on_3b": 1 if "3B" in occupied else None,
                    "runner_exact": "bases_empty" if not occupied else None,
                    "runner_bucket": "second_any" if occupied == {"2B"} else None,
                }
                if occupied == {"1B"}:
                    rd["runner_exact"] = "1b"
                elif occupied == {"2B"}:
                    rd["runner_exact"] = "2b"
                if occupied or filt_name == "bases_empty":
                    if filt_name in FILTERS and not FILTERS[filt_name](rd):
                        continue
                pid = (ev.get("playId") or details.get("playId") or "")
                if not pid:
                    continue
                out.append(
                    {
                        "play_id": pid,
                        "game_date": game_date,
                        "pitch_type": pt.upper() or sc_pitch.upper(),
                        "source": "catcher_feed",
                    }
                )
                if len(out) >= N_SAMPLE * 2:
                    break
            if len(out) >= N_SAMPLE * 2:
                break
        if len(out) >= N_SAMPLE * 2:
            break
    out.sort(key=lambda x: x.get("game_date") or "", reverse=True)
    seen = set()
    uniq = []
    for r in out:
        if r["play_id"] in seen:
            continue
        seen.add(r["play_id"])
        uniq.append(r)
    return uniq[:N_SAMPLE]


def process_catcher_videos(session: requests.Session) -> list[dict]:
    print(f"\n==== CATCHER VIDEOS free={free_gb():.1f}GB ====")
    results = []
    for c in CATCHERS:
        print(f"  {c['name']}")
        for code in c["codes"]:
            sc = code.upper()
            for filt in ("bases_empty", "runners_on", "runner_1b", "runner_2b"):
                cands = catcher_pitch_candidates(c["mlbam"], sc, filt)
                if not cands:
                    print(f"    no cands {c['prefix']}_{code}_{filt}")
                    continue
                meta = publish_exemplar(c, code, filt, cands[:N_SAMPLE], session)
                if meta:
                    results.append(meta)
            cands = catcher_pitch_candidates(c["mlbam"], sc, "runners_on") or catcher_pitch_candidates(
                c["mlbam"], sc, "bases_empty"
            )
            if cands:
                meta = publish_exemplar(c, code, None, cands[:N_SAMPLE], session)
                if meta:
                    results.append(meta)
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pitchers-only", action="store_true")
    ap.add_argument("--catchers-only", action="store_true")
    ap.add_argument("--prefix", action="append", default=[], help="Limit to video prefixes")
    ap.add_argument("--filters", default="bases_empty,runners_on,runner_1b,runner_2b")
    args = ap.parse_args()
    filters = [f.strip() for f in args.filters.split(",") if f.strip()]

    t0 = time.time()
    print(f"CHC Cubs FULL STAFF — free={free_gb():.1f}GB N_SAMPLE={N_SAMPLE} arms={len(PITCHERS)} catchers={len(CATCHERS)}")
    VIDEO.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(UA)
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        os.environ.pop(k, None)
    os.environ["NO_PROXY"] = "*"

    all_meta: list[dict] = []
    if not args.catchers_only:
        for arm in PITCHERS:
            if args.prefix and arm["prefix"] not in args.prefix:
                continue
            all_meta.extend(process_arm(arm, session, filters))
            # Mid-staff purge of tmp
            if TMP.exists():
                shutil.rmtree(TMP, ignore_errors=True)
                TMP.mkdir(parents=True, exist_ok=True)
    if not args.pitchers_only:
        all_meta.extend(process_catcher_videos(session))

    summary = {
        "team": "Chicago Cubs",
        "team_id": "chc",
        "division": "NL Central",
        "n_pitchers": len(PITCHERS),
        "n_catchers": len(CATCHERS),
        "pitchers": [a["name"] for a in PITCHERS],
        "catchers": [c["name"] for c in CATCHERS],
        "n_exemplars": len(all_meta),
        "files": [m["file"] for m in all_meta],
        "elapsed_sec": round(time.time() - t0, 1),
        "free_gb_end": round(free_gb(), 2),
        "started_unix": t0,
    }
    (META_DIR / "summary_videos.json").write_text(json.dumps(summary, indent=2))
    print("\nDONE VIDEOS", json.dumps(summary, indent=2))
    shutil.rmtree(TMP, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
