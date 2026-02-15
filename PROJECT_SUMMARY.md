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

## Current Findings (Updated 2026-02-15 UTC)
- Full Stage 1 rerun is complete for all six target single factors.
- Stage 1 ranking by segmented `ic_mean`:
  1. `value` (`0.054063`)
  2. `momentum` (`0.012868`, 6-1 specification)
  3. `reversal` (`0.003564`)
  4. `low_vol` (`0.003209`)
  5. `quality` (`0.000957`)
  6. `pead` (`0.000766`)
- Current shortlist for Stage 2 priority: `value`, `momentum`, then `reversal`.

## Engineering Strengths Demonstrated
- Research infra design instead of one-off scripts
- Bias control implementation (PIT + survivorship + metric correctness)
- Reproducible experiment governance and reporting
- Practical quant-engineering tradeoff management under real data constraints
