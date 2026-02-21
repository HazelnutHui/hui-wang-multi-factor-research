#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

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
  cat <<USAGE
Usage:
  bash scripts/workstation_official_run.sh --workflow <name> --tag <decision_tag> [--owner <owner>] [--notes <notes>] [--require-clean] [--threads <n>] [--dq-input-csv <path>] [--skip-data-quality-check] -- <workflow args>

Example:
  bash scripts/workstation_official_run.sh \
    --workflow production_gates \
    --tag committee_2026-02-21_ws_run1 \
    --owner hui \
    --notes "official workstation run" \
    -- \
    --strategy configs/strategies/combo_v2_prod.yaml \
    --factor combo_v2 \
    --freeze-file runs/freeze/combo_v2_prod.freeze.json \
    --out-dir gate_results
USAGE
}

WORKFLOW=""
TAG=""
OWNER=""
NOTES=""
REQUIRE_CLEAN=0
THREADS="${THREADS:-8}"
DQ_INPUT_CSV=""
DQ_REQUIRED_COLUMNS="${DQ_REQUIRED_COLUMNS:-date,ticker,score}"
DQ_NUMERIC_COLUMNS="${DQ_NUMERIC_COLUMNS:-score}"
DQ_KEY_COLUMNS="${DQ_KEY_COLUMNS:-date,ticker}"
DQ_DATE_COLUMN="${DQ_DATE_COLUMN:-date}"
DQ_MIN_ROWS="${DQ_MIN_ROWS:-1000}"
DQ_MAX_MISSING_RATIO="${DQ_MAX_MISSING_RATIO:-0.05}"
DQ_MAX_DUPLICATE_RATIO="${DQ_MAX_DUPLICATE_RATIO:-0.01}"
DQ_MAX_STALENESS_DAYS="${DQ_MAX_STALENESS_DAYS:-7}"
SKIP_DATA_QUALITY_CHECK=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --workflow)
      WORKFLOW="$2"
      shift 2
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    --owner)
      OWNER="$2"
      shift 2
      ;;
    --notes)
      NOTES="$2"
      shift 2
      ;;
    --require-clean)
      REQUIRE_CLEAN=1
      shift
      ;;
    --threads)
      THREADS="$2"
      shift 2
      ;;
    --dq-input-csv)
      DQ_INPUT_CSV="$2"
      shift 2
      ;;
    --skip-data-quality-check)
      SKIP_DATA_QUALITY_CHECK=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [ -z "$WORKFLOW" ] || [ -z "$TAG" ]; then
  usage
  exit 1
fi

if [ "$#" -eq 0 ]; then
  echo "Missing workflow args after --" >&2
  usage
  exit 1
fi

TS="$(date '+%Y-%m-%d_%H%M%S')"
SAFE_TAG="$(echo "$TAG" | tr ' /:' '___')"
AUDIT_DIR="audit/workstation_runs/${TS}_${WORKFLOW}_${SAFE_TAG}"
mkdir -p "$AUDIT_DIR"

PRE_JSON="$AUDIT_DIR/preflight.json"
if REQUIRE_CLEAN="$REQUIRE_CLEAN" bash scripts/workstation_preflight.sh > "$PRE_JSON"; then
  :
else
  echo "Preflight failed. See $PRE_JSON" >&2
  exit 2
fi

GIT_COMMIT="$(git rev-parse HEAD)"
GIT_BRANCH="$(git branch --show-current)"
HOSTNAME_VAL="$(hostname)"
DQ_REPORT_JSON=""

if [ "$SKIP_DATA_QUALITY_CHECK" -ne 1 ]; then
  if [ "$WORKFLOW" = "production_gates" ] && [ -z "$DQ_INPUT_CSV" ]; then
    echo "For production_gates official runs, --dq-input-csv is required (or explicitly set --skip-data-quality-check)." >&2
    exit 1
  fi
  if [ -n "$DQ_INPUT_CSV" ]; then
    DQ_ROOT="$AUDIT_DIR/data_quality"
    mkdir -p "$DQ_ROOT"
    DQ_CMD=(
      "$PYTHON_BIN" scripts/data_quality_gate.py
      --input-csv "$DQ_INPUT_CSV"
      --required-columns "$DQ_REQUIRED_COLUMNS"
      --numeric-columns "$DQ_NUMERIC_COLUMNS"
      --key-columns "$DQ_KEY_COLUMNS"
      --date-column "$DQ_DATE_COLUMN"
      --min-rows "$DQ_MIN_ROWS"
      --max-missing-ratio "$DQ_MAX_MISSING_RATIO"
      --max-duplicate-ratio "$DQ_MAX_DUPLICATE_RATIO"
      --max-staleness-days "$DQ_MAX_STALENESS_DAYS"
      --out-dir "$DQ_ROOT"
    )
    printf '%q ' "${DQ_CMD[@]}" > "$AUDIT_DIR/data_quality_command.sh"
    printf '\n' >> "$AUDIT_DIR/data_quality_command.sh"
    set +e
    "${DQ_CMD[@]}" 2>&1 | tee "$AUDIT_DIR/data_quality.log"
    DQ_RC="${PIPESTATUS[0]}"
    set -e
    if [ "$DQ_RC" -ne 0 ]; then
      echo "Data quality gate failed (exit=${DQ_RC}). See $AUDIT_DIR/data_quality.log" >&2
      exit "$DQ_RC"
    fi
    DQ_REPORT_JSON="$(ls -td "$DQ_ROOT"/data_quality_*/data_quality_report.json 2>/dev/null | head -n1 || true)"
    if [ -z "$DQ_REPORT_JSON" ] || [ ! -f "$DQ_REPORT_JSON" ]; then
      echo "Data quality gate passed but report json not found under $DQ_ROOT" >&2
      exit 1
    fi
  fi
fi

CMD=("$PYTHON_BIN" scripts/run_research_workflow.py --workflow "$WORKFLOW" -- "$@")
printf '%q ' "${CMD[@]}" > "$AUDIT_DIR/command.sh"
printf '\n' >> "$AUDIT_DIR/command.sh"

cat > "$AUDIT_DIR/context.json" <<CTX
{
  "timestamp": "${TS}",
  "hostname": "${HOSTNAME_VAL}",
  "git_branch": "${GIT_BRANCH}",
  "git_commit": "${GIT_COMMIT}",
  "workflow": "${WORKFLOW}",
  "decision_tag": "${TAG}",
  "owner": "${OWNER}",
  "notes": "${NOTES}",
  "threads": ${THREADS},
  "skip_data_quality_check": ${SKIP_DATA_QUALITY_CHECK},
  "data_quality_input_csv": "${DQ_INPUT_CSV}",
  "data_quality_report_json": "${DQ_REPORT_JSON}"
}
CTX

export OMP_NUM_THREADS="${THREADS}"
export MKL_NUM_THREADS="${THREADS}"
export OPENBLAS_NUM_THREADS="${THREADS}"
export NUMEXPR_NUM_THREADS="${THREADS}"

set +e
"${CMD[@]}" 2>&1 | tee "$AUDIT_DIR/run.log"
RC="${PIPESTATUS[0]}"
set -e

cat > "$AUDIT_DIR/result.json" <<RES
{
  "workflow": "${WORKFLOW}",
  "decision_tag": "${TAG}",
  "exit_code": ${RC},
  "audit_dir": "${AUDIT_DIR}"
}
RES

if [ "$RC" -ne 0 ]; then
  echo "Run failed (exit=${RC}). Audit: $AUDIT_DIR" >&2
  exit "$RC"
fi

echo "Run succeeded. Audit: $AUDIT_DIR"
