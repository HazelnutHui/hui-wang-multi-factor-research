import config
from backtest_engine import BacktestEngine

# Patch factor_engine to use shifted version
import sys
sys.path.append('.')

# Replace import before loading
from . import factor_engine
original_import = factor_engine.AdvancedPEADFactor

from pead_factor_shifted import ShiftedPEADFactor
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

print("\n=== SHIFTED PEAD (earnings date+1 → signal) ===\n")

results = engine.run_out_of_sample_test(
    train_start='2023-01-01', train_end='2023-12-31',
    test_start='2024-01-01', test_end='2026-01-28',
    factor_weights=factor_weights,
    rebalance_freq=5,
    holding_period=10,
    long_pct=0.2, short_pct=0.0
)

print(f"\nTrain IC: {results['oos_analysis']['train_ic']:.4f}")
print(f"Test IC: {results['oos_analysis']['test_ic']:.4f}")
