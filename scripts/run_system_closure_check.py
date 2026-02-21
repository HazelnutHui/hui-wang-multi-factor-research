#!/usr/bin/env python3
"""Run end-of-phase closure checks and produce an audit report."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run(cmd: list[str], cwd: Path) -> dict[str, Any]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return {"cmd": cmd, "rc": int(p.returncode), "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))


def main() -> None:
    ap = argparse.ArgumentParser(description="Run closure checks for auto-research system.")
    ap.add_argument("--out-dir", default="")
    ap.add_argument("--skip-alert-selftest", action="store_true")
    args = ap.parse_args()

    root = Path(".").resolve()
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path(args.out_dir).resolve() if args.out_dir else (root / "audit" / "system_closure" / f"{ts}_closure")
    out_dir.mkdir(parents=True, exist_ok=True)

    checks: dict[str, Any] = {}

    checks["handoff_readiness"] = _run([sys.executable, "scripts/check_session_handoff_readiness.py"], root)
    if args.skip_alert_selftest:
        checks["scheduler_alert_selftest"] = {"skipped": True, "rc": 0}
    else:
        checks["scheduler_alert_selftest"] = _run([sys.executable, "scripts/test_scheduler_alert_channels.py"], root)

    pass_flags = []
    for k, v in checks.items():
        if isinstance(v, dict) and v.get("skipped"):
            continue
        pass_flags.append(int(v.get("rc", 1)) == 0)
    overall_pass = all(pass_flags) if pass_flags else True

    payload = {
        "generated_at": dt.datetime.now().isoformat(),
        "root_dir": str(root),
        "checks": checks,
        "overall_pass": overall_pass,
    }
    out_json = out_dir / "system_closure_report.json"
    out_md = out_dir / "system_closure_report.md"
    _write_json(out_json, payload)

    lines = [
        "# System Closure Report",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- overall_pass: {overall_pass}",
        f"- out_dir: `{out_dir}`",
        "",
        "## Checks",
        "",
    ]
    for k, v in checks.items():
        if isinstance(v, dict) and v.get("skipped"):
            lines.append(f"- {k}: skipped")
        else:
            lines.append(f"- {k}: rc={v.get('rc')}")
    lines += ["", f"- output_json: `{out_json}`"]
    out_md.write_text("\n".join(lines) + "\n")

    print(f"[done] closure_json={out_json}")
    print(f"[done] closure_md={out_md}")
    print(f"[done] overall_pass={overall_pass}")
    raise SystemExit(0 if overall_pass else 2)


if __name__ == "__main__":
    main()
