#!/bin/zsh
# Stop the Mac LaunchAgent so only GitHub Actions sends the 6 AM daily email.
set -euo pipefail
LABEL="com.colbymorris.apexdashboard.morning"
PLIST="${HOME}/Library/LaunchAgents/${LABEL}.plist"
UID="$(id -u)"
launchctl bootout "gui/${UID}/${LABEL}" 2>/dev/null || true
launchctl bootout "gui/${UID}" "${PLIST}" 2>/dev/null || true
if [[ -f "${PLIST}" ]]; then
  rm -f "${PLIST}"
  echo "Removed ${PLIST}"
fi
echo "Mac morning agent disabled. Daily email: GitHub Actions at 6:00 AM Pacific only."
