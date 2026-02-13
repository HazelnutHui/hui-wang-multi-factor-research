# Quality Strategy v1 (ROE + Cashflow Quality + Gross Margin)

> Goal: Select companies with strong profitability and high-quality cash flows as a long-term stable factor.

---

## 1. Strategy Summary

**Core hypothesis**: High-quality companies (strong profitability + solid cash flow quality) outperform over the long run.

**Quality score definition**:
- Metrics (from financial statements / TTM):
  - ROE (Net Income / Shareholder Equity)
  - Gross Margin (Gross Profit / Revenue)
  - Operating Cash Flow / Total Assets
- Quality score:
  \[
  score = w_1 \cdot ROE + w_2 \cdot GrossMargin + w_3 \cdot CFO/Assets
  \]

**Portfolio construction**:
- Rank quality scores cross-sectionally on rebalance dates.
- Long top 20% only.
- Execute at next open; hold 20 trading days.

---

## 2. Timing and Data Flow

**Execution flow**:
1) Build trading calendar and rebalance dates
2) Build tradable universe (delisting/price/liquidity filters)
3) Load latest available fundamentals (as of signal date)
4) Compute quality score → rank → build positions
5) Execute next open; hold 20 days
6) Compute returns and output results

---

## 3. Module Responsibilities

### 3.1 FundamentalsEngine
- Loads fundamentals cache (one file per symbol)
- Uses the latest record not later than signal date

### 3.2 FactorEngine
- Computes quality score (weighted sum)
- Emits quality signal

### 3.3 ExecutionSimulator
- Executes next open; holds 20 days

---

## 4. Default Configuration

Location: `strategies/quality_v1/config.py`

- `QUALITY_WEIGHTS = {roe:1, gross_margin:1, cfo_to_assets:1}`
- `HOLDING_PERIOD = 20`
- `REBALANCE_FREQ = 21`
- `EXECUTION_DELAY = 1`
- `TRANSACTION_COST = 0.0020`
- `USE_ADJ_PRICES = True`
- `FUNDAMENTALS_DIR = ../data/fmp/ratios/quality`

---

## 5. Data Convention

- Use point-in-time fundamentals (as-of signal date).
- TTM or quarterly fundamentals recommended; update quarterly.

---

## 6. Risks and Notes

- Fundamentals update slowly; not sensitive to short-term moves.
- Data delays/missing can reduce coverage.
- Avoid look-ahead: only use data available by signal date.

---

## 7. Outputs

Directories: `strategies/quality_v1/results` and `strategies/quality_v1/runs`

- `train_signals_latest.csv`
- `train_returns_latest.csv`
- `test_signals_latest.csv`
- `test_returns_latest.csv`
- `runs/<timestamp>.json`

---

## 8. Run

```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.quality_v1.run
```
