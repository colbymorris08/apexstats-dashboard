#!/bin/zsh
# Unstick rebase conflicts on auto-generated JSON and push workflow-only changes.
set -euo pipefail
cd /Users/colbymorris/apexstats

git rebase --abort 2>/dev/null || true
git merge --abort 2>/dev/null || true

TMP="$(mktemp -d)"
mkdir -p scripts
cp .github/workflows/apex_daily.yml "${TMP}/apex_daily.yml"
cp apex_last_night_pdf_email.py "${TMP}/apex_last_night_pdf_email.py"
cp apex_daily_manual.sh "${TMP}/apex_daily_manual.sh"
cp com.colbymorris.apexdashboard.morning.plist "${TMP}/morning.plist"
[[ -f scripts/enable_github_only_daily.sh ]] && \
  cp scripts/enable_github_only_daily.sh "${TMP}/enable_github_only_daily.sh"
cp scripts/fix_git_and_push_automation.sh "${TMP}/fix_git_and_push_automation.sh"

git fetch origin main
git reset --hard origin/main

mkdir -p scripts
cp "${TMP}/apex_daily.yml" .github/workflows/apex_daily.yml
cp "${TMP}/apex_last_night_pdf_email.py" apex_last_night_pdf_email.py
cp "${TMP}/apex_daily_manual.sh" apex_daily_manual.sh
cp "${TMP}/morning.plist" com.colbymorris.apexdashboard.morning.plist
[[ -f "${TMP}/enable_github_only_daily.sh" ]] && \
  cp "${TMP}/enable_github_only_daily.sh" scripts/enable_github_only_daily.sh
cp "${TMP}/fix_git_and_push_automation.sh" scripts/fix_git_and_push_automation.sh
rm -rf "${TMP}"

# Recreate helper if missing after reset
if [[ ! -f scripts/enable_github_only_daily.sh ]]; then
  cat > scripts/enable_github_only_daily.sh <<'EOF'
#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
zsh "${ROOT}/scripts/disable_mac_morning_agent.sh"
EOF
  chmod +x scripts/enable_github_only_daily.sh
fi

git checkout origin/main -- apex_dashboard_data.json

TO_ADD=(
  .github/workflows/apex_daily.yml
  apex_last_night_pdf_email.py
  apex_daily_manual.sh
  com.colbymorris.apexdashboard.morning.plist
  scripts/fix_git_and_push_automation.sh
  scripts/enable_github_only_daily.sh
  scripts/disable_mac_morning_agent.sh
)
for f in "${TO_ADD[@]}"; do
  [[ -f "$f" ]] && git add "$f"
done

if git diff --cached --quiet; then
  echo "Nothing new to push (automation may already be on origin/main)."
else
  git commit -m "One daily email at 6 AM PT via GitHub Actions only"
  git push origin main
  echo "Pushed to origin/main."
fi

echo ""
head -12 .github/workflows/apex_daily.yml
echo ""
echo "Verify: https://github.com/colbymorris08/apexstats-dashboard/blob/main/.github/workflows/apex_daily.yml"
