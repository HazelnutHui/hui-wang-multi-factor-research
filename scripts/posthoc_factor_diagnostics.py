#!/usr/bin/env python3
"""
Post-hoc diagnostics for factor runs (no changes to backtest logic).
Reads *_latest.csv outputs + latest run config, then computes:
  - portfolio return series (equal-weight by signal_date)
  - market beta vs SPY
  - industry/sector exposure summary
  - signal coverage + turnover (top-quantile overlap)
  - optional size exposure (corr with log market cap)
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _find_latest_run_json(strategy_dir: Path) -> Path | None:
    runs = strategy_dir / "runs"
    if not runs.exists():
        return None
    files = sorted(runs.glob("*.json"))
    return files[-1] if files else None


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _resolve_price_path(symbol: str) -> Path | None:
    data_root = PROJECT_ROOT / "data"
    candidates = [
        data_root / "prices_divadj" / f"{symbol}.pkl",
        data_root / "prices" / f"{symbol}.pkl",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _load_price_series(symbol: str) -> pd.DataFrame | None:
    p = _resolve_price_path(symbol)
    if p is None:
        return None
    try:
        df = pd.read_pickle(p)
    except Exception:
        return None
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        return df
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index().rename(columns={"index": "date"})
        df = df.sort_values("date")
        return df
    return None


def _first_bar_on_or_after(df: pd.DataFrame, target_date: pd.Timestamp) -> float | None:
    if df is None or df.empty:
        return None
    idx = df["date"].searchsorted(target_date)
    if idx >= len(df):
        return None
    row = df.iloc[idx]
    if "open" in row and not pd.isna(row["open"]):
        return float(row["open"])
    if "close" in row and not pd.isna(row["close"]):
        return float(row["close"])
    return None


def _market_return_series(signal_dates, execution_delay, holding_period, market_symbol="SPY"):
    df_mkt = _load_price_series(market_symbol)
    if df_mkt is None:
        return None
    returns = {}
    for d in signal_dates:
        d = pd.to_datetime(d)
        entry_date = d + timedelta(days=int(execution_delay))
        exit_date = entry_date + timedelta(days=int(holding_period))
        entry_px = _first_bar_on_or_after(df_mkt, entry_date)
        exit_px = _first_bar_on_or_after(df_mkt, exit_date)
        if entry_px is None or exit_px is None:
            continue
        returns[d] = (exit_px / entry_px) - 1.0
    if not returns:
        return None
    return pd.Series(returns).sort_index()


def _portfolio_return_series(returns_df: pd.DataFrame) -> pd.Series:
    # Equal-weight by signal_date
    returns_df["signal_date"] = pd.to_datetime(returns_df["signal_date"])
    grouped = returns_df.groupby("signal_date")["return"].mean()
    return grouped.sort_index()


def _beta(port: pd.Series, mkt: pd.Series) -> float | None:
    common = port.index.intersection(mkt.index)
    if len(common) < 20:
        return None
    x = mkt.loc[common].values
    y = port.loc[common].values
    if np.std(x) == 0:
        return None
    return float(np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1))


def _industry_exposure(signals: pd.DataFrame, profiles: pd.DataFrame):
    if profiles is None:
        return None
    prof = profiles[["symbol", "industry", "sector"]].copy()
    merged = signals.merge(prof, on="symbol", how="left")
    coverage = 1.0 - merged["industry"].isna().mean()
    # Mean signal by industry/sector across all dates
    ind = (
        merged.groupby("industry")["signal"]
        .mean()
        .dropna()
        .sort_values(key=lambda s: s.abs(), ascending=False)
        .head(10)
    )
    sec = (
        merged.groupby("sector")["signal"]
        .mean()
        .dropna()
        .sort_values(key=lambda s: s.abs(), ascending=False)
        .head(10)
    )
    return {
        "coverage": float(coverage),
        "top_industry_mean_signal": ind.round(6).to_dict(),
        "top_sector_mean_signal": sec.round(6).to_dict(),
    }


def _turnover(signals: pd.DataFrame, top_pct=0.2):
    signals = signals.copy()
    signals["date"] = pd.to_datetime(signals["date"])
    dates = sorted(signals["date"].unique())
    if len(dates) < 2:
        return None
    overlaps = []
    for i in range(1, len(dates)):
        d0 = dates[i - 1]
        d1 = dates[i]
        s0 = signals[signals["date"] == d0]
        s1 = signals[signals["date"] == d1]
        n0 = max(1, int(len(s0) * top_pct))
        n1 = max(1, int(len(s1) * top_pct))
        top0 = set(s0.nlargest(n0, "signal")["symbol"])
        top1 = set(s1.nlargest(n1, "signal")["symbol"])
        overlap = len(top0 & top1) / max(1, len(top1))
        overlaps.append(overlap)
    return float(np.mean(overlaps))


def _size_exposure(signals: pd.DataFrame, market_cap_dir: Path, max_dates=24):
    if not market_cap_dir.exists():
        return None
    # sample dates to avoid heavy scan
    dates = sorted(pd.to_datetime(signals["date"].unique()))
    if not dates:
        return None
    if len(dates) > max_dates:
        step = len(dates) // max_dates
        dates = dates[::step]

    cap_cache = {}
    def _load_cap(symbol: str):
        if symbol in cap_cache:
            return cap_cache[symbol]
        p = market_cap_dir / f"{symbol}.csv"
        if not p.exists():
            cap_cache[symbol] = None
            return None
        try:
            df = pd.read_csv(p)
        except Exception:
            cap_cache[symbol] = None
            return None
        if "date" not in df.columns or "marketCap" not in df.columns:
            cap_cache[symbol] = None
            return None
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        cap_cache[symbol] = df
        return df

    corrs = []
    for d in dates:
        sub = signals[pd.to_datetime(signals["date"]) == d]
        if sub.empty:
            continue
        caps = []
        sigs = []
        for _, row in sub.iterrows():
            df = _load_cap(row["symbol"])
            if df is None:
                continue
            idx = df["date"].searchsorted(d, side="right") - 1
            if idx < 0:
                continue
            cap = df.iloc[idx]["marketCap"]
            if pd.isna(cap) or cap <= 0:
                continue
            caps.append(np.log(cap))
            sigs.append(row["signal"])
        if len(caps) < 30:
            continue
        corrs.append(np.corrcoef(caps, sigs)[0, 1])
    if not corrs:
        return None
    return float(np.nanmean(corrs))


def run_diagnostics(strategy_dir: Path, out_dir: Path, top_pct=0.2):
    results_dir = strategy_dir / "results"
    signals_path = results_dir / "test_signals_latest.csv"
    returns_path = results_dir / "test_returns_latest.csv"
    if not signals_path.exists() or not returns_path.exists():
        raise FileNotFoundError("Missing latest signals/returns in results/")

    signals = pd.read_csv(signals_path)
    returns_df = pd.read_csv(returns_path)

    latest_run = _find_latest_run_json(strategy_dir)
    run_cfg = _load_json(latest_run) if latest_run else {}
    exec_delay = run_cfg.get("config", {}).get("execution_delay", 1)
    holding = run_cfg.get("config", {}).get("holding_period", 20)

    # Portfolio returns + beta
    port = _portfolio_return_series(returns_df)
    mkt = _market_return_series(port.index, exec_delay, holding, market_symbol="SPY")
    beta = _beta(port, mkt) if mkt is not None else None

    # Industry exposure
    profiles_path = PROJECT_ROOT / "data" / "company_profiles.csv"
    profiles = pd.read_csv(profiles_path) if profiles_path.exists() else None
    industry = _industry_exposure(signals, profiles)

    # Turnover
    turnover = _turnover(signals, top_pct=top_pct)

    # Size exposure (optional)
    mcap_dir = PROJECT_ROOT / "data" / "fmp" / "market_cap_history"
    size_corr = _size_exposure(signals, mcap_dir, max_dates=24)

    report = {
        "strategy": strategy_dir.name,
        "run_date": datetime.now().isoformat(),
        "inputs": {
            "signals": str(signals_path),
            "returns": str(returns_path),
            "latest_run": str(latest_run) if latest_run else None,
        },
        "diagnostics": {
            "beta_vs_spy": beta,
            "turnover_top_pct_overlap": turnover,
            "industry_exposure": industry,
            "size_signal_corr_log_mcap": size_corr,
        },
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    json_path = out_dir / f"diagnostics_{ts}.json"
    json_path.write_text(json.dumps(report, indent=2))

    # Simple markdown summary
    md_path = out_dir / f"diagnostics_{ts}.md"
    lines = [
        f"# Diagnostics: {strategy_dir.name}",
        "",
        f"- Run date: {report['run_date']}",
        f"- Beta vs SPY: {beta}",
        f"- Turnover (top {int(top_pct*100)}% overlap): {turnover}",
        f"- Size corr (log mcap): {size_corr}",
        "",
        "## Industry Exposure (top 10 by |mean signal|)",
        "",
    ]
    if industry:
        for k, v in industry.get("top_industry_mean_signal", {}).items():
            lines.append(f"- {k}: {v}")
        lines += ["", "## Sector Exposure (top 10 by |mean signal|)", ""]
        for k, v in industry.get("top_sector_mean_signal", {}).items():
            lines.append(f"- {k}: {v}")
        lines += ["", f"- Industry coverage: {industry.get('coverage')}"]
    else:
        lines.append("- industry map not available")
    md_path.write_text("\n".join(lines))

    return json_path, md_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", type=str, help="strategy dir, e.g. strategies/value_v1")
    parser.add_argument("--all", action="store_true", help="run for all strategies with results")
    parser.add_argument("--top-pct", type=float, default=0.2)
    args = parser.parse_args()

    if not args.strategy and not args.all:
        raise SystemExit("Provide --strategy or --all")

    if args.all:
        strategies = sorted((PROJECT_ROOT / "strategies").glob("*_v1"))
    else:
        strategies = [Path(args.strategy)]
        if not strategies[0].is_absolute():
            strategies[0] = PROJECT_ROOT / strategies[0]

    for strat in strategies:
        results_dir = strat / "results"
        if not results_dir.exists():
            continue
        out_dir = strat / "reports"
        print(f"[diag] {strat.name}")
        run_diagnostics(strat, out_dir, top_pct=args.top_pct)


if __name__ == "__main__":
    main()
