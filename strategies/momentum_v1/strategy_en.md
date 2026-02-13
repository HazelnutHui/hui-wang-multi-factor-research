# Medium-Term Momentum Strategy v1 (12-1 Momentum)

> Goal: Capture medium-term trend persistence. Signals are computed after close; trades execute at next open.

---

## 1. Strategy Summary

**Core hypothesis**: Medium-term price trends tend to persist (momentum effect).

**Signal definition (12-1 momentum)**:
- Compute 12-month cumulative return on daily bars, skipping the most recent 1 month:
  \[
  mom_{12-1} = \frac{P_{t-21}}{P_{t-252}} - 1
  \]
- Interpretation:
  - Strong medium-term winners → higher signal
  - Weak medium-term performers → lower signal (long-only here)

**Portfolio construction**:
- Rank signals cross-sectionally on rebalance dates (monthly by default).
- Long top 20%, no shorts.
- Execute next open, hold 21 trading days.

---

## 2. Timing and Data Flow

**Execution flow**:
1) Build trading calendar and rebalance dates
2) Build tradable universe (delisting/price/liquidity filters)
3) Compute momentum signals (12-1)
4) Rank and build positions (long-only)
5) Execute next open; hold 21 trading days
6) Compute returns and output results

**Timeline**:
- Day T close: compute signals
- Day T+1 open: execute
- Day T+21 open: exit (21-day holding)

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
  - Optional volatility filter (`UNIVERSE_MAX_VOL`, `UNIVERSE_VOL_LOOKBACK`)

### 3.3 FactorEngine
- Computes 12-1 momentum (daily bars):
  - 252-day lookback, skip recent 21 days
- Parameters: `MOMENTUM_LOOKBACK`, `MOMENTUM_SKIP`
- Optional winsorization: `MOMENTUM_WINSOR_Z`
- Optional industry neutralization: `INDUSTRY_NEUTRAL` (needs `INDUSTRY_MAP_PATH`)

### 3.4 Position Builder
- Sort signals descending
- Long top 20%, no shorts

### 3.5 ExecutionSimulator
- Execution price: next open (or next available trading day)
- Holding period: 21 trading days
- Transaction cost via `TRANSACTION_COST`

### 3.6 Outputs
- Signals/returns (timestamped + latest)
- Minimal JSON report (config + performance summary)

---

## 4. Default Configuration

Location: `strategies/momentum_v1/config.py`

- `MOMENTUM_LOOKBACK = 252`
- `MOMENTUM_SKIP = 21`
- `MOMENTUM_VOL_LOOKBACK = 60`
- `MOMENTUM_WINSOR_Z = 3.0`
- `HOLDING_PERIOD = 21`
- `REBALANCE_FREQ = 21`
- `EXECUTION_DELAY = 1`
- `TRANSACTION_COST = 0.0020`
- `MIN_PRICE = 5.0`
- `MIN_DOLLAR_VOLUME = 1e6`
- `UNIVERSE_VOL_LOOKBACK = 60`
- `UNIVERSE_MAX_VOL = 0.08`
- `USE_ADJ_PRICES = True`

---

## 5. Price Data Convention

- Signals should use adjusted prices to avoid split/dividend distortions.
- Execution uses open prices; if adjusted prices are used globally, consistency is preserved.
- If adjusted data is incomplete, the system falls back to unadjusted prices.

---

## 6. Risks and Notes

- Momentum is a medium-term factor, not suited for high-frequency turnover.
- Transaction costs can erode returns at high turnover.
- Be mindful of momentum crash regimes.

---

## 7. Outputs

Directories: `strategies/momentum_v1/results` and `strategies/momentum_v1/runs`

- `train_signals_latest.csv`
- `train_returns_latest.csv`
- `test_signals_latest.csv`
- `test_returns_latest.csv`
- `runs/<timestamp>.json`

---

## 8. Run

```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.momentum_v1.run
```

---

## 9. Optional Enhancements

- Volatility-adjusted momentum (signal / vol)
- Long-short construction
- Combine momentum with quality factors
