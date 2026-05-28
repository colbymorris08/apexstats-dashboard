#!/bin/zsh
# Daily manual cadence (run once when you want): rebuild JSON -> commit/push (site) -> PDF + optional email.
# Same pipeline runs in GitHub Actions at 6 AM Pacific when the Mac is off — see docs/GITHUB_ACTIONS_SETUP.md.
#
# Intended to match this working one-liner (same order, same git pattern, same SSH):
#   cd /Users/colbymorris/apexstats && source ~/.apexstats_morning_email.env 2>/dev/null; \
#     export TZ=America/Los_Angeles GIT_SSH_COMMAND="ssh -i ${HOME}/.ssh/id_ed25519 -o IdentitiesOnly=yes" && \
#     python3 apex_dashboard_builder.py && \
#     git add apex_dashboard_data.json && (git diff --cached --quiet || (git commit -m "Auto-refresh Apex dashboard data" && git pull --rebase origin main)) && git push && \
#     python3 apex_last_night_pdf_email.py
#
# Why a script can "fail" when the one-liner works: with set -e, sourcing the env file
# must not abort the run. Your shell uses ';' after source so exports still run if source
# returns non-zero. This script uses set +e only around source for the same effect.
#
# Email: ~/.apexstats_morning_email.env (chmod 600). If APEX_PDF_EMAIL_TO is unset, PDF only.
# Optional: export APEX_GIT_SSH_KEY="${HOME}/.ssh/other_key" in that file to override id_ed25519.
#
# Email-only (JSON already built; rebuilds PDF from apex_dashboard_data.json + sends mail if TO set):
#   cd /Users/colbymorris/apexstats && source ~/.apexstats_morning_email.env && python3 apex_last_night_pdf_email.py
#
# If SMTP/recipients live in a different path, set this in your shell BEFORE running this script:
#   export APEX_EMAIL_ENV="/path/to/your.env"
# Install: pip install -r apex_dashboard_requirements.txt
set -euo pipefail
EMAIL_ENV="${APEX_EMAIL_ENV:-${HOME}/.apexstats_morning_email.env}"
if [[ -f "${EMAIL_ENV}" ]]; then
  set +e
  # shellcheck source=/dev/null
  source "${EMAIL_ENV}" 2>/dev/null
  set -e
fi
if [[ -f "${EMAIL_ENV}" && -z "${APEX_PDF_EMAIL_TO:-}" ]]; then
  echo "Note: ${EMAIL_ENV} was sourced but APEX_PDF_EMAIL_TO is still empty." >&2
  echo "      Uncomment the export lines (SMTP + APEX_PDF_EMAIL_TO) in that file to enable email." >&2
fi

cd /Users/colbymorris/apexstats
APEX_LOCKDIR="${PWD}/.apex_daily.lockdir"
if ! mkdir "${APEX_LOCKDIR}" 2>/dev/null; then
  echo "Another apex_daily_manual.sh is already running; skipping." >&2
  exit 0
fi
trap 'rmdir "${APEX_LOCKDIR}" 2>/dev/null || true' EXIT INT TERM

export TZ=America/Los_Angeles
# LaunchAgent has a minimal PATH; prefer Homebrew Python 3.11+ (needs datetime.UTC).
if [[ -x /opt/homebrew/bin/python3 ]]; then
  export PATH="/opt/homebrew/bin:${PATH}"
  PYTHON3=/opt/homebrew/bin/python3
elif [[ -x /usr/local/bin/python3 ]]; then
  export PATH="/usr/local/bin:${PATH}"
  PYTHON3=/usr/local/bin/python3
else
  PYTHON3="$(command -v python3)"
fi
export GIT_SSH_COMMAND="ssh -i ${HOME}/.ssh/id_ed25519 -o IdentitiesOnly=yes"
if [[ -n "${APEX_GIT_SSH_KEY:-}" && -f "${APEX_GIT_SSH_KEY}" ]]; then
  export GIT_SSH_COMMAND="ssh -i ${APEX_GIT_SSH_KEY} -o IdentitiesOnly=yes"
fi

# Scheduled runs: skip enriching every arb/FA row (pinned rows still enriched; ~5–15 min vs hours).
export APEX_DAILY_FAST="${APEX_DAILY_FAST:-1}"

# Recover from a stuck rebase or detached HEAD so push does not block email.
git rebase --abort 2>/dev/null || true
if ! git symbolic-ref -q HEAD >/dev/null 2>&1; then
  git checkout -f main 2>/dev/null || git checkout -B main origin/main
fi

builder_ok=0
if perl -e 'alarm shift; exec @ARGV' 3600 "${PYTHON3}" apex_dashboard_builder.py; then
  builder_ok=1
  git add apex_dashboard_data.json
  if git diff --cached --quiet; then
    echo "No JSON changes to commit."
  else
    git commit -m "Auto-refresh Apex dashboard data"
  fi
  if ! git pull --rebase --autostash origin main; then
    echo "Warning: git pull --rebase failed; continuing to PDF/email." >&2
  fi
  if ! git push; then
    echo "Warning: git push failed; continuing to PDF/email." >&2
  fi
else
  echo "Warning: builder timed out or failed after 60m; emailing from existing JSON." >&2
fi

# Exit 2 = PDF OK but SMTP/email failed; do not abort the whole manual run (set -e).
pdf_stat=0
if ! perl -e 'alarm shift; exec @ARGV' 1200 "${PYTHON3}" apex_last_night_pdf_email.py; then
  pdf_stat=$?
fi
if [[ "${pdf_stat:-0}" -eq 2 ]]; then
  echo "Note: PDF was written, but email failed (check ~/.apexstats_morning_email.env SMTP / App Password)." >&2
elif [[ "${pdf_stat:-0}" -ne 0 ]]; then
  exit "${pdf_stat}"
fi
echo "Done: builder + push finished; PDF written (and emailed if APEX_PDF_EMAIL_TO is set)."
