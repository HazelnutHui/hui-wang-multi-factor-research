#!/usr/bin/env python3
"""Run multi-round auto-research loop with audit artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))


def _default_policy() -> dict[str, Any]:
    return {
        "max_rounds": 3,
        "max_executions": 1,
        "execute_rank": 1,
        "execute_enabled": False,
        "stop_on_validation_failure": True,
        "stop_on_empty_plan": True,
        "sleep_seconds_between_rounds": 0,
        "dq_input_csv": "data/your_input.csv",
        "candidate_queue": {
            "policy_json": "configs/research/candidate_queue_policy.json",
            "out_csv": "audit/factor_registry/factor_candidate_queue.csv",
            "out_md": "audit/factor_registry/factor_candidate_queue.md",
        },
        "next_run_plan": {
            "out_json": "audit/factor_registry/next_run_plan.json",
            "out_md": "audit/factor_registry/next_run_plan.md",
            "fixed_out_json": "audit/factor_registry/next_run_plan_fixed.json",
            "fixed_out_md": "audit/factor_registry/next_run_plan_fixed.md",
        },
    }


def _load_policy(path: Path | None) -> dict[str, Any]:
    out = _default_policy()
    if path is None or not path.exists():
        return out
    try:
        loaded = json.loads(path.read_text())
        if not isinstance(loaded, dict):
            return out
        out.update({k: v for k, v in loaded.items() if k in out and not isinstance(out[k], dict)})
        for k in ["candidate_queue", "next_run_plan"]:
            if isinstance(loaded.get(k), dict):
                out[k].update(loaded[k])
    except Exception:
        return out
    return out


def _run(cmd: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return {
        "cmd": cmd,
        "rc": int(proc.returncode),
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def _parse_plan_commands(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        obj = _read_json(path)
        rows = obj.get("commands") or []
        if isinstance(rows, list):
            return [r for r in rows if isinstance(r, dict)]
    except Exception:
        return []
    return []


def _write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Auto Research Orchestrator Run",
        "",
        f"- generated_at: {payload.get('generated_at','')}",
        f"- root_dir: `{payload.get('root_dir','')}`",
        f"- execute_enabled: {payload.get('execute_enabled', False)}",
        f"- max_rounds: {payload.get('max_rounds', 0)}",
        f"- max_executions: {payload.get('max_executions', 0)}",
        f"- rounds_completed: {payload.get('rounds_completed', 0)}",
        f"- executions_done: {payload.get('executions_done', 0)}",
        f"- stopped_reason: {payload.get('stopped_reason','')}",
        "",
        "## Round Summary",
        "",
        "| round | queue_rc | plan_rc | repair_rc | validate_rc | execute_rc | selected_factor | selected_tag |",
        "|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for rr in payload.get("rounds", []):
        lines.append(
            f"| {rr.get('round')} | {rr.get('queue_rc')} | {rr.get('plan_rc')} | {rr.get('repair_rc')} | "
            f"{rr.get('validate_rc')} | {rr.get('execute_rc')} | {rr.get('selected_factor','')} | {rr.get('selected_tag','')} |"
        )
    lines += ["", f"- output_json: `{payload.get('output_json','')}`"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description="Auto research orchestrator with audit trail.")
    p.add_argument("--policy-json", default="configs/research/auto_research_policy.json")
    p.add_argument("--max-rounds", type=int, default=0)
    p.add_argument("--max-executions", type=int, default=0)
    p.add_argument("--execute", action="store_true", help="Actually execute selected run command.")
    p.add_argument("--out-dir", default="")
    args = p.parse_args()

    root = Path(".").resolve()
    policy = _load_policy(Path(args.policy_json).resolve() if args.policy_json else None)
    max_rounds = int(args.max_rounds) if int(args.max_rounds) > 0 else int(policy.get("max_rounds", 3))
    max_executions = int(args.max_executions) if int(args.max_executions) > 0 else int(policy.get("max_executions", 1))
    execute_enabled = bool(policy.get("execute_enabled", False)) or bool(args.execute)
    execute_rank = int(policy.get("execute_rank", 1))
    stop_on_validation_failure = bool(policy.get("stop_on_validation_failure", True))
    stop_on_empty_plan = bool(policy.get("stop_on_empty_plan", True))
    sleep_secs = int(policy.get("sleep_seconds_between_rounds", 0))
    dq_input_csv = str(policy.get("dq_input_csv", "data/your_input.csv"))
    cqp = policy.get("candidate_queue") or {}
    npp = policy.get("next_run_plan") or {}

    ts = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path(args.out_dir).resolve() if args.out_dir else (root / "audit" / "auto_research" / f"{ts}_orchestrator")
    out_dir.mkdir(parents=True, exist_ok=True)

    rounds: list[dict[str, Any]] = []
    executions_done = 0
    stopped_reason = "max_rounds_reached"

    for r in range(1, max_rounds + 1):
        rr: dict[str, Any] = {"round": r}

        queue_cmd = [
            sys.executable,
            "scripts/generate_candidate_queue.py",
            "--policy-json",
            str(cqp.get("policy_json", "configs/research/candidate_queue_policy.json")),
            "--out-csv",
            str(cqp.get("out_csv", "audit/factor_registry/factor_candidate_queue.csv")),
            "--out-md",
            str(cqp.get("out_md", "audit/factor_registry/factor_candidate_queue.md")),
        ]
        q = _run(queue_cmd, root)
        rr["queue_rc"] = q["rc"]
        rr["queue_stdout"] = q["stdout"]
        rr["queue_stderr"] = q["stderr"]
        if q["rc"] != 0:
            stopped_reason = "candidate_queue_failed"
            rounds.append(rr)
            break

        plan_cmd = [
            sys.executable,
            "scripts/generate_next_run_plan.py",
            "--dq-input-csv",
            dq_input_csv,
            "--out-json",
            str(npp.get("out_json", "audit/factor_registry/next_run_plan.json")),
            "--out-md",
            str(npp.get("out_md", "audit/factor_registry/next_run_plan.md")),
        ]
        gp = _run(plan_cmd, root)
        rr["plan_rc"] = gp["rc"]
        rr["plan_stdout"] = gp["stdout"]
        rr["plan_stderr"] = gp["stderr"]
        if gp["rc"] != 0:
            stopped_reason = "next_run_plan_failed"
            rounds.append(rr)
            break

        repair_cmd = [
            sys.executable,
            "scripts/repair_next_run_plan_paths.py",
            "--plan-json",
            str(npp.get("out_json", "audit/factor_registry/next_run_plan.json")),
            "--out-json",
            str(npp.get("fixed_out_json", "audit/factor_registry/next_run_plan_fixed.json")),
            "--out-md",
            str(npp.get("fixed_out_md", "audit/factor_registry/next_run_plan_fixed.md")),
            "--dq-input-csv",
            dq_input_csv,
        ]
        rp = _run(repair_cmd, root)
        rr["repair_rc"] = rp["rc"]
        rr["repair_stdout"] = rp["stdout"]
        rr["repair_stderr"] = rp["stderr"]
        if rp["rc"] != 0:
            stopped_reason = "repair_plan_failed"
            rounds.append(rr)
            break

        fixed_plan = (root / str(npp.get("fixed_out_json", "audit/factor_registry/next_run_plan_fixed.json"))).resolve()
        commands = _parse_plan_commands(fixed_plan)
        if not commands:
            rr["validate_rc"] = 0
            rr["execute_rc"] = 0
            stopped_reason = "empty_plan"
            rounds.append(rr)
            if stop_on_empty_plan:
                break
            continue
        rank = max(1, min(execute_rank, len(commands)))
        selected = commands[rank - 1]
        rr["selected_factor"] = str(selected.get("factor", ""))
        rr["selected_tag"] = str(selected.get("proposed_decision_tag", ""))

        validate_cmd = [
            sys.executable,
            "scripts/execute_next_run_plan.py",
            "--plan-json",
            str(fixed_plan),
            "--rank",
            str(rank),
            "--dry-run",
        ]
        vd = _run(validate_cmd, root)
        rr["validate_rc"] = vd["rc"]
        rr["validate_stdout"] = vd["stdout"]
        rr["validate_stderr"] = vd["stderr"]
        if vd["rc"] != 0:
            rr["execute_rc"] = -1
            rounds.append(rr)
            stopped_reason = "validation_failed"
            if stop_on_validation_failure:
                break
            continue

        if execute_enabled and executions_done < max_executions:
            exe_cmd = [
                sys.executable,
                "scripts/execute_next_run_plan.py",
                "--plan-json",
                str(fixed_plan),
                "--rank",
                str(rank),
            ]
            ex = _run(exe_cmd, root)
            rr["execute_rc"] = ex["rc"]
            rr["execute_stdout"] = ex["stdout"]
            rr["execute_stderr"] = ex["stderr"]
            executions_done += 1
            if ex["rc"] != 0:
                stopped_reason = "execution_failed"
                rounds.append(rr)
                break
        else:
            rr["execute_rc"] = 0
            rr["execute_stdout"] = "execution skipped (safe mode)"
            rr["execute_stderr"] = ""

        rounds.append(rr)
        if executions_done >= max_executions and execute_enabled:
            stopped_reason = "execution_budget_reached"
            break
        if sleep_secs > 0 and r < max_rounds:
            time.sleep(sleep_secs)

    payload = {
        "generated_at": dt.datetime.now().isoformat(),
        "root_dir": str(root),
        "policy_json": str(Path(args.policy_json).resolve()) if args.policy_json else "",
        "execute_enabled": execute_enabled,
        "max_rounds": max_rounds,
        "max_executions": max_executions,
        "rounds_completed": len(rounds),
        "executions_done": executions_done,
        "stopped_reason": stopped_reason,
        "rounds": rounds,
    }
    out_json = out_dir / "auto_research_orchestrator_report.json"
    out_md = out_dir / "auto_research_orchestrator_report.md"
    payload["output_json"] = str(out_json)
    _write_json(out_json, payload)
    _write_md(out_md, payload)
    print(f"[done] orchestrator_json={out_json}")
    print(f"[done] orchestrator_md={out_md}")
    print(f"[done] stopped_reason={stopped_reason} rounds={len(rounds)} executions={executions_done}")

    bad = {"candidate_queue_failed", "next_run_plan_failed", "repair_plan_failed", "validation_failed", "execution_failed"}
    raise SystemExit(2 if stopped_reason in bad else 0)


if __name__ == "__main__":
    main()
