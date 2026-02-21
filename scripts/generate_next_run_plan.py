#!/usr/bin/env python3
"""Generate next-run execution plan from candidate queue + remediation artifacts."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _load_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"csv not found: {path}")
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _latest(path_glob: str) -> Path | None:
    cands = sorted(Path(".").glob(path_glob), key=lambda p: p.stat().st_mtime)
    return cands[-1] if cands else None


def _domain_hypothesis(domain: str) -> str:
    d = domain.lower()
    if d == "consistency":
        return "Execution metadata must be single-source consistent across context/report/registry."
    if d == "dataquality":
        return "Input data contract and freshness failures are the primary source of false promotion decisions."
    if d == "runtime":
        return "Runtime instability and partial artifact writes are blocking reproducible decisions."
    if d == "artifacts":
        return "Missing audit artifacts invalidate otherwise strong quantitative results."
    if d == "ledger":
        return "Ledger linkage gaps break downstream governance automation."
    return "Investigate failure and convert to explicit control before rerun."


def _replace_dq_input(cmd: str, dq_input_csv: str) -> str:
    if "--dq-input-csv" not in cmd:
        return f"{cmd} --dq-input-csv {dq_input_csv}"
    parts = cmd.split("--dq-input-csv", 1)
    tail = parts[1].strip().split(maxsplit=1)
    if not tail:
        return cmd
    if len(tail) == 1:
        return f"{parts[0]}--dq-input-csv {dq_input_csv}"
    return f"{parts[0]}--dq-input-csv {dq_input_csv} {tail[1]}"


def main() -> None:
    p = argparse.ArgumentParser(description="Generate next official rerun plan.")
    p.add_argument("--queue-csv", default="audit/factor_registry/factor_candidate_queue.csv")
    p.add_argument("--remediation-json", default="")
    p.add_argument("--report-json", default="")
    p.add_argument("--dq-input-csv", default="data/your_input.csv")
    p.add_argument("--out-json", default="audit/factor_registry/next_run_plan.json")
    p.add_argument("--out-md", default="audit/factor_registry/next_run_plan.md")
    args = p.parse_args()

    queue_csv = Path(args.queue_csv).resolve()
    queue = _load_csv(queue_csv)
    remediation_json = (
        Path(args.remediation_json).resolve()
        if args.remediation_json
        else _latest("audit/workstation_runs/*/governance_remediation_plan.json")
    )
    report_json = (
        Path(args.report_json).resolve()
        if args.report_json
        else _latest("gate_results/production_gates_*/production_gates_report.json")
    )

    remediation = _read_json(remediation_json) if remediation_json and remediation_json.exists() else {}
    report = _read_json(report_json) if report_json and report_json.exists() else {}
    gates = report.get("gates") or report.get("gate") or {}

    high_items = [x for x in (remediation.get("remediation_items") or []) if str(x.get("severity")) == "High"]
    hypotheses = []
    for it in high_items:
        hypotheses.append(
            {
                "domain": it.get("domain"),
                "hypothesis": _domain_hypothesis(str(it.get("domain", ""))),
                "action": it.get("action"),
            }
        )

    gate_failures = [k for k, v in gates.items() if k != "overall_pass" and v is False]

    commands = []
    for i, row in enumerate(queue, start=1):
        cmd = str(row.get("proposed_command") or "").strip()
        if not cmd:
            continue
        cmd = _replace_dq_input(cmd, args.dq_input_csv)
        commands.append(
            {
                "rank": i,
                "factor": row.get("factor"),
                "source_decision_tag": row.get("source_decision_tag"),
                "proposed_decision_tag": row.get("proposed_decision_tag"),
                "suggested_action": row.get("suggested_action"),
                "priority_score": row.get("priority_score"),
                "command": cmd,
            }
        )

    payload = {
        "generated_at": dt.datetime.now().isoformat(),
        "source_queue_csv": str(queue_csv),
        "source_remediation_json": str(remediation_json) if remediation_json else "",
        "source_report_json": str(report_json) if report_json else "",
        "gate_failures": gate_failures,
        "high_severity_remediations": high_items,
        "next_run_hypotheses": hypotheses,
        "commands": commands,
    }

    out_json = Path(args.out_json).resolve()
    out_md = Path(args.out_md).resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=True))

    lines = [
        "# Next Run Plan",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- source_queue_csv: `{queue_csv}`",
        f"- source_remediation_json: `{payload['source_remediation_json']}`",
        f"- source_report_json: `{payload['source_report_json']}`",
        "",
        "## Gate Failures",
        "",
    ]
    if gate_failures:
        for g in gate_failures:
            lines.append(f"- {g}")
    else:
        lines.append("- none")
    lines += ["", "## High Severity Remediations", ""]
    if high_items:
        for it in high_items:
            lines.append(f"- [{it.get('domain')}] {it.get('failure')} -> {it.get('action')}")
    else:
        lines.append("- none")
    lines += ["", "## Hypotheses", ""]
    if hypotheses:
        for h in hypotheses:
            lines.append(f"- [{h.get('domain')}] {h.get('hypothesis')}")
    else:
        lines.append("- none")
    lines += ["", "## Commands", ""]
    if commands:
        for c in commands:
            lines.append(
                f"- rank {c['rank']} `{c['factor']}` ({c['suggested_action']}, priority={c['priority_score']}): `{c['command']}`"
            )
    else:
        lines.append("- none")
    lines += ["", f"- output_json: `{out_json}`"]
    out_md.write_text("\n".join(lines) + "\n")
    print(f"[done] next_run_plan_json={out_json}")
    print(f"[done] next_run_plan_md={out_md}")


if __name__ == "__main__":
    main()
