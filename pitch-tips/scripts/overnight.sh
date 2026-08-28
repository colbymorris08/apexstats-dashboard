#!/bin/bash
# Overnight NL West depth run, supervised.
#
# Two failure modes have to be covered, and the first version only covered one:
#
#   1. The scaler exits (crash, unhandled arm failure). The loop restarts it.
#   2. The scaler is alive but wedged — a stalled download, a hung decode. An
#      exit-only supervisor waits forever on this, which looks supervised while
#      nothing progresses.
#
# The watchdog covers (2) by tracking the heartbeat in league_progress_2026.json.
# If the heartbeat stops advancing, it kills the scaler so the loop can restart
# it. The scaler is resumable, so a restart re-enters where it left off.
set -u

ROOT="/Users/colbymorris/apexstats/pitch-tips"
cd "$ROOT/cv" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export PYTHONPATH="$ROOT/cv"
export MPLCONFIGDIR=/tmp/mpl

LOG="$ROOT/runs/league_run_retrack.log"
SUP="$ROOT/runs/overnight_supervisor.log"
HEARTBEAT="$ROOT/runs/league_progress_2026.json"
STALL_SECS=1800   # 30 min with no heartbeat means wedged, not merely slow

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$SUP"; }

for attempt in $(seq 1 500); do
  log "=== scaler start #$attempt ==="

  /opt/homebrew/bin/python3 -u -m preflight.scale_nlwest \
    --season 2026 \
    --quota \
    --min-pitches 100 \
    --skip-catchers \
    --merge-demo \
    --plan "$ROOT/runs/league_plan_2026.json" >> "$LOG" 2>&1 &
  scaler=$!
  log "scaler pid=$scaler"

  # Watchdog: runs alongside this attempt only, exits when the scaler does.
  (
    while kill -0 "$scaler" 2>/dev/null; do
      sleep 120
      # Liveness is the newest track file anywhere, not the heartbeat snapshot:
      # the scaler only snapshots between arms, so a long arm looks idle for an
      # hour while it is in fact tracking a pitch every few seconds.
      if [ -f "$HEARTBEAT" ]; then
        now=$(date +%s)
        touched=$(find "$ROOT/runs" -name '*_tracks.csv' -newermt '-40 minutes' -print -quit 2>/dev/null)
        if [ -n "$touched" ]; then
          idle=0
        else
          hb=$(stat -f %m "$HEARTBEAT" 2>/dev/null || echo "$now")
          idle=$(( now - hb ))
        fi
        if [ "$idle" -gt "$STALL_SECS" ]; then
          log "WATCHDOG: heartbeat idle ${idle}s > ${STALL_SECS}s — killing pid $scaler"
          kill -9 "$scaler" 2>/dev/null
          break
        fi
      fi
    done
  ) &
  watchdog=$!

  wait "$scaler"
  code=$?
  kill "$watchdog" 2>/dev/null
  log "scaler exit=$code"

  if [ "$code" -eq 0 ]; then
    log "=== queue exhausted cleanly; supervisor stopping ==="
    break
  fi
  sleep 20
done
