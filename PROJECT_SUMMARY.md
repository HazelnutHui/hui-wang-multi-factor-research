# Project Summary (Interview Version)

## One-Line Positioning
Built a reproducible, bias-aware daily-factor research platform that distinguishes robust alpha signals from unstable ones under institutional-style validation.

## What I Implemented
- Modular backtest architecture for daily, rebalance-driven factor research
- Standardized factor processing pipeline (winsor, rank/zscore, neutralization, lag)
- Protocol-driven configuration system for reproducible experiments
- PIT fundamentals timing controls and delisting-aware data handling
- Structured diagnostics and reporting workflow (IC, quantiles, turnover, cost stress)

## Validation Methodology
1. Segmented IC stability (2-year slices)
2. Fixed train/test out-of-sample check
3. Walk-forward deployment-style validation

Factors that fail segmented stability are filtered out early.

## Current Findings (Updated 2026-02-17 UTC)
- `v2.1` Stage 1 rerun is completed for six target factors (54/54 segment tasks).
- `v2.1` Stage 1 ranking (`ic_mean`):
  1. `value_v2` (`0.047520`)
  2. `momentum_v2` (`0.012868`)
  3. `quality_v2` (`0.009247`)
  4. `low_vol_v2` (`0.009101`)
  5. `reversal_v2` (`0.005704`)
  6. `pead_v2` (`0.000766`)
- Stage 2 priority for this cycle: `value_v2`, `momentum_v2`, `quality_v2`.
- `v2` has been overwritten to `v2.1` for institutional-style formula upgrades:
  - residual momentum branch
  - residual downside low-vol baseline
  - reversal gap/liquidity filters
- `v2.1` Stage2 strict + cache core-pair rerun (`value_v2,momentum_v2`) completed (18/18 segments).
- Stage2 cache pipeline is now implemented and verified in real run (`395` cache artifacts generated).
- Combination layer (`combo_v2`) is fully validated under locked strict settings (Layer1/Layer2/Layer3 completed).
- Combo weight-grid status:
  - An early segmented grid batch was invalidated due to a weight-source bug in `run_segmented_factors.py` (hardcoded combo defaults).
  - The runner was fixed to read `COMBO_WEIGHTS` from `strategies/combo_v2/config.py`.
  - Corrected 3-weight grid rerun completed: `0.90/0.10` ranked first.
  - Formula comparison completed under same strict settings:
    - `value_momentum_gated`: `ic_mean=0.038463`, `ic_std=0.070371`
    - `value_momentum_two_stage`: `ic_mean=0.048188`, `ic_std=0.081973`
  - Final combo lock: linear `value=0.90`, `momentum=0.10`.
- Stage2 top3 results:
  - `value_v2`: `0.055206`
  - `momentum_v2`: `0.016483`
  - `quality_v2`: `-0.003500`
- Current combo decision: use core pair `value + momentum`; keep `quality` as rework candidate.
- Latest strict+cache core-pair metrics:
  - `value_v2`: `0.053457`
  - `momentum_v2`: `0.014055`
- Final combo validation (locked `linear`, `value=0.90`, `momentum=0.10`):
  - Layer2 fixed train/test: `train_ic=0.080637`, `test_ic=0.053038`
  - Layer3 walk-forward (2013-2025, `REBALANCE_MODE=None`):
    - `test_ic`: `mean=0.057578`, `std=0.033470`, `pos_ratio=1.0000`, `n=13`
    - `test_ic_overall`: `mean=0.050814`, `std=0.032703`, `pos_ratio=1.0000`, `n=13`
- Post-WF stress validation (passed):
  - Stress profile: `COST_MULTIPLIER=1.5`, `MIN_MARKET_CAP=2e9`, `MIN_DOLLAR_VOLUME=5e6`
  - `test_ic`: `mean=0.053310`, `std=0.032486`, `pos_ratio=1.0000`, `n=13`
  - `test_ic_overall`: `mean=0.046618`, `std=0.032058`, `pos_ratio=1.0000`, `n=13`

## Engineering Strengths Demonstrated
- Research infra design instead of one-off scripts
- Bias control implementation (PIT + survivorship + metric correctness)
- Reproducible experiment governance and reporting
- Practical quant-engineering tradeoff management under real data constraints
