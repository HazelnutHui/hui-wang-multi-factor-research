#!/usr/bin/env python3
"""Validate governance artifact completeness for an official production gate run."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _contains_text(path: Path, needle: str) -> bool:
    if not path.exists():
        return False
    try:
        return needle in path.read_text()
    except Exception:
        return False


def main() -> None:
    p = argparse.ArgumentParser(description="Governance audit checker for production gate runs.")
    p.add_argument("--run-dir", required=True, help="audit/workstation_runs/<...>")
    p.add_argument("--report-json", required=True, help="gate_results/.../production_gates_report.json")
    p.add_argument("--stage-log", default="docs/production_research/STAGE_AUDIT_LOG.md")
    p.add_argument("--require-final-summary", action="store_true", default=False)
    args = p.parse_args()

    run_dir = Path(args.run_dir).resolve()
    report_json = Path(args.report_json).resolve()
    stage_log = Path(args.stage_log).resolve()
    report_md = report_json.with_name("production_gates_report.md")
    summary_md = report_json.with_name("production_gates_final_summary.md")

    checks: dict[str, bool] = {}
    details: dict[str, object] = {"run_dir": str(run_dir), "report_json": str(report_json)}
    failures: list[str] = []

    required_run_files = [
        run_dir / "preflight.json",
        run_dir / "context.json",
        run_dir / "command.sh",
        run_dir / "run.log",
        run_dir / "result.json",
    ]
    for f in required_run_files:
        ok = f.exists()
        checks[f"exists::{f.name}"] = ok
        if not ok:
            failures.append(f"missing required run artifact: {f}")

    checks["exists::report_json"] = report_json.exists()
    checks["exists::report_md"] = report_md.exists()
    if not report_json.exists():
        failures.append(f"missing report_json: {report_json}")
    if not report_md.exists():
        failures.append(f"missing report_md: {report_md}")

    if args.require_final_summary:
        checks["exists::final_summary_md"] = summary_md.exists()
        if not summary_md.exists():
            failures.append(f"missing final summary markdown: {summary_md}")

    context = {}
    report = {}
    result = {}
    if (run_dir / "context.json").exists():
        context = _read_json(run_dir / "context.json")
    if report_json.exists():
        report = _read_json(report_json)
    if (run_dir / "result.json").exists():
        result = _read_json(run_dir / "result.json")

    decision_tag_ctx = str(context.get("decision_tag") or "").strip()
    owner_ctx = str(context.get("owner") or "").strip()
    details["decision_tag"] = decision_tag_ctx
    details["owner"] = owner_ctx

    exit_code = result.get("exit_code")
    checks["result_exit_code_zero"] = (exit_code == 0)
    if exit_code != 0:
        failures.append(f"result exit_code is not zero: {exit_code}")

    report_inputs = report.get("inputs") or {}
    decision_tag_report = str(report_inputs.get("decision_tag") or "").strip()
    details["decision_tag_report"] = decision_tag_report
    checks["decision_tag_consistent"] = bool(decision_tag_ctx) and (decision_tag_ctx == decision_tag_report)
    if not checks["decision_tag_consistent"]:
        failures.append(
            f"decision_tag mismatch or missing: context={decision_tag_ctx!r}, report={decision_tag_report!r}"
        )

    gate_obj = report.get("gates") or report.get("gate") or {}
    checks["gates_has_overall_pass"] = "overall_pass" in gate_obj
    if "overall_pass" not in gate_obj:
        failures.append("report missing gates.overall_pass")
    details["overall_pass"] = gate_obj.get("overall_pass")

    dq_skipped = bool(context.get("skip_data_quality_check"))
    dq_report_path_raw = str(context.get("data_quality_report_json") or "").strip()
    details["skip_data_quality_check"] = dq_skipped
    details["data_quality_report_json"] = dq_report_path_raw
    checks["dq_not_skipped"] = not dq_skipped
    if dq_skipped:
        failures.append("data quality check was skipped for this run")

    dq_report_ok = False
    if dq_report_path_raw:
        dq_path = Path(dq_report_path_raw).expanduser()
        if not dq_path.is_absolute():
            dq_path = (run_dir / dq_path).resolve()
        if dq_path.exists():
            dq_obj = _read_json(dq_path)
            dq_report_ok = bool(dq_obj.get("overall_pass"))
            details["data_quality_overall_pass"] = dq_obj.get("overall_pass")
            if not dq_report_ok:
                failures.append(f"data quality report overall_pass is not true: {dq_path}")
        else:
            failures.append(f"data quality report path not found: {dq_path}")
    else:
        failures.append("data quality report path missing in context.json")
    checks["dq_report_pass"] = dq_report_ok

    checks["stage_log_exists"] = stage_log.exists()
    if not stage_log.exists():
        failures.append(f"stage log not found: {stage_log}")
    else:
        checks["stage_log_has_decision_tag"] = bool(decision_tag_ctx) and _contains_text(stage_log, decision_tag_ctx)
        if not checks["stage_log_has_decision_tag"]:
            failures.append(f"stage log missing decision_tag row: {decision_tag_ctx}")

    overall_pass = all(checks.values()) and len(failures) == 0
    audit_payload = {
        "generated_at": dt.datetime.now().isoformat(),
        "checks": checks,
        "details": details,
        "overall_pass": overall_pass,
        "failures": failures,
    }

    out_json = run_dir / "governance_audit_check.json"
    out_md = run_dir / "governance_audit_check.md"
    out_json.write_text(json.dumps(audit_payload, indent=2, ensure_ascii=True))

    lines = [
        "# Governance Audit Check",
        "",
        f"- generated_at: {audit_payload['generated_at']}",
        f"- overall_pass: {overall_pass}",
        f"- run_dir: `{run_dir}`",
        f"- report_json: `{report_json}`",
        "",
        "## Checks",
        "",
    ]
    for k in sorted(checks.keys()):
        lines.append(f"- {k}: {checks[k]}")
    lines += ["", "## Failures", ""]
    if failures:
        for msg in failures:
            lines.append(f"- {msg}")
    else:
        lines.append("- none")
    lines += ["", f"- output_json: `{out_json}`"]
    out_md.write_text("\n".join(lines) + "\n")

    print(f"[done] governance_audit_json={out_json}")
    print(f"[done] governance_audit_md={out_md}")

    raise SystemExit(0 if overall_pass else 2)


if __name__ == "__main__":
    main()
