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

if [[ "${OPS_ENTRY_CALLER:-0}" != "1" ]]; then
  echo "[note] direct script is compatibility path; preferred: bash scripts/ops_entry.sh fast"
fi

usage() {
  cat <<'USAGE'
Speed-first research screen (non-official, isolated outputs).

Usage:
  bash scripts/fast_research_run.sh [options]

Options:
  --strategy <yaml>              Base strategy yaml (default: configs/strategies/combo_v2_prod.yaml)
  --factor <name>                Factor name for WF (default: combo_v2)
  --tag <label>                  Run label (default: fast_YYYY-MM-DD_HHMMSS)
  --wf-start-year <yyyy>         WF start year (default: 2016)
  --wf-end-year <yyyy>           WF end year (default: 2025)
  --wf-train-years <n>           WF train years (default: 3)
  --wf-test-years <n>            WF test years (default: 1)
  --wf-shards <n>                WF shards (default: 8)
  --cost-multipliers <csv>       Cost multipliers (default: 1.5,2.0)
  --out-dir <path>               Gate output root (default: gate_results/fast_research)
  --with-risk                    Enable risk diagnostics (default: off)
  --with-stat                    Enable statistical gates (default: off)
  --dry-run                      Build isolated config and dry-run production gates
  --help                         Show this message

Notes:
  - This command auto-generates an isolated strategy yaml under runs/fast_research/strategies/.
  - It rewrites strategy.output_dir to strategies/fast_research/<tag>/combo_v2.
  - Designed for fast screening before official workstation runs.
USAGE
}

BASE_STRATEGY="configs/strategies/combo_v2_prod.yaml"
FACTOR="combo_v2"
TAG="fast_$(date '+%Y-%m-%d_%H%M%S')"
WF_START_YEAR="2016"
WF_END_YEAR="2025"
WF_TRAIN_YEARS="3"
WF_TEST_YEARS="1"
WF_SHARDS="8"
COST_MULTIPLIERS="1.5,2.0"
OUT_DIR="gate_results/fast_research"
WITH_RISK="0"
WITH_STAT="0"
DRY_RUN="0"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --strategy) BASE_STRATEGY="$2"; shift 2 ;;
    --factor) FACTOR="$2"; shift 2 ;;
    --tag) TAG="$2"; shift 2 ;;
    --wf-start-year) WF_START_YEAR="$2"; shift 2 ;;
    --wf-end-year) WF_END_YEAR="$2"; shift 2 ;;
    --wf-train-years) WF_TRAIN_YEARS="$2"; shift 2 ;;
    --wf-test-years) WF_TEST_YEARS="$2"; shift 2 ;;
    --wf-shards) WF_SHARDS="$2"; shift 2 ;;
    --cost-multipliers) COST_MULTIPLIERS="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --with-risk) WITH_RISK="1"; shift ;;
    --with-stat) WITH_STAT="1"; shift ;;
    --dry-run) DRY_RUN="1"; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [ ! -f "$BASE_STRATEGY" ]; then
  echo "base strategy not found: $BASE_STRATEGY" >&2
  exit 2
fi

SAFE_TAG="$(echo "$TAG" | tr ' /:' '___')"
FAST_STRATEGY_DIR="runs/fast_research/strategies"
FAST_META_DIR="runs/fast_research/meta"
mkdir -p "$FAST_STRATEGY_DIR" "$FAST_META_DIR"
FAST_STRATEGY="$FAST_STRATEGY_DIR/${SAFE_TAG}.yaml"
FAST_OUTPUT_DIR="strategies/fast_research/${SAFE_TAG}/combo_v2"

"$PYTHON_BIN" - <<PY
import yaml
from pathlib import Path
base = Path("$BASE_STRATEGY")
out = Path("$FAST_STRATEGY")
tag = "$SAFE_TAG"
out_dir = "$FAST_OUTPUT_DIR"
d = yaml.safe_load(base.read_text())
if not isinstance(d, dict):
    raise SystemExit("invalid strategy yaml")
s = d.get("strategy")
if not isinstance(s, dict):
    s = {}
    d["strategy"] = s
s["output_dir"] = out_dir
s["id"] = f"{s.get('id','strategy')}_fast_{tag}"
s["name"] = f"{s.get('name','strategy')}_FAST_{tag}"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(yaml.safe_dump(d, sort_keys=False))
print(f"[done] fast_strategy={out}")
print(f"[done] fast_output_dir={out_dir}")
PY

CMD=(
  "$PYTHON_BIN" scripts/run_production_gates.py
  --strategy "$FAST_STRATEGY"
  --factor "$FACTOR"
  --cost-multipliers "$COST_MULTIPLIERS"
  --wf-train-years "$WF_TRAIN_YEARS"
  --wf-test-years "$WF_TEST_YEARS"
  --wf-start-year "$WF_START_YEAR"
  --wf-end-year "$WF_END_YEAR"
  --wf-shards "$WF_SHARDS"
  --out-dir "$OUT_DIR"
  --decision-tag "$SAFE_TAG"
  --owner "hui"
  --notes "fast_research_screen"
)

if [ "$WITH_RISK" != "1" ]; then
  CMD+=(--skip-risk-diagnostics)
fi
if [ "$WITH_STAT" != "1" ]; then
  CMD+=(--skip-statistical-gates)
fi
if [ "$DRY_RUN" = "1" ]; then
  CMD+=(--dry-run)
fi

printf '%q ' "${CMD[@]}" > "$FAST_META_DIR/${SAFE_TAG}.command.sh"
printf '\n' >> "$FAST_META_DIR/${SAFE_TAG}.command.sh"
echo "[cmd] ${CMD[*]}"
"${CMD[@]}"

echo "[done] fast_meta_cmd=$FAST_META_DIR/${SAFE_TAG}.command.sh"
echo "[done] fast_strategy=$FAST_STRATEGY"
echo "[done] fast_gate_out_root=$OUT_DIR"
