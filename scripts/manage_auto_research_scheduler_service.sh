#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="auto-research-scheduler"
ACTION=""
LINES=80
FOLLOW=0

usage() {
  cat <<USAGE
Usage:
  bash scripts/manage_auto_research_scheduler_service.sh --action <status|start|stop|restart|enable|disable|logs>

Options:
  --service-name <name>   Service name without suffix (default: auto-research-scheduler)
  --action <action>       status|start|stop|restart|enable|disable|logs
  --lines <n>             For logs action (default: 80)
  --follow                For logs action, stream live logs
  -h, --help              Show this help
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --service-name) SERVICE_NAME="$2"; shift 2 ;;
    --action) ACTION="$2"; shift 2 ;;
    --lines) LINES="$2"; shift 2 ;;
    --follow) FOLLOW=1; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [ -z "$ACTION" ]; then
  usage
  exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl not found" >&2
  exit 127
fi

UNIT="${SERVICE_NAME}.service"

case "$ACTION" in
  status)
    systemctl --user status "$UNIT" --no-pager
    ;;
  start)
    systemctl --user start "$UNIT"
    systemctl --user status "$UNIT" --no-pager
    ;;
  stop)
    systemctl --user stop "$UNIT"
    systemctl --user status "$UNIT" --no-pager || true
    ;;
  restart)
    systemctl --user restart "$UNIT"
    systemctl --user status "$UNIT" --no-pager
    ;;
  enable)
    systemctl --user enable --now "$UNIT"
    systemctl --user status "$UNIT" --no-pager
    ;;
  disable)
    systemctl --user disable --now "$UNIT"
    systemctl --user status "$UNIT" --no-pager || true
    ;;
  logs)
    if [ "$FOLLOW" -eq 1 ]; then
      journalctl --user -u "$UNIT" -n "$LINES" -f
    else
      journalctl --user -u "$UNIT" -n "$LINES" --no-pager
    fi
    ;;
  *)
    echo "unsupported action: $ACTION" >&2
    usage
    exit 1
    ;;
esac
