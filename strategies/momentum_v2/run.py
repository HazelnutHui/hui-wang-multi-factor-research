import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Ensure project root importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

# Load local config
from pathlib import Path as _Path
import importlib.util as _ilu
_cfg_path = _Path(__file__).resolve().parent / "config.py"
_spec = _ilu.spec_from_file_location("momentum_v2_config", _cfg_path)
cfg = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(cfg)

from backtest.backtest_engine import BacktestEngine
import backtest.config as core

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_path(p: str) -> str:
    path = Path(p)
    if path.is_absolute():
        return str(path.resolve())
    base = Path(core.__file__).resolve().parent
    return str((base / p).resolve())


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


def _make_engine_config():
    price_active, price_delisted = _pick_price_dirs()
    return {
        'PRICE_DIR_ACTIVE': price_active,
        'PRICE_DIR_DELISTED': price_delisted,
        'DELISTED_INFO': str(PROJECT_ROOT / 'data' / 'delisted_companies_2010_2026.csv'),

        'MIN_MARKET_CAP': cfg.MIN_MARKET_CAP,
        'MIN_DOLLAR_VOLUME': cfg.MIN_DOLLAR_VOLUME,
        'MIN_PRICE': cfg.MIN_PRICE,

        'TRANSACTION_COST': cfg.TRANSACTION_COST,
        'EXECUTION_DELAY': cfg.EXECUTION_DELAY,

        'CALENDAR_SYMBOL': getattr(cfg, 'CALENDAR_SYMBOL', 'SPY'),
        'REBALANCE_MODE': getattr(cfg, 'REBALANCE_MODE', None),
        'EXECUTION_USE_TRADING_DAYS': getattr(cfg, 'EXECUTION_USE_TRADING_DAYS', False),
        'ENABLE_DYNAMIC_COST': getattr(cfg, 'ENABLE_DYNAMIC_COST', False),
        'TRADE_SIZE_USD': getattr(cfg, 'TRADE_SIZE_USD', 10000),

        'MOMENTUM_LOOKBACK': cfg.MOMENTUM_LOOKBACK,
        'MOMENTUM_SKIP': cfg.MOMENTUM_SKIP,
        'MOMENTUM_VOL_LOOKBACK': cfg.MOMENTUM_VOL_LOOKBACK,
        'MOMENTUM_USE_MONTHLY': cfg.MOMENTUM_USE_MONTHLY,
        'MOMENTUM_LOOKBACK_MONTHS': cfg.MOMENTUM_LOOKBACK_MONTHS,
        'MOMENTUM_SKIP_MONTHS': cfg.MOMENTUM_SKIP_MONTHS,
        'MOMENTUM_ZSCORE': cfg.MOMENTUM_ZSCORE,
        'MOMENTUM_WINSOR_Z': cfg.MOMENTUM_WINSOR_Z,
        'MOMENTUM_USE_RESIDUAL': getattr(cfg, 'MOMENTUM_USE_RESIDUAL', False),
        'MOMENTUM_BENCH_SYMBOL': getattr(cfg, 'MOMENTUM_BENCH_SYMBOL', 'SPY'),
        'MOMENTUM_RESID_EST_WINDOW': getattr(cfg, 'MOMENTUM_RESID_EST_WINDOW', 252),

        'INDUSTRY_NEUTRAL': cfg.INDUSTRY_NEUTRAL,
        'INDUSTRY_MIN_GROUP': cfg.INDUSTRY_MIN_GROUP,
        'INDUSTRY_COL': cfg.INDUSTRY_COL,
        'INDUSTRY_MAP_PATH': _resolve_path(cfg.INDUSTRY_MAP_PATH),

        'UNIVERSE_MAX_VOL': cfg.UNIVERSE_MAX_VOL,
        'UNIVERSE_VOL_LOOKBACK': cfg.UNIVERSE_VOL_LOOKBACK,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--long-pct", type=float, default=0.2)
    parser.add_argument("--short-pct", type=float, default=0.0)
    args = parser.parse_args()

    cfg_dict = _make_engine_config()
    engine = BacktestEngine(cfg_dict)

    factor_weights = {'momentum': 1.0, 'reversal': 0.0, 'low_vol': 0.0, 'pead': 0.0}

    results = engine.run_out_of_sample_test(
        train_start=cfg.TRAIN_START, train_end=cfg.TRAIN_END,
        test_start=cfg.TEST_START, test_end=cfg.TEST_END,
        factor_weights=factor_weights,
        rebalance_freq=cfg.REBALANCE_FREQ,
        holding_period=cfg.HOLDING_PERIOD,
        long_pct=args.long_pct, short_pct=args.short_pct
    )

    # Save outputs
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    train_sig_path = out_dir / f"train_signals_{ts}.csv"
    train_ret_path = out_dir / f"train_returns_{ts}.csv"
    test_sig_path  = out_dir / f"test_signals_{ts}.csv"
    test_ret_path  = out_dir / f"test_returns_{ts}.csv"

    results['train']['signals'].to_csv(train_sig_path, index=False)
    results['train']['returns'].to_csv(train_ret_path, index=False)
    results['test']['signals'].to_csv(test_sig_path, index=False)
    results['test']['returns'].to_csv(test_ret_path, index=False)

    results['train']['signals'].to_csv(out_dir / "train_signals_latest.csv", index=False)
    results['train']['returns'].to_csv(out_dir / "train_returns_latest.csv", index=False)
    results['test']['signals'].to_csv(out_dir / "test_signals_latest.csv", index=False)
    results['test']['returns'].to_csv(out_dir / "test_returns_latest.csv", index=False)

    report = {
        "metadata": {
            "strategy": cfg.STRATEGY_NAME,
            "version": cfg.STRATEGY_VERSION,
            "run_date": datetime.now().isoformat(),
        },
        "config": {
            "momentum_lookback": cfg.MOMENTUM_LOOKBACK,
            "momentum_skip": cfg.MOMENTUM_SKIP,
            "holding_period": cfg.HOLDING_PERIOD,
            "rebalance_freq": cfg.REBALANCE_FREQ,
            "execution_delay": cfg.EXECUTION_DELAY,
            "execution_use_trading_days": getattr(cfg, "EXECUTION_USE_TRADING_DAYS", False),
            "enable_dynamic_cost": getattr(cfg, "ENABLE_DYNAMIC_COST", False),
            "trade_size_usd": getattr(cfg, "TRADE_SIZE_USD", 10000),
            "transaction_cost": cfg.TRANSACTION_COST,
            "use_adj_prices": getattr(cfg, "USE_ADJ_PRICES", False),
        },
        "performance": {
            "train": _json_safe(results['train']['analysis']),
            "test": _json_safe(results['test']['analysis']),
            "oos": _json_safe(results.get('oos_analysis', {})),
        },
        "output_files": {
            "csv_files": {
                "train_signals": str(train_sig_path.relative_to(out_dir.parent)),
                "train_returns": str(train_ret_path.relative_to(out_dir.parent)),
                "test_signals": str(test_sig_path.relative_to(out_dir.parent)),
                "test_returns": str(test_ret_path.relative_to(out_dir.parent)),
            },
            "latest_files": {
                "train_signals": "results/train_signals_latest.csv",
                "train_returns": "results/train_returns_latest.csv",
                "test_signals": "results/test_signals_latest.csv",
                "test_returns": "results/test_returns_latest.csv",
            }
        }
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
    print(f"Signals (test):     {results['test']['analysis'].get('n_signals')}")
    print(f"Saved report:       {run_path.relative_to(out_dir.parent)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
