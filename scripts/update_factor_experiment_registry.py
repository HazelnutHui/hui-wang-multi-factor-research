#!/usr/bin/env python3
"""Update factor experiment registry and leaderboard from production gate artifacts."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _to_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _find_run_dir_by_tag(tag: str) -> Path | None:
    if not tag:
        return None
    cands = sorted(Path("audit/workstation_runs").glob(f"*{tag}*"), key=lambda p: p.stat().st_mtime)
    return cands[-1] if cands else None


def _cost_ic(cost_rows: list[dict[str, Any]], mult: float) -> float | None:
    for r in cost_rows:
        try:
            if float(r.get("cost_multiplier")) == float(mult):
                return _to_float(r.get("test_ic"))
        except Exception:
            continue
    return None


def _score_row(row: dict[str, Any]) -> tuple[float, float, float, str]:
    x15 = _to_float(row.get("cost_ic_x1_5"))
    x20 = _to_float(row.get("cost_ic_x2_0"))
    wf_mean = _to_float(row.get("wf_test_ic_mean"))
    wf_pos = _to_float(row.get("wf_test_ic_pos_ratio"))
    beta = _to_float(row.get("risk_beta_vs_spy"))
    size_corr = _to_float(row.get("risk_size_corr_abs"))
    overlap = _to_float(row.get("risk_turnover_overlap"))
    coverage = _to_float(row.get("risk_industry_coverage"))
    qval = _to_float(row.get("stat_q_value_bh"))
    stat_pass = str(row.get("stat_factor_gate_pass", "")).lower() == "true"
    overall_pass = str(row.get("overall_pass", "")).lower() == "true"
    dq_pass = str(row.get("data_quality_pass", "")).lower() == "true"
    gov_pass = str(row.get("governance_audit_pass", "")).lower() == "true"
    stage_link = str(row.get("stage_log_linked", "")).lower() == "true"
    high_rem = int(float(row.get("remediation_high_count", 0) or 0))

    cost_score = 0.0
    if x15 is not None and x15 > 0:
        cost_score += 6.0
    if x20 is not None and x20 > 0:
        cost_score += 6.0
    vals = [v for v in [x15, x20] if v is not None]
    if vals:
        cost_score += _clip(sum(vals) / len(vals) * 100.0, 0.0, 8.0)
    cost_score = _clip(cost_score, 0.0, 20.0)

    wf_score = 0.0
    if wf_mean is not None and wf_mean > 0:
        wf_score += 10.0
    if wf_mean is not None:
        wf_score += _clip(wf_mean * 120.0, 0.0, 10.0)
    if wf_pos is not None:
        wf_score += _clip((wf_pos - 0.5) * 50.0, 0.0, 10.0)
    wf_score = _clip(wf_score, 0.0, 30.0)

    risk_score = 20.0
    if beta is not None and abs(beta) > 0.5:
        risk_score -= 8.0
    if size_corr is not None and abs(size_corr) > 0.3:
        risk_score -= 6.0
    if overlap is not None and overlap < 0.2:
        risk_score -= 4.0
    if coverage is not None and coverage < 0.7:
        risk_score -= 4.0
    risk_score = _clip(risk_score, 0.0, 20.0)

    stat_score = 0.0
    if stat_pass:
        stat_score += 6.0
    if qval is not None:
        if qval <= 0.10:
            stat_score += 4.0
        elif qval <= 0.20:
            stat_score += 2.0
    stat_score = _clip(stat_score, 0.0, 10.0)

    governance_score = 0.0
    if dq_pass:
        governance_score += 8.0
    if gov_pass:
        governance_score += 8.0
    if stage_link:
        governance_score += 2.0
    if high_rem == 0:
        governance_score += 2.0
    governance_score = _clip(governance_score, 0.0, 20.0)

    total = cost_score + wf_score + risk_score + stat_score + governance_score
    if not overall_pass and total > 75.0:
        total = 75.0

    if overall_pass and gov_pass and dq_pass and total >= 80.0:
        rec = "promote_candidate"
    elif total >= 65.0:
        rec = "watchlist_rerun"
    else:
        rec = "reject_or_research"
    return round(total, 4), round(wf_score + cost_score + risk_score + stat_score, 4), round(governance_score, 4), rec


def _build_row(report_json: Path, run_dir_hint: Path | None = None) -> dict[str, Any]:
    rep = _read_json(report_json)
    inputs = rep.get("inputs") or {}
    gates = rep.get("gates") or rep.get("gate") or {}
    cost_rows = rep.get("cost_stress") or []
    wf = rep.get("wf_stress") or {}
    risk = rep.get("risk_diagnostics") or {}
    stat = rep.get("statistical_gates") or {}

    decision_tag = str(inputs.get("decision_tag") or "")
    run_dir = run_dir_hint if run_dir_hint is not None else _find_run_dir_by_tag(decision_tag)
    ctx: dict[str, Any] = {}
    gov: dict[str, Any] = {}
    rem: dict[str, Any] = {}
    dq_pass = None
    stage_link = None
    gov_pass = None
    rem_high = 0
    if run_dir and run_dir.exists():
        ctx_path = run_dir / "context.json"
        if ctx_path.exists():
            ctx = _read_json(ctx_path)
        gov_path = run_dir / "governance_audit_check.json"
        if gov_path.exists():
            gov = _read_json(gov_path)
            gov_pass = gov.get("overall_pass")
            stage_link = (gov.get("checks") or {}).get("stage_log_has_decision_tag")
        rem_path = run_dir / "governance_remediation_plan.json"
        if rem_path.exists():
            rem = _read_json(rem_path)
            for item in rem.get("remediation_items") or []:
                if str(item.get("severity")) == "High":
                    rem_high += 1
        dq_path_raw = str(ctx.get("data_quality_report_json") or "").strip()
        if dq_path_raw:
            dq_path = Path(dq_path_raw)
            if not dq_path.is_absolute():
                dq_path = (run_dir / dq_path).resolve()
            if dq_path.exists():
                dq_pass = (_read_json(dq_path).get("overall_pass"))

    row = {
        "generated_at": dt.datetime.now().isoformat(),
        "report_json": str(report_json.resolve()),
        "report_md": str(report_json.with_name("production_gates_report.md").resolve()),
        "run_dir": str(run_dir.resolve()) if run_dir and run_dir.exists() else "",
        "decision_tag": decision_tag,
        "owner": str(inputs.get("owner") or ""),
        "factor": str(inputs.get("factor") or ""),
        "strategy": str(inputs.get("strategy") or ""),
        "freeze_file": str(inputs.get("freeze_file") or ""),
        "overall_pass": bool(gates.get("overall_pass")),
        "cost_ic_x1_5": _cost_ic(cost_rows, 1.5),
        "cost_ic_x2_0": _cost_ic(cost_rows, 2.0),
        "wf_test_ic_mean": _to_float(wf.get("test_ic_mean")),
        "wf_test_ic_pos_ratio": _to_float(wf.get("test_ic_pos_ratio")),
        "risk_beta_vs_spy": _to_float(risk.get("beta_vs_spy")),
        "risk_turnover_overlap": _to_float(risk.get("turnover_top_pct_overlap")),
        "risk_size_corr_abs": abs(_to_float(risk.get("size_signal_corr_log_mcap")) or 0.0)
        if _to_float(risk.get("size_signal_corr_log_mcap")) is not None else None,
        "risk_industry_coverage": _to_float(risk.get("industry_coverage")),
        "stat_q_value_bh": _to_float(stat.get("q_value_bh")),
        "stat_factor_gate_pass": bool(stat.get("factor_gate_pass")),
        "data_quality_pass": dq_pass,
        "governance_audit_pass": gov_pass,
        "stage_log_linked": stage_link,
        "remediation_high_count": rem_high,
    }
    total, quality, gov_score, rec = _score_row({k: str(v) if isinstance(v, bool) else v for k, v in row.items()})
    row["score_total"] = total
    row["score_quality"] = quality
    row["score_governance"] = gov_score
    row["recommendation"] = rec
    row["run_review_md"] = str(report_json.with_name("production_gates_run_review.md").resolve())
    return row


def _write_registry(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for r in rows:
        for k in r.keys():
            if k not in fieldnames:
                fieldnames.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _load_existing(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _write_leaderboard(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ranked = sorted(rows, key=lambda r: float(r.get("score_total") or 0.0), reverse=True)
    top = ranked[:20]
    lines = [
        "# Factor Experiment Leaderboard",
        "",
        f"- generated_at: {dt.datetime.now().isoformat()}",
        f"- total_experiments: {len(rows)}",
        "",
        "| rank | decision_tag | factor | overall_pass | score_total | recommendation | report_json |",
        "|---|---|---|---|---:|---|---|",
    ]
    for i, r in enumerate(top, start=1):
        lines.append(
            f"| {i} | {r.get('decision_tag','')} | {r.get('factor','')} | {r.get('overall_pass','')} | {r.get('score_total','')} | {r.get('recommendation','')} | `{r.get('report_json','')}` |"
        )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description="Update factor experiment registry from production gate runs.")
    p.add_argument("--report-json", action="append", default=[], help="Specific report json(s) to update.")
    p.add_argument("--run-dir", default="", help="Optional run dir hint (for single report update).")
    p.add_argument("--scan-glob", default="gate_results/production_gates_*/production_gates_report.json")
    p.add_argument("--registry-csv", default="audit/factor_registry/factor_experiment_registry.csv")
    p.add_argument("--leaderboard-md", default="audit/factor_registry/factor_experiment_leaderboard.md")
    args = p.parse_args()

    registry_csv = Path(args.registry_csv).resolve()
    leaderboard_md = Path(args.leaderboard_md).resolve()
    existing = _load_existing(registry_csv)
    keep: dict[str, dict[str, Any]] = {}
    for r in existing:
        keep[str(r.get("report_json"))] = r

    reports: list[Path] = []
    if args.report_json:
        for pth in args.report_json:
            rp = Path(pth).resolve()
            if rp.exists():
                reports.append(rp)
    else:
        reports = sorted([p.resolve() for p in Path(".").glob(args.scan_glob)], key=lambda p: p.stat().st_mtime)

    run_dir_hint = Path(args.run_dir).resolve() if args.run_dir else None
    updated = 0
    for rp in reports:
        row = _build_row(rp, run_dir_hint=run_dir_hint)
        keep[str(row["report_json"])] = row
        updated += 1

    rows = list(keep.values())
    rows = sorted(rows, key=lambda r: str(r.get("generated_at", "")))
    _write_registry(registry_csv, rows)
    _write_leaderboard(leaderboard_md, rows)
    print(f"[done] registry_csv={registry_csv}")
    print(f"[done] leaderboard_md={leaderboard_md}")
    print(f"[done] rows_total={len(rows)} updated={updated}")


if __name__ == "__main__":
    main()
