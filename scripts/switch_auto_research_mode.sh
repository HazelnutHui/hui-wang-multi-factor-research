#!/usr/bin/env bash
set -euo pipefail

MODE=""
ROOT_DIR="$(pwd)"
TARGET_REL="configs/research/auto_research_scheduler_policy.json"
LOW_NETWORK_REL="configs/research/auto_research_scheduler_policy.low_network.json"

usage() {
  cat <<USAGE
Usage:
  bash scripts/switch_auto_research_mode.sh --mode <low-network|standard>

Options:
  --mode <name>      low-network | standard
  --root-dir <path>  repo root (default: current directory)
  -h, --help         show help
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    --root-dir) ROOT_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [ -z "$MODE" ]; then
  usage
  exit 1
fi

ROOT_DIR="$(cd "$ROOT_DIR" && pwd)"
TARGET="$ROOT_DIR/$TARGET_REL"
LOW_NETWORK="$ROOT_DIR/$LOW_NETWORK_REL"
AUDIT_DIR="$ROOT_DIR/audit/auto_research/mode_switch"
TS="$(date +%Y-%m-%d_%H%M%S)"

if [ ! -f "$TARGET" ]; then
  echo "target policy not found: $TARGET" >&2
  exit 1
fi
if [ ! -f "$LOW_NETWORK" ]; then
  echo "low-network policy template not found: $LOW_NETWORK" >&2
  exit 1
fi

mkdir -p "$AUDIT_DIR"
cp "$TARGET" "$AUDIT_DIR/${TS}_before.json"

case "$MODE" in
  low-network)
    cp "$LOW_NETWORK" "$TARGET"
    ;;
  standard)
    # Standard mode keeps same schema with external channels disabled by default.
    PY_BIN="python3"
    if ! command -v "$PY_BIN" >/dev/null 2>&1; then
      PY_BIN="python"
    fi
    "$PY_BIN" - <<PY
import json
from pathlib import Path
p=Path("$TARGET")
obj=json.loads(p.read_text())
obj["alert_webhook_url"]=""
obj["alert_on_failure"]=False
obj["alert_command"]=""
obj["alert_email_enabled"]=False
obj["alert_email_dry_run"]=False
p.write_text(json.dumps(obj, indent=2, ensure_ascii=True))
PY
    ;;
  *)
    echo "unsupported mode: $MODE" >&2
    exit 1
    ;;
esac

cp "$TARGET" "$AUDIT_DIR/${TS}_after.json"
cat > "$AUDIT_DIR/${TS}_switch.md" <<MD
# Auto Research Mode Switch

- switched_at: $TS
- mode: $MODE
- target: \`$TARGET_REL\`
- before: \`audit/auto_research/mode_switch/${TS}_before.json\`
- after: \`audit/auto_research/mode_switch/${TS}_after.json\`
MD

echo "[done] mode=$MODE"
echo "[done] target=$TARGET"
echo "[done] audit_note=audit/auto_research/mode_switch/${TS}_switch.md"
