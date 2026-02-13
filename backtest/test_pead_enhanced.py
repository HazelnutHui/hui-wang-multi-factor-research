"""
Test PEAD with all enhancements enabled
Compare: baseline vs enhanced performance
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
print("PEAD WITH FULL ENHANCEMENTS")
print("="*70)
print("Enhancements enabled:")
print("  ✓ Data quality filtering (remove abnormal prices)")
print("  ✓ Smart delisting handling (merger vs bankruptcy)")
print("  ✓ Dynamic cost model (liquidity + volatility adjusted)")
print("="*70 + "\n")

results = engine.run_out_of_sample_test(
    train_start='2015-01-01', train_end='2020-12-31',
    test_start='2021-01-01', test_end='2026-01-28',
    factor_weights=factor_weights,
    rebalance_freq=5,
    holding_period=10,
    long_pct=0.2, short_pct=0.0
)

print(f"\n{'='*70}")
print("ENHANCED RESULTS:")
print(f"Train IC: {results['oos_analysis']['train_ic']:.4f}")
print(f"Test IC: {results['oos_analysis']['test_ic']:.4f}")
print(f"Signals: {results['oos_analysis']['test_n']:,}")
print(f"{'='*70}\n")

print("Comparison with baseline (Test IC = 0.0958):")
baseline_ic = 0.0958
enhanced_ic = results['oos_analysis']['test_ic']
change = (enhanced_ic - baseline_ic) / baseline_ic * 100
print(f"Baseline IC: {baseline_ic:.4f}")
print(f"Enhanced IC: {enhanced_ic:.4f}")
print(f"Change: {change:+.1f}%\n")
