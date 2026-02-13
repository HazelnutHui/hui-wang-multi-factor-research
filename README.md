# V4 - Multi-Factor Alpha Backtest System

Last checked: 2026-02-12

This repo documents a multi-factor backtest system (momentum, reversal, value, quality, low-vol, PEAD, and more). The descriptions below reflect current code behavior and are intended to help reason about data flow, timing, and diagnostics.

**Current intent (2026-02-12)**
- Focus on daily-frequency factor research and scoring (not intraday).
- Stage 1 = baseline screening (winsor + rank).
- Stage 2 = institutional mode (industry + size/beta neutralization + zscore; optional smoothing).
- Only move to combo factors after 2–3 single factors are stable.
- Post-hoc diagnostics and committee checklist are available (non-invasive).
 - Trading-day execution and dynamic costs are now the default (`EXECUTION_USE_TRADING_DAYS`, `ENABLE_DYNAMIC_COST`).

**Intended usage (daily, not intraday):**
- The system targets **daily-frequency analysis and scoring**.
- Inputs are based on **regular session open/close** data (and other daily bars).
- It does **not** support intraday/high-frequency execution.
- Execution timing can be modeled flexibly (e.g., next day open), but the core signal is daily.

---

## Quick Summary

Latest segmented results (Stage 1/Stage 2) are tracked in `STATUS.md`. Stage 1 (winsor + rank) is the default baseline for new factors; Stage 2 (industry neutral + size/beta neutral + zscore, optional smoothing) is optional for robustness.
Current plan: finish single-factor screening with Stage 1, then apply Stage 2 only as robustness checks at the combination stage.

---

## Backtest Standard (Three Layers)

We use a simple three-layer backtest standard to judge a factor/strategy:

1. **Segmented backtest** (stability check)  
   - Split history into fixed windows (e.g., 2-year segments) and compute IC per segment.
   - Purpose: verify signal stability across regimes.

2. **Fixed train/test** (overfit sanity check)  
   - Run a single strategy with a fixed train window and a fixed test window.
   - Purpose: check out-of-sample degradation and signal counts.

3. **Walk-forward** (deployability check)  
   - Rolling train/test windows across time.
   - Purpose: approximate live behavior under rolling retraining.

If a strategy can’t pass layer 1, do not proceed to layers 2–3.

---

## 0) What’s Included

Single-factor strategies implemented in `strategies/`:
- PEAD (SUE)
- Momentum (12-1)
- Reversal (intraday / short-term)
- Quality (composite: ROE/ROA + gross margin + CFO/Assets + leverage penalty)
- Value (EY + FCFY + EV/EBITDA)
- Low-vol (validation baseline in `strategies/low_vol_v1/`)

Utilities:
- Segmented factor backtest runner: `scripts/run_segmented_factors.py`
- Walk-forward validation runner: `scripts/run_walk_forward.py`
- FMP company profile bulk fetcher (industry/sector mapping): `scripts/fmp_profile_bulk_to_csv.py`
- Unified config runner: `scripts/run_with_config.py`
- Professional factor report generator: `scripts/generate_factor_report.py`
 - FMP dataset index: `data/fmp/DATASETS.md`

Configs:
- Global protocol: `configs/protocol.yaml`
- Strategy overrides: `configs/strategies/*.yaml`

---

## 1) System Overview (Data Flow + Timing)

The backtest is **rebalance-date driven**, not daily. Signals and positions are only computed on a sparse schedule.

High-level flow:
1. Build trading calendar (SPY or fallback) and generate `rebalance_dates`.
2. For each rebalance date:
   - Build tradable universe
   - Compute factor signals
   - Build positions
3. Execute trades with a fixed delay and holding period.
4. Compute returns and diagnostics.
5. Save outputs (signals/returns + report JSON).

**Important**: the system is config-driven. The canonical configuration is:
- `configs/protocol.yaml` (global rules)
- `configs/strategies/<strategy>.yaml` (strategy-specific overrides)

---

## 2) Core Backtest Modules

### 2.1 BacktestEngine (`backtest/backtest_engine.py`)
- **Trading calendar**: uses SPY data if available; otherwise falls back to another symbol or business days.
- **Rebalance dates**: every `REBALANCE_FREQ` trading days.
- **Main loop**: for each rebalance date, call `FactorEngine.compute_signals`, then `FactorEngine.build_positions`, then execute + compute returns.

Key behavior:
- `signals_df.date` is the **rebalance date** (i.e., the signal date).
- The strategy only "sees" events on rebalance dates.

### 2.2 UniverseBuilder (`backtest/universe_builder.py`)
Builds a dynamic tradable universe per rebalance date.

Filters (current implementation):
- **Delisted filter**: skip if delisted on date.
- **Lookback window**: require at least `lookback` price rows.
- **Min price**: average close >= `MIN_PRICE` over lookback.
- **Min dollar volume**: average (close * volume) >= `MIN_DOLLAR_VOLUME` if volume exists.

Note: `MIN_MARKET_CAP` is enforced when `MarketCapEngine` is configured (PIT market cap history required).

### 2.3 FactorEngine (`backtest/factor_engine.py`)
Computes factors per symbol and aggregates into a single signal.

- Factors implemented: momentum, reversal, low-vol, pead, value, quality.
- Signals are computed as:
  `signal = sum(weight_k * factor_k)` using only non-null factors.
- Output is restricted to columns: `symbol`, `date`, `signal` by default.
- Optional: set `factors.include_components: true` to include factor columns in signals.

Factor weights are strategy-defined. Example (`strategies/pead_v1/`):
```
{'momentum': 0.0, 'reversal': 0.0, 'low_vol': 0.0, 'pead': 1.0}
```
So `signal == pead` for this specific strategy.

### 2.4 Position Builder (`FactorEngine.build_positions`)
- Sort signals descending.
- Long top `floor(n * long_pct)`.
- Short top `floor(n * short_pct)` (not used here).
- If `long_pct > 0` and there is data, at least one long is kept.

### 2.5 ExecutionSimulator (`backtest/execution_simulator.py`)
Execution uses **natural-day offsets**, not trading-day offsets.

- **Execution date**: `signal_date + EXECUTION_DELAY`.
- **Exit date**: `signal_date + EXECUTION_DELAY + HOLDING_PERIOD`.
- **Entry/exit price**: first available bar on or after execution date; prefer `open` then `close`.
- **Costs**: apply base cost (default 20 bps) or dynamic cost model if enabled.
- **Missing data**: exits can fall back to delisting logic or conservative loss.

---

## 3) Event-Driven Factor Example: PEAD (SUE) Timing Alignment

This section is an example of event-driven alignment. Non-event factors (e.g., momentum, reversal, value, quality) do not use earnings-date alignment.

### 3.1 Cached PEAD (`backtest/pead_factor_cached.py`)
- Loads cached Owner_Earnings-labeled data per symbol (source: FMP `/stable/earnings`).
- Computes SUE:
  - `surprise = epsActual - epsEstimated`
  - rolling std with window = `LOOKBACK_QUARTERS` (min periods = window)
  - `sue = surprise / (surprise_std + 1e-9)`, clipped to [-10, 10]
- Legacy event detection: **last 5 days** window (not used in current strategy).

### 3.2 Shifted PEAD (`strategies/pead_v1/factor.py`)
This is the active PEAD factor. It **does not use the 5-day window**. Instead, it enforces an exact day alignment with a +1 day shift.

**Current alignment logic**:
- Input to factor: `signal_date` (the rebalance date)
- Internal target: `target_date = signal_date + 1`
- Only use an event if `earnings_date == target_date`
- Apply SUE threshold: `abs(sue) > SUE_THRESHOLD`

**Implication**:
```
earnings_date = signal_date + 1
signal_date   = earnings_date - 1
```

### 3.3 Effective trade timing
Given `EXECUTION_DELAY = 1`:
```
execution_date = signal_date + 1 = earnings_date
```
So the strategy **enters at the earnings date open**.

---

## 4) Rebalance Effects (Why event signals can cluster)

Because the system only scans events on rebalance dates, earnings that occur between two rebalance dates will only be captured on the nearest rebalance date that satisfies the alignment rule. This creates clustering of signals on certain rebalance days.

---

## 5) Outputs and Diagnostics

### 5.1 Primary outputs (from a strategy run, e.g. `strategies/pead_v1/run.py`)
- `train_signals_latest.csv` / `test_signals_latest.csv`
  - columns: `symbol, date, signal`
  - date = rebalance date
- `train_returns_latest.csv` / `test_returns_latest.csv`
  - entry/exit prices, return, exit_type, holding_period, etc.
- Timestamped versions of the same files.

### 5.2 Report JSON (`strategies/*/runs/*.json`)
Includes:
- performance metrics (IC, robust IC, n_signals)
- quality metrics (exit types, data coverage, filtering stats)
- data manifest (file hashes, git info)
- strategy_rules (alignment + execution)

### 5.3 Research/diagnostic artifacts (if generated, example from PEAD)
- `pead_full_cross_section_ic_input.csv` / `pead_fullcs_engine_ic_input.csv`
- `pead_ic_by_date_*.csv`
- `pead_top20_vs_all_by_date.csv`
- `pead_quantile_summary_tradableset.csv`
- `pead_quantile_portfolio_returns_tradableset.csv`
- `pead_quantile_equity_tradableset.csv` (+ PNG)

---

### IC Caveat (Engine)
IC is computed on the full signal cross-section using forward returns
(`forward_returns`). The legacy IC on executed positions is still available as
`ic_positions` for reference. If you need the old behavior explicitly, use
`analysis.ic_positions` / `analysis.ic_yearly_positions`.

---

## 9) Recent Progress

Older result directories have been pruned; update this section after new runs complete.

## 5.4 Validation Baseline (Low-Vol)

If a factor underperforms, run a simple low-vol sanity check to validate
the backtest/execution pipeline:
```bash
PYTHONPATH=/Users/hui/quant_score/v4 /Users/hui/miniconda3/envs/qscore/bin/python \
  /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --factors low_vol --max-segments 3
```

This uses `strategies/low_vol_v1/config.py` and the engine’s built-in
low-volatility factor.

## 10) Industry/Sector Mapping (for Industry-Neutral Signals)

Industry-neutral z-scoring is optional and requires a local mapping file:
- `data/company_profiles.csv` with columns `symbol`, `industry`, `sector`
- Generate it via FMP profile-bulk:
  - `scripts/fmp_profile_bulk_to_csv.py`

---

## 6) Default Parameters (PEAD v1 example)

From `strategies/pead_v1/config.py`:
- `SUE_THRESHOLD = 0.5`
- `LOOKBACK_QUARTERS = 8`
- `DATE_SHIFT_DAYS = 1` (note: code currently hardcodes +1 rather than reading this constant)
- `REBALANCE_FREQ = 5`
- `EXECUTION_DELAY = 1`
- `HOLDING_PERIOD = 10`
- `MIN_PRICE = 5.0`
- `MIN_DOLLAR_VOLUME = 1e6`

---

## 7) Timing Diagram (Current Implementation)

```
          earnings_date (event day)
                   ▲
                   │  matches when earnings_date == signal_date + 1
                   │
signal_date (rebalance day)
      │
      └── execution_date = signal_date + 1 = earnings_date
```

---

## 8) Practical Interpretation (PEAD example)

- The strategy is **event-driven but rebalance-gated**.
- PEAD signals are **shifted** to align with a specific earnings-day convention.
- Execution is **T+1 from signal**, which coincides with earnings date given the shift.

If you want to change the alignment (e.g., signal on earnings day or day-after), the `ShiftedPEADFactor` is the single point of truth.

---

## 9) Segmented Backtests (2-year IC slices)

Use the segmented runner to split a long backtest into smaller windows and compute per-segment IC.

Example:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py
```

Common options:
```bash
# 2010-2025, 2-year slices
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --start-date 2010-01-01 --end-date 2025-12-31 --years 2

# Only momentum + value
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --factors momentum,value --years 2

# Resume an existing run (continue remaining segments)
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --resume --out-dir /Users/hui/quant_score/v4/segment_results/<timestamp>

# Run only first 3 segments this time
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --max-segments 3

# Invert momentum signal (quick direction check)
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --factors momentum --invert-momentum --max-segments 3
```

Outputs are saved under:
`segment_results/<timestamp>/`

---

## 10) Walk-Forward Validation (rolling train/test)

Walk-forward simulates rolling training and next-period testing.
This is a third, more “live-like” IC perspective.

Example:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py
```

Common options:
```bash
# 3-year train, 1-year test, 2010-2026
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --train-years 3 --test-years 1 --start-year 2010 --end-year 2026

# Only momentum + value
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --factors momentum,value

# Resume an existing run (continue remaining windows)
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --resume --out-dir /Users/hui/quant_score/v4/walk_forward_results/<timestamp>

# Run only first 3 windows this time
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --max-windows 3

# Run only specific test years (e.g., 2018 and 2019)
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --only-years 2018,2019
```

Outputs are saved under:
`walk_forward_results/<timestamp>/`

---

## 11) Repo Layout (Quick Map)

Top-level folders:
- `backtest/` Core engine, data handling, universe, execution, analysis
- `strategies/` Strategy entrypoints + configs + outputs
- `data/` Price, Owner_Earnings-labeled data, delisted list, fundamentals cache
- `scripts/` Data download and helper scripts
- `results/` Ad-hoc backtest outputs (older scripts)
- `segment_results/` Segmented runner outputs (created by `run_segmented_factors.py`)
- `archive/` Historical artifacts (if any)

Key files:
- `backtest/backtest_engine.py` main engine loop
- `backtest/data_engine.py` price loading + delisted cutoff
- `backtest/universe_builder.py` tradable universe filters
- `backtest/factor_engine.py` factor calculations
- `backtest/execution_simulator.py` trade execution + returns
- `backtest/performance_analyzer.py` IC and stats (per-date IC mean)

Strategy entrypoints:
- `strategies/pead_v1/run.py`
- `strategies/momentum_v1/run.py`
- `strategies/reversal_v1/run.py`
- `strategies/quality_v1/run.py`
- `strategies/value_v1/run.py`

---

## 12) Data Dependencies (What must exist on disk)

Price data (pickle per symbol):
- Active: `data/prices_divadj/` (preferred if `USE_ADJ_PRICES=True`)
- Delisted: `data/prices_delisted_divadj/`
- Non-adjusted fallback: `data/prices/` and `data/prices_delisted/`

**Important (data provenance):**
- This repo expects **both active and delisted** price files to be present on disk.
- The backtest will look in the delisted directories and use `data/delisted_companies_2010_2026.csv` to cut off prices after delisting.
- If your price source only contains currently listed stocks, results will suffer **survivorship bias** and may be invalid.
- Make sure you can explain and verify the **actual source** of price files in `data/prices*` and `data/prices_delisted*`.

Delisted list:
- `data/delisted_companies_2010_2026.csv` (used to clip price history after delist date)

Coverage note (last checked 2026-02-05):
- Delisted list updated from FMP; total 4718 symbols
- Delisted price coverage (adj) has 4256 symbols
- US-only missing adj: 9 symbols
- Report: `data/fmp/delisted_coverage_report.md`
 - US-only missing adj blacklist: `data/fmp/missing_delisted_adj_us_blacklist.txt`

Price provenance note:
- `data/fmp/price_provenance.md`

China A-share quick start (minimal validation):
1. Get stock list: `scripts/akshare_stock_list.py`
2. Download daily data (qfq): `scripts/akshare_download_daily.py --symbols-csv /Users/hui/quant_score/v4/data/cn/stock_list.csv`
3. Run CN reversal: `scripts/run_with_config.py --protocol /Users/hui/quant_score/v4/configs/protocol_cn.yaml --strategy /Users/hui/quant_score/v4/configs/strategies/cn_reversal_v1.yaml`

Earnings cache (event factors like PEAD):
- `data/Owner_Earnings/` (one file per symbol; used by `CachedPEADFactor`)

Fundamentals cache:
- Quality: `data/fmp/ratios/quality/`
- Value: `data/fmp/ratios/value/`

Market cap history (PIT universe filter):
- `data/fmp/market_cap_history/` (one CSV per symbol)

If a cache is missing or empty, the related factor will return no signal.
If fundamentals files include `available_date`, the engine will use it for point-in-time filtering.

PIT status (last checked 2026-02-05):
- Fundamentals are being rebuilt with `available_date` using FMP `acceptedDate` / `fillingDate`
- Re-run scripts:
  - `scripts/download_quality_fundamentals.py --overwrite`
  - `scripts/download_value_fundamentals.py --overwrite`
PIT verification:
- `data/fmp/fundamentals_available_date_coverage.md` (sample coverage 100%)

Execution cost sensitivity:
- `ExecutionSimulator` supports `cost_multiplier` to stress slippage (e.g., 2x/3x)

Unified run cost multiplier:
- `scripts/run_with_config.py --cost-multiplier 2.0`

PEAD timing risk note:
- `data/fmp/pead_timing_risk.md`

---

## 13) Data Download Scripts

Adjusted prices:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/download_dividend_adjusted_prices.py
```

Quality fundamentals:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/download_quality_fundamentals.py
```

Value fundamentals:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/download_value_fundamentals.py
```

Notes:
- Expect some symbols to return empty data; this is normal.
- If you see repeated 402 responses, the API plan likely does not allow that endpoint.

---

## 14) How to Run Each Strategy

All strategies load their own config and call the shared engine.

PEAD:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.pead_v1.run
```

Momentum:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.momentum_v1.run
```

Reversal:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.reversal_v1.run
```

Quality:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.quality_v1.run
```

Value:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.value_v1.run
```

Common options (strategy run scripts):
- `--long-pct` (default 0.2)
- `--short-pct` (default 0.0)

---

## 15) Strategy Configs (What is actually used)

Each strategy has a locked `config.py`:
- `strategies/*/config.py`

Important fields:
- Date ranges: `TRAIN_START`, `TRAIN_END`, `TEST_START`, `TEST_END`
- Rebalance: `REBALANCE_FREQ`
- Holding: `HOLDING_PERIOD`
- Execution delay: `EXECUTION_DELAY`
- Costs: `TRANSACTION_COST`
- Universe: `MIN_PRICE`, `MIN_DOLLAR_VOLUME`, `MIN_MARKET_CAP`

Important detail:
- `MIN_MARKET_CAP` is enforced **only when** market-cap history is available (`data/fmp/market_cap_history`).
- If market-cap history is missing, the filter is skipped to avoid empty universes.

Adjusted prices:
- The run scripts select adjusted-price directories when `USE_ADJ_PRICES=True`
- `DataEngine` also maps `adjOpen/adjClose` -> `open/close` if needed

Current default train/test split (as of 2026-02-10, unchanged):
- Train: `2010-01-04` to `2017-12-31`
- Test: `2018-01-01` to `2026-01-28`

Momentum implementation notes:
- Current default uses **daily** momentum (6-1):
  - `log(price[t-skip] / price[t-lookback-skip])`
  - `MOMENTUM_LOOKBACK = 126`, `MOMENTUM_SKIP = 21`
- Monthly momentum is still supported when `MOMENTUM_USE_MONTHLY = True`
- Cross-sectional z-score is disabled by default for momentum

---

## 16) Outputs Per Strategy

All strategy runners save into `strategies/<name>/results/`:
- `train_signals_latest.csv`
- `train_returns_latest.csv`
- `test_signals_latest.csv`
- `test_returns_latest.csv`
- Timestamped copies of the above

Some strategies additionally write a run JSON (e.g., PEAD):
- `strategies/pead_v1/runs/<timestamp>.json`

JSON includes:
- `performance` (IC, n_signals, etc.)
- `filter_stats`
- `strategy_rules` (alignment/execution)

---

## 17) IC Definitions (Important)

There are two IC calculations in the codebase:

1) `PerformanceAnalyzer.calculate_ic` (preferred)
- Computes **per-date cross-sectional IC** and then averages
- Returns `ic` (mean of daily IC), `ic_overall` (global correlation)

2) `BacktestEngine.run_backtest` summary
- Computes a single overall correlation on the merged data

Implication:
- `analysis['ic']` from `BacktestEngine` is **overall** correlation.
- `PerformanceAnalyzer` provides **per-date mean IC**, which is more robust.

The segmented runner uses `PerformanceAnalyzer` (per-date mean IC).

---

## 18) Known Timing and Alignment Notes

- The system is rebalance-date driven. Events between rebalances may be skipped.
- Execution uses **calendar days** (not trading days).
- PEAD `ShiftedPEADFactor` aligns signal date = earnings date - 1 day.

If you change alignment or execution delay, update both:
- `strategies/pead_v1/factor.py` for alignment logic
- `strategies/pead_v1/config.py` for expected parameters

---

## 19) Performance and Memory Tips (MacBook Pro M1 16G)

- Prefer segmented runs for long history (`scripts/run_segmented_factors.py`)
- Use smaller universes if needed (tighten filters)
- Avoid running multiple strategies concurrently
- If running long jobs, use `nohup` or `tmux`

---

## 20) Troubleshooting

Common issues:
- `KeyError: open` or `close`
  - Usually missing OHLC columns in adjusted data
  - `DataEngine._normalize_price_df` maps adjusted OHLC

- `n_signals = 0`
- Data missing for the factor (Owner_Earnings-labeled data / fundamentals)
  - Universe filters too strict

- IC is NaN or None
  - Too few signals for correlation
  - Per-date IC needs enough names on each date

---

## 21) Cleanup Notes

If disk usage grows:
- `logs/` can be safely cleared
- `strategies/*/results/` and `strategies/*/runs/` can be pruned to keep only latest

Keep data caches under `data/` unless re-downloading is acceptable.

---

## 22) Unified Config System (New)

**Why**: lock research protocol and make runs reproducible.

### 22.1 Files
- `configs/protocol.yaml`: global research protocol (locked)
- `configs/strategies/<strategy>.yaml`: strategy overrides (small, explicit)

### 22.2 How to Run (Preferred)
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_with_config.py \
  --strategy /Users/hui/quant_score/v4/configs/strategies/momentum_v1.yaml
```

### 22.3 What is locked vs changeable
- Protocol: trading rules, costs, data paths, neutralization defaults
- Strategy: factor weights, factor params, train/test window

---

## 23) Factor Factory (New)

Location: `backtest/factor_factory.py`

Standardization:
- `signal_rank` (pct rank) OR `signal_zscore`
- Winsorization
- Missing handling (`drop | fill | keep`)
- Optional industry neutralization
- Global and per-factor lag (`factors.lag_days` and `<factor>.lag_days`)

Where it is applied:
- `FactorEngine.compute_signals` uses the factory for standardization

---

## 24) Professional Factor Report (New)

Script: `scripts/generate_factor_report.py`

Outputs:
- Markdown report
- JSON report
- CSV artifacts (rolling IC, quantile cumulative, factor correlation)

Example:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/generate_factor_report.py \
  --strategy /Users/hui/quant_score/v4/configs/strategies/momentum_v1.yaml \
  --quantiles 5 \
  --rolling-window 60 \
  --cost-multipliers 2,3
```

Metrics included:
- Train/Test IC (forward returns)
- Quantile mean + cumulative returns
- Rolling IC
- Turnover
- Factor correlation (if components included)
- Cost sensitivity (optional)

---

## 25) Tests (New)

Location: `tests/`

Coverage:
- Rank/zscore/winsor/missing
- Lag behavior
- No-lookahead regression tests

Run:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m pytest /Users/hui/quant_score/v4/tests
```
