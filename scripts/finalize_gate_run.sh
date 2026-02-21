#!/usr/bin/env bash
set -euo pipefail

RUN_DIR=""
REPORT_JSON=""
TAG=""

usage() {
  cat <<USAGE
Usage:
  bash scripts/finalize_gate_run.sh [--tag <decision_tag>] [--run-dir <audit_dir>] [--report-json <path>]

Behavior:
- If --run-dir not set, auto-pick latest audit/workstation_runs entry (or by --tag).
- If --report-json not set, auto-pick latest production_gates_report.json under gate_results.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --tag)
      TAG="$2"; shift 2 ;;
    --run-dir)
      RUN_DIR="$2"; shift 2 ;;
    --report-json)
      REPORT_JSON="$2"; shift 2 ;;
    --help|-h)
      usage; exit 0 ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      exit 1 ;;
  esac
done

if [ -z "$RUN_DIR" ]; then
  if [ -n "$TAG" ]; then
    RUN_DIR="$(ls -td audit/workstation_runs/*${TAG}* 2>/dev/null | head -n1 || true)"
  else
    RUN_DIR="$(ls -td audit/workstation_runs/* 2>/dev/null | head -n1 || true)"
  fi
fi

if [ -z "$RUN_DIR" ] || [ ! -d "$RUN_DIR" ]; then
  echo "run_dir not found" >&2
  exit 1
fi

if [ -z "$REPORT_JSON" ]; then
  REPORT_JSON="$(ls -td gate_results/production_gates_*/production_gates_report.json 2>/dev/null | head -n1 || true)"
fi

if [ -z "$REPORT_JSON" ] || [ ! -f "$REPORT_JSON" ]; then
  echo "report_json not found" >&2
  exit 1
fi

python scripts/finalize_gate_run.py --run-dir "$RUN_DIR" --report-json "$REPORT_JSON"
echo "finalized: run_dir=$RUN_DIR report_json=$REPORT_JSON"
