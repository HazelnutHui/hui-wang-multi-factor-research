"""
Medium-Term Momentum Strategy v1 - Locked Configuration
"""

STRATEGY_VERSION = "1.0"
STRATEGY_NAME = "MOMENTUM_6_1"

# Factor (LOCKED)
# Daily 6-1 momentum: 6-month lookback, skip last 1 month (daily bars)
MOMENTUM_LOOKBACK = 126
MOMENTUM_SKIP = 21
MOMENTUM_VOL_LOOKBACK = None
MOMENTUM_ZSCORE = False
MOMENTUM_USE_MONTHLY = False
MOMENTUM_LOOKBACK_MONTHS = 6
MOMENTUM_SKIP_MONTHS = 1
MOMENTUM_WINSOR_Z = None

# Optional industry neutralization (requires a mapping file)
INDUSTRY_NEUTRAL = False
INDUSTRY_MIN_GROUP = 3
INDUSTRY_COL = "industry"
INDUSTRY_MAP_PATH = "../data/company_profiles.csv"

# Execution (LOCKED)
HOLDING_PERIOD = 21
REBALANCE_FREQ = 1
REBALANCE_MODE = "month_end"
EXECUTION_DELAY = 1
TRANSACTION_COST = 0.0020
EXECUTION_USE_TRADING_DAYS = True
ENABLE_DYNAMIC_COST = True
TRADE_SIZE_USD = 10000

# Universe (LOCKED)
MIN_MARKET_CAP = 500e6
MIN_DOLLAR_VOLUME = 1e6
MIN_PRICE = 5.0
UNIVERSE_VOL_LOOKBACK = None
UNIVERSE_MAX_VOL = None

# Backtest periods (LOCKED)
TRAIN_START = "2010-01-04"
TRAIN_END   = "2017-12-31"
TEST_START  = "2018-01-01"
TEST_END    = "2026-01-28"

# Price data selection
USE_ADJ_PRICES = True

# Calendar symbol for rebalance calendar (optional)
CALENDAR_SYMBOL = "SPY"
