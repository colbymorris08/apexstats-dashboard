#!/usr/bin/env bash
# Gracefully pause the supervisor and active scaler / workers.
set -u

ROOT="/Users/colbymorris/apexstats/pitch-tips"
LOG="$ROOT/runs/pause_resume.log"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') [PAUSE] $*" | tee -a "$LOG"
}

log "Initiating pipeline pause at 6:00 PM PDT..."

# 1. Unload the launchd supervisor agent so it doesn't immediately restart the scaler.
UID_NUM="$(id -u)"
if launchctl list | grep -q "com.apexstats.supervisor"; then
  log "Unloading launchd agent com.apexstats.supervisor..."
  launchctl bootout "gui/${UID_NUM}/com.apexstats.supervisor" 2>/dev/null || true
  sleep 2
else
  log "launchd agent com.apexstats.supervisor was not loaded."
fi

# 2. Check for any remaining overnight.sh or scale_nlwest processes and send SIGTERM for clean shutdown.
# SIGTERM allows python and subprocesses to finish their current in-memory operations and exit cleanly without corrupting files.
PIDS=$(pgrep -f "preflight\.scale_nlwest|scripts/overnight\.sh" || true)
if [ -n "$PIDS" ]; then
  log "Sending SIGTERM to active scaler/supervisor processes: $PIDS"
  kill -TERM $PIDS 2>/dev/null || true
  
  # Give up to 15 seconds for clean exit
  for i in $(seq 1 15); do
    REMAINING=$(pgrep -f "preflight\.scale_nlwest|scripts/overnight\.sh" || true)
    if [ -z "$REMAINING" ]; then
      log "All scaler/supervisor processes exited cleanly."
      break
    fi
    sleep 1
  done
else
  log "No active scaler/supervisor processes found."
fi

# 3. Final verification
STILL_RUNNING=$(pgrep -f "preflight\.scale_nlwest|scripts/overnight\.sh" || true)
if [ -n "$STILL_RUNNING" ]; then
  log "WARNING: Processes still alive: $STILL_RUNNING. Sending SIGTERM again."
  kill -TERM $STILL_RUNNING 2>/dev/null || true
else
  log "Pipeline is fully paused and clean."
fi
