#!/usr/bin/env bash
set -euo pipefail

# Incremental data pull (no full overwrite by default).
# Focuses on "latest usable" daily refresh, not full historical rebuild.

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
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOG_DIR}"

# Load local env files if present (not tracked by git due .gitignore).
set -a
if [[ -f "${ROOT_DIR}/.env.daily" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.env.daily"
fi
if [[ -f "${ROOT_DIR}/.env" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.env"
fi
set +a

TODAY_UTC="$(date -u +%F)"
RECENT_DAYS="${RECENT_DAYS:-45}"
START_DATE_UTC="${START_DATE_UTC:-$("${PY_BIN}" - <<PY
from datetime import datetime, timedelta, timezone
print((datetime.now(timezone.utc).date()-timedelta(days=int("${RECENT_DAYS}"))).isoformat())
PY
)}"
END_DATE_UTC="${END_DATE_UTC:-${TODAY_UTC}}"
EARNINGS_YEARS_BACK="${EARNINGS_YEARS_BACK:-1}"
DRY_RUN="${DRY_RUN:-0}"
PULL_CONTINUE_ON_ERROR="${PULL_CONTINUE_ON_ERROR:-1}"
FMP_RESOLVE_IPS="${FMP_RESOLVE_IPS:-}"

if [[ -z "${FMP_API_KEY:-}" ]]; then
  echo "ERROR: FMP_API_KEY is not set." >&2
  exit 1
fi

run_cmd() {
  local rendered="$*"
  if [[ -n "${FMP_API_KEY:-}" ]]; then
    rendered="${rendered//${FMP_API_KEY}/***}"
  fi
  echo "+ ${rendered}"
  if [[ "${DRY_RUN}" == "1" ]]; then
    return 0
  fi
  local rc=0
  set +e
  "$@"
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    return 0
  fi
  if [[ "${PULL_CONTINUE_ON_ERROR}" == "1" ]]; then
    echo "[pull][warn] command failed (rc=${rc}), continue: ${rendered}" >&2
    return 0
  fi
  return $rc
}

echo "[pull] root=${ROOT_DIR}"
echo "[pull] range=${START_DATE_UTC}..${END_DATE_UTC} (UTC)"
echo "[pull] dry_run=${DRY_RUN}"

# 1) Earnings calendar (recent window) - refreshes single csv in place.
run_cmd "${PY_BIN}" "${ROOT_DIR}/scripts/fmp_earnings_calendar.py" \
  --api-key "${FMP_API_KEY}" \
  --start "${START_DATE_UTC}" \
  --end "${END_DATE_UTC}" \
  --out "${ROOT_DIR}/data/fmp/earnings/earnings_calendar.csv"

# 2) Earnings surprises bulk (recent years), script itself skips existing year files.
START_YEAR="$("${PY_BIN}" - <<PY
from datetime import datetime, timezone
print(datetime.now(timezone.utc).year - int("${EARNINGS_YEARS_BACK}"))
PY
)"
END_YEAR="$("${PY_BIN}" - <<PY
from datetime import datetime, timezone
print(datetime.now(timezone.utc).year)
PY
)"
run_cmd "${PY_BIN}" "${ROOT_DIR}/scripts/fmp_earnings_surprises_bulk.py" \
  --api-key "${FMP_API_KEY}" \
  --start-year "${START_YEAR}" \
  --end-year "${END_YEAR}" \
  --out-dir "${ROOT_DIR}/data/fmp/earnings"

# 3) Delisted missing fill (incremental: only missing symbols).
run_cmd "${PY_BIN}" "${ROOT_DIR}/scripts/fmp_fill_missing_delisted.py"

# 4) Dividend-adjusted prices incremental patch (active universe, latest date only).
run_cmd "${PY_BIN}" "${ROOT_DIR}/scripts/update_divadj_prices_incremental.py" \
  --scope active \
  --sleep 0.12 \
  ${FMP_RESOLVE_IPS:+--resolve-ip "${FMP_RESOLVE_IPS}"}

echo "[pull] done."
