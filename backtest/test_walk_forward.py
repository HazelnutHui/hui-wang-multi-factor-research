"""
Walk-forward validation for PEAD
Rolling 3-year train / 1-year test windows
"""
import config
from backtest_engine import BacktestEngine
from walk_forward_validator import WalkForwardValidator
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

validator = WalkForwardValidator(train_years=3, test_years=1)
windows = validator.generate_windows(start_year=2015, end_year=2025)

engine = BacktestEngine(config_dict)
factor_weights = {'momentum': 0.0, 'reversal': 0.0, 'low_vol': 0.0, 'pead': 1.0}

print("\n" + "="*70)
print("WALK-FORWARD VALIDATION")
print("="*70)
print(f"Training window: 3 years")
print(f"Testing window: 1 year")
print(f"Total windows: {len(windows)}")
print("="*70 + "\n")

import pandas as pd
results_list = []

for i, window in enumerate(windows):
    print(f"[{i+1}/{len(windows)}] Train: {window['train_start'][:4]}-{window['train_end'][:4]}, Test: {window['test_year']}")
    
    results = engine.run_out_of_sample_test(
        train_start=window['train_start'],
        train_end=window['train_end'],
        test_start=window['test_start'],
        test_end=window['test_end'],
        factor_weights=factor_weights,
        rebalance_freq=5,
        holding_period=10,
        long_pct=0.2, short_pct=0.0
    )
    
    results_list.append({
        'test_year': window['test_year'],
        'train_ic': results['oos_analysis']['train_ic'],
        'test_ic': results['oos_analysis']['test_ic'],
        'test_n': results['oos_analysis']['test_n']
    })
    
    print(f"  Train IC: {results['oos_analysis']['train_ic']:.4f}, Test IC: {results['oos_analysis']['test_ic']:.4f}\n")

df_results = pd.DataFrame(results_list)

print("\n" + "="*70)
print("WALK-FORWARD SUMMARY")
print("="*70)
print(df_results.to_string(index=False))
print(f"\nAverage Test IC: {df_results['test_ic'].mean():.4f}")
print(f"IC Std Dev: {df_results['test_ic'].std():.4f}")
print(f"Positive years: {(df_results['test_ic'] > 0).sum()}/{len(df_results)}")
print("="*70 + "\n")

df_results.to_csv('../results/walk_forward_results.csv', index=False)
print("Saved: results/walk_forward_results.csv\n")
