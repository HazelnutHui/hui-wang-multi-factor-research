#!/usr/bin/env bash
set -euo pipefail

# Sync completed official run artifacts from workstation to local, then finalize ledger locally.

HOST="hui@100.66.103.44"
REMOTE_ROOT="~/projects/hui-wang-multi-factor-research"
LOCAL_ROOT="/Users/hui/quant_score/v4"
TAG=""
RUN_DIR_REMOTE=""
REPORT_JSON_REMOTE=""

usage() {
  cat <<USAGE
Usage:
  bash scripts/post_run_sync_and_finalize.sh --tag <decision_tag> [--host <ssh_host>] [--remote-root <path>] [--local-root <path>]

Optional explicit overrides:
  --run-dir-remote <audit/workstation_runs/...>
  --report-json-remote <gate_results/.../production_gates_report.json>

Behavior:
1) resolve remote run_dir/report_json by tag (unless explicit overrides provided)
2) rsync run_dir + gate_results folder to local
3) run local finalize script to update stage ledger and summary
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
    --run-dir-remote)
      RUN_DIR_REMOTE="$2"; shift 2 ;;
    --report-json-remote)
      REPORT_JSON_REMOTE="$2"; shift 2 ;;
    --help|-h)
      usage; exit 0 ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      exit 1 ;;
  esac
done

if [ -z "$TAG" ] && { [ -z "$RUN_DIR_REMOTE" ] || [ -z "$REPORT_JSON_REMOTE" ]; }; then
  echo "--tag is required unless both --run-dir-remote and --report-json-remote are provided." >&2
  usage
  exit 1
fi

if [ -z "$RUN_DIR_REMOTE" ]; then
  RUN_DIR_REMOTE="$(ssh "$HOST" "cd $REMOTE_ROOT && ls -td audit/workstation_runs/*${TAG}* 2>/dev/null | head -n1")"
fi

if [ -z "$RUN_DIR_REMOTE" ]; then
  echo "remote run_dir not found" >&2
  exit 1
fi

if [ -z "$REPORT_JSON_REMOTE" ]; then
  REPORT_JSON_REMOTE="$(ssh "$HOST" "cd $REMOTE_ROOT && ls -td gate_results/production_gates_*/production_gates_report.json 2>/dev/null | head -n1")"
fi

if [ -z "$REPORT_JSON_REMOTE" ]; then
  echo "remote report_json not found" >&2
  exit 1
fi

GATE_DIR_REMOTE="$(dirname "$REPORT_JSON_REMOTE")"
GATE_DIR_PARENT_REMOTE="$(dirname "$GATE_DIR_REMOTE")"
GATE_DIR_BASENAME="$(basename "$GATE_DIR_REMOTE")"
RUN_DIR_BASENAME="$(basename "$RUN_DIR_REMOTE")"

mkdir -p "$LOCAL_ROOT/gate_results" "$LOCAL_ROOT/audit/workstation_runs"

# Sync latest gate folder and run audit folder.
rsync -avh --progress "$HOST:$REMOTE_ROOT/$GATE_DIR_REMOTE/" "$LOCAL_ROOT/gate_results/$GATE_DIR_BASENAME/"
rsync -avh --progress "$HOST:$REMOTE_ROOT/$RUN_DIR_REMOTE/" "$LOCAL_ROOT/audit/workstation_runs/$RUN_DIR_BASENAME/"

LOCAL_RUN_DIR="$LOCAL_ROOT/audit/workstation_runs/$RUN_DIR_BASENAME"
LOCAL_REPORT_JSON="$LOCAL_ROOT/gate_results/$GATE_DIR_BASENAME/production_gates_report.json"

if [ ! -f "$LOCAL_REPORT_JSON" ]; then
  echo "local report not found after sync: $LOCAL_REPORT_JSON" >&2
  exit 1
fi

(
  cd "$LOCAL_ROOT"
  bash scripts/finalize_gate_run.sh --run-dir "$LOCAL_RUN_DIR" --report-json "$LOCAL_REPORT_JSON"
)

echo "done: synced + finalized"
echo "run_dir_local=$LOCAL_RUN_DIR"
echo "report_json_local=$LOCAL_REPORT_JSON"
