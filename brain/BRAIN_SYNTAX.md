# BRAIN Formula Syntax (Public Notes)

This file summarizes **publicly available** (unofficial) descriptions of WorldQuant BRAIN expression syntax and operators.
It is intended as a quick reference for drafting factors before validating directly on the BRAIN platform.
Because BRAIN changes over time and some docs are behind login, **treat this as approximate** and verify in-platform.

## 1) Scope & Caveats
- Sources below are **community / third-party summaries**, not official platform docs.
- Operator names, field availability, and defaults can differ by region/universe or account permissions.
- Always validate an expression in BRAIN and record any mismatch in `brain/logs/brain_factor_log.md`.

## 2) Operator Categories (High-Level)
Unverified but commonly referenced categories:
- Arithmetic operators (basic math, rounding)
- Logical operators (booleans; true=1, false=0)
- Time-series operators (operate on past *d* days)
- Cross-sectional operators (rank/normalize across stocks at a date)
- Group operators (industry/sector neutralization, group stats)
- Vector / transform operators (reduce vectors to scalars)

These categories appear in multiple community references.

## 3) Common Time-Series Operators (Examples)
Frequently referenced time-series operators include:
- `ts_mean(x, d)` : average over past *d* days
- `ts_std_dev(x, d)` : standard deviation over past *d* days
- `ts_delta(x, d)` : `x - ts_delay(x, d)`
- `ts_sum(x, d)` : sum over past *d* days
- `ts_rank(x, d)` : time-series rank over past *d* days
- `ts_delay(x, d)` : lag/shift by *d* days

These are widely referenced in community guides.

## 4) Common Cross-Section Operators
Frequently referenced cross-sectional operators include:
- `rank(x)` : rank across stocks at a date (often scaled to 0..1)
- `zscore(x)` : cross-sectional z-score

These show up in community BRAIN-related references.

## 5) Common Conditional Syntax
A commonly referenced conditional form is:
- `if_else(condition, a, b)`
- ternary: `condition ? a : b`

These appear in BRAIN community examples for constructing conditions.

## 6) Common Field Examples (Public References)
Commonly referenced fields in BRAIN/Alpha101-style examples include:
- `open`, `close`, `high`, `low`, `volume`, `vwap`
- `returns` (daily close-to-close returns)
- `cap` (market cap)
- `adv{d}` (average daily dollar volume over *d* days)

Field naming and availability should be verified in your BRAIN account.

## 7) Example Drafts (Validate in BRAIN)
These are **drafts** only; verify syntax and field names in BRAIN:

- 12-1 momentum (illustrative):
  - `ts_delay(ts_delta(close, 250) / ts_delay(close, 250), 20)`

- Low-volatility (illustrative):
  - `-ts_std_dev(returns, 60)`

- Short-term reversal (illustrative):
  - `-ts_delta(close, 5)`

## 8) Next Step
If you can access official BRAIN docs or field lists in-platform, paste them here and I will update this file with authoritative syntax and your exact field set.
