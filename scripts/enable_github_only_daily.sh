#!/bin/zsh
# One daily email at 6 AM Pacific via GitHub Actions; Mac scheduler off.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
zsh "${ROOT}/scripts/disable_mac_morning_agent.sh"
echo "Mac off. Push workflow: zsh ${ROOT}/scripts/fix_git_and_push_automation.sh"
