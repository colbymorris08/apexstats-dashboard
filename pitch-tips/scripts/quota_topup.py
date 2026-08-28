#!/usr/bin/env python3
"""
Top up already-tracked arms to a full set of quota cells, in priority order.

These arms are marked done in progress.json from game-based acquisition, so the
scaler skips them — but "done" there means "tracked six games", which is not the
same as "has testable cells". Woo is the case in point: 196 tracked pitches and
zero testable runner-on-second cells, because game-based sampling gave him the
pitches he throws most rather than the pitches the question needs.

Runs strictly one arm at a time. Tracking is CPU-bound on the pose model and the
machine is already carrying the scaler and the janitor, so a second worker would
slow both rather than add throughput. Already-tracked pitches count towards each
cell's quota, so an arm that is partly covered only fetches the remainder.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Priority order: arms with zero testable cells first, since a cell that cannot
# be tested contributes nothing at all, then arms needing a top-up to five.
ARMS = [
    ("Bryan Woo", "bryan_woo_poc"),
    ("Gabriel Hughes", "gabriel_hughes_poc"),
    ("Griffin Canning", "griffin_canning_poc"),
    ("Landen Roupp", "landen_roupp_poc"),
    ("Merrill Kelly", "merrill_kelly_poc"),
    ("Tomoyuki Sugano", "tomoyuki_sugano_poc"),
]

QUIET_SECS = 300


def _busy(work: Path) -> bool:
    """Is something else writing this run dir? Never track an arm concurrently."""
    newest = 0.0
    for p in list(work.glob("tracks/*_tracks.csv")) + list(work.glob("features*.csv")):
        newest = max(newest, p.stat().st_mtime)
    return newest > 0 and (time.time() - newest) < QUIET_SECS


def main() -> int:
    for display, slug in ARMS:
        work = ROOT / "runs" / slug
        if _busy(work):
            print(f"SKIP {display}: run dir written within {QUIET_SECS}s, leaving it alone", flush=True)
            continue
        print(f"\n===== quota top-up: {display} =====", flush=True)
        rc = subprocess.call(
            [
                sys.executable, "-u", str(ROOT / "cv" / "preflight" / "run_poc.py"),
                "--pitcher", display, "--season", "2026", "--quota",
                "--work", str(work),
            ],
            cwd=str(ROOT),
        )
        # A single arm failing is not a reason to abandon the rest of the list.
        print(f"{display}: exit={rc}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
