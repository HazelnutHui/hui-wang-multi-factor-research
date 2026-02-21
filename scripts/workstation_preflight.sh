#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

MIN_CORES="${MIN_CORES:-8}"
MIN_MEM_GB="${MIN_MEM_GB:-60}"
REQUIRE_CLEAN="${REQUIRE_CLEAN:-0}"

CORES=0
if command -v nproc >/dev/null 2>&1; then
  CORES="$(nproc)"
elif command -v getconf >/dev/null 2>&1; then
  CORES="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 0)"
elif command -v sysctl >/dev/null 2>&1; then
  CORES="$(sysctl -n hw.ncpu 2>/dev/null || echo 0)"
fi

MEM_GB=0
if [ -r /proc/meminfo ]; then
  MEM_KB="$(awk '/MemTotal/ {print $2}' /proc/meminfo)"
  MEM_GB="$((MEM_KB / 1024 / 1024))"
elif command -v sysctl >/dev/null 2>&1; then
  MEM_BYTES="$(sysctl -n hw.memsize 2>/dev/null || echo 0)"
  MEM_GB="$((MEM_BYTES / 1024 / 1024 / 1024))"
fi

if [ "${CORES:-0}" -le 0 ] && command -v python >/dev/null 2>&1; then
  CORES="$(
    python - <<'PY'
import os
print(os.cpu_count() or 0)
PY
  )"
fi

if [ "${MEM_GB:-0}" -le 0 ] && command -v python >/dev/null 2>&1; then
  MEM_GB="$(
    python - <<'PY'
import os
import re

mem_gb = 0
try:
    if os.path.exists("/proc/meminfo"):
        with open("/proc/meminfo") as f:
            match = re.search(r"^MemTotal:\s+(\d+)\s+kB", f.read(), re.M)
            if match:
                mem_gb = int(int(match.group(1)) / 1024 / 1024)
except Exception:
    pass
print(mem_gb)
PY
  )"
fi

GIT_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
GIT_BRANCH="$(git branch --show-current 2>/dev/null || echo unknown)"
DIRTY_COUNT="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
HOSTNAME_VAL="$(hostname)"
TS="$(date '+%Y-%m-%dT%H:%M:%S%z')"

PASS=1
REASONS=()

if [ "${CORES:-0}" -lt "$MIN_CORES" ]; then
  PASS=0
  REASONS+=("cores ${CORES} < required ${MIN_CORES}")
fi

if [ "${MEM_GB:-0}" -lt "$MIN_MEM_GB" ]; then
  PASS=0
  REASONS+=("memory ${MEM_GB}GB < required ${MIN_MEM_GB}GB")
fi

if [ "$REQUIRE_CLEAN" = "1" ] && [ "$DIRTY_COUNT" -gt 0 ]; then
  PASS=0
  REASONS+=("git worktree is dirty and REQUIRE_CLEAN=1")
fi

STATUS="pass"
if [ "$PASS" -ne 1 ]; then
  STATUS="fail"
fi

printf '{\n' 
printf '  "timestamp": "%s",\n' "$TS"
printf '  "hostname": "%s",\n' "$HOSTNAME_VAL"
printf '  "root_dir": "%s",\n' "$ROOT_DIR"
printf '  "git_branch": "%s",\n' "$GIT_BRANCH"
printf '  "git_commit": "%s",\n' "$GIT_COMMIT"
printf '  "git_dirty_count": %s,\n' "$DIRTY_COUNT"
printf '  "cores": %s,\n' "$CORES"
printf '  "memory_gb": %s,\n' "$MEM_GB"
printf '  "min_cores": %s,\n' "$MIN_CORES"
printf '  "min_memory_gb": %s,\n' "$MIN_MEM_GB"
printf '  "require_clean": %s,\n' "$REQUIRE_CLEAN"
printf '  "status": "%s",\n' "$STATUS"
printf '  "reasons": ['
for i in "${!REASONS[@]}"; do
  if [ "$i" -gt 0 ]; then
    printf ', '
  fi
  printf '"%s"' "${REASONS[$i]}"
done
printf ']\n' 
printf '}\n'

if [ "$PASS" -ne 1 ]; then
  exit 2
fi
