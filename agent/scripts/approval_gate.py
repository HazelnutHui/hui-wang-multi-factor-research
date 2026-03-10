#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APPROVAL_FILE = ROOT / "configs" / "research" / "factory_queue" / "run_approval.json"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _make_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d-agent-%H%M%S")


def cmd_status() -> int:
    if not APPROVAL_FILE.exists():
        print(f"[approval] file_missing path={APPROVAL_FILE}")
        return 1
    payload = _read_json(APPROVAL_FILE)
    print(f"[approval] approved={bool(payload.get('approved', False))}")
    print(f"[approval] approval_id={payload.get('approval_id', '')}")
    print(f"[approval] approved_by={payload.get('approved_by', '')}")
    print(f"[approval] approved_at={payload.get('approved_at', '')}")
    print(f"[approval] path={APPROVAL_FILE}")
    return 0


def cmd_close(notes: str) -> int:
    payload = _read_json(APPROVAL_FILE) if APPROVAL_FILE.exists() else {}
    payload.update(
        {
            "approved": False,
            "approved_queue": "",
            "approval_id": "",
            "approved_by": "",
            "approved_at": "",
            "notes": notes or "Default closed. Open only for a single approved execution window.",
        }
    )
    _write_json(APPROVAL_FILE, payload)
    print(f"[approval] closed path={APPROVAL_FILE}")
    return 0


def cmd_open(approval_id: str, approved_by: str, notes: str) -> int:
    payload = _read_json(APPROVAL_FILE) if APPROVAL_FILE.exists() else {}
    payload.update(
        {
            "approved": True,
            "approved_queue": "",
            "approval_id": approval_id or _make_id(),
            "approved_by": approved_by or "hui",
            "approved_at": _utc_now(),
            "notes": notes or "Temporary approval for a single execution window.",
        }
    )
    _write_json(APPROVAL_FILE, payload)
    print(f"[approval] opened path={APPROVAL_FILE}")
    print(f"[approval] approval_id={payload['approval_id']}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage agent execute approval gate.")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("status", help="Show approval status.")

    p_open = sub.add_parser("open", help="Open approval gate.")
    p_open.add_argument("--approval-id", default="", help="Approval id. Auto-generated if empty.")
    p_open.add_argument("--approved-by", default="hui", help="Approver name.")
    p_open.add_argument("--notes", default="", help="Approval note.")

    p_close = sub.add_parser("close", help="Close approval gate.")
    p_close.add_argument(
        "--notes",
        default="Default closed. Open only for a single approved execution window.",
        help="Close note.",
    )

    args = parser.parse_args()

    if args.action == "status":
        raise SystemExit(cmd_status())
    if args.action == "close":
        raise SystemExit(cmd_close(args.notes))
    if args.action == "open":
        raise SystemExit(cmd_open(args.approval_id, args.approved_by, args.notes))
    raise SystemExit(2)


if __name__ == "__main__":
    main()
