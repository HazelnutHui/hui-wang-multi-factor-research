#!/usr/bin/env bash
set -euo pipefail

HOST="hui@100.66.103.44"
REMOTE_ROOT="~/projects/hui-wang-multi-factor-research"
TAG=""
INTERVAL=30

usage() {
  cat <<USAGE
Usage:
  bash scripts/monitor_gate_run.sh --tag <decision_tag> [--host <ssh_host>] [--remote-root <path>] [--interval <sec>]

Example:
  bash scripts/monitor_gate_run.sh \
    --tag committee_2026-02-21_run1_rerun4 \
    --host hui@100.66.103.44 \
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
    --interval)
      INTERVAL="$2"; shift 2 ;;
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
  ssh "$HOST" "cd $REMOTE_ROOT && RUN_DIR=\$(ls -td audit/workstation_runs/*${TAG}* 2>/dev/null | head -n1); \
    if [ -z \"\$RUN_DIR\" ]; then echo 'run_dir_not_found'; exit 0; fi; \
    echo RUN_DIR=\$RUN_DIR; \
    if [ -f \"\$RUN_DIR/result.json\" ]; then echo '[result.json]'; cat \"\$RUN_DIR/result.json\"; fi; \
    echo '[tail run.log]'; tail -n 20 \"\$RUN_DIR/run.log\"; \
    echo '[wf processes]'; pgrep -af 'run_walk_forward.py --factors combo_v2' || true; \
    echo '[gate reports]'; ls -1 gate_results/production_gates_*/production_gates_report.json 2>/dev/null | tail -n 3 || true"
  sleep "$INTERVAL"
done
