#!/usr/bin/env python3
"""Finalize a production gate run into stage audit ledger (non-destructive)."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _append_stage_log(stage_log: Path, row_cells: list[str]) -> None:
    text = stage_log.read_text() if stage_log.exists() else ""
    lines = text.splitlines()
    header = "| date | stage | decision_tag | owner | objective | command_ref | artifact_ref | result | next_action |"
    sep = "|---|---|---|---|---|---|---|---|---|"
    if header not in text:
        lines.extend([
            "# Stage Audit Log",
            "",
            f"Last updated: {dt.date.today().isoformat()}",
            "",
            "## Ledger",
            "",
            header,
            sep,
        ])
    entry = "| " + " | ".join(row_cells) + " |"
    if entry not in lines:
        insert_idx = len(lines)
        for i, ln in enumerate(lines):
            if ln.strip().startswith("## Update Rule"):
                insert_idx = i
                break
        lines.insert(insert_idx, entry)
    stage_log.write_text("\n".join(lines) + "\n")


def _fmt_num(v) -> str:
    try:
        if v is None:
            return "null"
        fv = float(v)
        if math.isnan(fv):
            return "nan"
        return f"{fv:.6f}"
    except Exception:
        return str(v)


def _write_summary_md(path: Path, ctx: dict, rep: dict, decision_tag: str, owner: str, result: str) -> None:
    gates = rep.get("gates") or rep.get("gate") or {}
    wf = rep.get("wf_stress") or {}
    cost_rows = rep.get("cost_stress") or []
    lines = [
        f"# Gate Final Summary ({decision_tag})",
        "",
        f"- date: {dt.date.today().isoformat()}",
        f"- owner: {owner}",
        f"- result: {result}",
        f"- run_dir: `{ctx.get('run_dir', 'unknown')}`",
        "",
        "## Key Metrics",
        "",
        f"- wf_test_ic_mean: {_fmt_num(wf.get('test_ic_mean'))}",
        f"- wf_test_ic_pos_ratio: {_fmt_num(wf.get('test_ic_pos_ratio'))}",
        f"- wf_test_ic_n: {_fmt_num(wf.get('test_ic_n'))}",
        "",
        "## Cost Stress",
        "",
    ]
    if cost_rows:
        for r in cost_rows:
            lines.append(
                f"- x{r.get('cost_multiplier')}: return_code={r.get('return_code')}, test_ic={_fmt_num(r.get('test_ic'))}"
            )
    else:
        lines.append("- no cost rows found")

    lines.extend([
        "",
        "## Gate Booleans",
        "",
    ])
    if gates:
        for k in sorted(gates.keys()):
            lines.append(f"- {k}: {gates.get(k)}")
    else:
        lines.append("- no gate booleans found")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description="Finalize production gate run and append stage audit row.")
    p.add_argument("--run-dir", required=True, help="workstation run dir (audit/workstation_runs/<...>)")
    p.add_argument("--report-json", required=True, help="production_gates_report.json path")
    p.add_argument("--stage-log", default="docs/production_research/STAGE_AUDIT_LOG.md")
    p.add_argument("--objective", default="S3 production gates official rerun")
    p.add_argument("--summary-md", default="", help="Optional output markdown summary path")
    args = p.parse_args()

    run_dir = Path(args.run_dir)
    report_json = Path(args.report_json)
    stage_log = Path(args.stage_log)

    ctx = _read_json(run_dir / "context.json") if (run_dir / "context.json").exists() else {}
    rep = _read_json(report_json)

    decision_tag = str(ctx.get("decision_tag") or rep.get("args", {}).get("decision_tag") or "unknown")
    owner = str(ctx.get("owner") or rep.get("args", {}).get("owner") or "")
    overall = (rep.get("gates") or rep.get("gate") or {}).get("overall_pass")
    result = "pass" if bool(overall) else "fail"

    command_ref = str((run_dir / "command.sh").as_posix())
    artifact_ref = str(report_json.as_posix())
    next_action = "promote to next stage" if result == "pass" else "review failed gate components and rerun"

    row = [
        dt.date.today().isoformat(),
        "S3 Production Gates",
        decision_tag,
        owner,
        args.objective,
        f"`{command_ref}`",
        f"`{artifact_ref}`",
        result,
        next_action,
    ]
    _append_stage_log(stage_log, row)
    print(f"updated: {stage_log}")

    summary_md = Path(args.summary_md) if args.summary_md else report_json.with_name("production_gates_final_summary.md")
    ctx["run_dir"] = str(run_dir.as_posix())
    _write_summary_md(summary_md, ctx, rep, decision_tag, owner, result)
    print(f"updated: {summary_md}")


if __name__ == "__main__":
    main()
