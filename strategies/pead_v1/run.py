import os, sys

# Ensure project root + backtest are importable when running from strategies/*
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKTEST_DIR = os.path.join(ROOT, "backtest")
sys.path.insert(0, ROOT)
# sys.path.insert(0, BACKTEST_DIR)  # disabled: use package imports
# Force-load local strategies/pead_v1/config.py (avoid backtest/config.py collision)
from pathlib import Path as _Path
import importlib.util as _ilu
_cfg_path = _Path(__file__).resolve().parent / "config.py"
_spec = _ilu.spec_from_file_location("pead_v1_config", _cfg_path)
cfg = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(cfg)


import os
import json
import argparse
from datetime import datetime

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # v4/
# Use patched backtest engine + patched execution simulator
from backtest.backtest_engine import BacktestEngine
import backtest.config as core

# Patch factor to shifted version for this strategy
from .factor import ShiftedPEADFactor
from .report import generate_report, compare_with_baseline


def _resolve_path(p: str) -> str:
    path = Path(p)
    if path.is_absolute():
        return str(path.resolve())
    base = Path(core.__file__).resolve().parent
    return str((base / p).resolve())


def _make_engine_config():
    def _pick_price_dirs():
        adj_active = Path(_resolve_path(core.PRICE_DIR_ACTIVE_ADJ))
        adj_del = Path(_resolve_path(core.PRICE_DIR_DELISTED_ADJ))
        use_adj = getattr(cfg, "USE_ADJ_PRICES", False) or getattr(core, "USE_ADJ_PRICES", False)
        if use_adj and adj_active.exists() and adj_del.exists():
            if any(adj_active.glob("*.pkl")) or any(adj_del.glob("*.pkl")):
                return str(adj_active), str(adj_del)
        return _resolve_path(core.PRICE_DIR_ACTIVE), _resolve_path(core.PRICE_DIR_DELISTED)

    price_active, price_delisted = _pick_price_dirs()

    return {
        'PRICE_DIR_ACTIVE': price_active,
        'PRICE_DIR_DELISTED': price_delisted,
        'DELISTED_INFO': str(PROJECT_ROOT / 'data' / 'delisted_companies_2010_2026.csv'),

        'MIN_MARKET_CAP': cfg.MIN_MARKET_CAP,
        'MIN_DOLLAR_VOLUME': cfg.MIN_DOLLAR_VOLUME,
        'MIN_PRICE': cfg.MIN_PRICE,

        'SUE_THRESHOLD': cfg.SUE_THRESHOLD,
        'LOOKBACK_QUARTERS': cfg.LOOKBACK_QUARTERS,
        'DATE_SHIFT_DAYS': cfg.DATE_SHIFT_DAYS,

        'TRANSACTION_COST': cfg.TRANSACTION_COST,
        'EXECUTION_DELAY': cfg.EXECUTION_DELAY + (1 if getattr(cfg, 'PEAD_T1_EXECUTION', False) else 0),
        'EXECUTION_USE_TRADING_DAYS': getattr(cfg, 'EXECUTION_USE_TRADING_DAYS', False),
        'ENABLE_DYNAMIC_COST': getattr(cfg, 'ENABLE_DYNAMIC_COST', False),
        'TRADE_SIZE_USD': getattr(cfg, 'TRADE_SIZE_USD', 10000),

        'CALENDAR_SYMBOL': getattr(cfg, 'CALENDAR_SYMBOL', 'SPY'),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-baseline", action="store_true")
    parser.add_argument("--long-pct", type=float, default=0.2)
    parser.add_argument("--short-pct", type=float, default=0.0)
    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    here = os.path.dirname(__file__)

    cfg_dict = _make_engine_config()
    cfg_dict['PEAD_FACTOR_CLASS'] = ShiftedPEADFactor
    engine = BacktestEngine(cfg_dict)

    factor_weights = {'momentum': 0.0, 'reversal': 0.0, 'low_vol': 0.0, 'pead': 1.0}

    results = engine.run_out_of_sample_test(
        train_start=cfg.TRAIN_START, train_end=cfg.TRAIN_END,
        test_start=cfg.TEST_START, test_end=cfg.TEST_END,
        factor_weights=factor_weights,
        rebalance_freq=cfg.REBALANCE_FREQ,
        holding_period=cfg.HOLDING_PERIOD,
        long_pct=args.long_pct, short_pct=args.short_pct
    )

    # Attach engine so report can access factor_engine/universe_builder for coverage
    results['_engine'] = engine

    strategy_rules = {
        "alignment": cfg.ALIGNMENT_RULES,
        "execution": {
            "delay_days": cfg.EXECUTION_DELAY,
            "holding_days": cfg.HOLDING_PERIOD,
            "transaction_cost_bps": cfg.TRANSACTION_COST * 10000,
            "execution_use_trading_days": getattr(cfg, "EXECUTION_USE_TRADING_DAYS", False),
            "enable_dynamic_cost": getattr(cfg, "ENABLE_DYNAMIC_COST", False),
            "trade_size_usd": getattr(cfg, "TRADE_SIZE_USD", 10000),
        }
    }

    report = generate_report(repo_root, results, cfg, strategy_rules=strategy_rules)

    # Save detailed CSV outputs (latest + timestamped)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = os.path.join(here, "results")
    os.makedirs(out_dir, exist_ok=True)

    # Timestamped
    train_sig_path = os.path.join(out_dir, f"train_signals_{ts}.csv")
    train_ret_path = os.path.join(out_dir, f"train_returns_{ts}.csv")
    test_sig_path  = os.path.join(out_dir, f"test_signals_{ts}.csv")
    test_ret_path  = os.path.join(out_dir, f"test_returns_{ts}.csv")

    results['train']['signals'].to_csv(train_sig_path, index=False)
    results['train']['returns'].to_csv(train_ret_path, index=False)
    results['test']['signals'].to_csv(test_sig_path, index=False)
    results['test']['returns'].to_csv(test_ret_path, index=False)

    # Latest
    results['train']['signals'].to_csv(os.path.join(out_dir, "train_signals_latest.csv"), index=False)
    results['train']['returns'].to_csv(os.path.join(out_dir, "train_returns_latest.csv"), index=False)
    results['test']['signals'].to_csv(os.path.join(out_dir, "test_signals_latest.csv"), index=False)
    results['test']['returns'].to_csv(os.path.join(out_dir, "test_returns_latest.csv"), index=False)

    report["output_files"] = {
        "csv_files": {
            "train_signals": os.path.relpath(train_sig_path, here),
            "train_returns": os.path.relpath(train_ret_path, here),
            "test_signals": os.path.relpath(test_sig_path, here),
            "test_returns": os.path.relpath(test_ret_path, here),
        },
        "latest_files": {
            "train_signals": "results/train_signals_latest.csv",
            "train_returns": "results/train_returns_latest.csv",
            "test_signals": "results/test_signals_latest.csv",
            "test_returns": "results/test_returns_latest.csv",
        }
    }

    baseline_path = os.path.join(here, "baseline.json")

    # Compare baseline (do NOT stop if manifest differs)
    comp = compare_with_baseline(report, baseline_path)
    report["baseline_comparison"] = comp

    # Save run ONCE
    runs_dir = os.path.join(here, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    run_path = os.path.join(runs_dir, f"{ts}.json")
    with open(run_path, "w") as f:
        json.dump(report, f, indent=2)

    # Baseline management
    if args.save_baseline:
        # Backup old baseline
        if os.path.exists(baseline_path):
            bkp = os.path.join(runs_dir, f"baseline_backup_{ts}.json")
            os.rename(baseline_path, bkp)
        with open(baseline_path, "w") as f:
            json.dump(report, f, indent=2)

    # Console summary (minimal)
    print("=" * 70)
    print(f"{cfg.STRATEGY_NAME} v{cfg.STRATEGY_VERSION}")
    print("=" * 70)
    train_ic_mean = report.get('performance', {}).get('train', {}).get('ic_by_period', {}).get('mean')
    test_ic_mean = report.get('performance', {}).get('test', {}).get('ic_by_period', {}).get('mean')
    print(f"Train IC (robust mean): {train_ic_mean}")
    print(f"Test  IC (robust mean): {test_ic_mean}")
    print(f"Test IC (overall):      {report.get('performance', {}).get('test', {}).get('ic')}")
    print(f"Signals (test):         {report.get('performance', {}).get('test', {}).get('n_signals')}")
    print(f"Saved report:           {os.path.relpath(run_path, here)}")
    if args.save_baseline:
        print("Saved baseline:         baseline.json")
    print(f"Baseline valid:         {report['baseline_comparison'].get('comparison_valid')}")
    if report['baseline_comparison'].get('manifest_changes'):
        print("Manifest changes:")
        for x in report['baseline_comparison']['manifest_changes']:
            print(f"  - {x}")
    print("=" * 70)


if __name__ == "__main__":
    main()
