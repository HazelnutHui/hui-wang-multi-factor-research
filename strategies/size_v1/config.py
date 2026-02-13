"""
Size Strategy v1 - Framework Health Check
"""

STRATEGY_VERSION = "1.0"
STRATEGY_NAME = "SIZE_CHECK"

# Execution
HOLDING_PERIOD = 21
REBALANCE_FREQ = 1
REBALANCE_MODE = "month_end"
EXECUTION_DELAY = 1
TRANSACTION_COST = 0.0020

# Universe (keep broad to expose size effect)
MIN_MARKET_CAP = 0.0
MIN_DOLLAR_VOLUME = 1e6
MIN_PRICE = 5.0

# Backtest periods
TRAIN_START = "2010-01-04"
TRAIN_END   = "2017-12-31"
TEST_START  = "2018-01-01"
TEST_END    = "2026-01-28"

# Price data selection
USE_ADJ_PRICES = True

# Calendar symbol for rebalance calendar (optional)
CALENDAR_SYMBOL = "SPY"

# Market cap history (PIT)
MARKET_CAP_DIR = "data/fmp/market_cap_history"
MARKET_CAP_STRICT = False

# Rank signals cross-section (small cap = high rank)
SIGNAL_RANK = True
SIGNAL_RANK_PCT = True
