import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str], dry_run: bool) -> int:
    print("[cmd]", " ".join(cmd), flush=True)
    if dry_run:
        return 0
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT) if not existing else f"{ROOT}:{existing}"
    p = subprocess.run(cmd, cwd=str(ROOT), env=env)
    return int(p.returncode)


def _latest_json(path: Path) -> Path | None:
    files = []
    for p in path.glob("*.json"):
        n = p.name
        if n.endswith(".manifest.json") or n == "run_manifest_latest.json":
            continue
        files.append(p)
    files = sorted(files, key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def _safe_float(v):
    try:
        return float(v)
    except Exception:
        return None


def _append_registry(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_df = pd.DataFrame([row])
    if path.exists():
        try:
            old_df = pd.read_csv(path)
            all_cols = list(dict.fromkeys(list(old_df.columns) + list(new_df.columns)))
            old_df = old_df.reindex(columns=all_cols)
            new_df = new_df.reindex(columns=all_cols)
            out = pd.concat([old_df, new_df], ignore_index=True)
            out.to_csv(path, index=False)
            return
        except Exception:
            pass
    new_df.to_csv(path, index=False)


def _load_yaml(path: Path) -> dict:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML: {path}")
    return data


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(out.get(k), dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _summarize_wf(path: Path) -> dict:
    if not path.exists():
        return {"ok": False, "reason": f"missing summary csv: {path}"}
    df = pd.read_csv(path)
    x = pd.to_numeric(df.get("test_ic"), errors="coerce").dropna()
    y = pd.to_numeric(df.get("test_ic_overall"), errors="coerce").dropna()
    return {
        "ok": True,
        "rows": int(len(df)),
        "test_ic_mean": float(x.mean()) if len(x) else None,
        "test_ic_std": float(x.std(ddof=1)) if len(x) > 1 else None,
        "test_ic_pos_ratio": float((x > 0).mean()) if len(x) else None,
        "test_ic_n": int(len(x)),
        "test_ic_overall_mean": float(y.mean()) if len(y) else None,
        "test_ic_overall_std": float(y.std(ddof=1)) if len(y) > 1 else None,
        "test_ic_overall_pos_ratio": float((y > 0).mean()) if len(y) else None,
        "test_ic_overall_n": int(len(y)),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Production-grade hard-gate runner (cost + stress + pass/fail).")
    p.add_argument("--strategy", required=True, help="Strategy yaml for fixed train/test runs")
    p.add_argument("--protocol", default=str(ROOT / "configs" / "protocol.yaml"))
    p.add_argument("--factor", default="combo_v2", help="Factor name for walk-forward stress run")
    p.add_argument("--cost-multipliers", default="1.0,1.5,2.0")
    p.add_argument("--wf-train-years", type=int, default=3)
    p.add_argument("--wf-test-years", type=int, default=1)
    p.add_argument("--wf-start-year", type=int, default=2010)
    p.add_argument("--wf-end-year", type=int, default=2025)
    p.add_argument("--wf-rebalance-mode", default="None", help="WF REBALANCE_MODE override (combo default: None)")
    p.add_argument("--stress-cost-multiplier", type=float, default=1.5)
    p.add_argument("--stress-min-market-cap", type=float, default=2_000_000_000)
    p.add_argument("--stress-min-dollar-volume", type=float, default=5_000_000)
    p.add_argument("--stress-min-price", type=float, default=5.0)
    p.add_argument("--stress-market-cap-dir", default="", help="Optional MARKET_CAP_DIR override for WF stress")
    p.add_argument("--stress-market-cap-strict", default="True", help="MARKET_CAP_STRICT override for WF stress")
    p.add_argument("--min-pos-ratio", type=float, default=0.70)
    p.add_argument("--risk-beta-abs-max", type=float, default=0.50)
    p.add_argument("--risk-turnover-overlap-min", type=float, default=0.20)
    p.add_argument("--risk-size-corr-abs-max", type=float, default=0.30)
    p.add_argument("--risk-industry-coverage-min", type=float, default=0.70)
    p.add_argument("--risk-top-pct", type=float, default=0.20)
    p.add_argument("--skip-risk-diagnostics", action="store_true")
    p.add_argument("--skip-statistical-gates", action="store_true")
    p.add_argument("--stat-summary-csv", default="", help="Segmented summary csv for statistical gates")
    p.add_argument("--stat-alpha", type=float, default=0.10)
    p.add_argument("--stat-min-pos-ratio", type=float, default=0.60)
    p.add_argument("--stat-min-ic-mean", type=float, default=0.0)
    p.add_argument("--out-dir", default="gate_results")
    p.add_argument("--registry-csv", default="gate_results/gate_registry.csv")
    p.add_argument("--decision-tag", default="")
    p.add_argument("--owner", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--no-registry", action="store_true")
    p.add_argument("--freeze-file", default="", help="Optional freeze file for train/test cost runs")
    p.add_argument("--wf-freeze-file", default="", help="Optional freeze file for walk-forward stress runs")
    p.add_argument("--skip-guardrails", action="store_true", help="Forward skip-guardrails to child runs")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_root = (ROOT / args.out_dir / f"production_gates_{ts}").resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    protocol_path = Path(args.protocol).resolve()
    strategy_path = Path(args.strategy).resolve()
    merged_cfg = _deep_merge(_load_yaml(protocol_path), _load_yaml(strategy_path))
    strategy_output_dir = merged_cfg.get("strategy", {}).get("output_dir", "strategies/run_with_config")
    strategy_runs_dir = (ROOT / strategy_output_dir / "runs").resolve()
    strategy_dir = (ROOT / strategy_output_dir).resolve()

    # 1) Cost stress on fixed train/test
    cm = [x.strip() for x in args.cost_multipliers.split(",") if x.strip()]
    cost_rows = []
    for c in cm:
        c_val = float(c)
        cmd = [sys.executable, str(ROOT / "scripts" / "run_with_config.py"), "--strategy", str(args.strategy), "--cost-multiplier", str(c_val)]
        if args.freeze_file:
            cmd += ["--freeze-file", str(args.freeze_file)]
        if args.skip_guardrails:
            cmd += ["--skip-guardrails"]
        code = _run(cmd, dry_run=args.dry_run)
        rec = {"cost_multiplier": c_val, "return_code": code, "test_ic": None, "train_ic": None, "run_json": None}
        if code == 0 and not args.dry_run:
            latest = _latest_json(strategy_runs_dir)
            if latest:
                payload = json.loads(latest.read_text())
                test_ic = payload.get("performance", {}).get("test", {}).get("ic")
                train_ic = payload.get("performance", {}).get("train", {}).get("ic")
                rec["test_ic"] = _safe_float(test_ic)
                rec["train_ic"] = _safe_float(train_ic)
                rec["run_json"] = str(latest)
        cost_rows.append(rec)

    cost_df = pd.DataFrame(cost_rows)
    cost_csv = out_root / "cost_stress_results.csv"
    cost_df.to_csv(cost_csv, index=False)

    # 2) Walk-forward stress under stricter universe
    wf_out = out_root / "walk_forward_stress"
    wf_cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_walk_forward.py"),
        "--factors",
        args.factor,
        "--train-years",
        str(args.wf_train_years),
        "--test-years",
        str(args.wf_test_years),
        "--start-year",
        str(args.wf_start_year),
        "--end-year",
        str(args.wf_end_year),
        "--out-dir",
        str(wf_out),
        "--set",
        f"COST_MULTIPLIER={args.stress_cost_multiplier}",
        "--set",
        f"MIN_MARKET_CAP={int(args.stress_min_market_cap)}",
        "--set",
        f"MIN_DOLLAR_VOLUME={int(args.stress_min_dollar_volume)}",
        "--set",
        f"MIN_PRICE={args.stress_min_price}",
        "--set",
        f"REBALANCE_MODE={args.wf_rebalance_mode}",
    ]
    if args.stress_market_cap_dir:
        mc_path = Path(args.stress_market_cap_dir).expanduser()
        if not mc_path.is_absolute():
            mc_path = (ROOT / mc_path).resolve()
        wf_cmd += ["--set", f"MARKET_CAP_DIR={mc_path}"]
        wf_cmd += ["--set", f"MARKET_CAP_STRICT={args.stress_market_cap_strict}"]
    if args.wf_freeze_file:
        wf_cmd += ["--freeze-file", str(args.wf_freeze_file)]
    if args.skip_guardrails:
        wf_cmd += ["--skip-guardrails"]
    wf_code = _run(wf_cmd, dry_run=args.dry_run)

    wf_summary_path = wf_out / args.factor / "walk_forward_summary.csv"
    wf_stats = {"ok": False, "reason": "dry_run"}
    if not args.dry_run:
        wf_stats = _summarize_wf(wf_summary_path)
        wf_stats["return_code"] = wf_code
        wf_stats["summary_csv"] = str(wf_summary_path)

    # 2.5) Risk diagnostics gates
    risk_stats = {"ok": False, "reason": "skipped"}
    if not args.skip_risk_diagnostics:
        diag_cmd = [
            sys.executable,
            str(ROOT / "scripts" / "posthoc_factor_diagnostics.py"),
            "--strategy",
            str(strategy_dir),
            "--top-pct",
            str(args.risk_top_pct),
        ]
        diag_code = _run(diag_cmd, dry_run=args.dry_run)
        if args.dry_run:
            risk_stats = {"ok": False, "reason": "dry_run", "return_code": diag_code}
        else:
            diag_files = sorted((strategy_dir / "reports").glob("diagnostics_*.json"), key=lambda p: p.stat().st_mtime)
            if not diag_files:
                risk_stats = {"ok": False, "reason": "diagnostics json not found", "return_code": diag_code}
            else:
                latest_diag = diag_files[-1]
                d = json.loads(latest_diag.read_text()).get("diagnostics", {})
                ind = d.get("industry_exposure") or {}
                risk_stats = {
                    "ok": True,
                    "return_code": diag_code,
                    "diagnostics_json": str(latest_diag),
                    "beta_vs_spy": _safe_float(d.get("beta_vs_spy")),
                    "turnover_top_pct_overlap": _safe_float(d.get("turnover_top_pct_overlap")),
                    "size_signal_corr_log_mcap": _safe_float(d.get("size_signal_corr_log_mcap")),
                    "industry_coverage": _safe_float(ind.get("coverage")),
                }

    # 2.6) Statistical gates (multiple-testing control)
    stat_stats = {"ok": False, "reason": "skipped"}
    if not args.skip_statistical_gates:
        stat_cmd = [
            sys.executable,
            str(ROOT / "scripts" / "run_statistical_gates.py"),
            "--factor",
            str(args.factor),
            "--alpha",
            str(args.stat_alpha),
            "--min-pos-ratio",
            str(args.stat_min_pos_ratio),
            "--min-ic-mean",
            str(args.stat_min_ic_mean),
            "--out-dir",
            str(out_root / "statistical"),
        ]
        if args.stat_summary_csv:
            stat_cmd += ["--summary-csv", str(args.stat_summary_csv)]
        stat_code = _run(stat_cmd, dry_run=args.dry_run)
        if args.dry_run:
            stat_stats = {"ok": False, "reason": "dry_run", "return_code": stat_code}
        else:
            rep_files = sorted((out_root / "statistical").glob("statistical_gates_*/statistical_gates_report.json"), key=lambda p: p.stat().st_mtime)
            if not rep_files:
                stat_stats = {"ok": False, "reason": "statistical report not found", "return_code": stat_code}
            else:
                rep = json.loads(rep_files[-1].read_text())
                focus = rep.get("focus") or {}
                stat_stats = {
                    "ok": True,
                    "return_code": stat_code,
                    "report_json": str(rep_files[-1]),
                    "factor_found": bool(focus.get("found")),
                    "factor_gate_pass": bool(focus.get("gate_pass")) if focus.get("found") else False,
                    "q_value_bh": _safe_float(focus.get("q_value_bh")),
                    "n_factors": rep.get("n_factors"),
                    "n_pass": rep.get("n_pass"),
                }

    # 3) Hard gates
    gate = {
        "cost_gate_x1_5_positive": None,
        "cost_gate_x2_0_positive": None,
        "wf_gate_positive_mean": None,
        "wf_gate_pos_ratio": None,
        "risk_gate_beta_abs": None,
        "risk_gate_turnover_overlap": None,
        "risk_gate_size_corr_abs": None,
        "risk_gate_industry_coverage": None,
        "stat_gate_factor_pass": None,
        "overall_pass": None,
    }
    if not args.dry_run:
        def _test_ic_for(mult: float):
            hit = cost_df.loc[cost_df["cost_multiplier"] == float(mult)]
            if len(hit) == 0:
                return None
            return _safe_float(hit.iloc[-1].get("test_ic"))

        x15 = _test_ic_for(1.5)
        x20 = _test_ic_for(2.0)
        gate["cost_gate_x1_5_positive"] = (x15 is not None and x15 > 0)
        gate["cost_gate_x2_0_positive"] = (x20 is not None and x20 > 0)
        m = wf_stats.get("test_ic_mean")
        pr = wf_stats.get("test_ic_pos_ratio")
        gate["wf_gate_positive_mean"] = (m is not None and m > 0)
        gate["wf_gate_pos_ratio"] = (pr is not None and pr >= float(args.min_pos_ratio))
        if not args.skip_risk_diagnostics:
            beta = risk_stats.get("beta_vs_spy")
            tovr = risk_stats.get("turnover_top_pct_overlap")
            sz = risk_stats.get("size_signal_corr_log_mcap")
            cov = risk_stats.get("industry_coverage")
            gate["risk_gate_beta_abs"] = (beta is not None and abs(beta) <= float(args.risk_beta_abs_max))
            gate["risk_gate_turnover_overlap"] = (tovr is not None and tovr >= float(args.risk_turnover_overlap_min))
            gate["risk_gate_size_corr_abs"] = (sz is not None and abs(sz) <= float(args.risk_size_corr_abs_max))
            gate["risk_gate_industry_coverage"] = (cov is not None and cov >= float(args.risk_industry_coverage_min))
        if not args.skip_statistical_gates:
            gate["stat_gate_factor_pass"] = bool(stat_stats.get("factor_gate_pass"))
        required = [
            "cost_gate_x1_5_positive",
            "cost_gate_x2_0_positive",
            "wf_gate_positive_mean",
            "wf_gate_pos_ratio",
        ]
        if not args.skip_risk_diagnostics:
            required += [
                "risk_gate_beta_abs",
                "risk_gate_turnover_overlap",
                "risk_gate_size_corr_abs",
                "risk_gate_industry_coverage",
            ]
        if not args.skip_statistical_gates:
            required.append("stat_gate_factor_pass")
        gate["overall_pass"] = all(gate.get(k) is True for k in required)

    report = {
        "generated_at": datetime.now().isoformat(),
        "inputs": vars(args),
        "outputs": {
            "out_root": str(out_root),
            "cost_csv": str(cost_csv),
            "wf_summary_csv": str(wf_summary_path),
        },
        "cost_stress": cost_rows,
        "wf_stress": wf_stats,
        "risk_diagnostics": risk_stats,
        "statistical_gates": stat_stats,
        "gates": gate,
    }
    report_json = out_root / "production_gates_report.json"
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=True))

    md = out_root / "production_gates_report.md"
    lines = [
        "# Production Gates Report",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- overall_pass: {gate.get('overall_pass')}",
        "",
        "## Cost Stress",
        "",
        f"- csv: `{cost_csv}`",
        "",
    ]
    for r in cost_rows:
        lines.append(
            f"- x{r['cost_multiplier']}: rc={r['return_code']}, train_ic={r['train_ic']}, test_ic={r['test_ic']}"
        )
    lines += [
        "",
        "## WF Stress",
        "",
        f"- summary_csv: `{wf_summary_path}`",
        f"- stats: `{json.dumps(wf_stats, ensure_ascii=True)}`",
        "",
        "## Gates",
        "",
        f"- cost_gate_x1_5_positive: {gate.get('cost_gate_x1_5_positive')}",
        f"- cost_gate_x2_0_positive: {gate.get('cost_gate_x2_0_positive')}",
        f"- wf_gate_positive_mean: {gate.get('wf_gate_positive_mean')}",
        f"- wf_gate_pos_ratio: {gate.get('wf_gate_pos_ratio')}",
        f"- risk_gate_beta_abs: {gate.get('risk_gate_beta_abs')}",
        f"- risk_gate_turnover_overlap: {gate.get('risk_gate_turnover_overlap')}",
        f"- risk_gate_size_corr_abs: {gate.get('risk_gate_size_corr_abs')}",
        f"- risk_gate_industry_coverage: {gate.get('risk_gate_industry_coverage')}",
        f"- stat_gate_factor_pass: {gate.get('stat_gate_factor_pass')}",
        f"- overall_pass: {gate.get('overall_pass')}",
    ]
    md.write_text("\n".join(lines))

    if not args.no_registry:
        registry_row = {
            "run_ts": ts,
            "generated_at": report["generated_at"],
            "decision_tag": args.decision_tag,
            "owner": args.owner,
            "strategy": str(args.strategy),
            "factor": str(args.factor),
            "freeze_file": str(args.freeze_file),
            "skip_guardrails": bool(args.skip_guardrails),
            "skip_risk_diagnostics": bool(args.skip_risk_diagnostics),
            "skip_statistical_gates": bool(args.skip_statistical_gates),
            "overall_pass": gate.get("overall_pass"),
            "cost_gate_x1_5_positive": gate.get("cost_gate_x1_5_positive"),
            "cost_gate_x2_0_positive": gate.get("cost_gate_x2_0_positive"),
            "wf_gate_positive_mean": gate.get("wf_gate_positive_mean"),
            "wf_gate_pos_ratio": gate.get("wf_gate_pos_ratio"),
            "risk_gate_beta_abs": gate.get("risk_gate_beta_abs"),
            "risk_gate_turnover_overlap": gate.get("risk_gate_turnover_overlap"),
            "risk_gate_size_corr_abs": gate.get("risk_gate_size_corr_abs"),
            "risk_gate_industry_coverage": gate.get("risk_gate_industry_coverage"),
            "stat_gate_factor_pass": gate.get("stat_gate_factor_pass"),
            "wf_test_ic_mean": wf_stats.get("test_ic_mean"),
            "wf_test_ic_pos_ratio": wf_stats.get("test_ic_pos_ratio"),
            "stat_q_value_bh": stat_stats.get("q_value_bh"),
            "report_json": str(report_json),
            "report_md": str(md),
            "notes": args.notes,
        }
        _append_registry((ROOT / args.registry_csv).resolve(), registry_row)

    print(f"[done] report_json={report_json}")
    print(f"[done] report_md={md}")


if __name__ == "__main__":
    main()
