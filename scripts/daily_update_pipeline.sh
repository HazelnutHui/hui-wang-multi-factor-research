#!/usr/bin/env bash
set -euo pipefail

# End-to-end daily pipeline:
# 1) incremental pull
# 2) run current combo strategy
# 3) sync minimal outputs to web side

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DO_PULL="${DO_PULL:-1}"
DO_RUN="${DO_RUN:-1}"
DO_SYNC="${DO_SYNC:-1}"
DRY_RUN="${DRY_RUN:-0}"

echo "[pipeline] root=${ROOT_DIR}"
echo "[pipeline] do_pull=${DO_PULL} do_run=${DO_RUN} do_sync=${DO_SYNC} dry_run=${DRY_RUN}"

if [[ "${DO_PULL}" == "1" ]]; then
  DRY_RUN="${DRY_RUN}" "${ROOT_DIR}/scripts/daily_pull_incremental.sh"
fi

if [[ "${DO_RUN}" == "1" ]]; then
  DRY_RUN="${DRY_RUN}" "${ROOT_DIR}/scripts/daily_run_combo_current.sh"
fi

if [[ "${DO_SYNC}" == "1" ]]; then
  DRY_RUN="${DRY_RUN}" "${ROOT_DIR}/scripts/daily_sync_web.sh"
fi

echo "[pipeline] done."
