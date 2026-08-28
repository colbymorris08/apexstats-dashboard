#!/usr/bin/env python3
"""
Purge tracked clips on a loop while the run is in flight.

scale_nlwest now purges an arm's clips when it finishes, but the scaler running
tonight was started before that existed, and restarting it to pick the change up
would need an interactive approval with the user asleep. This does the same job
from outside the process, so the disk cannot fill again mid-run.

Purges only mp4s whose track already exists, so a pending re-track keeps the
clips it still needs.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cv"))

from preflight.clip_cache import KEEP_PER_ARM, free_bytes, purge_tracked_clips  # noqa: E402
from preflight.readiness import write_index  # noqa: E402

RUNS = ROOT / "runs"
LOG = RUNS / "clip_janitor.log"
POLL = 300
# Tracks are the only permanent cost and they are tiny: Kelly's 2180 tracks are
# 0.16 GB. What needs headroom is the transient clip working set for one arm,
# which the purge keeps to a few GB, so warn near that rather than at a level
# that fires constantly and trains everyone to ignore it.
LOW_WATER_GB = 8.0

# The retention floor has to be bounded globally, not just per arm. Keeping 40
# clips for every arm is 0.22 GB each, which is 138 GB across the 617-arm league
# against 14 GB free — it does not scale and would reproduce the "no space left
# on device" stall with extra steps.
#
# What pixel work actually needs is park diversity, not arm coverage: the
# detector fails across stadiums, not across pitchers. Roughly 30 parks means a
# few dozen arms is sufficient, so retention is granted to the first
# RETAIN_ARMS arms and every other arm is purged completely as before.
RETAIN_ARMS = 30
# Retention is a convenience for labelling; a stalled run is not. Below this the
# floor is abandoned and everything tracked is purged.
RETENTION_FLOOR_GB = 6.0


def main() -> None:
    with LOG.open("a", buffering=1) as log:
        log.write(f"{time.strftime('%H:%M:%S')} clip_janitor start\n")
        while True:
            try:
                total = 0
                freed = 0.0
                arms = sorted(RUNS.glob("*_poc"))
                tight = free_bytes(RUNS) / 1e9 < RETENTION_FLOOR_GB
                for i, d in enumerate(arms):
                    keep = 0 if (tight or i >= RETAIN_ARMS) else KEEP_PER_ARM
                    n, f = purge_tracked_clips(d, keep_per_arm=keep)
                    total += n
                    freed += f
                if tight:
                    log.write(
                        f"{time.strftime('%H:%M:%S')} below {RETENTION_FLOOR_GB} GB: "
                        "clip retention suspended, purging all tracked clips\n"
                    )
                # Refresh readiness here too: the scaler only rewrites it on
                # snapshot, which can be an hour apart, and a consumer needs an
                # arm to flip out of "tracking" promptly once it goes quiet.
                write_index(RUNS)
                free_gb = free_bytes(RUNS) / 1e9
                if total:
                    log.write(
                        f"{time.strftime('%H:%M:%S')} purged {total} clips, "
                        f"freed {freed / 1e9:.2f} GB, {free_gb:.1f} GB free\n"
                    )
                if free_gb < LOW_WATER_GB:
                    log.write(
                        f"{time.strftime('%H:%M:%S')} WARNING low disk: {free_gb:.1f} GB\n"
                    )
            except Exception as exc:
                log.write(f"{time.strftime('%H:%M:%S')} error: {exc}\n")
            time.sleep(POLL)


if __name__ == "__main__":
    main()
