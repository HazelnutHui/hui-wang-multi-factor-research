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
- Stage 1 rerun is partially completed under latest formula logic updates.
- Completed so far:
  - `value` (`ic_mean=0.054063`)
  - `momentum` (`ic_mean=0.012868`, 6-1 specification)
- Running now (8-core parallel segmented rerun):
  - `reversal`, `low_vol`, `quality`, `pead`
- Stage 2 shortlist will be finalized after the remaining four factors complete Stage 1.

## Engineering Strengths Demonstrated
- Research infra design instead of one-off scripts
- Bias control implementation (PIT + survivorship + metric correctness)
- Reproducible experiment governance and reporting
- Practical quant-engineering tradeoff management under real data constraints
