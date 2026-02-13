"""
Low-Volatility Strategy (Simple Baseline)
"""

STRATEGY_VERSION = "1.0"
STRATEGY_NAME = "LOW_VOL_SIMPLE_60D"

# Execution
HOLDING_PERIOD = 21
REBALANCE_FREQ = 1
REBALANCE_MODE = "month_end"
EXECUTION_DELAY = 1
TRANSACTION_COST = 0.0020

# Universe
MIN_MARKET_CAP = 500e6
MIN_DOLLAR_VOLUME = 1e6
MIN_PRICE = 5.0

# Backtest periods
TRAIN_START = "2010-01-04"
TRAIN_END   = "2017-12-31"
TEST_START  = "2018-01-01"
TEST_END    = "2026-01-28"

# Price data selection
USE_ADJ_PRICES = True

# Calendar symbol
CALENDAR_SYMBOL = "SPY"

# Low-vol simple baseline
LOW_VOL_WINDOW = 60
LOW_VOL_LOG_RETURN = True
LOW_VOL_USE_RESIDUAL = False

# Standardize low-vol cross-section
SIGNAL_RANK = True
SIGNAL_RANK_PCT = True
