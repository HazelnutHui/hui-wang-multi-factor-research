#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR"

PYTHON_BIN=""
if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Neither python3 nor python is available." >&2
  exit 127
fi

OUT_DIR="${1:-segment_results/new_factor_batch1_2026-02-22}"
SEG_YEARS="${SEG_YEARS:-2}"
JOBS="${JOBS:-3}"

echo "[info] out_dir=$OUT_DIR years=$SEG_YEARS jobs=$JOBS"
mkdir -p "$OUT_DIR" "$OUT_DIR/logs"

FACTORS=(turnover_shock vol_regime quality_trend)
if [ "$JOBS" -lt 1 ]; then
  JOBS=1
fi

PIDS=()
for f in "${FACTORS[@]}"; do
  LOG="$OUT_DIR/logs/${f}.log"
  echo "[launch] factor=$f log=$LOG"
  "$PYTHON_BIN" scripts/run_segmented_factors.py \
    --factors "$f" \
    --years "$SEG_YEARS" \
    --out-dir "$OUT_DIR" \
    --set MARKET_CAP_DIR=data/fmp/market_cap_history \
    --set MARKET_CAP_STRICT=True \
    --set REBALANCE_FREQ=5 \
    --set HOLDING_PERIOD=3 \
    --set REBALANCE_MODE=None \
    --set EXECUTION_USE_TRADING_DAYS=True \
    > "$LOG" 2>&1 &
  PIDS+=("$!")
  while [ "$(jobs -r | wc -l | tr -d ' ')" -ge "$JOBS" ]; do
    sleep 1
  done
done

FAIL=0
for p in "${PIDS[@]}"; do
  if ! wait "$p"; then
    FAIL=1
  fi
done

if [ "$FAIL" -ne 0 ]; then
  echo "[fail] one or more factors failed; check $OUT_DIR/logs/*.log" >&2
  exit 1
fi

echo "[done] $OUT_DIR"
