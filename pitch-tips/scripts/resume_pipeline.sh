#!/usr/bin/env bash
# Seamlessly resume the supervisor and pipeline via launchd.
set -u

ROOT="/Users/colbymorris/apexstats/pitch-tips"
DEST="$HOME/Library/LaunchAgents"
LOG="$ROOT/runs/pause_resume.log"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') [RESUME] $*" | tee -a "$LOG"
}

log "Initiating pipeline resume at 8:15 PM PDT..."

UID_NUM="$(id -u)"
PLIST="$DEST/com.apexstats.supervisor.plist"

if [ ! -f "$PLIST" ]; then
  log "Copying supervisor plist to $PLIST..."
  cp "$ROOT/scripts/launchd/com.apexstats.supervisor.plist" "$PLIST"
fi

# Ensure previous instance unloaded cleanly
launchctl bootout "gui/${UID_NUM}/com.apexstats.supervisor" 2>/dev/null || true
sleep 1

# Bootstrap launchd supervisor
log "Bootstrapping launchd agent com.apexstats.supervisor..."
launchctl bootstrap "gui/${UID_NUM}" "$PLIST"

sleep 3

# Verify supervisor is loaded and running
if launchctl list | grep -q "com.apexstats.supervisor"; then
  log "com.apexstats.supervisor is active and running under launchd."
else
  log "ERROR: com.apexstats.supervisor failed to start!"
fi

log "Resume sequence completed."
