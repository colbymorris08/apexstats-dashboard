#!/bin/zsh
# Push SMTP settings from ~/.apexstats_morning_email.env to GitHub Actions repository secrets.
set -euo pipefail
ENV_FILE="${APEX_EMAIL_ENV:-${HOME}/.apexstats_morning_email.env}"
REPO="${APEX_GITHUB_REPO:-colbymorris08/apexstats-dashboard}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}" >&2
  exit 1
fi
set +e
# shellcheck source=/dev/null
source "${ENV_FILE}" 2>/dev/null
set -e

for var in APEX_SMTP_HOST APEX_SMTP_PORT APEX_SMTP_USER APEX_SMTP_PASSWORD APEX_PDF_EMAIL_FROM APEX_PDF_EMAIL_TO; do
  val="${(P)var}"
  if [[ -z "${val}" ]]; then
    echo "Unset in ${ENV_FILE}: ${var}" >&2
    exit 1
  fi
  echo "Setting ${var} on ${REPO}..."
  printf '%s' "${val}" | gh secret set "${var}" --repo "${REPO}"
done

if [[ -n "${APEX_SMTP_USE_SSL:-}" ]]; then
  printf '%s' "${APEX_SMTP_USE_SSL}" | gh secret set APEX_SMTP_USE_SSL --repo "${REPO}"
fi

echo "Done. Run: gh workflow run Apex daily --repo ${REPO}"
