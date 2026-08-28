#!/usr/bin/env bash
# Install the launchd user agents that keep the pipeline alive.
#
# Why launchd rather than the existing detached launcher: start_new_session=True
# survives shell teardown, which was the original bug, but it does not restart a
# process that crashes, is OOM-killed, or is lost at logout. The supervisor,
# janitor and heartbeat have each died silently, and a dead heartbeat is worse
# than lost time because downstream artifacts keep showing last-known values as
# current. KeepAlive hands that job to the OS.
#
# Idempotent: safe to re-run after editing a plist.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/scripts/launchd"
DEST="$HOME/Library/LaunchAgents"
mkdir -p "$DEST"

for label in com.apexstats.supervisor com.apexstats.janitor com.apexstats.heartbeat com.apexstats.scheduler com.apexstats.pause com.apexstats.resume; do
  cp "$SRC/$label.plist" "$DEST/$label.plist"
  # bootout is expected to fail when the agent is not loaded yet.
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$DEST/$label.plist"
  echo "loaded $label"
done

echo
launchctl list | grep apexstats || echo "WARNING: no apexstats agents listed"
