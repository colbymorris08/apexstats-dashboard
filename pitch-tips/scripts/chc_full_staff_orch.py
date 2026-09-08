#!/usr/bin/env python3
"""Timed Chicago Cubs FULL STAFF orchestrator: tips → videos → merge → deploy.

Wall-clock starts at runs/chc_cubs_exemplars/wallclock_start.json (or now).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "runs" / "chc_cubs_exemplars"
LOG = META / "orchestrator.log"

sys.path.insert(0, str(ROOT / "scripts"))
from complete_chc_cubs_team import (  # noqa: E402
    CATCHERS,
    PITCHERS,
    free_gb,
    process_arm,
    process_catcher_videos,
)
import requests

ARMS = [(a["name"], a["run"], a["prefix"], a["mlbam"]) for a in PITCHERS]


def log(msg: str) -> None:
    META.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def _clear_proxy() -> None:
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
        os.environ.pop(k, None)
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"


def start_unix() -> float:
    p = META / "wallclock_start.json"
    if p.exists():
        return float(json.loads(p.read_text())["started_unix"])
    t = time.time()
    p.write_text(json.dumps({"started_unix": t, "team": "Chicago Cubs"}))
    return t


def tip_sample_n() -> int:
    # Speed path: n≈12 is enough for 5 tips; override with CHC_TIP_SAMPLE.
    try:
        return max(8, min(60, int(os.environ.get("CHC_TIP_SAMPLE", "12"))))
    except ValueError:
        return 12


def run_poc(display: str, work: Path, mlbam: int) -> int:
    _clear_proxy()
    report = work / "report.json"
    feats = work / "features.csv"
    sample_n = tip_sample_n()
    if feats.exists() and feats.stat().st_size > 2_000:
        n = sum(1 for _ in feats.open()) - 1
        # Skip re-tracking when we already have enough pitches for tips.
        if n >= max(10, sample_n - 2):
            if report.exists():
                log(f"SKIP tip {display}: features={n} report=yes")
                return 0
            log(f"REMINE tip {display}: features={n} (no report)")
            rc = subprocess.call(
                [
                    sys.executable,
                    "-u",
                    str(ROOT / "cv" / "preflight" / "run_poc.py"),
                    "--pitcher",
                    display,
                    "--season",
                    "2026",
                    "--sample",
                    str(sample_n),
                    "--mlbam",
                    str(mlbam),
                    "--work",
                    str(work),
                    "--remine-only",
                ],
                cwd=str(ROOT),
                env={**os.environ, "NO_PROXY": "*", "no_proxy": "*", "PYTHONUNBUFFERED": "1"},
            )
            clips = work / "clips"
            if clips.exists():
                shutil.rmtree(clips, ignore_errors=True)
            log(f"REMINE DONE {display} rc={rc} free={free_gb():.1f}GB")
            return rc
    log(f"TIP START {display} mlbam={mlbam} sample={sample_n} free={free_gb():.1f}GB")
    t0 = time.time()
    rc = subprocess.call(
        [
            sys.executable,
            "-u",
            str(ROOT / "cv" / "preflight" / "run_poc.py"),
            "--pitcher",
            display,
            "--season",
            "2026",
            "--sample",
            str(sample_n),
            "--mlbam",
            str(mlbam),
            "--work",
            str(work),
        ],
        cwd=str(ROOT),
        env={
            **os.environ,
            "NO_PROXY": "*",
            "no_proxy": "*",
            "HTTP_PROXY": "",
            "HTTPS_PROXY": "",
            "http_proxy": "",
            "https_proxy": "",
            "ALL_PROXY": "",
            "all_proxy": "",
            "PYTHONUNBUFFERED": "1",
            "CHC_TIP_SAMPLE": str(sample_n),
        },
    )
    clips = work / "clips"
    if clips.exists():
        shutil.rmtree(clips, ignore_errors=True)
    log(f"TIP DONE {display} rc={rc} {(time.time()-t0)/60:.1f}min free={free_gb():.1f}GB")
    return rc


def run_catcher(display: str, work: Path, mlbam: int) -> int:
    if (work / "report.json").exists():
        log(f"SKIP catcher tip {display}")
        return 0
    log(f"CATCHER TIP START {display}")
    t0 = time.time()
    sys.path.insert(0, str(ROOT / "cv"))
    from preflight.run_catcher_poc import run_catcher_poc

    try:
        run_catcher_poc(
            catcher_name=display,
            catcher_mlbam=mlbam,
            team="CHC",
            season=2026,
            games=6,
            work=work,
            sample=int(os.environ.get("CHC_CATCHER_SAMPLE", "12")),
        )
        rc = 0
    except Exception as e:
        log(f"CATCHER TIP FAIL {display}: {e}")
        rc = 1
    clips = work / "clips"
    if clips.exists():
        shutil.rmtree(clips, ignore_errors=True)
    log(f"CATCHER TIP DONE {display} rc={rc} {(time.time()-t0)/60:.1f}min")
    return rc


def merge_demo() -> None:
    log("MERGE demo.json")
    subprocess.call([sys.executable, "-u", str(ROOT / "cv" / "preflight" / "merge_demo.py")], cwd=str(ROOT))


def deploy() -> dict:
    """Push origin + force-push preflight main/gh-pages subtree."""
    log("DEPLOY start")
    env = os.environ.copy()
    # commit in apexstats
    subprocess.call(["git", "add", "pitch-tips/"], cwd=str(ROOT.parent))
    msg = "Publish Chicago Cubs full staff tips+videos (timed one-team benchmark)"
    subprocess.call(["git", "commit", "-m", msg], cwd=str(ROOT.parent))
    subprocess.call(["git", "push", "origin", "HEAD"], cwd=str(ROOT.parent))
    # subtree split + force push preflight
    split = subprocess.check_output(
        ["git", "subtree", "split", "--prefix=pitch-tips", "HEAD"],
        cwd=str(ROOT.parent),
        text=True,
    ).strip()
    subprocess.call(
        ["git", "push", "preflight", f"{split}:refs/heads/main", "--force"],
        cwd=str(ROOT.parent),
    )
    subprocess.call(
        ["git", "push", "preflight", f"{split}:refs/heads/gh-pages", "--force"],
        cwd=str(ROOT.parent),
    )
    hashes = {
        "apexstats_HEAD": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT.parent), text=True).strip(),
        "preflight_split": split,
    }
    log(f"DEPLOY done {hashes}")
    return hashes


def main() -> int:
    _clear_proxy()

    t0 = start_unix()
    log(f"ORCH START team=CHC free={free_gb():.1f}GB")
    session = requests.Session()
    session.headers.update({"User-Agent": "PreflightCV/0.7 (+chc-orch)"})
    filters = ["bases_empty", "runners_on", "runner_1b", "runner_2b"]

    video_metas = []
    tip_rcs = []

    # Per-arm: tips then videos (disk-safe)
    for name, run, prefix, mlbam in ARMS:
        work = ROOT / "runs" / run
        tip_rcs.append(run_poc(name, work, mlbam))
        arm = next(a for a in PITCHERS if a["prefix"] == prefix)
        video_metas.extend(process_arm(arm, session, filters))
        tmp = META / "_tmp_clips"
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)

    # Catchers tips + videos
    for c in CATCHERS:
        run_catcher(c["name"], ROOT / "runs" / f"{c['pid']}_catcher_poc", c["mlbam"])
    video_metas.extend(process_catcher_videos(session))

    merge_demo()
    hashes = {}
    try:
        hashes = deploy()
    except Exception as e:
        log(f"DEPLOY error {e}")

    elapsed = time.time() - t0
    # Only stamp a "done" summary when we actually published something
    ok_tips = sum(1 for c in tip_rcs if c == 0)
    if len(video_metas) < 10 and ok_tips < 3:
        log(f"ORCH INCOMPLETE tips_ok={ok_tips} videos={len(video_metas)} — not writing final summary")
        (META / "full_staff_partial.json").write_text(
            json.dumps(
                {
                    "status": "incomplete",
                    "ok_tips": ok_tips,
                    "n_video_exemplars": len(video_metas),
                    "elapsed_sec": round(elapsed, 1),
                    "tip_exit_codes": tip_rcs,
                },
                indent=2,
            )
        )
        return 1

    summary = {
        "team": "Chicago Cubs",
        "division": "NL Central",
        "n_pitchers": len(PITCHERS),
        "n_catchers": len(CATCHERS),
        "pitchers": [a["name"] for a in PITCHERS],
        "catchers": [c["name"] for c in CATCHERS],
        "n_video_exemplars": len(video_metas),
        "video_files": [m["file"] for m in video_metas],
        "elapsed_sec": round(elapsed, 1),
        "elapsed_hm": f"{int(elapsed//3600)}h {int((elapsed%3600)//60)}m",
        "free_gb_end": round(free_gb(), 2),
        "deploy": hashes,
        "tip_exit_codes": tip_rcs,
        "tip_mode": f"sample_{tip_sample_n()}",
    }
    (META / "full_staff_summary.json").write_text(json.dumps(summary, indent=2))
    log(f"ORCH DONE {summary['elapsed_hm']} exemplars={len(video_metas)}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
