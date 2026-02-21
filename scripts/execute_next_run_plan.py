#!/usr/bin/env python3
"""Execute one command from next_run_plan.json."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def main() -> None:
    p = argparse.ArgumentParser(description="Execute ranked command from next_run_plan.json.")
    p.add_argument("--plan-json", default="audit/factor_registry/next_run_plan.json")
    p.add_argument("--rank", type=int, default=1, help="1-based command rank to execute")
    p.add_argument("--dry-run", action="store_true")
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

    print(f"[selected] rank={rank} factor={item.get('factor')} suggested_action={item.get('suggested_action')}")
    print(f"[command] {cmd}")
    if args.dry_run:
        raise SystemExit(0)

    rc = subprocess.call(cmd, shell=True)
    raise SystemExit(int(rc))


if __name__ == "__main__":
    main()
