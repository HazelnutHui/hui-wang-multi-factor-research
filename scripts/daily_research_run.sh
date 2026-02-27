#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR"

if [[ "${OPS_ENTRY_CALLER:-0}" != "1" ]]; then
  echo "[note] direct script is compatibility path; preferred: bash scripts/ops_entry.sh daily"
fi

DQ_OUT_DIR="${DQ_OUT_DIR:-gate_results/data_quality_auto_daily}"
DQ_INPUT_CSV="${DQ_INPUT_CSV:-data/research_inputs/combo_v2_dq_input_latest.csv}"
PLAN_JSON="${PLAN_JSON:-audit/factor_registry/next_run_plan.json}"
PLAN_FIXED_JSON="${PLAN_FIXED_JSON:-audit/factor_registry/next_run_plan_fixed.json}"
PLAN_FIXED_MD="${PLAN_FIXED_MD:-audit/factor_registry/next_run_plan_fixed.md}"
RANK="${RANK:-1}"
EXECUTE="${EXECUTE:-0}"
REMOTE_STATUS_HOST="${REMOTE_STATUS_HOST:-hui@100.66.103.44}"
REMOTE_STATUS_ROOT="${REMOTE_STATUS_ROOT:-~/projects/hui-wang-multi-factor-research}"
REMOTE_STATUS_TIMEOUT_SEC="${REMOTE_STATUS_TIMEOUT_SEC:-5}"

echo "[step] prepare canonical dq input"
python scripts/prepare_dq_input.py --out-csv "$DQ_INPUT_CSV"

echo "[step] run dq gate"
python scripts/data_quality_gate.py \
  --input-csv "$DQ_INPUT_CSV" \
  --required-columns date,ticker,score \
  --numeric-columns score \
  --key-columns date,ticker \
  --date-column date \
  --max-staleness-days 7 \
  --out-dir "$DQ_OUT_DIR"

echo "[step] refresh candidate queue"
python scripts/generate_candidate_queue.py

echo "[step] generate next-run plan"
python scripts/generate_next_run_plan.py --dq-input-csv "$DQ_INPUT_CSV"

echo "[step] repair next-run plan paths"
python scripts/repair_next_run_plan_paths.py \
  --plan-json "$PLAN_JSON" \
  --out-json "$PLAN_FIXED_JSON" \
  --out-md "$PLAN_FIXED_MD" \
  --dq-input-csv "$DQ_INPUT_CSV"

echo "[step] validate ranked command (dry-run)"
python scripts/execute_next_run_plan.py --plan-json "$PLAN_FIXED_JSON" --rank "$RANK" --dry-run

echo "[step] command-surface drift check (non-blocking)"
if python scripts/check_command_surface.py; then
  echo "[done] command surface check pass"
else
  echo "[warn] command surface drift detected (non-blocking); see audit/command_surface/command_surface_check_latest.md"
fi

echo "[step] script-surface check (non-blocking)"
if python scripts/check_script_surface.py; then
  echo "[done] script surface check pass"
else
  echo "[warn] script surface check reported issues (non-blocking); see audit/script_surface/script_surface_check.md"
fi

echo "[step] safe cleanup preview (non-blocking)"
if python scripts/safe_artifact_cleanup.py; then
  echo "[done] cleanup preview pass"
else
  echo "[warn] cleanup preview reported issues (non-blocking); see audit/cleanup/cleanup_report_latest.md"
fi

if [[ "$EXECUTE" == "1" ]]; then
  echo "[step] execute ranked command"
  python scripts/execute_next_run_plan.py --plan-json "$PLAN_FIXED_JSON" --rank "$RANK"
else
  echo "[step] skip execution (set EXECUTE=1 to run)"
fi

echo "[step] generate concise daily brief"
python scripts/generate_daily_research_brief.py \
  --remote-host "$REMOTE_STATUS_HOST" \
  --remote-root "$REMOTE_STATUS_ROOT" \
  --remote-timeout-sec "$REMOTE_STATUS_TIMEOUT_SEC"

echo "[done] audit/daily/daily_research_brief_latest.md"
