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

## Current Findings (Rerun In Progress, 2026-02-15 UTC)
- This repository is currently under a full single-factor rerun with updated research protocol assumptions.
- Stage 1 completed so far:
  - `value`: `ic_mean=0.054063`, `pos_ratio=0.8889`
  - `momentum`: `ic_mean=0.012868`, `pos_ratio=0.6667`
  - `quality`: `ic_mean=0.000957`, `pos_ratio=0.4444`
  - `low_vol`: `ic_mean=0.003209`, `pos_ratio=0.4444`
- Remaining Stage 1 factors (`reversal`, `pead`) are running in 2-year parallel segments.
- Final ranking and combination candidates will be decided only after all factors finish Stage 1 and Stage 2 reruns.

## Engineering Strengths Demonstrated
- Research infra design instead of one-off scripts
- Bias control implementation (PIT + survivorship + metric correctness)
- Reproducible experiment governance and reporting
- Practical quant-engineering tradeoff management under real data constraints
