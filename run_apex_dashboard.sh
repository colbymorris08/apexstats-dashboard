#!/bin/zsh
set -e
cd /Users/colbymorris/apexstats
python3 -m pip install -r apex_dashboard_requirements.txt
python3 apex_dashboard_api.py
