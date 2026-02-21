#!/usr/bin/env python3
"""Periodic scheduler for auto research orchestrator with audit trail."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


def _default_policy() -> dict[str, Any]:
    return {
        "interval_seconds": 3600,
        "max_cycles": 0,
        "stop_on_orchestrator_failure": True,
        "orchestrator_policy_json": "configs/research/auto_research_policy.json",
        "orchestrator_execute": False,
        "lock_file": "audit/auto_research/auto_research_scheduler.lock",
        "heartbeat_json": "audit/auto_research/auto_research_scheduler_heartbeat.json",
        "ledger_csv": "audit/auto_research/auto_research_scheduler_ledger.csv",
        "ledger_md": "audit/auto_research/auto_research_scheduler_ledger.md",
        "alert_on_failure": False,
        "alert_state_json": "audit/auto_research/auto_research_scheduler_alert_state.json",
        "alert_dedupe_window_seconds": 1800,
        "alert_webhook_url": "",
        "alert_webhook_timeout_seconds": 10,
        "alert_recent_failures_limit": 5,
        "alert_command": "",
    }


def _load_policy(path: Path | None) -> dict[str, Any]:
    out = _default_policy()
    if path is None or not path.exists():
        return out
    try:
        obj = json.loads(path.read_text())
        if isinstance(obj, dict):
            out.update({k: v for k, v in obj.items() if k in out})
    except Exception:
        return out
    return out


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _write_csv_rows(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def _write_ledger_md(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Auto Research Scheduler Ledger",
        "",
        f"- updated_at: {dt.datetime.now().isoformat()}",
        f"- rows: {len(rows)}",
        "",
        "| cycle | started_at | ended_at | rc | run_dir | stopped_reason |",
        "|---:|---|---|---:|---|---|",
    ]
    for r in reversed(rows[-100:]):
        lines.append(
            f"| {r.get('cycle','')} | {r.get('started_at','')} | {r.get('ended_at','')} | {r.get('rc','')} | "
            f"`{r.get('run_dir','')}` | {r.get('stopped_reason','')} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def _acquire_lock(lock_file: Path) -> None:
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("ascii", errors="ignore"))
        os.close(fd)
    except FileExistsError:
        raise SystemExit(f"scheduler lock exists: {lock_file}")


def _release_lock(lock_file: Path) -> None:
    try:
        lock_file.unlink(missing_ok=True)
    except Exception:
        pass


def _run_orchestrator(root: Path, orchestrator_policy_json: str, execute: bool) -> dict[str, Any]:
    cmd = [sys.executable, "scripts/auto_research_orchestrator.py", "--policy-json", orchestrator_policy_json]
    if execute:
        cmd.append("--execute")
    proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
    run_dir = ""
    report_json = ""
    stopped_reason = ""
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("[done] orchestrator_json="):
            p = line.split("=", 1)[1].strip()
            report_json = str(Path(p).resolve())
            run_dir = str(Path(p).resolve().parent)
        if line.startswith("[done] stopped_reason="):
            rest = line.split("=", 1)[1]
            stopped_reason = rest.split(" ", 1)[0].strip()
    return {
        "cmd": cmd,
        "rc": int(proc.returncode),
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "run_dir": run_dir,
        "report_json": report_json,
        "stopped_reason": stopped_reason,
    }


def _recent_failures(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    bad = {"candidate_queue_failed", "next_run_plan_failed", "repair_plan_failed", "validation_failed", "execution_failed"}
    for r in reversed(rows):
        if str(r.get("stopped_reason", "")) in bad or str(r.get("rc", "")) not in {"0", "0.0", ""}:
            out.append(
                {
                    "cycle": r.get("cycle", ""),
                    "started_at": r.get("started_at", ""),
                    "ended_at": r.get("ended_at", ""),
                    "rc": r.get("rc", ""),
                    "run_dir": r.get("run_dir", ""),
                    "stopped_reason": r.get("stopped_reason", ""),
                }
            )
        if len(out) >= max(1, int(limit)):
            break
    return out


def _maybe_alert(
    policy: dict[str, Any],
    msg: str,
    root: Path,
    *,
    dedupe_key: str = "",
    payload: dict[str, Any] | None = None,
) -> None:
    if not bool(policy.get("alert_on_failure", False)):
        return
    state_path = (root / str(policy.get("alert_state_json", "audit/auto_research/auto_research_scheduler_alert_state.json"))).resolve()
    dedupe_window = max(0, int(policy.get("alert_dedupe_window_seconds", 1800)))
    now = int(time.time())
    alert_key = dedupe_key.strip() if dedupe_key.strip() else msg
    state: dict[str, Any] = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text())
        except Exception:
            state = {}
    key_map = state.get("keys") if isinstance(state.get("keys"), dict) else {}
    last_ts = int(key_map.get(alert_key, 0)) if str(key_map.get(alert_key, "")).strip() else 0
    if dedupe_window > 0 and (now - last_ts) < dedupe_window:
        return

    sent_any = False
    payload_obj = payload or {}
    webhook_url = str(policy.get("alert_webhook_url", "")).strip()
    if webhook_url:
        webhook_payload = {
            "timestamp": dt.datetime.now().isoformat(),
            "source": "auto_research_scheduler",
            "event_type": "scheduler_orchestrator_failure",
            "message": msg,
            "dedupe_window_seconds": dedupe_window,
            "payload": payload_obj,
        }
        body = json.dumps(webhook_payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            timeout = max(1, int(policy.get("alert_webhook_timeout_seconds", 10)))
            with urllib.request.urlopen(req, timeout=timeout):
                pass
            sent_any = True
        except Exception:
            sent_any = False

    cmd = str(policy.get("alert_command", "")).strip()
    if cmd:
        env = os.environ.copy()
        env["AUTO_RESEARCH_ALERT_MSG"] = msg
        env["AUTO_RESEARCH_ALERT_JSON"] = json.dumps(payload_obj, ensure_ascii=True)
        rc = subprocess.run(cmd, cwd=str(root), env=env, shell=True, check=False).returncode
        sent_any = sent_any or (rc == 0)

    if sent_any:
        key_map[alert_key] = now
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"updated_at": dt.datetime.now().isoformat(), "keys": key_map}, indent=2, ensure_ascii=True))


def main() -> None:
    p = argparse.ArgumentParser(description="Periodic scheduler for auto research orchestrator.")
    p.add_argument("--policy-json", default="configs/research/auto_research_scheduler_policy.json")
    p.add_argument("--interval-seconds", type=int, default=0)
    p.add_argument("--max-cycles", type=int, default=0)
    p.add_argument("--run-once", action="store_true")
    args = p.parse_args()

    root = Path(".").resolve()
    policy = _load_policy(Path(args.policy_json).resolve() if args.policy_json else None)
    interval_seconds = int(args.interval_seconds) if int(args.interval_seconds) > 0 else int(policy.get("interval_seconds", 3600))
    max_cycles = int(args.max_cycles) if int(args.max_cycles) > 0 else int(policy.get("max_cycles", 0))
    if args.run_once:
        max_cycles = 1
    stop_on_fail = bool(policy.get("stop_on_orchestrator_failure", True))
    orchestrator_policy_json = str(policy.get("orchestrator_policy_json", "configs/research/auto_research_policy.json"))
    orchestrator_execute = bool(policy.get("orchestrator_execute", False))
    lock_file = (root / str(policy.get("lock_file", "audit/auto_research/auto_research_scheduler.lock"))).resolve()
    heartbeat_json = (root / str(policy.get("heartbeat_json", "audit/auto_research/auto_research_scheduler_heartbeat.json"))).resolve()
    ledger_csv = (root / str(policy.get("ledger_csv", "audit/auto_research/auto_research_scheduler_ledger.csv"))).resolve()
    ledger_md = (root / str(policy.get("ledger_md", "audit/auto_research/auto_research_scheduler_ledger.md"))).resolve()

    _acquire_lock(lock_file)
    started = dt.datetime.now().isoformat()
    _write_json(
        heartbeat_json,
        {
            "status": "running",
            "started_at": started,
            "last_heartbeat_at": started,
            "pid": os.getpid(),
            "policy_json": str(Path(args.policy_json).resolve()),
        },
    )

    rows = _read_csv_rows(ledger_csv)
    cycle = 0
    stop_reason = "max_cycles_reached"
    try:
        while True:
            if max_cycles > 0 and cycle >= max_cycles:
                break
            cycle += 1
            started_at = dt.datetime.now().isoformat()
            res = _run_orchestrator(root, orchestrator_policy_json=orchestrator_policy_json, execute=orchestrator_execute)
            ended_at = dt.datetime.now().isoformat()
            row = {
                "cycle": cycle,
                "started_at": started_at,
                "ended_at": ended_at,
                "rc": res["rc"],
                "run_dir": res["run_dir"],
                "report_json": res.get("report_json", ""),
                "stopped_reason": res["stopped_reason"],
                "orchestrator_policy_json": orchestrator_policy_json,
                "orchestrator_execute": str(orchestrator_execute),
            }
            rows.append(row)
            _write_csv_rows(ledger_csv, rows, list(row.keys()))
            _write_ledger_md(ledger_md, rows)
            _write_json(
                heartbeat_json,
                {
                    "status": "running",
                    "started_at": started,
                    "last_heartbeat_at": ended_at,
                    "last_cycle": cycle,
                    "last_cycle_rc": res["rc"],
                    "last_cycle_run_dir": res["run_dir"],
                    "last_cycle_stopped_reason": res["stopped_reason"],
                    "pid": os.getpid(),
                    "policy_json": str(Path(args.policy_json).resolve()),
                },
            )
            print(f"[cycle] {cycle} rc={res['rc']} run_dir={res['run_dir']} stopped_reason={res['stopped_reason']}")
            if int(res["rc"]) != 0:
                stop_reason = "orchestrator_failure"
                recent_limit = int(policy.get("alert_recent_failures_limit", 5))
                alert_payload = {
                    "cycle": cycle,
                    "scheduler_policy_json": str(Path(args.policy_json).resolve()),
                    "orchestrator_policy_json": orchestrator_policy_json,
                    "orchestrator_execute": orchestrator_execute,
                    "rc": res["rc"],
                    "stopped_reason": res["stopped_reason"],
                    "run_dir": res.get("run_dir", ""),
                    "orchestrator_report_json": res.get("report_json", ""),
                    "recent_failures": _recent_failures(rows, limit=recent_limit),
                }
                _maybe_alert(
                    policy,
                    (
                        "auto research scheduler cycle failed "
                        f"(cycle={cycle}, rc={res['rc']}, stopped_reason={res['stopped_reason']})"
                    ),
                    root,
                    dedupe_key=f"orchestrator_failure:rc={res['rc']}:reason={res['stopped_reason']}",
                    payload=alert_payload,
                )
                if stop_on_fail:
                    break
            if max_cycles > 0 and cycle >= max_cycles:
                break
            time.sleep(max(1, int(interval_seconds)))
    finally:
        finished = dt.datetime.now().isoformat()
        _write_json(
            heartbeat_json,
            {
                "status": "stopped",
                "started_at": started,
                "stopped_at": finished,
                "last_heartbeat_at": finished,
                "cycles_completed": cycle,
                "stop_reason": stop_reason,
                "pid": os.getpid(),
                "policy_json": str(Path(args.policy_json).resolve()),
                "ledger_csv": str(ledger_csv),
                "ledger_md": str(ledger_md),
            },
        )
        _release_lock(lock_file)

    print(f"[done] scheduler_heartbeat={heartbeat_json}")
    print(f"[done] scheduler_ledger_csv={ledger_csv}")
    print(f"[done] scheduler_ledger_md={ledger_md}")
    print(f"[done] stop_reason={stop_reason} cycles={cycle}")
    raise SystemExit(0 if stop_reason != "orchestrator_failure" else 2)


if __name__ == "__main__":
    main()
