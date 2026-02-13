import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Ensure project root importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

# Load local config
from pathlib import Path as _Path
import importlib.util as _ilu
_cfg_path = _Path(__file__).resolve().parent / "config.py"
_spec = _ilu.spec_from_file_location("momentum_v1_config", _cfg_path)
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


def _make_engine_config(momentum_lookback: int, momentum_skip: int, momentum_vol_lookback: int):
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

        'MOMENTUM_LOOKBACK': momentum_lookback,
        'MOMENTUM_SKIP': momentum_skip,
        'MOMENTUM_VOL_LOOKBACK': momentum_vol_lookback,
    }


def main():
    lookbacks = [126, 252, 504]
    skips = [10, 21, 42]
    holding_periods = [5, 10, 20]
    rebalance_freqs = [5, 21]

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path(__file__).resolve().parent / "grid_runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / f"grid_summary_{ts}.csv"
    detail_path = out_dir / f"grid_detail_{ts}.json"

    rows = []
    detail = []

    for lookback in lookbacks:
        for skip in skips:
            for hold in holding_periods:
                for freq in rebalance_freqs:
                    cfg_dict = _make_engine_config(lookback, skip, cfg.MOMENTUM_VOL_LOOKBACK)
                    engine = BacktestEngine(cfg_dict)
                    factor_weights = {'momentum': 1.0, 'reversal': 0.0, 'low_vol': 0.0, 'pead': 0.0}

                    results = engine.run_out_of_sample_test(
                        train_start=cfg.TRAIN_START, train_end=cfg.TRAIN_END,
                        test_start=cfg.TEST_START, test_end=cfg.TEST_END,
                        factor_weights=factor_weights,
                        rebalance_freq=freq,
                        holding_period=hold,
                        long_pct=0.2, short_pct=0.0
                    )

                    train_ic = results['train']['analysis'].get('ic')
                    test_ic = results['test']['analysis'].get('ic')
                    train_n = len(results['train']['returns'])
                    test_n = len(results['test']['returns'])

                    row = {
                        'lookback': lookback,
                        'skip': skip,
                        'holding_period': hold,
                        'rebalance_freq': freq,
                        'train_ic': train_ic,
                        'test_ic': test_ic,
                        'train_n': train_n,
                        'test_n': test_n,
                    }
                    rows.append(row)
                    detail.append({
                        'params': row,
                        'train_analysis': results['train']['analysis'],
                        'test_analysis': results['test']['analysis'],
                    })

                    print(f"done lb={lookback} skip={skip} hold={hold} freq={freq} "
                          f"train_ic={train_ic} test_ic={test_ic}")

    import pandas as pd
    pd.DataFrame(rows).to_csv(summary_path, index=False)
    with open(detail_path, "w") as f:
        json.dump(detail, f, indent=2, default=str)

    print(f"Saved summary: {summary_path}")
    print(f"Saved detail:  {detail_path}")


if __name__ == "__main__":
    main()
