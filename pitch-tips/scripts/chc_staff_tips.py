#!/usr/bin/env python3
"""Quota-fetch Chicago Cubs full pitching staff + catchers for tip mining.

Runs one arm at a time (CPU-bound pose). Purges tracked clips after each arm.
Records per-arm wall-clock into runs/chc_cubs_exemplars/tip_timing.jsonl.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "runs" / "chc_cubs_exemplars"
TIMING = META / "tip_timing.jsonl"

# Full active staff — same order as complete_chc_cubs_team.PITCHERS
ARMS = [
    ("Shota Imanaga", "shota_imanaga_poc"),
    ("Matthew Boyd", "matthew_boyd_poc"),
    ("Kevin Gausman", "kevin_gausman_poc"),
    ("Colin Rea", "colin_rea_poc"),
    ("Clay Holmes", "clay_holmes_poc"),
    ("Aaron Civale", "aaron_civale_poc"),
    ("Javier Assad", "javier_assad_poc"),
    ("Daniel Palencia", "daniel_palencia_poc"),
    ("Caleb Thielbar", "caleb_thielbar_poc"),
    ("Jacob Webb", "jacob_webb_poc"),
    ("Ryan Zeferjahn", "ryan_zeferjahn_poc"),
    ("David Peterson", "david_peterson_poc"),
    ("Ryan Rolison", "ryan_rolison_poc"),
    ("Trent Thornton", "trent_thornton_poc"),
]

CATCHERS = [
    ("Carson Kelly", "carson_kelly_catcher_poc"),
    ("Miguel Amaya", "miguel_amaya_catcher_poc"),
]

QUIET_SECS = 300


def _busy(work: Path) -> bool:
    newest = 0.0
    for p in list(work.glob("tracks/*_tracks.csv")) + list(work.glob("features*.csv")):
        newest = max(newest, p.stat().st_mtime)
    return newest > 0 and (time.time() - newest) < QUIET_SECS


def _has_tips(work: Path) -> bool:
    report = work / "report.json"
    if not report.exists():
        return False
    try:
        r = json.loads(report.read_text())
        tips = r.get("tips") or r.get("leads") or []
        # also check nested poc tips
        if not tips and isinstance(r.get("poc"), dict):
            tips = r["poc"].get("tips") or []
        # discernable tips live in report via tip_split / leads file
        leads = work / "leads.json"
        if leads.exists():
            lj = json.loads(leads.read_text())
            if isinstance(lj, list) and lj:
                return True
            if isinstance(lj, dict) and (lj.get("tips") or lj.get("leads")):
                return True
        # report with tip_split and holdout means mining ran
        return bool(tips) or bool(r.get("tip_split")) or int(r.get("n_tracked") or 0) >= 40
    except Exception:
        return False


def _purge_clips(work: Path) -> None:
    clips = work / "clips"
    if clips.exists():
        import shutil

        shutil.rmtree(clips, ignore_errors=True)


def _log(row: dict) -> None:
    META.mkdir(parents=True, exist_ok=True)
    with TIMING.open("a") as f:
        f.write(json.dumps(row) + "\n")


def run_pitcher(display: str, slug: str) -> int:
    work = ROOT / "runs" / slug
    if _has_tips(work) and not _busy(work):
        print(f"SKIP {display}: already has tips/report", flush=True)
        _log({"player": display, "slug": slug, "skipped": True, "reason": "has_tips"})
        return 0
    if _busy(work):
        print(f"SKIP {display}: busy within {QUIET_SECS}s", flush=True)
        _log({"player": display, "slug": slug, "skipped": True, "reason": "busy"})
        return 0
    started = time.time()
    print(f"\n===== CHC tip quota: {display} =====", flush=True)
    rc = subprocess.call(
        [
            sys.executable,
            "-u",
            str(ROOT / "cv" / "preflight" / "run_poc.py"),
            "--pitcher",
            display,
            "--season",
            "2026",
            "--quota",
            "--work",
            str(work),
        ],
        cwd=str(ROOT),
    )
    elapsed = (time.time() - started) / 60.0
    print(f"{display}: exit={rc} elapsed={elapsed:.1f} min", flush=True)
    _purge_clips(work)
    _log(
        {
            "player": display,
            "slug": slug,
            "kind": "pitcher",
            "exit": rc,
            "elapsed_min": round(elapsed, 2),
            "unix": started,
        }
    )
    return rc


def run_catcher(display: str, slug: str) -> int:
    work = ROOT / "runs" / slug
    catcher_script = ROOT / "cv" / "preflight" / "run_catcher_poc.py"
    if not catcher_script.exists():
        print(f"NO catcher script for {display}", flush=True)
        return 1
    if (work / "report.json").exists() and not _busy(work):
        print(f"SKIP catcher {display}: report exists", flush=True)
        _log({"player": display, "slug": slug, "skipped": True, "reason": "has_report", "kind": "catcher"})
        return 0
    started = time.time()
    print(f"\n===== CHC catcher: {display} =====", flush=True)
    # Prefer CLI shape used elsewhere; fall back to --catcher if needed
    cmd = [
        sys.executable,
        "-u",
        str(catcher_script),
        "--catcher",
        display,
        "--season",
        "2026",
        "--work",
        str(work),
    ]
    rc = subprocess.call(cmd, cwd=str(ROOT))
    if rc != 0:
        # alternate flag
        cmd2 = [
            sys.executable,
            "-u",
            str(catcher_script),
            "--name",
            display,
            "--season",
            "2026",
            "--work",
            str(work),
        ]
        rc = subprocess.call(cmd2, cwd=str(ROOT))
    elapsed = (time.time() - started) / 60.0
    print(f"{display} catcher: exit={rc} elapsed={elapsed:.1f} min", flush=True)
    _purge_clips(work)
    _log(
        {
            "player": display,
            "slug": slug,
            "kind": "catcher",
            "exit": rc,
            "elapsed_min": round(elapsed, 2),
            "unix": started,
        }
    )
    return rc


def main() -> int:
    META.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    (META / "tips_started.json").write_text(json.dumps({"started_unix": t0}))
    for display, slug in ARMS:
        run_pitcher(display, slug)
    for display, slug in CATCHERS:
        run_catcher(display, slug)
    summary = {
        "team": "Chicago Cubs",
        "elapsed_min": round((time.time() - t0) / 60.0, 2),
        "arms": len(ARMS),
        "catchers": len(CATCHERS),
    }
    (META / "tips_summary.json").write_text(json.dumps(summary, indent=2))
    print("TIPS DONE", summary, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
