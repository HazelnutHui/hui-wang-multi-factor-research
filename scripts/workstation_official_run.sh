#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

usage() {
  cat <<USAGE
Usage:
  bash scripts/workstation_official_run.sh --workflow <name> --tag <decision_tag> [--owner <owner>] [--notes <notes>] [--require-clean] -- <workflow args>

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

CMD=(python scripts/run_research_workflow.py --workflow "$WORKFLOW" -- "$@")
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
  "notes": "${NOTES}"
}
CTX

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
