import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    import yaml
except Exception as exc:
    raise SystemExit("Missing dependency: PyYAML. Install with `pip install pyyaml`.") from exc

from backtest.backtest_engine import BacktestEngine


def _json_safe(obj: Any) -> Any:
    try:
        import pandas as pd
        import numpy as np
    except Exception:
        pd = None
        np = None

    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]

    if pd is not None:
        if isinstance(obj, pd.DataFrame):
            max_cells = 5000
            cells = int(obj.shape[0]) * int(obj.shape[1])
            if cells <= max_cells:
                return {
                    "__type__": "DataFrame",
                    "shape": list(obj.shape),
                    "data": obj.to_dict(orient="records"),
                }
            return {
                "__type__": "DataFrame",
                "shape": list(obj.shape),
                "columns": list(obj.columns),
                "sample": obj.head(5).to_dict(orient="records"),
            }
        if isinstance(obj, pd.Series):
            return {
                "__type__": "Series",
                "shape": [int(obj.shape[0])],
                "data": obj.to_dict(),
            }

    if np is not None and isinstance(obj, np.generic):
        return obj.item()
    return obj


def _load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML (expected dict): {path}")
    return data


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _resolve_path(base_dir: Path, p: Any) -> Any:
    if p is None:
        return None
    if not isinstance(p, str):
        return p
    path = Path(p)
    if path.is_absolute():
        return str(path)
    return str((base_dir / path).resolve())


def _pick_price_dirs(paths: Dict[str, Any], use_adj: bool, base_dir: Path) -> tuple[str, str]:
    adj_active = Path(_resolve_path(base_dir, paths.get("price_dir_active_adj")))
    adj_del = Path(_resolve_path(base_dir, paths.get("price_dir_delisted_adj")))
    if use_adj and adj_active.exists() and adj_del.exists():
        if any(adj_active.glob("*.pkl")) or any(adj_del.glob("*.pkl")):
            return str(adj_active), str(adj_del)
    active = _resolve_path(base_dir, paths.get("price_dir_active"))
    delisted = _resolve_path(base_dir, paths.get("price_dir_delisted"))
    return str(active), str(delisted)


def _build_engine_config(cfg: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
    paths = cfg.get("paths", {})
    universe = cfg.get("universe", {})
    execution = cfg.get("execution", {})
    calendar = cfg.get("calendar", {})
    neutral = cfg.get("neutralization", {})
    factors = cfg.get("factors", {})
    momentum = factors.get("momentum", {})
    pead = factors.get("pead", {})
    reversal = factors.get("reversal", {})
    quality = factors.get("quality", {})
    value = factors.get("value", {})
    low_vol = factors.get("low_vol", {})
    data_sel = cfg.get("data_selection", {})

    use_adj = bool(data_sel.get("use_adj_prices", False))
    price_active, price_delisted = _pick_price_dirs(paths, use_adj, base_dir)

    config = {
        "PRICE_DIR_ACTIVE": price_active,
        "PRICE_DIR_DELISTED": price_delisted,
        "DELISTED_INFO": _resolve_path(base_dir, paths.get("delisted_info")),
        "EARNINGS_DIR": _resolve_path(base_dir, paths.get("earnings_dir")),
        "FUNDAMENTALS_DIR": _resolve_path(base_dir, paths.get("fundamentals_dir")),
        "VALUE_DIR": _resolve_path(base_dir, paths.get("value_dir")),
        "INDUSTRY_MAP_PATH": _resolve_path(base_dir, paths.get("industry_map_path")),
        "MARKET_CAP_DIR": _resolve_path(base_dir, paths.get("market_cap_dir")),
        "MARKET_CAP_STRICT": universe.get("market_cap_strict"),

        "MIN_MARKET_CAP": universe.get("min_market_cap"),
        "MIN_DOLLAR_VOLUME": universe.get("min_dollar_volume"),
        "MIN_PRICE": universe.get("min_price"),
        "UNIVERSE_MAX_VOL": universe.get("max_volatility"),
        "UNIVERSE_VOL_LOOKBACK": universe.get("vol_lookback"),
        "UNIVERSE_EXCLUDE_SYMBOLS_PATH": universe.get("exclude_symbols_path"),

        "TRANSACTION_COST": execution.get("transaction_cost"),
        "EXECUTION_DELAY": execution.get("execution_delay"),
        "EXECUTION_USE_TRADING_DAYS": execution.get("execution_use_trading_days"),
        "ENABLE_DYNAMIC_COST": execution.get("enable_dynamic_cost"),
        "TRADE_SIZE_USD": execution.get("trade_size_usd"),
        "APPLY_LIMIT_UP_DOWN": execution.get("apply_limit_up_down"),
        "LIMIT_UP_DOWN_PCT": execution.get("limit_up_down_pct"),
        "APPLY_STAMP_TAX": execution.get("apply_stamp_tax"),
        "STAMP_TAX_RATE": execution.get("stamp_tax_rate"),

        "CALENDAR_SYMBOL": calendar.get("calendar_symbol"),
        "REBALANCE_MODE": calendar.get("rebalance_mode"),

        "MOMENTUM_LOOKBACK": momentum.get("lookback"),
        "MOMENTUM_SKIP": momentum.get("skip"),
        "MOMENTUM_VOL_LOOKBACK": momentum.get("vol_lookback"),
        "MOMENTUM_USE_MONTHLY": momentum.get("use_monthly"),
        "MOMENTUM_LOOKBACK_MONTHS": momentum.get("lookback_months"),
        "MOMENTUM_SKIP_MONTHS": momentum.get("skip_months"),
        "MOMENTUM_ZSCORE": momentum.get("zscore"),
        "MOMENTUM_WINSOR_Z": momentum.get("winsor_z"),
        "MOMENTUM_LAG_DAYS": momentum.get("lag_days"),

        "SUE_THRESHOLD": pead.get("sue_threshold"),
        "LOOKBACK_QUARTERS": pead.get("lookback_quarters"),
        "DATE_SHIFT_DAYS": pead.get("date_shift_days"),
        "PEAD_EVENT_MAX_AGE_DAYS": pead.get("event_max_age_days"),
        "PEAD_LAG_DAYS": pead.get("lag_days"),

        "REVERSAL_LOOKBACK": reversal.get("lookback"),
        "REVERSAL_MODE": reversal.get("mode"),
        "REVERSAL_VOL_LOOKBACK": reversal.get("vol_lookback"),
        "REVERSAL_EARNINGS_FILTER_DAYS": reversal.get("earnings_filter_days"),
        "REVERSAL_LAG_DAYS": reversal.get("lag_days"),

        "QUALITY_WEIGHTS": quality.get("weights"),
        "QUALITY_MAX_STALENESS_DAYS": quality.get("max_staleness_days"),
        "QUALITY_LAG_DAYS": quality.get("lag_days"),
        "VALUE_WEIGHTS": value.get("weights"),
        "VALUE_MAX_STALENESS_DAYS": value.get("max_staleness_days"),
        "VALUE_LAG_DAYS": value.get("lag_days"),
        "LOW_VOL_LAG_DAYS": low_vol.get("lag_days"),
        "BETA_LOOKBACK": factors.get("beta", {}).get("lookback"),
        "BETA_BENCH_SYMBOL": factors.get("beta", {}).get("bench_symbol"),
        "BETA_USE_LOG_RETURN": factors.get("beta", {}).get("use_log_return"),
        "BETA_LAG_DAYS": factors.get("beta", {}).get("lag_days"),

        "INDUSTRY_NEUTRAL": neutral.get("industry_neutral"),
        "INDUSTRY_MIN_GROUP": neutral.get("industry_min_group"),
        "INDUSTRY_COL": neutral.get("industry_col"),
        "SIGNAL_ZSCORE": neutral.get("signal_zscore"),
        "SIGNAL_WINSOR_Z": neutral.get("signal_winsor_z"),
        "SIGNAL_WINSOR_PCT_LOW": neutral.get("signal_winsor_pct_low"),
        "SIGNAL_WINSOR_PCT_HIGH": neutral.get("signal_winsor_pct_high"),
        "SIGNAL_RANK": neutral.get("signal_rank"),
        "SIGNAL_RANK_METHOD": neutral.get("signal_rank_method"),
        "SIGNAL_RANK_PCT": neutral.get("signal_rank_pct"),
        "SIGNAL_MISSING_POLICY": neutral.get("signal_missing_policy"),
        "SIGNAL_MISSING_FILL": neutral.get("signal_missing_fill"),
        "SIGNAL_SMOOTH_WINDOW": neutral.get("signal_smooth_window"),
        "SIGNAL_SMOOTH_METHOD": neutral.get("signal_smooth_method"),
        "SIGNAL_SMOOTH_ALPHA": neutral.get("signal_smooth_alpha"),
        "SIGNAL_NEUTRALIZE_SIZE": neutral.get("signal_neutralize_size"),
        "SIGNAL_NEUTRALIZE_BETA": neutral.get("signal_neutralize_beta"),
        "SIGNAL_NEUTRALIZE_COLS": neutral.get("signal_neutralize_cols"),

        "FACTOR_LAG_DAYS": factors.get("lag_days", 0),
        "SIGNALS_INCLUDE_FACTORS": bool(factors.get("include_components", False)),
    }

    # Optional PEAD factor class
    if pead.get("use_shifted_factor"):
        try:
            from strategies.pead_v1.factor import ShiftedPEADFactor
            config["PEAD_FACTOR_CLASS"] = ShiftedPEADFactor
        except Exception:
            pass

    return config


def _validate_weights(weights: Dict[str, Any]) -> Dict[str, float]:
    if not isinstance(weights, dict) or len(weights) == 0:
        raise ValueError("factors.weights must be a non-empty mapping")
    out = {}
    for k, v in weights.items():
        if v is None:
            continue
        out[str(k)] = float(v)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", default=str(ROOT / "configs" / "protocol.yaml"))
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--long-pct", type=float, default=None)
    parser.add_argument("--short-pct", type=float, default=None)
    parser.add_argument("--cost-multiplier", type=float, default=None)
    args = parser.parse_args()

    protocol_path = Path(args.protocol).resolve()
    strategy_path = Path(args.strategy).resolve()
    protocol = _load_yaml(protocol_path)
    strategy = _load_yaml(strategy_path)

    merged = _deep_merge(protocol, strategy)

    base_dir = protocol_path.parent
    engine_cfg = _build_engine_config(merged, base_dir)
    if args.cost_multiplier is not None:
        engine_cfg["COST_MULTIPLIER"] = float(args.cost_multiplier)

    execution = merged.get("execution", {})
    long_pct = execution.get("long_pct", 0.2) if args.long_pct is None else args.long_pct
    short_pct = execution.get("short_pct", 0.0) if args.short_pct is None else args.short_pct
    rebalance_freq = execution.get("rebalance_freq")
    holding_period = execution.get("holding_period")

    periods = merged.get("backtest_periods", {})

    weights = _validate_weights(merged.get("factors", {}).get("weights", {}))

    engine = BacktestEngine(engine_cfg)

    results = engine.run_out_of_sample_test(
        train_start=periods.get("train_start"),
        train_end=periods.get("train_end"),
        test_start=periods.get("test_start"),
        test_end=periods.get("test_end"),
        factor_weights=weights,
        rebalance_freq=rebalance_freq,
        holding_period=holding_period,
        long_pct=long_pct,
        short_pct=short_pct,
    )

    strategy_meta = merged.get("strategy", {})
    output_dir = strategy_meta.get("output_dir", "strategies/run_with_config")
    out_root = (ROOT / output_dir).resolve()
    results_dir = out_root / "results"
    runs_dir = out_root / "runs"
    results_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # CSV outputs
    train_sig_path = results_dir / f"train_signals_{ts}.csv"
    train_ret_path = results_dir / f"train_returns_{ts}.csv"
    test_sig_path = results_dir / f"test_signals_{ts}.csv"
    test_ret_path = results_dir / f"test_returns_{ts}.csv"

    results["train"]["signals"].to_csv(train_sig_path, index=False)
    results["train"]["returns"].to_csv(train_ret_path, index=False)
    results["test"]["signals"].to_csv(test_sig_path, index=False)
    results["test"]["returns"].to_csv(test_ret_path, index=False)

    results["train"]["signals"].to_csv(results_dir / "train_signals_latest.csv", index=False)
    results["train"]["returns"].to_csv(results_dir / "train_returns_latest.csv", index=False)
    results["test"]["signals"].to_csv(results_dir / "test_signals_latest.csv", index=False)
    results["test"]["returns"].to_csv(results_dir / "test_returns_latest.csv", index=False)

    report = {
        "metadata": {
            "strategy": strategy_meta.get("name"),
            "strategy_id": strategy_meta.get("id"),
            "strategy_version": strategy_meta.get("version"),
            "protocol_version": merged.get("protocol", {}).get("version"),
            "run_date": datetime.now().isoformat(),
        },
        "config": _json_safe(merged),
        "performance": {
            "train": _json_safe(results["train"]["analysis"]),
            "test": _json_safe(results["test"]["analysis"]),
            "oos": _json_safe(results.get("oos_analysis", {})),
        },
        "output_files": {
            "csv_files": {
                "train_signals": str(train_sig_path.relative_to(out_root)),
                "train_returns": str(train_ret_path.relative_to(out_root)),
                "test_signals": str(test_sig_path.relative_to(out_root)),
                "test_returns": str(test_ret_path.relative_to(out_root)),
            },
            "latest_files": {
                "train_signals": "results/train_signals_latest.csv",
                "train_returns": "results/train_returns_latest.csv",
                "test_signals": "results/test_signals_latest.csv",
                "test_returns": "results/test_returns_latest.csv",
            },
            "protocol_yaml": str(protocol_path),
            "strategy_yaml": str(strategy_path),
        },
    }

    run_path = runs_dir / f"{ts}.json"
    with open(run_path, "w") as f:
        json.dump(report, f, indent=2)

    print("=" * 70)
    print(f"{strategy_meta.get('name')} v{strategy_meta.get('version')}")
    print("=" * 70)
    print(f"Train IC (overall): {results['train']['analysis'].get('ic')}")
    print(f"Test  IC (overall): {results['test']['analysis'].get('ic')}")
    print(f"Signals (test):     {results['test']['analysis'].get('n_signals')}")
    print(f"Saved report:       {run_path.relative_to(out_root)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
