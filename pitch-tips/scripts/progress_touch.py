#!/usr/bin/env python3
"""
Keep the supervisor's liveness signal honest.

The watchdog in overnight.sh judges liveness by the mtime of
league_progress_2026.json, but the scaler only snapshots that file between arms.
Measured mid-arm: 73 clips tracked in 420 s while the heartbeat sat unchanged.
An arm at ~5.8 s/clip and ~700 clips runs over an hour, so a 30-minute staleness
threshold would kill a perfectly healthy arm and do it again after every restart.

Raising the threshold past the longest arm would blind the watchdog to real
stalls. Instead this republishes the true work signal into the file the watchdog
already reads: the heartbeat is touched only when a new track file has actually
appeared. Staleness then means "no pitch tracked anywhere in 30 minutes", which
is the condition worth killing for.

Runs detached alongside the supervisor.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
HEARTBEAT = RUNS / "league_progress_2026.json"
LOG = RUNS / "progress_touch.log"
POLL = 60


def newest_track_mtime() -> float:
    newest = 0.0
    for d in RUNS.glob("*_poc/tracks"):
        try:
            for f in d.iterdir():
                if f.name.endswith("_tracks.csv"):
                    m = f.stat().st_mtime
                    if m > newest:
                        newest = m
        except OSError:
            continue
    return newest


def main() -> None:
    seen = 0.0
    with LOG.open("a", buffering=1) as log:
        log.write(f"{time.strftime('%H:%M:%S')} progress_touch start pid={os.getpid()}\n")
        while True:
            try:
                m = newest_track_mtime()
                if m > seen:
                    seen = m
                    if HEARTBEAT.is_file():
                        now = time.time()
                        os.utime(HEARTBEAT, (now, now))
            except Exception as exc:  # never let the keepalive be the thing that dies
                log.write(f"{time.strftime('%H:%M:%S')} error: {exc}\n")
            time.sleep(POLL)


if __name__ == "__main__":
    main()
