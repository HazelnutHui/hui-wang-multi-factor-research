"""
PEAD Strategy v1 - Locked Configuration
DO NOT MODIFY - Create v2 for experiments
"""

STRATEGY_VERSION = "1.0"
STRATEGY_NAME = "PEAD_SUE_Shifted"

# Factor (LOCKED)
SUE_THRESHOLD = 0.5
LOOKBACK_QUARTERS = 8
DATE_SHIFT_DAYS = 0  # signal uses event date (no forward date lookup)
PEAD_USE_TRADING_DAY_SHIFT = True
PEAD_EVENT_MAX_AGE_DAYS = 5  # allow recent event carry-over (e.g., weekend event dates)

# Execution (LOCKED)
HOLDING_PERIOD = 1
REBALANCE_FREQ = 5
EXECUTION_DELAY = 1
PEAD_T1_EXECUTION = False
TRANSACTION_COST = 0.0020
EXECUTION_USE_TRADING_DAYS = True
ENABLE_DYNAMIC_COST = True
TRADE_SIZE_USD = 10000

# Universe (LOCKED)
MIN_MARKET_CAP = 500e6
MIN_DOLLAR_VOLUME = 1e6
MIN_PRICE = 5.0

# Backtest periods (LOCKED)
TRAIN_START = "2015-01-01"
TRAIN_END   = "2020-12-31"
TEST_START  = "2021-01-01"
TEST_END    = "2026-01-28"

# Alignment rules (AUDITABLE)
ALIGNMENT_RULES = {
    "earnings_date_definition": "FMP earnings API 'date' field",
    "date_interpretation": "event date is used as signal reference date",
    "signal_date_shift": "0 day (no forward lookup)",
    "example": {
        "fmp_date": "2024-02-01",
        "assumed_announcement": "2024-01-31 after-market",
        "signal_generated": "2024-02-01 close",
        "execution": "2024-02-02 open"
    },
    "execution_timing": {
        "signal_day": "T (close)",
        "execution_day": "T+1 (open)",
        "holding_period_start": "T+1 open",
        "holding_period_end": "T+1+H open",
        "intraday_assumption": "All announcements treated as after-market"
    }
}

# Calendar symbol for rebalance calendar (optional)
CALENDAR_SYMBOL = "SPY"

# Price data selection
USE_ADJ_PRICES = True
