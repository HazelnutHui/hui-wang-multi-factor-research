"""
Backtest Configuration
"""

# Data Paths
PRICE_DIR_ACTIVE = "../data/prices"
PRICE_DIR_DELISTED = "../data/prices_delisted"
PRICE_DIR_ACTIVE_ADJ = "../data/prices_divadj"
PRICE_DIR_DELISTED_ADJ = "../data/prices_delisted_divadj"
USE_ADJ_PRICES = True
DELISTED_INFO = "../data/delisted_companies_2010_2026.csv"

# Universe Filters
MIN_MARKET_CAP = 500e6  # $500M
MIN_DOLLAR_VOLUME = 1e6  # $1M daily
MIN_PRICE = 5.0  # $5

# Backtest Period
TRAIN_START = "2010-01-04"
TRAIN_END = "2017-12-31"
TEST_START = "2018-01-01"
TEST_END = "2026-01-28"

# Execution
EXECUTION_DELAY = 1  # T+1
TRANSACTION_COST = 0.0020  # 20bps per trade
EXECUTION_USE_TRADING_DAYS = True
ENABLE_DYNAMIC_COST = True
TRADE_SIZE_USD = 10000

# Portfolio
MAX_POSITION_SIZE = 0.02  # 2% per stock
REBALANCE_FREQUENCY = 20  # Trading days

# Risk
MAX_TURNOVER_MONTHLY = 0.50  # 50% per month
