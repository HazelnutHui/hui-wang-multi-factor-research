#!/usr/bin/env python3
"""Generate a committee-ready run review markdown from finalized artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _fmt(v) -> str:
    if v is None:
        return "null"
    try:
        f = float(v)
        return f"{f:.6f}"
    except Exception:
        return str(v)


def _latest(pattern: str) -> Path | None:
    cands = sorted(Path(".").glob(pattern), key=lambda p: p.stat().st_mtime)
    return cands[-1] if cands else None


def main() -> None:
    p = argparse.ArgumentParser(description="Generate standardized run review markdown.")
    p.add_argument("--report-json", default="", help="Path to production_gates_report.json")
    p.add_argument("--run-dir", default="", help="Path to audit/workstation_runs/<...>")
    p.add_argument("--out-md", default="", help="Optional output markdown path")
    args = p.parse_args()

    report_json = Path(args.report_json) if args.report_json else _latest("gate_results/production_gates_*/production_gates_report.json")
    run_dir = Path(args.run_dir) if args.run_dir else _latest("audit/workstation_runs/*")
    if report_json is None or not report_json.exists():
        raise SystemExit("report_json not found")
    if run_dir is None or not run_dir.exists():
        raise SystemExit("run_dir not found")

    rep = _read_json(report_json)
    ctx_path = run_dir / "context.json"
    ctx = _read_json(ctx_path) if ctx_path.exists() else {}

    gates = rep.get("gates") or rep.get("gate") or {}
    wf = rep.get("wf_stress") or {}
    risk = rep.get("risk_diagnostics") or {}
    stat = rep.get("statistical_gates") or {}
    costs = rep.get("cost_stress") or []
    inputs = rep.get("inputs") or {}

    dq_path_raw = str(ctx.get("data_quality_report_json") or "").strip()
    dq_pass = None
    if dq_path_raw:
        dq_path = Path(dq_path_raw)
        if dq_path.exists():
            dq_pass = bool(_read_json(dq_path).get("overall_pass"))

    gov_path = run_dir / "governance_audit_check.json"
    gov = _read_json(gov_path) if gov_path.exists() else {}
    gov_pass = gov.get("overall_pass")
    rem_path = run_dir / "governance_remediation_plan.json"
    rem = _read_json(rem_path) if rem_path.exists() else {}
    rem_items = rem.get("remediation_items") or []
    top_item = rem_items[0] if rem_items else {}

    def _cost(mult: float):
        for r in costs:
            if float(r.get("cost_multiplier", -1)) == float(mult):
                return r
        return {}

    c15 = _cost(1.5)
    c20 = _cost(2.0)
    decision_tag = str(ctx.get("decision_tag") or inputs.get("decision_tag") or "unknown")
    owner = str(ctx.get("owner") or inputs.get("owner") or "")
    overall = gates.get("overall_pass")
    recommendation = "approve" if overall is True else "reject/rerun"
    blocking = "none" if overall is True else "one or more required gates failed"

    out_md = Path(args.out_md) if args.out_md else report_json.with_name("production_gates_run_review.md")
    lines = [
        "# Run Review",
        "",
        f"- decision_tag: {decision_tag}",
        f"- run_date: {dt.date.today().isoformat()}",
        f"- owner: {owner}",
        f"- run_dir: `{run_dir}`",
        f"- gate_report_json: `{report_json}`",
        f"- overall_pass: {overall}",
        "",
        "## 1) Executive Decision",
        "",
        f"- recommendation: {recommendation}",
        f"- reason summary: overall_pass={overall}",
        f"- blocking issues: {blocking}",
        "",
        "## 2) Cost Stress Summary",
        "",
        f"- x1.5 test_ic: {_fmt(c15.get('test_ic'))}",
        f"- x2.0 test_ic: {_fmt(c20.get('test_ic'))}",
        f"- pass/fail: {gates.get('cost_gate_x1_5_positive')} / {gates.get('cost_gate_x2_0_positive')}",
        "",
        "## 3) Walk-Forward Stress Summary",
        "",
        f"- wf_test_ic_mean: {_fmt(wf.get('test_ic_mean'))}",
        f"- wf_test_ic_pos_ratio: {_fmt(wf.get('test_ic_pos_ratio'))}",
        f"- wf_test_ic_n: {_fmt(wf.get('test_ic_n'))}",
        f"- pass/fail: {gates.get('wf_gate_positive_mean')} / {gates.get('wf_gate_pos_ratio')}",
        "",
        "## 4) Risk Diagnostics Summary",
        "",
        f"- beta_vs_spy: {_fmt(risk.get('beta_vs_spy'))}",
        f"- turnover_top_pct_overlap: {_fmt(risk.get('turnover_top_pct_overlap'))}",
        f"- size_signal_corr_log_mcap: {_fmt(risk.get('size_signal_corr_log_mcap'))}",
        f"- industry_coverage: {_fmt(risk.get('industry_coverage'))}",
        "",
        "## 5) Statistical Gates Summary",
        "",
        f"- q_value_bh: {_fmt(stat.get('q_value_bh'))}",
        f"- factor_gate_pass: {stat.get('factor_gate_pass')}",
        f"- n_factors: {stat.get('n_factors')}",
        f"- n_pass: {stat.get('n_pass')}",
        "",
        "## 6) Governance and Audit Completeness",
        "",
        f"- data_quality_pass: {dq_pass}",
        f"- governance_audit_pass: {gov_pass}",
        f"- remediation_items_count: {len(rem_items)}",
        f"- highest_severity_remediation: {top_item.get('severity', 'none')} {top_item.get('failure', '')}",
        "",
        "## 7) Evidence Paths",
        "",
        f"- `{run_dir / 'context.json'}`",
        f"- `{run_dir / 'run.log'}`",
        f"- `{run_dir / 'governance_audit_check.json'}`",
        f"- `{run_dir / 'governance_remediation_plan.json'}`",
        f"- `{report_json}`",
        f"- `{report_json.with_name('production_gates_final_summary.md')}`",
    ]
    out_md.write_text("\n".join(lines) + "\n")
    print(f"[done] run_review_md={out_md}")


if __name__ == "__main__":
    main()
