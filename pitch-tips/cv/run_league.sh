#!/usr/bin/env bash
# Supervisor for the continuous league run.
#
# Executes the priority-ordered plan (NL West rotations + catchers -> remaining
# NL West -> rest of MLB) in a single process, relaunching if it dies. Progress is
# resumable: pitchers with a completed report.json or progress entry are skipped,
# so a restart resumes where it left off rather than redoing work.
#
# One worker only: the box has 8 cores and MediaPipe already saturates them.

set -uo pipefail

CV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$CV_DIR/.." && pwd)"
RUNS="$ROOT/runs"
SEASON="${SEASON:-2026}"
GAMES="${GAMES:-5}"
PLAN="$RUNS/league_plan_${SEASON}.json"
LOG="$RUNS/league_run.log"
MAX_RETRIES="${MAX_RETRIES:-200}"

cd "$CV_DIR"

if [[ ! -f "$PLAN" ]]; then
  echo "[supervisor] building plan…"
  python3 -m preflight.build_plan --season "$SEASON" >>"$LOG" 2>&1
fi

attempt=0
while (( attempt < MAX_RETRIES )); do
  attempt=$((attempt + 1))
  echo "[supervisor] $(date '+%F %T') starting attempt $attempt" >>"$LOG"

  # Catchers are DEFERRED, not cancelled: the catcher_* columns were measuring
  # the pitcher's body on 71-91% of frames (see docs/catcher_subject_bug.md), so
  # tracking them now would produce data needing a full re-track once
  # detector-based catcher localization exists.
  python3 -u -m preflight.scale_nlwest \
    --plan "$PLAN" \
    --season "$SEASON" \
    --games "$GAMES" \
    --skip-catchers \
    --merge-demo >>"$LOG" 2>&1
  code=$?

  if (( code == 0 )); then
    echo "[supervisor] $(date '+%F %T') league complete" >>"$LOG"
    exit 0
  fi

  # 130/143 mean an operator stopped it; don't fight a deliberate shutdown.
  if (( code == 130 || code == 143 )); then
    echo "[supervisor] $(date '+%F %T') interrupted (code $code) — exiting" >>"$LOG"
    exit "$code"
  fi

  echo "[supervisor] $(date '+%F %T') exited $code — resuming in 30s" >>"$LOG"
  sleep 30
done

echo "[supervisor] retry ceiling reached" >>"$LOG"
exit 1
