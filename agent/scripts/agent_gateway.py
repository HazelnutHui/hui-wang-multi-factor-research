#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_SCRIPT = ROOT / "scripts" / "run_research_workflow.py"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _resolve(path_like: str) -> Path:
    p = Path(path_like).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (ROOT / p).resolve()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")


def _contains_blocked_flag(tokens: list[str], blocked_flags: list[str]) -> list[str]:
    blocked = set(blocked_flags)
    hits = []
    for t in tokens:
        if t in blocked:
            hits.append(t)
    return sorted(set(hits))


def _build_cmd(workflow: str, workflow_args: list[str]) -> list[str]:
    forwarded = list(workflow_args)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]
    return [sys.executable, str(WORKFLOW_SCRIPT), "--workflow", workflow, "--"] + forwarded


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _write_text(path, json.dumps(payload, indent=2, ensure_ascii=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Controlled gateway for AI-agent execution in V4."
    )
    parser.add_argument("--mode", choices=["plan", "execute"], required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument(
        "--policy-json",
        default="agent/configs/agent_policy.json",
        help="Agent policy json path (relative to project root allowed).",
    )
    parser.add_argument(
        "--approval-id",
        default="",
        help="Required in execute mode when policy requires approval.",
    )
    parser.add_argument(
        "workflow_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to run_research_workflow.py. Use '--' before forwarded args.",
    )
    args = parser.parse_args()

    policy_path = _resolve(args.policy_json)
    if not policy_path.exists():
        raise SystemExit(f"policy not found: {policy_path}")
    policy = _read_json(policy_path)

    allowed_workflows = [str(x) for x in policy.get("allowed_workflows", [])]
    if args.workflow not in allowed_workflows:
        raise SystemExit(
            f"workflow '{args.workflow}' is not allowed by policy. allowed={allowed_workflows}"
        )

    cmd = _build_cmd(args.workflow, args.workflow_args)
    cmd_str = " ".join(shlex.quote(x) for x in cmd)

    forwarded = list(args.workflow_args)
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]
    blocked_hits = _contains_blocked_flag(
        forwarded, [str(x) for x in policy.get("blocked_flags_execute", [])]
    )
    if args.mode == "execute" and blocked_hits:
        raise SystemExit(f"blocked flags in execute mode: {blocked_hits}")

    approval_ok = None
    approval_reason = ""
    if args.mode == "execute" and bool(policy.get("require_approval_for_execute", True)):
        approval_file = _resolve(str(policy.get("approval_file", "")))
        if not approval_file.exists():
            raise SystemExit(f"approval file not found: {approval_file}")
        approval = _read_json(approval_file)
        if not bool(approval.get("approved", False)):
            raise SystemExit(f"approval gate not open: {approval_file}")
        field = str(policy.get("approval_match_field", "approval_id")).strip()
        required_id = str(args.approval_id or "").strip()
        current_id = str(approval.get(field, "")).strip()
        if not required_id:
            raise SystemExit(
                f"execute mode requires --approval-id matching approval file field '{field}'"
            )
        if current_id != required_id:
            raise SystemExit(
                f"approval-id mismatch: expected '{current_id}' from {approval_file}, got '{required_id}'"
            )
        approval_ok = True
        approval_reason = f"approved=true and {field} matched"

    audit_root = _resolve(str(policy.get("audit_root", "audit/agent_gateway")))
    run_dir = audit_root / f"{_now()}_{args.workflow}_{args.mode}"
    run_dir.mkdir(parents=True, exist_ok=True)

    request = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "workflow": args.workflow,
        "policy_json": str(policy_path),
        "approval_id": args.approval_id,
        "workflow_args": forwarded,
        "blocked_flag_hits": blocked_hits,
        "command": cmd,
        "command_shell": cmd_str,
    }
    _write_json(run_dir / "request.json", request)
    _write_text(run_dir / "command.sh", cmd_str + "\n")

    if args.mode == "plan":
        result = {
            "status": "planned",
            "run_dir": str(run_dir),
            "workflow": args.workflow,
            "command_shell": cmd_str,
        }
        _write_json(run_dir / "result.json", result)
        print(f"[planned] run_dir={run_dir}")
        print(f"[planned] command={cmd_str}")
        raise SystemExit(0)

    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT) if not existing else f"{ROOT}:{existing}"
    started = datetime.now(timezone.utc).isoformat()
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env)
    ended = datetime.now(timezone.utc).isoformat()

    result = {
        "status": "executed",
        "run_dir": str(run_dir),
        "workflow": args.workflow,
        "approval_ok": approval_ok,
        "approval_reason": approval_reason,
        "command_shell": cmd_str,
        "started_at_utc": started,
        "ended_at_utc": ended,
        "exit_code": int(proc.returncode),
    }
    _write_json(run_dir / "result.json", result)
    print(f"[executed] run_dir={run_dir}")
    print(f"[executed] exit_code={proc.returncode}")
    raise SystemExit(int(proc.returncode))


if __name__ == "__main__":
    main()
