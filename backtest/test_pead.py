"""Test PEAD Factor"""
import config
from backtest_engine import BacktestEngine

# Add API key to config
API_KEY = "xW9GGtIZOfJeA2r2YBvqrLLFNs0oF8ov"

config_dict = {
    'PRICE_DIR_ACTIVE': config.PRICE_DIR_ACTIVE,
    'PRICE_DIR_DELISTED': config.PRICE_DIR_DELISTED,
    'DELISTED_INFO': config.DELISTED_INFO,
    'MIN_MARKET_CAP': config.MIN_MARKET_CAP,
    'MIN_DOLLAR_VOLUME': config.MIN_DOLLAR_VOLUME,
    'MIN_PRICE': config.MIN_PRICE,
    'TRANSACTION_COST': config.TRANSACTION_COST,
    'EXECUTION_DELAY': config.EXECUTION_DELAY,
    'API_KEY': API_KEY  # Add API key
}

engine = BacktestEngine(config_dict)

# Test PEAD
factor_weights = {
    'momentum': 0.0,
    'reversal': 0.0,
    'low_vol': 0.0,
    'pead': 1.0  # Pure PEAD
}

print("\n" + "="*70)
print("TESTING PEAD FACTOR (Post Earnings Announcement Drift)")
print("="*70 + "\n")

results = engine.run_out_of_sample_test(
    train_start=config.TRAIN_START,
    train_end=config.TRAIN_END,
    test_start=config.TEST_START,
    test_end=config.TEST_END,
    factor_weights=factor_weights,
    rebalance_freq=5,  # Weekly rebalance for event-driven
    holding_period=20,  # Hold 20 days after earnings
    long_pct=0.2,
    short_pct=0.0
)

print(f"\n{'='*70}")
print("PEAD RESULTS")
print(f"{'='*70}")
print(f"Train IC: {results['oos_analysis']['train_ic']:.4f}")
print(f"Test IC: {results['oos_analysis']['test_ic']:.4f}")
print(f"Train signals: {results['oos_analysis']['train_n']:,}")
print(f"Test signals: {results['oos_analysis']['test_n']:,}")
print(f"{'='*70}\n")
