"""
PEAD Production Backtest - Validated Configuration
Test IC: 0.0958 (2021-2026)
"""
import config
from pathlib import Path
from backtest_engine import BacktestEngine
import sys
sys.path.append('.')

# Use date-shifted PEAD factor (CRITICAL for accuracy)
from . import factor_engine
from pead_factor_final import ShiftedPEADFactor
factor_engine.AdvancedPEADFactor = ShiftedPEADFactor

def _pick_price_dirs():
    try:
        use_adj = getattr(config, "USE_ADJ_PRICES", False)
        adj_active = Path(getattr(config, "PRICE_DIR_ACTIVE_ADJ", ""))
        adj_del = Path(getattr(config, "PRICE_DIR_DELISTED_ADJ", ""))
        if use_adj and adj_active.exists() and adj_del.exists():
            if any(adj_active.glob("*.pkl")) or any(adj_del.glob("*.pkl")):
                return str(adj_active), str(adj_del)
    except Exception:
        pass
    return config.PRICE_DIR_ACTIVE, config.PRICE_DIR_DELISTED

price_active, price_delisted = _pick_price_dirs()

config_dict = {
    'PRICE_DIR_ACTIVE': price_active,
    'PRICE_DIR_DELISTED': price_delisted,
    'DELISTED_INFO': config.DELISTED_INFO,
    'MIN_MARKET_CAP': config.MIN_MARKET_CAP,
    'MIN_DOLLAR_VOLUME': config.MIN_DOLLAR_VOLUME,
    'MIN_PRICE': config.MIN_PRICE,
    'TRANSACTION_COST': config.TRANSACTION_COST,
    'EXECUTION_DELAY': 1  # T+1 execution
}

engine = BacktestEngine(config_dict)

# PEAD only, optimized parameters
factor_weights = {
    'momentum': 0.0,
    'reversal': 0.0,
    'low_vol': 0.0,
    'pead': 1.0  # Pure PEAD
}

print("\n" + "="*70)
print("PEAD PRODUCTION BACKTEST")
print("="*70)
print("Configuration:")
print("  - SUE threshold: 0.5")
print("  - Holding period: 10 days")
print("  - Rebalance: every 5 days")
print("  - Date shift: earnings_date + 1")
print("="*70 + "\n")

results = engine.run_out_of_sample_test(
    train_start='2015-01-01',
    train_end='2020-12-31',
    test_start='2021-01-01',
    test_end='2026-01-28',
    factor_weights=factor_weights,
    rebalance_freq=5,
    holding_period=10,
    long_pct=0.2,
    short_pct=0.0
)

print(f"\n{'='*70}")
print("RESULTS:")
print(f"Train IC: {results['oos_analysis']['train_ic']:.4f}")
print(f"Test IC: {results['oos_analysis']['test_ic']:.4f}")
print(f"Degradation: {results['oos_analysis']['ic_degradation_pct']:.1f}%")
print(f"{'='*70}\n")

# Save results
import pandas as pd
pd.DataFrame([results['oos_analysis']]).to_csv(
    '../results/pead_production_summary.csv', 
    index=False
)
print("Saved: results/pead_production_summary.csv\n")
