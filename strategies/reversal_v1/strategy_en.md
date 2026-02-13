# Short-Term Reversal Strategy v1 (3-Day Reversal + Next-Open + 1-Day Hold)

> Goal: Capture short-term mean reversion after price overreaction. Signals are computed after close; trades execute at next open.

---

## 1. Strategy Summary

**Core hypothesis**: Short-term price overreaction tends to revert in the next few days.

**Signal definition** (intraday reversal):
- Use same-day intraday return:
  \[
  r_{intra} = \frac{Close_t}{Open_t} - 1
  \]
- Reversal signal is the negative of that return:
  \[
  signal = -r_{intra}
  \]
- Interpretation:
  - Strong intraday gain → negative signal
  - Strong intraday loss → positive signal

**Portfolio construction**:
- Daily signals; rank cross-sectionally.
- Long top 20% only.
- Execute at next open; hold for 1 trading day.

---

## 2. Timing and Data Flow

**Execution flow**:
1) Build trading calendar and rebalance dates (daily)
2) Build tradable universe (delisting/price/liquidity filters)
3) Compute reversal signals
4) Rank and build positions (long-only)
5) Execute next open; hold 1 day
6) Compute returns and output results

**Timeline**:
- Day T close: compute intraday reversal signals
- Day T+1 open: execute
- Day T+2 open: exit (1-day holding)

---

## 3. Module Responsibilities

### 3.1 DataEngine
- Loads local price data (default: `data/prices` or `data/prices_divadj`).
- Applies delisting cutoff.

### 3.2 UniverseBuilder
- Dynamic filters:
  - Delisted filter
  - Minimum price (`MIN_PRICE`)
  - Minimum dollar volume (`MIN_DOLLAR_VOLUME`)

### 3.3 FactorEngine
- Computes short-term reversal:
  - Same-day intraday return
  - Negated as signal
- Optional volatility scaling (`REVERSAL_VOL_LOOKBACK`)\n+- Optional earnings-day filter (`REVERSAL_EARNINGS_FILTER_DAYS`)

### 3.4 Position Builder
- Sort signals descending
- Long top 20%, no shorts

### 3.5 ExecutionSimulator
- Execution price: next open (or next available trading day)
- Holding period: 1 day
- Transaction cost via `TRANSACTION_COST`

### 3.6 Outputs
- Signals/returns (timestamped + latest)
- Minimal JSON report (config + performance summary)

---

## 4. Default Configuration

Location: `strategies/reversal_v1/config.py`

- `REVERSAL_MODE = \"intraday\"`
- `REVERSAL_VOL_LOOKBACK = 20`
- `REVERSAL_EARNINGS_FILTER_DAYS = 1`
- `HOLDING_PERIOD = 1`
- `REBALANCE_FREQ = 1`
- `EXECUTION_DELAY = 1`
- `TRANSACTION_COST = 0.0020`
- `MIN_PRICE = 5.0`
- `MIN_DOLLAR_VOLUME = 1e6`
- `USE_ADJ_PRICES = True`

---

## 5. Price Data Convention

- Signals should ideally use adjusted prices to avoid split/dividend distortions.
- Execution uses open prices; if adjusted prices are used globally, the system remains consistent.
- If adjusted data is not fully available, it falls back to unadjusted prices.

---

## 6. Risks and Notes

- Short-term reversal is sensitive to trading costs and liquidity.
- Large event days can dominate short-horizon moves; results may degrade.
- Intraday timing is not modeled; this is a daily strategy.

---

## 7. Outputs

Directories: `strategies/reversal_v1/results` and `strategies/reversal_v1/runs`

- `train_signals_latest.csv`
- `train_returns_latest.csv`
- `test_signals_latest.csv`
- `test_returns_latest.csv`
- `runs/<timestamp>.json`

---

## 8. Run

```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.reversal_v1.run
```

---

## 9. Optional Enhancements

- Separate overnight vs intraday reversal signals
- Volatility scaling (signal / vol)
- Event-day filtering (earnings ±1)
- Quantile-based position sizing
