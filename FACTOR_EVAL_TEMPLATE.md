# Factor Evaluation Template

Last checked: 2026-02-10

Purpose: standardize how we assess new factors so results are comparable and decisions are traceable.

---

## 1) Factor Summary
- **Name**:
- **Family**: (risk/defensive, value, quality, behavior, event, liquidity, etc.)
- **Economic rationale** (1–3 sentences):
- **Direction**: (higher = better / lower = better / absolute / conditional)
- **Update frequency**: (daily / weekly / monthly / quarterly)
- **Data dependencies**:

---

## 2) Data Integrity & PIT
- **Data source**:
- **PIT fields**: (available_date / acceptedDate / filingDate / none)
- **As-of filtering**: (yes/no, where)
- **Coverage**:
  - symbols:
  - date range:
  - missing rate:
- **Known risks**:

---

## 3) Factor Definition (Exact)
- **Formula**:
- **Window / lookback**:
- **Lag / delay**:
- **Winsor / clipping**:
- **Standardization**: (rank / zscore / none)
- **Neutralization**: (industry / sector / market / none)
- **Notes on implementation**:

---

## 4) Backtest Setup
- **Universe filters**: (min cap, min price, min dollar vol, etc.)
- **Rebalance**: (mode, freq)
- **Execution**: (delay, entry/exit price)
- **Holding period**:
- **Costs**:
- **Stage**: (Stage 1 baseline / Stage 2 institutional)
- **Train/Test**:

---

## 5) Segmented IC (2-Year Slices)
Record segment results here (IC, IC_raw, n).

| Segment | Start | End | IC | IC_raw | n |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |
| 6 | | | | | |
| 7 | | | | | |
| 8 | | | | | |
| 9 | | | | | |

**Summary stats**
- IC mean:
- IC std:
- % positive segments:

---

## 6) Train/Test (Fixed Split)
- **Train IC**:
- **Test IC**:
- **Signals (train/test)**:
- **Notes**:

---

## 7) Walk-Forward (Optional)
- **Window plan**:
- **Avg IC**:
- **Stability**:

---

## 8) Robustness Checks
- **Parameter sensitivity** (±20% lookback):
- **Alt standardization** (rank vs zscore):
- **Sub‑universe** (e.g., large cap only):
- **Notes**:

---

## 9) Decision
- **Status**: (reject / keep / combine / revisit)
- **Why**:
- **Next action**:
