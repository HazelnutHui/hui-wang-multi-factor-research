#!/usr/bin/env python3
"""Self-test scheduler alert channels with dedupe verification."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))


def main() -> None:
    p = argparse.ArgumentParser(description="Self-test scheduler alert channels.")
    p.add_argument("--scheduler-policy-json", default="configs/research/auto_research_scheduler_policy.json")
    p.add_argument("--orchestrator-policy-json", default="configs/research/auto_research_policy.json")
    p.add_argument("--out-dir", default="")
    p.add_argument("--test-command-channel", action="store_true", default=True)
    p.add_argument("--test-email-dry-run", action="store_true", default=True)
    p.add_argument("--max-cycles", type=int, default=2)
    args = p.parse_args()

    root = Path(".").resolve()
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path(args.out_dir).resolve() if args.out_dir else (root / "audit" / "auto_research" / f"{ts}_alert_selftest")
    out_dir.mkdir(parents=True, exist_ok=True)

    base_policy = _read_json((root / args.scheduler_policy_json).resolve())
    test_policy = dict(base_policy)
    test_policy.update(
        {
            "interval_seconds": 1,
            "max_cycles": max(2, int(args.max_cycles)),
            "stop_on_orchestrator_failure": False,
            "orchestrator_policy_json": args.orchestrator_policy_json,
            "orchestrator_execute": False,
            "lock_file": str(out_dir / "scheduler.lock"),
            "heartbeat_json": str(out_dir / "scheduler_heartbeat.json"),
            "ledger_csv": str(out_dir / "scheduler_ledger.csv"),
            "ledger_md": str(out_dir / "scheduler_ledger.md"),
            "alert_on_failure": True,
            "alert_state_json": str(out_dir / "alert_state.json"),
            "alert_dedupe_window_seconds": 3600,
            "alert_webhook_url": "",
            "alert_recent_failures_limit": 5,
        }
    )

    command_log = out_dir / "command_alert.log"
    command_json_log = out_dir / "command_alert_json.log"
    if args.test_command_channel:
        test_policy["alert_command"] = (
            f"echo \"$AUTO_RESEARCH_ALERT_MSG\" >> {command_log}; "
            f"echo \"$AUTO_RESEARCH_ALERT_JSON\" >> {command_json_log}"
        )
    else:
        test_policy["alert_command"] = ""

    email_dry_dir = out_dir / "email_dry_run"
    if args.test_email_dry_run:
        test_policy["alert_email_enabled"] = True
        test_policy["alert_email_from"] = "noreply@example.com"
        test_policy["alert_email_to"] = ["ops@example.com"]
        test_policy["alert_email_dry_run"] = True
        test_policy["alert_email_dry_run_dir"] = str(email_dry_dir)
        test_policy["alert_email_smtp_host"] = ""
    else:
        test_policy["alert_email_enabled"] = False

    test_policy_path = out_dir / "scheduler_policy.test.json"
    _write_json(test_policy_path, test_policy)

    proc = subprocess.run(
        [sys.executable, "scripts/auto_research_scheduler.py", "--policy-json", str(test_policy_path)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )

    command_lines = 0
    command_json_lines = 0
    command_json_sample: dict[str, Any] = {}
    if command_log.exists():
        command_lines = len([x for x in command_log.read_text().splitlines() if x.strip()])
    if command_json_log.exists():
        raw = [x for x in command_json_log.read_text().splitlines() if x.strip()]
        command_json_lines = len(raw)
        if raw:
            try:
                command_json_sample = json.loads(raw[0])
            except Exception:
                command_json_sample = {}

    email_count = len(list(email_dry_dir.glob("*.eml"))) if email_dry_dir.exists() else 0
    alert_state = _read_json(out_dir / "alert_state.json") if (out_dir / "alert_state.json").exists() else {}
    dedupe_keys = list((alert_state.get("keys") or {}).keys()) if isinstance(alert_state, dict) else []

    checks = {
        "scheduler_exit_nonzero_expected": proc.returncode != 0,
        "command_channel_deduped": (command_lines == 1) if args.test_command_channel else True,
        "command_json_present": (command_json_lines == 1) if args.test_command_channel else True,
        "email_dry_run_deduped": (email_count == 1) if args.test_email_dry_run else True,
        "alert_state_has_dedupe_key": len(dedupe_keys) >= 1,
        "structured_payload_has_run_dir": bool(command_json_sample.get("run_dir")) if args.test_command_channel else True,
        "structured_payload_has_report_json": bool(command_json_sample.get("orchestrator_report_json"))
        if args.test_command_channel
        else True,
        "structured_payload_has_recent_failures": bool(command_json_sample.get("recent_failures"))
        if args.test_command_channel
        else True,
    }
    overall_pass = all(checks.values())

    payload = {
        "generated_at": datetime.now().isoformat(),
        "out_dir": str(out_dir),
        "scheduler_policy_test_json": str(test_policy_path),
        "scheduler_return_code": int(proc.returncode),
        "scheduler_stdout": proc.stdout.strip(),
        "scheduler_stderr": proc.stderr.strip(),
        "command_log": str(command_log),
        "command_json_log": str(command_json_log),
        "email_dry_run_dir": str(email_dry_dir),
        "command_lines": command_lines,
        "command_json_lines": command_json_lines,
        "email_dry_run_count": email_count,
        "dedupe_keys": dedupe_keys,
        "checks": checks,
        "overall_pass": overall_pass,
    }
    out_json = out_dir / "scheduler_alert_selftest_report.json"
    out_md = out_dir / "scheduler_alert_selftest_report.md"
    _write_json(out_json, payload)

    lines = [
        "# Scheduler Alert Selftest Report",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- overall_pass: {overall_pass}",
        f"- scheduler_return_code: {payload['scheduler_return_code']}",
        f"- out_dir: `{out_dir}`",
        "",
        "## Checks",
        "",
    ]
    for k, v in checks.items():
        lines.append(f"- {k}: {v}")
    lines += [
        "",
        "## Counters",
        "",
        f"- command_lines: {command_lines}",
        f"- command_json_lines: {command_json_lines}",
        f"- email_dry_run_count: {email_count}",
        f"- dedupe_keys: {len(dedupe_keys)}",
        "",
        f"- output_json: `{out_json}`",
    ]
    out_md.write_text("\n".join(lines) + "\n")

    print(f"[done] selftest_json={out_json}")
    print(f"[done] selftest_md={out_md}")
    print(f"[done] overall_pass={overall_pass}")
    raise SystemExit(0 if overall_pass else 2)


if __name__ == "__main__":
    main()
