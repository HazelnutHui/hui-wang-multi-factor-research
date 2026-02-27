#!/usr/bin/env bash
set -euo pipefail

# Sync minimal daily outputs to Hui web server side.
# Delegates to Hui project's sync script.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HUI_ROOT="${HUI_ROOT:-/Users/hui/Hui}"
DRY_RUN="${DRY_RUN:-0}"

SYNC_SCRIPT="${HUI_ROOT}/scripts/sync_daily_min.sh"
if [[ ! -x "${SYNC_SCRIPT}" ]]; then
  echo "ERROR: sync script not found or not executable: ${SYNC_SCRIPT}" >&2
  echo "Hint: ensure Hui repo exists locally and scripts/sync_daily_min.sh is present." >&2
  exit 1
fi

echo "[sync] using ${SYNC_SCRIPT}"
echo "[sync] dry_run=${DRY_RUN}"

# Pass-through envs for remote target and key.
export LOCAL_QUANT_ROOT="${LOCAL_QUANT_ROOT:-${ROOT_DIR}}"
export REMOTE_USER="${REMOTE_USER:-ubuntu}"
export REMOTE_HOST="${REMOTE_HOST:-132.226.88.196}"
export REMOTE_QUANT_ROOT="${REMOTE_QUANT_ROOT:-/home/ubuntu/Hui/data/quant_score/v4}"
export SSH_KEY="${SSH_KEY:-}"
export RUNS_TO_PUSH="${RUNS_TO_PUSH:-3}"
export DRY_RUN

"${SYNC_SCRIPT}"

echo "[sync] done."
