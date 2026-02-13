import config
from backtest_engine import BacktestEngine
import pandas as pd

# Hack: Modify signal date to T-1
# Create wrapper for signal_generator

config_dict = {
    'PRICE_DIR_ACTIVE': config.PRICE_DIR_ACTIVE,
    'PRICE_DIR_DELISTED': config.PRICE_DIR_DELISTED,
    'DELISTED_INFO': config.DELISTED_INFO,
    'MIN_MARKET_CAP': config.MIN_MARKET_CAP,
    'MIN_DOLLAR_VOLUME': config.MIN_DOLLAR_VOLUME,
    'MIN_PRICE': config.MIN_PRICE,
    'TRANSACTION_COST': config.TRANSACTION_COST,
    'EXECUTION_DELAY': 1  # T+1 from adjusted signal date
}

# Modify pead_factor to shift date forward by 1 day
import sys
sys.path.append('.')
from .pead_factor_cached import CachedPEADFactor

class ShiftedPEADFactor(CachedPEADFactor):
    def get_sue_signal(self, symbol, date):
        # Shift signal date forward by 1 day
        # So earnings on 2024-02-01 becomes signal on 2024-02-02
        shifted_date = (pd.Timestamp(date) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        return super().get_sue_signal(symbol, shifted_date)

# Monkey patch
from . import pead_factor_cached
pead_factor_cached.CachedPEADFactor = ShiftedPEADFactor

engine = BacktestEngine(config_dict)
factor_weights = {'momentum': 0.0, 'reversal': 0.0, 'low_vol': 0.0, 'pead': 1.0}

print("\n=== T-1 EXECUTION (Day before earnings date) ===\n")

results = engine.run_out_of_sample_test(
    train_start='2023-01-01', train_end='2023-12-31',
    test_start='2024-01-01', test_end='2026-01-28',
    factor_weights=factor_weights,
    rebalance_freq=5,
    holding_period=10,
    long_pct=0.2, short_pct=0.0
)

print(f"\n{'='*70}")
print(f"T-1 RESULTS:")
print(f"Train IC: {results['oos_analysis']['train_ic']:.4f}")
print(f"Test IC: {results['oos_analysis']['test_ic']:.4f}")
print(f"{'='*70}\n")
