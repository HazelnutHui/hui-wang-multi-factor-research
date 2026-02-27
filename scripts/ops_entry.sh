#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

REMOTE_STATUS_HOST_DEFAULT="hui@100.66.103.44"
REMOTE_STATUS_ROOT_DEFAULT="~/projects/hui-wang-multi-factor-research"
REMOTE_STATUS_TIMEOUT_SEC_DEFAULT="5"

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

usage() {
  cat <<'USAGE'
Unified ops entrypoint (primary):
  bash scripts/ops_entry.sh <subcommand> [args]

Subcommands:
  daily [--execute]
      Run daily research track pipeline.
      --execute: execute ranked command after dry-run validation.

  fast [fast_research_run args...]
      Run speed-first research screen with isolated outputs.
      This path is non-official and does not write official workstation audit artifacts.

  factory [run_factor_factory_batch args...]
      Run factor-factory batch (build candidates, execute, rank).
      Uses policy config and isolated segment_results/audit outputs.

  factory_queue [run_factor_factory_queue args...]
      Run queued factor-factory policies sequentially (e.g., 5x20 = 100 candidates).
      Approval gate is mandatory:
        configs/research/factory_queue/run_approval.json

  status
      Refresh concise daily brief only (fast status check).

  official [workstation_official_run args...]
      Pass-through to workstation official wrapper.
      Example:
        bash scripts/ops_entry.sh official \
          --workflow production_gates \
          --tag committee_YYYY-MM-DD_runN \
          --owner hui \
          --notes "official workstation gate run" \
          --threads 8 \
          --dq-input-csv data/research_inputs/combo_v2_dq_input_latest.csv \
          -- \
          --strategy configs/strategies/combo_v2_prod.yaml \
          --factor combo_v2 \
          --cost-multipliers 1.5,2.0 \
          --wf-shards 4 \
          --freeze-file runs/freeze/combo_v2_prod.freeze.json \
          --out-dir gate_results

  check
      Run command-surface drift check for docs.

  cleanup [--apply]
      Safe artifact cleanup (default dry-run preview).
      --apply: actually delete approved non-critical artifacts.

  hygiene
      Run check + cleanup preview in sequence.

Environment overrides (optional):
  REMOTE_STATUS_HOST
  REMOTE_STATUS_ROOT
  REMOTE_STATUS_TIMEOUT_SEC
USAGE
}

if [ "$#" -lt 1 ]; then
  usage
  exit 1
fi

SUB="$1"
shift

case "$SUB" in
  daily)
    EXECUTE_VAL="0"
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --execute)
          EXECUTE_VAL="1"
          shift
          ;;
        --help|-h)
          usage
          exit 0
          ;;
        *)
          echo "Unknown arg for daily: $1" >&2
          usage
          exit 1
          ;;
      esac
    done
    OPS_ENTRY_CALLER="1" \
    EXECUTE="$EXECUTE_VAL" \
    REMOTE_STATUS_HOST="${REMOTE_STATUS_HOST:-$REMOTE_STATUS_HOST_DEFAULT}" \
    REMOTE_STATUS_ROOT="${REMOTE_STATUS_ROOT:-$REMOTE_STATUS_ROOT_DEFAULT}" \
    REMOTE_STATUS_TIMEOUT_SEC="${REMOTE_STATUS_TIMEOUT_SEC:-$REMOTE_STATUS_TIMEOUT_SEC_DEFAULT}" \
      bash scripts/daily_research_run.sh
    ;;
  status)
    if [ "$#" -gt 0 ]; then
      echo "status takes no args" >&2
      usage
      exit 1
    fi
    "$PYTHON_BIN" scripts/generate_daily_research_brief.py \
      --remote-host "${REMOTE_STATUS_HOST:-$REMOTE_STATUS_HOST_DEFAULT}" \
      --remote-root "${REMOTE_STATUS_ROOT:-$REMOTE_STATUS_ROOT_DEFAULT}" \
      --remote-timeout-sec "${REMOTE_STATUS_TIMEOUT_SEC:-$REMOTE_STATUS_TIMEOUT_SEC_DEFAULT}"
    echo "[done] audit/daily/daily_research_brief_latest.md"
    ;;
  fast)
    OPS_ENTRY_CALLER="1" bash scripts/fast_research_run.sh "$@"
    ;;
  factory)
    "$PYTHON_BIN" scripts/run_factor_factory_batch.py "$@"
    ;;
  factory_queue)
    "$PYTHON_BIN" scripts/run_factor_factory_queue.py "$@"
    ;;
  official)
    OPS_ENTRY_CALLER="1" bash scripts/workstation_official_run.sh "$@"
    ;;
  check)
    if [ "$#" -gt 0 ]; then
      echo "check takes no args" >&2
      usage
      exit 1
    fi
    "$PYTHON_BIN" scripts/check_command_surface.py
    ;;
  cleanup)
    APPLY_FLAG=""
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --apply)
          APPLY_FLAG="--apply"
          shift
          ;;
        --help|-h)
          usage
          exit 0
          ;;
        *)
          echo "Unknown arg for cleanup: $1" >&2
          usage
          exit 1
          ;;
      esac
    done
    "$PYTHON_BIN" scripts/safe_artifact_cleanup.py $APPLY_FLAG
    ;;
  hygiene)
    if [ "$#" -gt 0 ]; then
      echo "hygiene takes no args" >&2
      usage
      exit 1
    fi
    "$PYTHON_BIN" scripts/check_command_surface.py
    "$PYTHON_BIN" scripts/check_script_surface.py
    "$PYTHON_BIN" scripts/safe_artifact_cleanup.py
    ;;
  --help|-h|help)
    usage
    ;;
  *)
    echo "Unknown subcommand: $SUB" >&2
    usage
    exit 1
    ;;
esac
