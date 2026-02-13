"""
Test PEAD with enhancements and save results
"""
import config
from backtest_engine import BacktestEngine
import sys
sys.path.append('.')

from . import factor_engine
from pead_factor_final import ShiftedPEADFactor
factor_engine.AdvancedPEADFactor = ShiftedPEADFactor

config_dict = {
    'PRICE_DIR_ACTIVE': config.PRICE_DIR_ACTIVE,
    'PRICE_DIR_DELISTED': config.PRICE_DIR_DELISTED,
    'DELISTED_INFO': config.DELISTED_INFO,
    'MIN_MARKET_CAP': config.MIN_MARKET_CAP,
    'MIN_DOLLAR_VOLUME': config.MIN_DOLLAR_VOLUME,
    'MIN_PRICE': config.MIN_PRICE,
    'TRANSACTION_COST': config.TRANSACTION_COST,
    'EXECUTION_DELAY': 1
}

engine = BacktestEngine(config_dict)
factor_weights = {'momentum': 0.0, 'reversal': 0.0, 'low_vol': 0.0, 'pead': 1.0}

print("\n" + "="*70)
print("PEAD ENHANCED - WITH RESULT SAVING")
print("="*70)

results = engine.run_out_of_sample_test(
    train_start='2015-01-01', train_end='2020-12-31',
    test_start='2021-01-01', test_end='2026-01-28',
    factor_weights=factor_weights,
    rebalance_freq=5,
    holding_period=10,
    long_pct=0.2, short_pct=0.0
)

print(f"\n{'='*70}")
print(f"Test IC: {results['oos_analysis']['test_ic']:.4f}")
print(f"Signals: {results['oos_analysis']['test_n']:,}")
print(f"{'='*70}\n")

# Save enhanced results
import pandas as pd
results['test']['returns'].to_csv('../results/test_returns_enhanced.csv', index=False)
print("Saved: results/test_returns_enhanced.csv")

# Check exit_type distribution
returns = results['test']['returns']

if 'exit_type' in returns.columns:
    print("\n" + "="*70)
    print("EXIT TYPE DISTRIBUTION")
    print("="*70)
    
    exit_counts = returns['exit_type'].value_counts()
    exit_pct = (exit_counts / len(returns) * 100).round(1)
    
    print("\nCounts:")
    for exit_type, count in exit_counts.items():
        pct = exit_pct[exit_type]
        print(f"  {exit_type:12s}: {count:5d} ({pct:5.1f}%)")
    
    print(f"\nTotal: {len(returns)}")
    
    # Return stats by type
    print("\n" + "="*70)
    print("RETURNS BY EXIT TYPE")
    print("="*70)
    
    for exit_type in exit_counts.index:
        subset = returns[returns['exit_type'] == exit_type]
        print(f"\n{exit_type}:")
        print(f"  Count: {len(subset)}")
        print(f"  Mean: {subset['return'].mean():+.4f}")
        print(f"  Median: {subset['return'].median():+.4f}")
else:
    print("\nNo exit_type column - feature not working")
