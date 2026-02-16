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

## Current Findings (Updated 2026-02-16 UTC)
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
- `v2.1` full 3-layer rerun is the current active task.

## Engineering Strengths Demonstrated
- Research infra design instead of one-off scripts
- Bias control implementation (PIT + survivorship + metric correctness)
- Reproducible experiment governance and reporting
- Practical quant-engineering tradeoff management under real data constraints
