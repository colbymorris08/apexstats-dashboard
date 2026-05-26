#!/bin/zsh
set -e
cd /Users/colbymorris/apexstats
# Pro team + stats from game logs (rehab/call-ups); lighter than a full amateur/HS rebuild.
python3 apex_dashboard_builder.py --pro-teams-only
git add apex_dashboard_data.json
if git diff --cached --quiet; then
  echo "No JSON changes to commit."
else
  git commit -m "Auto-refresh Apex dashboard data"
fi
git pull --rebase --autostash origin main || true
git push || true
