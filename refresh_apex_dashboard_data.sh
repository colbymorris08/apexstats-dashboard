#!/bin/zsh
set -e
cd /Users/colbymorris/apexstats
python3 apex_dashboard_builder.py
git add apex_dashboard_data.json
git diff --cached --quiet || git commit -m "Auto-refresh Apex dashboard data"
git push
