#!/usr/bin/env python3
"""
Quota-fetch the Dodgers pitching staff, rotation first.

Yamamoto is completed end to end separately and first, so the user sees one arm
land before the roster is committed to. He was chosen on pitch-type balance
rather than type count: 6 types with a top five of 192/186/138/90/72 pitches.
Balance is what produces contrasts — Ohtani carries 7 types but falls from 215 to
56 after two, so most of his pairings are too thin to test.

Catchers are excluded; catcher tracking is blocked on detector generalisation.

One arm at a time. Tracking is CPU-bound on the pose model and the machine is
already carrying the scaler and the janitor, so a second worker trades
throughput for contention.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Rotation first, then relievers. Volume within the 45-day window, measured from
# the game feed, is in the comment beside each arm.
# (Note: Michael King is SD, Jonathan Loáisiga & Dennis Santana are ARI; they are
# tracked in their respective team sequences).
ARMS = [
    ("Yoshinobu Yamamoto", "yoshinobu_yamamoto_poc"),   # 712 recent, 6 types (Done)
    ("Tarik Skubal", "tarik_skubal_poc"),               # 758 recent, 5 types (Done)
    ("Jack Dreyer", "jack_dreyer_poc"),                 # (Done)
    ("Shohei Ohtani", "shohei_ohtani_poc"),             # 668 recent, 7 types (skewed)
    ("Roki Sasaki", "roki_sasaki_poc"),                 # 630 recent, 4 types
    ("Eric Lauer", "eric_lauer_poc"),                   # 523 recent, 5 types
    ("Tyler Glasnow", "tyler_glasnow_poc"),             # 89 recent — likely IL, expect thin cells
    ("Justin Wrobleski", "justin_wrobleski_poc"),
    ("Emmet Sheehan", "emmet_sheehan_poc"),
    ("Kris Bubic", "kris_bubic_poc"),
    ("Blake Snell", "blake_snell_poc"),
    ("Will Klein", "will_klein_poc"),
    ("Alex Vesia", "alex_vesia_poc"),
    ("Tanner Scott", "tanner_scott_poc"),
]

QUIET_SECS = 300


def _busy(work: Path) -> bool:
    newest = 0.0
    for p in list(work.glob("tracks/*_tracks.csv")) + list(work.glob("features*.csv")):
        newest = max(newest, p.stat().st_mtime)
    return newest > 0 and (time.time() - newest) < QUIET_SECS


def main() -> int:
    for display, slug in ARMS:
        work = ROOT / "runs" / slug
        if _busy(work):
            print(f"SKIP {display}: written within {QUIET_SECS}s, another process owns it", flush=True)
            continue
        started = time.time()
        print(f"\n===== LAD quota: {display} =====", flush=True)
        rc = subprocess.call(
            [
                sys.executable, "-u", str(ROOT / "cv" / "preflight" / "run_poc.py"),
                "--pitcher", display, "--season", "2026", "--quota",
                "--work", str(work),
            ],
            cwd=str(ROOT),
        )
        # Elapsed per arm is the number the Savant-path decision rests on.
        print(f"{display}: exit={rc} elapsed={(time.time() - started) / 60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
