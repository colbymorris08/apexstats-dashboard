#!/bin/zsh
# Daily 6:00 AM (machine local time - use Mac set to Los Angeles for Pacific) LaunchAgent job:
#   1) Regenerate apex_dashboard_data.json
#   2) Commit + push JSON so the hosted site updates
#
# No email from this job. For JSON + push + PDF email in one shot when you run it yourself,
# use:  zsh apex_daily_manual.sh
#
# Git push uses SSH (origin should be git@github.com:...). ~/.ssh/config should use
# UseKeychain + AddKeysToAgent; run once: ssh-add --apple-use-keychain ~/.ssh/id_ed25519
# Add the matching public key at GitHub - Settings - SSH and GPG keys.
# Optional: export APEX_GIT_SSH_KEY="${HOME}/.ssh/your_key" in your shell or a sourced env file.
#
# Install: pip install -r apex_dashboard_requirements.txt
set -euo pipefail
cd /Users/colbymorris/apexstats
export TZ=America/Los_Angeles
if [[ -x /opt/homebrew/bin/python3 ]]; then
  export PATH="/opt/homebrew/bin:${PATH}"
elif [[ -x /usr/local/bin/python3 ]]; then
  export PATH="/usr/local/bin:${PATH}"
fi
KEY="${APEX_GIT_SSH_KEY:-${HOME}/.ssh/id_ed25519}"
if [[ -f "${KEY}" ]]; then
  export GIT_SSH_COMMAND="ssh -i ${KEY} -o IdentitiesOnly=yes"
else
  unset GIT_SSH_COMMAND 2>/dev/null || true
  echo "Note: no SSH key at ${KEY}; git push uses default SSH (agent/config)." >&2
fi
# Full sync: pro team assignment from game logs (rehab/call-ups) + all client stats.
python3 apex_dashboard_builder.py
(
  git add apex_dashboard_data.json
  if git diff --cached --quiet; then
    :
  else
    git commit -m "Auto-refresh Apex dashboard data (morning)"
  fi
  git pull --rebase --autostash origin main || true
  git push || true
) || echo "Warning: git push failed; site may be stale until the next refresh." >&2
