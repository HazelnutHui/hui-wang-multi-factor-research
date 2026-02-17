import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from pathlib import Path as _Path
import importlib.util as _ilu

_cfg_path = _Path(__file__).resolve().parent / "config.py"
_spec = _ilu.spec_from_file_location("combo_v2_config", _cfg_path)
cfg = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(cfg)

from backtest.backtest_engine import BacktestEngine
import backtest.config as core

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_path(p: str) -> str:
    path = Path(p)
    if path.is_absolute():
        return str(path.resolve())
    if str(path).startswith("data/") or str(path).startswith("data\\"):
        return str((PROJECT_ROOT / path).resolve())
    base = Path(core.__file__).resolve().parent
    return str((base / path).resolve())


def _pick_price_dirs():
    adj_active = Path(_resolve_path(getattr(core, "PRICE_DIR_ACTIVE_ADJ", "")))
    adj_del = Path(_resolve_path(getattr(core, "PRICE_DIR_DELISTED_ADJ", "")))
    use_adj = getattr(cfg, "USE_ADJ_PRICES", False) or getattr(core, "USE_ADJ_PRICES", False)
    if use_adj and adj_active.exists() and adj_del.exists():
        if any(adj_active.glob("*.pkl")) or any(adj_del.glob("*.pkl")):
            return str(adj_active), str(adj_del)
    return _resolve_path(core.PRICE_DIR_ACTIVE), _resolve_path(core.PRICE_DIR_DELISTED)


def _json_safe(obj):
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
            return {"__type__": "DataFrame", "shape": list(obj.shape), "sample": obj.head(5).to_dict(orient="records")}
        if isinstance(obj, pd.Series):
            return {"__type__": "Series", "shape": [int(obj.shape[0])], "data": obj.head(20).to_dict()}
    if np is not None and isinstance(obj, np.generic):
        return obj.item()
    return obj


def _make_engine_config():
    price_active, price_delisted = _pick_price_dirs()
    return {
        "PRICE_DIR_ACTIVE": price_active,
        "PRICE_DIR_DELISTED": price_delisted,
        "DELISTED_INFO": str(PROJECT_ROOT / "data" / "delisted_companies_2010_2026.csv"),
        "MIN_MARKET_CAP": cfg.MIN_MARKET_CAP,
        "MIN_DOLLAR_VOLUME": cfg.MIN_DOLLAR_VOLUME,
        "MIN_PRICE": cfg.MIN_PRICE,
        "TRANSACTION_COST": cfg.TRANSACTION_COST,
        "EXECUTION_DELAY": cfg.EXECUTION_DELAY,
        "EXECUTION_USE_TRADING_DAYS": cfg.EXECUTION_USE_TRADING_DAYS,
        "ENABLE_DYNAMIC_COST": cfg.ENABLE_DYNAMIC_COST,
        "TRADE_SIZE_USD": cfg.TRADE_SIZE_USD,
        "CALENDAR_SYMBOL": cfg.CALENDAR_SYMBOL,
        "REBALANCE_MODE": getattr(cfg, "REBALANCE_MODE", None),
        "MOMENTUM_LOOKBACK": cfg.MOMENTUM_LOOKBACK,
        "MOMENTUM_SKIP": cfg.MOMENTUM_SKIP,
        "MOMENTUM_USE_MONTHLY": cfg.MOMENTUM_USE_MONTHLY,
        "MOMENTUM_LOOKBACK_MONTHS": cfg.MOMENTUM_LOOKBACK_MONTHS,
        "MOMENTUM_SKIP_MONTHS": cfg.MOMENTUM_SKIP_MONTHS,
        "MOMENTUM_USE_RESIDUAL": cfg.MOMENTUM_USE_RESIDUAL,
        "MOMENTUM_BENCH_SYMBOL": cfg.MOMENTUM_BENCH_SYMBOL,
        "MOMENTUM_RESID_EST_WINDOW": cfg.MOMENTUM_RESID_EST_WINDOW,
        "MOMENTUM_ZSCORE": cfg.MOMENTUM_ZSCORE,
        "MOMENTUM_WINSOR_Z": cfg.MOMENTUM_WINSOR_Z,
        "VALUE_WEIGHTS": cfg.VALUE_WEIGHTS,
        "VALUE_DIR": _resolve_path(cfg.VALUE_DIR),
        "VALUE_MAINSTREAM_COMPOSITE": cfg.VALUE_MAINSTREAM_COMPOSITE,
        "VALUE_COMPONENT_TRANSFORM": cfg.VALUE_COMPONENT_TRANSFORM,
        "VALUE_COMPONENT_INDUSTRY_ZSCORE": cfg.VALUE_COMPONENT_INDUSTRY_ZSCORE,
        "VALUE_COMPONENT_WINSOR_PCT_LOW": cfg.VALUE_COMPONENT_WINSOR_PCT_LOW,
        "VALUE_COMPONENT_WINSOR_PCT_HIGH": cfg.VALUE_COMPONENT_WINSOR_PCT_HIGH,
        "VALUE_COMPONENT_MIN_COUNT": cfg.VALUE_COMPONENT_MIN_COUNT,
        "VALUE_COMPONENT_MISSING_POLICY": cfg.VALUE_COMPONENT_MISSING_POLICY,
        "QUALITY_WEIGHTS": cfg.QUALITY_WEIGHTS,
        "FUNDAMENTALS_DIR": _resolve_path(cfg.FUNDAMENTALS_DIR),
        "QUALITY_MAINSTREAM_COMPOSITE": cfg.QUALITY_MAINSTREAM_COMPOSITE,
        "QUALITY_COMPONENT_TRANSFORM": cfg.QUALITY_COMPONENT_TRANSFORM,
        "QUALITY_COMPONENT_INDUSTRY_ZSCORE": cfg.QUALITY_COMPONENT_INDUSTRY_ZSCORE,
        "QUALITY_COMPONENT_WINSOR_PCT_LOW": cfg.QUALITY_COMPONENT_WINSOR_PCT_LOW,
        "QUALITY_COMPONENT_WINSOR_PCT_HIGH": cfg.QUALITY_COMPONENT_WINSOR_PCT_HIGH,
        "QUALITY_COMPONENT_MIN_COUNT": cfg.QUALITY_COMPONENT_MIN_COUNT,
        "QUALITY_COMPONENT_MISSING_POLICY": cfg.QUALITY_COMPONENT_MISSING_POLICY,
        "SIGNAL_ZSCORE": cfg.SIGNAL_ZSCORE,
        "SIGNAL_RANK": cfg.SIGNAL_RANK,
        "SIGNAL_WINSOR_PCT_LOW": cfg.SIGNAL_WINSOR_PCT_LOW,
        "SIGNAL_WINSOR_PCT_HIGH": cfg.SIGNAL_WINSOR_PCT_HIGH,
        "SIGNAL_MISSING_POLICY": getattr(cfg, "SIGNAL_MISSING_POLICY", "drop"),
        "INDUSTRY_NEUTRAL": cfg.INDUSTRY_NEUTRAL,
        "INDUSTRY_MIN_GROUP": cfg.INDUSTRY_MIN_GROUP,
        "INDUSTRY_COL": cfg.INDUSTRY_COL,
        "INDUSTRY_MAP_PATH": _resolve_path(cfg.INDUSTRY_MAP_PATH),
        "SIGNAL_NEUTRALIZE_SIZE": cfg.SIGNAL_NEUTRALIZE_SIZE,
        "SIGNAL_NEUTRALIZE_BETA": cfg.SIGNAL_NEUTRALIZE_BETA,
        "SIGNAL_NEUTRALIZE_COLS": cfg.SIGNAL_NEUTRALIZE_COLS,
        "BETA_LOOKBACK": cfg.BETA_LOOKBACK,
        "BETA_BENCH_SYMBOL": cfg.BETA_BENCH_SYMBOL,
        "BETA_USE_LOG_RETURN": cfg.BETA_USE_LOG_RETURN,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--long-pct", type=float, default=0.2)
    parser.add_argument("--short-pct", type=float, default=0.0)
    args = parser.parse_args()

    engine = BacktestEngine(_make_engine_config())
    factor_weights = dict(cfg.COMBO_WEIGHTS)

    results = engine.run_out_of_sample_test(
        train_start=cfg.TRAIN_START,
        train_end=cfg.TRAIN_END,
        test_start=cfg.TEST_START,
        test_end=cfg.TEST_END,
        factor_weights=factor_weights,
        rebalance_freq=cfg.REBALANCE_FREQ,
        holding_period=cfg.HOLDING_PERIOD,
        long_pct=args.long_pct,
        short_pct=args.short_pct,
    )

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    results["train"]["signals"].to_csv(out_dir / f"train_signals_{ts}.csv", index=False)
    results["train"]["returns"].to_csv(out_dir / f"train_returns_{ts}.csv", index=False)
    results["test"]["signals"].to_csv(out_dir / f"test_signals_{ts}.csv", index=False)
    results["test"]["returns"].to_csv(out_dir / f"test_returns_{ts}.csv", index=False)

    results["train"]["signals"].to_csv(out_dir / "train_signals_latest.csv", index=False)
    results["train"]["returns"].to_csv(out_dir / "train_returns_latest.csv", index=False)
    results["test"]["signals"].to_csv(out_dir / "test_signals_latest.csv", index=False)
    results["test"]["returns"].to_csv(out_dir / "test_returns_latest.csv", index=False)

    report = {
        "metadata": {"strategy": cfg.STRATEGY_NAME, "version": cfg.STRATEGY_VERSION, "run_date": datetime.now().isoformat()},
        "config": {
            "combo_weights": factor_weights,
            "holding_period": cfg.HOLDING_PERIOD,
            "rebalance_freq": cfg.REBALANCE_FREQ,
            "execution_delay": cfg.EXECUTION_DELAY,
            "transaction_cost": cfg.TRANSACTION_COST,
            "execution_use_trading_days": cfg.EXECUTION_USE_TRADING_DAYS,
            "enable_dynamic_cost": cfg.ENABLE_DYNAMIC_COST,
            "trade_size_usd": cfg.TRADE_SIZE_USD,
        },
        "performance": {
            "train": _json_safe(results["train"]["analysis"]),
            "test": _json_safe(results["test"]["analysis"]),
            "oos": _json_safe(results.get("oos_analysis", {})),
        },
    }

    runs_dir = Path(__file__).resolve().parent / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_path = runs_dir / f"{ts}.json"
    with open(run_path, "w") as f:
        json.dump(report, f, indent=2)

    print("=" * 70)
    print(f"{cfg.STRATEGY_NAME} v{cfg.STRATEGY_VERSION}")
    print("=" * 70)
    print(f"Train IC (overall): {results['train']['analysis'].get('ic')}")
    print(f"Test  IC (overall): {results['test']['analysis'].get('ic')}")
    print(f"Saved report:       {run_path.relative_to(out_dir.parent)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
