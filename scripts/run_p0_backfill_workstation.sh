#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p logs
TS="$(date +%Y%m%d_%H%M%S)"
LOG="logs/p0_backfill_${TS}.log"
PID_FILE="logs/p0_backfill.pid"

if [[ -f "$PID_FILE" ]]; then
  OLD_PID="$(cat "$PID_FILE" || true)"
  if [[ -n "${OLD_PID}" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "P0 backfill already running, pid=${OLD_PID}" >&2
    exit 1
  fi
fi

CMD="python3 scripts/fmp_p0_backfill.py --workers 8"

echo "[run] ${CMD}" | tee -a "$LOG"
nohup bash -lc "$CMD" >> "$LOG" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"

echo "started pid=${NEW_PID} log=${LOG}"
echo "tail -f ${LOG}"
echo "python3 scripts/audit_fmp_p0_readiness.py"
