import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

from backtest.backtest_engine import BacktestEngine
from backtest.performance_analyzer import PerformanceAnalyzer
from scripts import run_with_config as cfg_loader


def _quantile_summary(signals: pd.DataFrame, fwd: pd.DataFrame, n_quantiles: int = 5) -> pd.DataFrame:
    merged = pd.merge(
        signals[["symbol", "date", "signal"]],
        fwd[["symbol", "signal_date", "return"]],
        left_on=["symbol", "date"],
        right_on=["symbol", "signal_date"],
        how="inner",
    )
    if merged.empty:
        return pd.DataFrame()

    merged["date"] = pd.to_datetime(merged["date"])
    rows = []
    for d, g in merged.groupby("date"):
        if len(g) < n_quantiles:
            continue
        g = g.copy()
        g["rank"] = g["signal"].rank(method="first")
        try:
            g["q"] = pd.qcut(g["rank"], n_quantiles, labels=False) + 1
        except ValueError:
            continue
        qret = g.groupby("q")["return"].mean()
        for q, r in qret.items():
            rows.append({"date": d, "quantile": int(q), "mean_return": float(r)})

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    summary = df.groupby("quantile")["mean_return"].mean().reset_index()
    return summary.sort_values("quantile").reset_index(drop=True)


def _rolling_ic(signals: pd.DataFrame, fwd: pd.DataFrame, window: int = 60) -> pd.Series:
    merged = pd.merge(
        signals[["symbol", "date", "signal"]],
        fwd[["symbol", "signal_date", "return"]],
        left_on=["symbol", "date"],
        right_on=["symbol", "signal_date"],
        how="inner",
    )
    if merged.empty:
        return pd.Series(dtype=float)
    merged["date"] = pd.to_datetime(merged["date"])
    ic_by_date = merged.groupby("date").apply(lambda g: g["signal"].corr(g["return"]))
    ic_by_date = ic_by_date.dropna().sort_index()
    if ic_by_date.empty:
        return ic_by_date
    return ic_by_date.rolling(window=window, min_periods=max(3, window // 5)).mean()


def _turnover_from_positions(positions: pd.DataFrame) -> Dict[str, Any]:
    if positions is None or len(positions) == 0:
        return {"avg_turnover": None, "n_dates": 0}
    df = positions.copy()
    df = df[df["position"] != 0]
    if df.empty:
        return {"avg_turnover": None, "n_dates": 0}
    by_date = df.groupby("date")
    dates = sorted(by_date.groups.keys())
    if len(dates) < 2:
        return {"avg_turnover": None, "n_dates": len(dates)}
    turnovers = []
    prev = None
    for d in dates:
        cur = set(by_date.get_group(d)["symbol"])
        if prev is not None:
            union = prev.union(cur)
            inter = prev.intersection(cur)
            t = 1.0 - (len(inter) / len(union)) if union else 0.0
            turnovers.append(t)
        prev = cur
    return {"avg_turnover": float(pd.Series(turnovers).mean()), "n_dates": len(dates)}


def _quantile_cumulative(signals: pd.DataFrame, fwd: pd.DataFrame, n_quantiles: int = 5) -> pd.DataFrame:
    merged = pd.merge(
        signals[["symbol", "date", "signal"]],
        fwd[["symbol", "signal_date", "return"]],
        left_on=["symbol", "date"],
        right_on=["symbol", "signal_date"],
        how="inner",
    )
    if merged.empty:
        return pd.DataFrame()

    merged["date"] = pd.to_datetime(merged["date"])
    rows = []
    for d, g in merged.groupby("date"):
        if len(g) < n_quantiles:
            continue
        g = g.copy()
        g["rank"] = g["signal"].rank(method="first")
        try:
            g["q"] = pd.qcut(g["rank"], n_quantiles, labels=False) + 1
        except ValueError:
            continue
        qret = g.groupby("q")["return"].mean()
        for q, r in qret.items():
            rows.append({"date": d, "quantile": int(q), "mean_return": float(r)})

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values(["quantile", "date"]).reset_index(drop=True)
    df["cum_return"] = df.groupby("quantile")["mean_return"].apply(lambda s: (1 + s).cumprod() - 1.0)
    return df


def _factor_corr(signals: pd.DataFrame) -> pd.DataFrame:
    if signals is None or len(signals) == 0:
        return pd.DataFrame()
    cols = [c for c in ["pead", "momentum", "reversal", "low_vol", "quality", "value"] if c in signals.columns]
    if len(cols) < 2:
        return pd.DataFrame()
    df = signals[cols].copy()
    df = df.replace([pd.NA, float("inf"), float("-inf")], pd.NA).dropna()
    if len(df) < 10:
        return pd.DataFrame()
    return df.corr()


def _cost_sensitivity(base_cfg: Dict[str, Any], multipliers: List[float]) -> List[Dict[str, Any]]:
    out = []
    for m in multipliers:
        cfg = dict(base_cfg)
        cfg["TRANSACTION_COST"] = float(cfg.get("TRANSACTION_COST", 0.0)) * float(m)
        engine = BacktestEngine(cfg)
        out.append({"multiplier": float(m), "engine": engine})
    return out


def _write_md(report: Dict[str, Any], out_path: Path) -> None:
    lines = []
    meta = report["metadata"]
    lines.append(f"# Factor Report - {meta.get('strategy_name')}")
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- Strategy: {meta.get('strategy_name')} ({meta.get('strategy_id')}) v{meta.get('strategy_version')}")
    lines.append(f"- Protocol: {meta.get('protocol_version')}")
    lines.append(f"- Run date: {meta.get('run_date')}")
    lines.append("")

    perf = report["performance"]
    lines.append("## IC Summary")
    for split in ["train", "test"]:
        s = perf.get(split, {})
        lines.append(f"- {split.title()}: ic_mean={s.get('ic')} ic_overall={s.get('ic_overall')} n_dates={s.get('n')}")
    lines.append("")

    lines.append("## Turnover (Test)")
    t = report.get("turnover_test", {})
    lines.append(f"- avg_turnover: {t.get('avg_turnover')} (n_dates={t.get('n_dates')})")
    lines.append("")

    lines.append("## Quantile Mean Returns (Test)")
    qdf = report.get("quantiles_test")
    if isinstance(qdf, list) and qdf:
        lines.append("| Quantile | Mean Return |")
        lines.append("|---|---|")
        for row in qdf:
            lines.append(f"| {row['quantile']} | {row['mean_return']:.6f} |")
    else:
        lines.append("- (no data)")
    lines.append("")

    lines.append("## Rolling IC (Test)")
    roll = report.get("rolling_ic_test")
    if isinstance(roll, dict) and roll:
        last = roll.get("last_value")
        lines.append(f"- rolling_window: {roll.get('window')}")
        lines.append(f"- last_value: {last}")
    else:
        lines.append("- (no data)")
    lines.append("")

    lines.append("## Factor Correlation (Test)")
    corr = report.get("factor_corr_test")
    if isinstance(corr, list) and corr:
        # corr stored as list of dicts
        cols = corr[0].keys()
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "|".join(["---"] * len(cols)) + "|")
        for row in corr:
            lines.append("| " + " | ".join([f\"{row[c]:.4f}\" if isinstance(row[c], (int, float)) else str(row[c]) for c in cols]) + " |")
    else:
        lines.append("- (no data)")
    lines.append("")

    lines.append("## Cost Sensitivity (Test)")
    cs = report.get("cost_sensitivity", [])
    if cs:
        lines.append("| Cost x | Test IC | Test IC Overall |")
        lines.append("|---|---|---|")
        for row in cs:
            lines.append(f"| {row['multiplier']} | {row['test_ic']} | {row['test_ic_overall']} |")
    else:
        lines.append("- (not run)")
    lines.append("")

    out_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", default=str(Path(__file__).resolve().parents[1] / "configs" / "protocol.yaml"))
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--quantiles", type=int, default=5)
    parser.add_argument("--rolling-window", type=int, default=60)
    parser.add_argument("--cost-multipliers", type=str, default="")
    args = parser.parse_args()

    protocol_path = Path(args.protocol).resolve()
    strategy_path = Path(args.strategy).resolve()
    protocol = cfg_loader._load_yaml(protocol_path)
    strategy = cfg_loader._load_yaml(strategy_path)
    merged = cfg_loader._deep_merge(protocol, strategy)

    engine_cfg = cfg_loader._build_engine_config(merged, protocol_path.parent)
    engine_cfg["SIGNALS_INCLUDE_FACTORS"] = True
    weights = cfg_loader._validate_weights(merged.get("factors", {}).get("weights", {}))

    execution = merged.get("execution", {})
    periods = merged.get("backtest_periods", {})
    long_pct = execution.get("long_pct", 0.2)
    short_pct = execution.get("short_pct", 0.0)

    engine = BacktestEngine(engine_cfg)
    results = engine.run_out_of_sample_test(
        train_start=periods.get("train_start"),
        train_end=periods.get("train_end"),
        test_start=periods.get("test_start"),
        test_end=periods.get("test_end"),
        factor_weights=weights,
        rebalance_freq=execution.get("rebalance_freq"),
        holding_period=execution.get("holding_period"),
        long_pct=long_pct,
        short_pct=short_pct,
    )

    pa = PerformanceAnalyzer()
    train_ic = pa.calculate_ic(results["train"]["signals"], results["train"]["forward_returns"])
    test_ic = pa.calculate_ic(results["test"]["signals"], results["test"]["forward_returns"])

    q_test = _quantile_summary(results["test"]["signals"], results["test"]["forward_returns"], args.quantiles)
    q_cum = _quantile_cumulative(results["test"]["signals"], results["test"]["forward_returns"], args.quantiles)
    rolling = _rolling_ic(results["test"]["signals"], results["test"]["forward_returns"], args.rolling_window)
    corr = _factor_corr(results["test"]["signals"])
    turnover = _turnover_from_positions(results["test"]["positions"])

    cost_sens = []
    if args.cost_multipliers:
        multipliers = [float(x.strip()) for x in args.cost_multipliers.split(",") if x.strip()]
        for m in multipliers:
            cfg = dict(engine_cfg)
            cfg["TRANSACTION_COST"] = float(cfg.get("TRANSACTION_COST", 0.0)) * float(m)
            eng = BacktestEngine(cfg)
            res = eng.run_out_of_sample_test(
                train_start=periods.get("train_start"),
                train_end=periods.get("train_end"),
                test_start=periods.get("test_start"),
                test_end=periods.get("test_end"),
                factor_weights=weights,
                rebalance_freq=execution.get("rebalance_freq"),
                holding_period=execution.get("holding_period"),
                long_pct=long_pct,
                short_pct=short_pct,
            )
            ic = pa.calculate_ic(res["test"]["signals"], res["test"]["forward_returns"])
            cost_sens.append({
                "multiplier": float(m),
                "test_ic": ic.get("ic"),
                "test_ic_overall": ic.get("ic_overall"),
            })

    strategy_meta = merged.get("strategy", {})
    output_dir = Path(merged.get("strategy", {}).get("output_dir", "strategies/reports")).resolve()
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_path = reports_dir / f"factor_report_{ts}.md"
    json_path = reports_dir / f"factor_report_{ts}.json"

    report = {
        "metadata": {
            "strategy_name": strategy_meta.get("name"),
            "strategy_id": strategy_meta.get("id"),
            "strategy_version": strategy_meta.get("version"),
            "protocol_version": merged.get("protocol", {}).get("version"),
            "run_date": datetime.now().isoformat(),
        },
        "performance": {
            "train": train_ic,
            "test": test_ic,
        },
        "quantiles_test": q_test.to_dict(orient="records") if isinstance(q_test, pd.DataFrame) and len(q_test) > 0 else [],
        "quantiles_cum_test": q_cum.to_dict(orient="records") if isinstance(q_cum, pd.DataFrame) and len(q_cum) > 0 else [],
        "rolling_ic_test": {
            "window": args.rolling_window,
            "last_value": float(rolling.dropna().iloc[-1]) if not rolling.dropna().empty else None,
        },
        "turnover_test": turnover,
        "factor_corr_test": corr.reset_index().to_dict(orient="records") if isinstance(corr, pd.DataFrame) and len(corr) > 0 else [],
        "cost_sensitivity": cost_sens,
        "artifacts": {
            "protocol_yaml": str(protocol_path),
            "strategy_yaml": str(strategy_path),
        },
    }

    _write_md(report, report_path)
    # Save auxiliary CSVs
    if isinstance(q_cum, pd.DataFrame) and len(q_cum) > 0:
        q_cum.to_csv(reports_dir / f"quantile_cum_{ts}.csv", index=False)
    if isinstance(corr, pd.DataFrame) and len(corr) > 0:
        corr.to_csv(reports_dir / f"factor_corr_{ts}.csv")
    if isinstance(rolling, pd.Series) and len(rolling) > 0:
        rolling.reset_index().rename(columns={0: "rolling_ic"}).to_csv(
            reports_dir / f"rolling_ic_{ts}.csv", index=False
        )
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    print("=" * 70)
    print(f"Saved report: {report_path}")
    print(f"Saved json:   {json_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
