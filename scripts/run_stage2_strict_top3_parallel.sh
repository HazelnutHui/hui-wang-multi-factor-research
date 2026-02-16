#!/usr/bin/env bash
set -euo pipefail

# Institutional-style Stage2 strict runner (top3 factors).
# Usage:
#   bash scripts/run_stage2_strict_top3_parallel.sh [JOBS] [OUT_ROOT] [FORCE]
# Example:
#   bash scripts/run_stage2_strict_top3_parallel.sh 6 segment_results/stage2_v2026_02_16b_top3

JOBS="${1:-6}"
OUT_ROOT="${2:-segment_results/stage2_v2026_02_16b_top3}"
FORCE="${3:-0}"   # 1 = rerun even if segment_summary.csv exists

cd "$(dirname "$0")/.."
if [[ ! -f ".venv/bin/activate" ]]; then
  echo "[error] .venv not found. expected: $(pwd)/.venv/bin/activate"
  exit 1
fi
source .venv/bin/activate
export PYTHONPATH="$(pwd)"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

if ! [[ "${JOBS}" =~ ^[0-9]+$ ]] || [[ "${JOBS}" -le 0 ]]; then
  echo "[error] JOBS must be a positive integer, got: ${JOBS}"
  exit 1
fi

printf "%s\n" \
"value_v2 2010-01-04 2012-01-03" \
"value_v2 2012-01-04 2014-01-03" \
"value_v2 2014-01-04 2016-01-03" \
"value_v2 2016-01-04 2018-01-03" \
"value_v2 2018-01-04 2020-01-03" \
"value_v2 2020-01-04 2022-01-03" \
"value_v2 2022-01-04 2024-01-03" \
"value_v2 2024-01-04 2026-01-03" \
"value_v2 2026-01-04 2026-01-28" \
"momentum_v2 2010-01-04 2012-01-03" \
"momentum_v2 2012-01-04 2014-01-03" \
"momentum_v2 2014-01-04 2016-01-03" \
"momentum_v2 2016-01-04 2018-01-03" \
"momentum_v2 2018-01-04 2020-01-03" \
"momentum_v2 2020-01-04 2022-01-03" \
"momentum_v2 2022-01-04 2024-01-03" \
"momentum_v2 2024-01-04 2026-01-03" \
"momentum_v2 2026-01-04 2026-01-28" \
"quality_v2 2010-01-04 2012-01-03" \
"quality_v2 2012-01-04 2014-01-03" \
"quality_v2 2014-01-04 2016-01-03" \
"quality_v2 2016-01-04 2018-01-03" \
"quality_v2 2018-01-04 2020-01-03" \
"quality_v2 2020-01-04 2022-01-03" \
"quality_v2 2022-01-04 2024-01-03" \
"quality_v2 2024-01-04 2026-01-03" \
"quality_v2 2026-01-04 2026-01-28" \
| xargs -n3 -P"${JOBS}" bash -lc '
  f="$1"; s="$2"; e="$3"
  cd "'"$(pwd)"'" || exit 1
  source .venv/bin/activate
  export PYTHONPATH=$(pwd)
  export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
  tag="${s//-/}_${e//-/}"
  out="'"${OUT_ROOT}"'/${f}/${tag}"
  mkdir -p "$(dirname "$out")" logs
  summary_path="${out}/${f}/segment_summary.csv"
  if [[ "'"${FORCE}"'" != "1" && -f "${summary_path}" ]]; then
    echo "[skip] ${f} ${tag} already exists -> ${summary_path}"
    exit 0
  fi
  echo "[run] ${f} ${s} -> ${e}"
  python3 scripts/run_segmented_factors.py \
    --factors "$f" \
    --start-date "$s" \
    --end-date "$e" \
    --years 2 \
    --max-segments 1 \
    --out-dir "$out" \
    --set SIGNAL_ZSCORE=True \
    --set SIGNAL_RANK=False \
    --set SIGNAL_WINSOR_PCT_LOW=0.01 \
    --set SIGNAL_WINSOR_PCT_HIGH=0.99 \
    --set SIGNAL_MISSING_POLICY=drop \
    --set INDUSTRY_NEUTRAL=True \
    --set INDUSTRY_MIN_GROUP=5 \
    --set SIGNAL_NEUTRALIZE_SIZE=True \
    --set SIGNAL_NEUTRALIZE_BETA=True \
    --set MIN_MARKET_CAP=1000000000 \
    --set MIN_DOLLAR_VOLUME=2000000 \
    --set MIN_PRICE=5 \
    |& tee "logs/${f}_stage2_v2026_02_16b_${tag}.log"
' _

echo "Done. Results root: ${OUT_ROOT} (force=${FORCE})"
