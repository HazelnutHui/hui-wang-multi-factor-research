#!/usr/bin/env python3
"""Execute one command from next_run_plan.json."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _extract_flag(tokens: list[str], flag: str) -> str:
    for i, tok in enumerate(tokens):
        if tok == flag and i + 1 < len(tokens):
            return tokens[i + 1]
    return ""


def _has_token(tokens: list[str], token: str) -> bool:
    return any(t == token for t in tokens)


def _validate_command(cmd: str, allow_placeholder_dq: bool) -> list[str]:
    errs: list[str] = []
    try:
        tokens = shlex.split(cmd)
    except Exception as e:
        return [f"command parse failed: {e}"]

    if "workstation_official_run.sh" not in cmd:
        errs.append("command does not use workstation_official_run.sh")
    if not _has_token(tokens, "--workflow"):
        errs.append("missing --workflow")
    if _extract_flag(tokens, "--workflow") != "production_gates":
        errs.append("workflow is not production_gates")

    tag = _extract_flag(tokens, "--tag")
    if not tag:
        errs.append("missing --tag")
    else:
        existing = sorted(Path("audit/workstation_runs").glob(f"*{tag}*")) if Path("audit/workstation_runs").exists() else []
        if existing:
            errs.append(f"decision_tag already exists in audit/workstation_runs: {tag}")

    freeze_file = _extract_flag(tokens, "--freeze-file")
    if not freeze_file:
        errs.append("missing --freeze-file")
    else:
        p = Path(freeze_file).expanduser()
        if not p.is_absolute():
            p = (Path(".").resolve() / p).resolve()
        if not p.exists():
            errs.append(f"freeze-file not found: {p}")

    dq_input = _extract_flag(tokens, "--dq-input-csv")
    if not dq_input:
        errs.append("missing --dq-input-csv")
    else:
        if (dq_input == "data/your_input.csv") and not allow_placeholder_dq:
            errs.append("dq-input-csv is still placeholder data/your_input.csv")
        dq = Path(dq_input).expanduser()
        if not dq.is_absolute():
            dq = (Path(".").resolve() / dq).resolve()
        if not dq.exists():
            errs.append(f"dq-input-csv path not found locally: {dq}")
    return errs


def main() -> None:
    p = argparse.ArgumentParser(description="Execute ranked command from next_run_plan.json.")
    p.add_argument("--plan-json", default="audit/factor_registry/next_run_plan.json")
    p.add_argument("--rank", type=int, default=1, help="1-based command rank to execute")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-validation", action="store_true")
    p.add_argument("--allow-placeholder-dq", action="store_true")
    args = p.parse_args()

    plan_json = Path(args.plan_json).resolve()
    if not plan_json.exists():
        raise SystemExit(f"plan json not found: {plan_json}")
    plan = _read_json(plan_json)
    cmds = plan.get("commands") or []
    rank = max(1, int(args.rank))
    if rank > len(cmds):
        raise SystemExit(f"rank {rank} out of range, available={len(cmds)}")
    item = cmds[rank - 1]
    cmd = str(item.get("command") or "").strip()
    if not cmd:
        raise SystemExit(f"empty command at rank {rank}")

    if not args.skip_validation:
        errors = _validate_command(cmd, allow_placeholder_dq=bool(args.allow_placeholder_dq))
        if errors:
            print("[blocked] pre-execution validation failed:")
            for e in errors:
                print(f"- {e}")
            raise SystemExit(2)

    print(f"[selected] rank={rank} factor={item.get('factor')} suggested_action={item.get('suggested_action')}")
    print(f"[command] {cmd}")
    if args.dry_run:
        raise SystemExit(0)

    rc = subprocess.call(cmd, shell=True)
    raise SystemExit(int(rc))


if __name__ == "__main__":
    main()
