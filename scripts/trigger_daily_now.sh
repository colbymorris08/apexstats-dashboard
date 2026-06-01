#!/bin/zsh
# Trigger today's Apex daily on GitHub (use when the 6 AM schedule was skipped).
set -euo pipefail
gh workflow run "Apex daily" --repo colbymorris08/apexstats-dashboard
echo "Started. Watch: https://github.com/colbymorris08/apexstats-dashboard/actions/workflows/apex_daily.yml"
