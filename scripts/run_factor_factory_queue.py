#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _pybin() -> str:
    v = ROOT / ".venv" / "bin" / "python"
    if v.exists():
        return str(v)
    return "python3"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))


def _extract_run_dir(stdout_text: str) -> str | None:
    for line in stdout_text.splitlines():
        s = line.strip()
        if s.startswith("[done] run_dir="):
            return s.split("=", 1)[1].strip()
    return None


def _write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Factor Factory Queue Report",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- queue_json: `{payload.get('queue_json')}`",
        f"- queue_name: `{payload.get('queue_name')}`",
        f"- jobs: {payload.get('jobs')}",
        f"- repeat: {payload.get('repeat')}",
        f"- cycles_completed: {payload.get('cycles_completed')}",
        "",
        "## Items",
        "",
        "| idx | cycle | tag | policy_json | return_code | run_dir | log_path |",
        "|---:|---:|---|---|---:|---|---|",
    ]
    for i, row in enumerate(payload.get("records", []), start=1):
        lines.append(
            f"| {i} | {row.get('cycle')} | {row.get('tag')} | "
            f"`{row.get('policy_json')}` | {row.get('return_code')} | "
            f"`{row.get('run_dir')}` | `{row.get('log_path')}` |"
        )
    if len(payload.get("records", [])) == 0:
        lines.append("| - | - | - | - | - | - | - |")
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Run queued factor-factory policies sequentially.")
    ap.add_argument(
        "--queue-json",
        required=True,
        help="Queue definition JSON path (relative to project root allowed).",
    )
    ap.add_argument(
        "--approval-json",
        default="configs/research/factory_queue/run_approval.json",
        help="Approval JSON path. Queue run is blocked unless this file explicitly approves the target queue.",
    )
    ap.add_argument("--jobs", type=int, default=8, help="Parallel workers per batch.")
    ap.add_argument("--repeat", action="store_true", help="Repeat queue cycles indefinitely.")
    ap.add_argument("--sleep-sec", type=float, default=5.0, help="Sleep between queue items.")
    ap.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue queue execution even when one item fails.",
    )
    args = ap.parse_args()

    queue_path = (ROOT / args.queue_json).resolve()
    if not queue_path.exists():
        raise SystemExit(f"queue not found: {queue_path}")

    approval_path = (ROOT / args.approval_json).resolve()
    if not approval_path.exists():
        raise SystemExit(
            f"approval file not found: {approval_path}. "
            "Create approval json with approved=true and approved_queue matching --queue-json."
        )
    approval = _read_json(approval_path)
    approved = bool(approval.get("approved", False))
    approved_queue = str(approval.get("approved_queue", "")).strip()
    queue_rel = str(queue_path.relative_to(ROOT))
    if (not approved) or (approved_queue != queue_rel):
        raise SystemExit(
            "queue run blocked by approval gate: "
            f"approved={approved}, approved_queue='{approved_queue}', target_queue='{queue_rel}'."
        )

    queue = _read_json(queue_path)
    items = queue.get("items") if isinstance(queue.get("items"), list) else []
    if not items:
        raise SystemExit("queue has no items")

    queue_name = str(queue.get("name", "queue")).strip() or "queue"
    repeat = bool(args.repeat or bool(queue.get("repeat", False)))
    continue_on_error = bool(args.continue_on_error or bool(queue.get("continue_on_error", False)))
    sleep_sec = float(queue.get("sleep_sec", args.sleep_sec))
    jobs = max(1, int(args.jobs))

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = (ROOT / "audit" / "factor_factory_queue" / f"{ts}_{queue_name}").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    cycle = 0
    py = _pybin()
    batch_runner = ROOT / "scripts" / "run_factor_factory_batch.py"

    while True:
        cycle += 1
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            rel_policy = str(item.get("policy_json", "")).strip()
            if not rel_policy:
                continue
            policy_path = (ROOT / rel_policy).resolve()
            if not policy_path.exists():
                rc = 2
                run_dir = None
                log_path = str((out_dir / f"cycle{cycle:03d}_item{idx:03d}.log").resolve())
                Path(log_path).write_text(f"policy not found: {policy_path}\n")
            else:
                tag = str(item.get("tag", f"item_{idx:03d}"))
                max_candidates = item.get("max_candidates")
                cmd = [
                    py,
                    str(batch_runner),
                    "--policy-json",
                    str(policy_path.relative_to(ROOT)),
                    "--jobs",
                    str(jobs),
                ]
                if max_candidates is not None:
                    cmd += ["--max-candidates", str(int(max_candidates))]
                if bool(item.get("dry_run", False)):
                    cmd += ["--dry-run"]
                if item.get("seed") is not None:
                    cmd += ["--seed", str(int(item.get("seed")))]

                log_file = (out_dir / f"cycle{cycle:03d}_item{idx:03d}_{tag}.log").resolve()
                with open(log_file, "w") as f:
                    proc = subprocess.run(
                        cmd,
                        cwd=str(ROOT),
                        stdout=f,
                        stderr=subprocess.STDOUT,
                    )
                rc = int(proc.returncode)
                text = log_file.read_text(errors="ignore")
                run_dir = _extract_run_dir(text)
                log_path = str(log_file)

            rec = {
                "cycle": cycle,
                "index": idx,
                "tag": str(item.get("tag", f"item_{idx:03d}")),
                "policy_json": rel_policy,
                "return_code": rc,
                "run_dir": run_dir,
                "log_path": log_path,
            }
            records.append(rec)

            payload = {
                "generated_at": datetime.now().isoformat(),
                "queue_json": str(queue_path),
                "queue_name": queue_name,
                "jobs": jobs,
                "repeat": repeat,
                "continue_on_error": continue_on_error,
                "cycles_completed": cycle if idx == len(items) else cycle - 1,
                "records": records,
                "out_dir": str(out_dir),
            }
            _write_json(out_dir / "factor_factory_queue_report.json", payload)
            _write_md(out_dir / "factor_factory_queue_report.md", payload)

            if rc != 0 and not continue_on_error:
                raise SystemExit(f"queue stopped on failure: cycle={cycle} idx={idx} tag={rec['tag']}")
            if sleep_sec > 0:
                time.sleep(sleep_sec)

        if not repeat:
            break

    print(f"[done] out_dir={out_dir}")
    print(f"[done] report_json={out_dir / 'factor_factory_queue_report.json'}")
    print(f"[done] report_md={out_dir / 'factor_factory_queue_report.md'}")


if __name__ == "__main__":
    main()
