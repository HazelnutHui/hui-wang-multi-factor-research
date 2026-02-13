# Value Strategy v1 (Earnings Yield + FCF Yield + EV/EBITDA Yield)

> Goal: Select undervalued companies by combining multiple valuation yields.

---

## 1. Strategy Summary

**Core hypothesis**: Cheaper companies (higher valuation yields) outperform over the long run.

**Value score definition**:
- Metrics (from TTM ratios):
  - Earnings yield: \(1 / PE\)
  - Free cash flow yield: \(1 / (P/FCF)\)
  - EV/EBITDA yield: \(1 / (EV/EBITDA)\)

**Combination**:
\[
score = w_1 \cdot EY + w_2 \cdot FCFY + w_3 \cdot EVEBITDAY
\]

**Portfolio construction**:
- Rank value scores cross-sectionally on rebalance dates.
- Long top 20% only.
- Execute next open; hold 20 trading days.

---

## 2. Timing and Data Flow

**Execution flow**:
1) Build trading calendar and rebalance dates
2) Build tradable universe (delisting/price/liquidity filters)
3) Load latest available valuation metrics (as of signal date)
4) Compute value score → rank → build positions
5) Execute next open; hold 20 days
6) Compute returns and output results

---

## 3. Module Responsibilities

### 3.1 ValueFundamentalsEngine
- Loads local valuation cache (one file per symbol)
- Uses the latest record not later than signal date

### 3.2 FactorEngine
- Computes value score (weighted sum)
- Emits value signal

---

## 4. Default Configuration

Location: `strategies/value_v1/config.py`

- `VALUE_WEIGHTS = {earnings_yield:1, fcf_yield:1, ev_ebitda_yield:1}`
- `HOLDING_PERIOD = 20`
- `REBALANCE_FREQ = 21`
- `EXECUTION_DELAY = 1`
- `TRANSACTION_COST = 0.0020`
- `USE_ADJ_PRICES = True`
- `VALUE_DIR = ../data/fmp/ratios/value`

---

## 5. Data Convention

- Use point-in-time valuation metrics (as-of signal date).
- TTM ratios should be updated quarterly.

---

## 6. Risks and Notes

- Value can be slow to mean-revert.
- Extremely cheap names may reflect fundamental deterioration.

---

## 7. Outputs

Directories: `strategies/value_v1/results` and `strategies/value_v1/runs`

- `train_signals_latest.csv`
- `train_returns_latest.csv`
- `test_signals_latest.csv`
- `test_returns_latest.csv`
- `runs/<timestamp>.json`

---

## 8. Run

```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.value_v1.run
```
