#!/usr/bin/env bash
set -euo pipefail

# Install a user-level systemd service for auto_research_scheduler.py.

SERVICE_NAME="auto-research-scheduler"
REPO_ROOT="$(pwd)"
POLICY_JSON="configs/research/auto_research_scheduler_policy.json"
PYTHON_BIN=""
ENABLE_NOW=0

usage() {
  cat <<USAGE
Usage:
  bash scripts/install_auto_research_scheduler_service.sh [options]

Options:
  --service-name <name>      Service name (default: auto-research-scheduler)
  --repo-root <path>         Repo root path (default: current directory)
  --policy-json <path>       Scheduler policy path relative to repo root
  --python-bin <path>        Python binary path (default: .venv/bin/python or python3)
  --enable-now               Run 'systemctl --user enable --now <service>'
  -h, --help                 Show this help
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --service-name) SERVICE_NAME="$2"; shift 2 ;;
    --repo-root) REPO_ROOT="$2"; shift 2 ;;
    --policy-json) POLICY_JSON="$2"; shift 2 ;;
    --python-bin) PYTHON_BIN="$2"; shift 2 ;;
    --enable-now) ENABLE_NOW=1; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl not found; this installer is for Linux systemd hosts." >&2
  exit 127
fi

REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"
if [ ! -f "$REPO_ROOT/scripts/auto_research_scheduler.py" ]; then
  echo "scheduler script not found under repo root: $REPO_ROOT" >&2
  exit 1
fi

if [ -z "$PYTHON_BIN" ]; then
  if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
    PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    echo "python3 not found and no .venv python present" >&2
    exit 127
  fi
fi

SYSTEMD_USER_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
ENV_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/auto-research-scheduler"
UNIT_PATH="$SYSTEMD_USER_DIR/${SERVICE_NAME}.service"
ENV_PATH="$ENV_DIR/${SERVICE_NAME}.env"

mkdir -p "$SYSTEMD_USER_DIR" "$ENV_DIR"

cat > "$UNIT_PATH" <<UNIT
[Unit]
Description=Auto Research Scheduler Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$REPO_ROOT
EnvironmentFile=-$ENV_PATH
ExecStart=$PYTHON_BIN $REPO_ROOT/scripts/auto_research_scheduler.py --policy-json $POLICY_JSON
Restart=always
RestartSec=20
TimeoutStopSec=30

[Install]
WantedBy=default.target
UNIT

if [ ! -f "$ENV_PATH" ]; then
  cat > "$ENV_PATH" <<ENV
# Optional SMTP credentials for scheduler email alerts.
# AUTO_RESEARCH_SMTP_USER=your_smtp_user
# AUTO_RESEARCH_SMTP_PASS=your_smtp_pass
ENV
  chmod 600 "$ENV_PATH" || true
fi

systemctl --user daemon-reload
echo "[done] installed_unit=$UNIT_PATH"
echo "[done] env_file=$ENV_PATH"
echo "[done] policy_json=$POLICY_JSON"

if [ "$ENABLE_NOW" -eq 1 ]; then
  systemctl --user enable --now "${SERVICE_NAME}.service"
  echo "[done] enabled_and_started=${SERVICE_NAME}.service"
else
  echo "next:"
  echo "  systemctl --user enable --now ${SERVICE_NAME}.service"
  echo "  systemctl --user status ${SERVICE_NAME}.service"
fi
