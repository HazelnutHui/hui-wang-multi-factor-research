#!/usr/bin/env bash
set -euo pipefail

# Run current combo strategy once and refresh latest signals/run json.
# Default mode is live snapshot (latest-date signals only).
# Optional full mode runs full train/test with run_with_config.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -z "${PY_BIN:-}" ]]; then
  if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
    PY_BIN="${ROOT_DIR}/.venv/bin/python"
  elif [[ -x "/Users/hui/miniconda3/bin/python3" ]]; then
    PY_BIN="/Users/hui/miniconda3/bin/python3"
  else
    PY_BIN="python3"
  fi
fi
STRATEGY_CFG="${STRATEGY_CFG:-${ROOT_DIR}/configs/strategies/combo_v2_live_daily.yaml}"
COST_MULTIPLIER="${COST_MULTIPLIER:-1.0}"
DRY_RUN="${DRY_RUN:-0}"
RUN_MODE="${RUN_MODE:-live_snapshot}" # live_snapshot | full_backtest

if [[ ! -f "${STRATEGY_CFG}" ]]; then
  echo "ERROR: strategy config not found: ${STRATEGY_CFG}" >&2
  exit 1
fi

run_cmd() {
  echo "+ $*"
  if [[ "${DRY_RUN}" == "1" ]]; then
    return 0
  fi
  "$@"
}

echo "[run] root=${ROOT_DIR}"
echo "[run] strategy=${STRATEGY_CFG}"
echo "[run] cost_multiplier=${COST_MULTIPLIER}"
echo "[run] mode=${RUN_MODE}"
echo "[run] dry_run=${DRY_RUN}"

if [[ "${RUN_MODE}" == "full_backtest" ]]; then
  run_cmd "${PY_BIN}" "${ROOT_DIR}/scripts/run_with_config.py" \
    --strategy "${STRATEGY_CFG}" \
    --cost-multiplier "${COST_MULTIPLIER}"
else
  run_cmd "${PY_BIN}" "${ROOT_DIR}/scripts/run_live_signal_snapshot.py" \
    --strategy "${STRATEGY_CFG}"
fi

echo "[run] done."
