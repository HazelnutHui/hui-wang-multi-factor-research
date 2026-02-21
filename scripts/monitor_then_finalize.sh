#!/usr/bin/env bash
set -euo pipefail

HOST="hui@100.66.103.44"
REMOTE_ROOT="~/projects/hui-wang-multi-factor-research"
LOCAL_ROOT="/Users/hui/quant_score/v4"
TAG=""
INTERVAL=30
WF_PATTERN="run_walk_forward.py --factors combo_v2"
DRY_RUN=0

usage() {
  cat <<USAGE
Usage:
  bash scripts/monitor_then_finalize.sh --tag <decision_tag> [--host <ssh_host>] [--remote-root <path>] [--local-root <path>] [--interval <sec>] [--wf-pattern <pgrep pattern>] [--dry-run]

Behavior:
1) poll remote run_dir by decision_tag
2) wait until run_dir/result.json exists
3) ensure no active matching WF process remains
4) call scripts/post_run_sync_and_finalize.sh automatically

Example:
  bash scripts/monitor_then_finalize.sh \
    --tag committee_2026-02-21_run1_rerun4 \
    --interval 30
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --tag)
      TAG="$2"; shift 2 ;;
    --host)
      HOST="$2"; shift 2 ;;
    --remote-root)
      REMOTE_ROOT="$2"; shift 2 ;;
    --local-root)
      LOCAL_ROOT="$2"; shift 2 ;;
    --interval)
      INTERVAL="$2"; shift 2 ;;
    --wf-pattern)
      WF_PATTERN="$2"; shift 2 ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    --help|-h)
      usage; exit 0 ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      exit 1 ;;
  esac
done

if [ -z "$TAG" ]; then
  echo "--tag is required" >&2
  usage
  exit 1
fi

while true; do
  echo "================ $(date '+%Y-%m-%d %H:%M:%S') ================"
  OUT="$(ssh "$HOST" "cd $REMOTE_ROOT && RUN_DIR=\$(ls -td audit/workstation_runs/*${TAG}* 2>/dev/null | head -n1); \
if [ -z \"\$RUN_DIR\" ]; then echo STATUS=run_dir_not_found; exit 0; fi; \
echo RUN_DIR=\$RUN_DIR; \
if [ -f \"\$RUN_DIR/result.json\" ]; then echo HAS_RESULT=1; else echo HAS_RESULT=0; fi; \
if pgrep -af \"$WF_PATTERN\" >/tmp/monitor_then_finalize_pids.$$ 2>/dev/null; then \
  CNT=\$(wc -l </tmp/monitor_then_finalize_pids.$$ | tr -d ' '); \
  echo WF_COUNT=\$CNT; \
  cat /tmp/monitor_then_finalize_pids.$$; \
else \
  echo WF_COUNT=0; \
fi; \
echo LOG_TAIL_BEGIN; \
tail -n 20 \"\$RUN_DIR/run.log\" 2>/dev/null || true; \
echo LOG_TAIL_END; \
rm -f /tmp/monitor_then_finalize_pids.$$" || true)"

  printf '%s\n' "$OUT"

  HAS_RESULT="$(printf '%s\n' "$OUT" | awk -F= '/^HAS_RESULT=/{print $2}' | tail -n1)"
  WF_COUNT="$(printf '%s\n' "$OUT" | awk -F= '/^WF_COUNT=/{print $2}' | tail -n1)"
  RUN_DIR_REMOTE="$(printf '%s\n' "$OUT" | awk -F= '/^RUN_DIR=/{print $2}' | tail -n1)"

  if [ "$HAS_RESULT" = "1" ] && [ "${WF_COUNT:-0}" = "0" ] && [ -n "$RUN_DIR_REMOTE" ]; then
    echo "Run appears complete and stable for finalize."
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "[dry-run] skip finalize: bash scripts/post_run_sync_and_finalize.sh --tag $TAG --host $HOST --remote-root $REMOTE_ROOT --local-root $LOCAL_ROOT"
      exit 0
    fi
    (
      cd "$LOCAL_ROOT"
      bash scripts/post_run_sync_and_finalize.sh \
        --tag "$TAG" \
        --host "$HOST" \
        --remote-root "$REMOTE_ROOT" \
        --local-root "$LOCAL_ROOT"
    )
    exit 0
  fi

  echo "Not ready for finalize. Sleeping ${INTERVAL}s..."
  sleep "$INTERVAL"
done
