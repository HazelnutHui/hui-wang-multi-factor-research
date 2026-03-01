#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PID_FILE="logs/p0_backfill.pid"
if [[ -f "$PID_FILE" ]]; then
  PID="$(cat "$PID_FILE" || true)"
  if [[ -n "${PID}" ]] && kill -0 "$PID" 2>/dev/null; then
    echo "running pid=${PID}"
  else
    echo "not running (stale pid file: ${PID})"
  fi
else
  echo "not running (no pid file)"
fi

LATEST_LOG="$(ls -1t logs/p0_backfill_*.log 2>/dev/null | head -n 1 || true)"
if [[ -n "$LATEST_LOG" ]]; then
  echo "latest_log=${LATEST_LOG}"
  tail -n 40 "$LATEST_LOG"
else
  echo "no p0_backfill log found"
fi
