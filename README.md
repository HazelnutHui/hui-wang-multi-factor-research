# Multi-Factor Alpha Research Platform (V4)

A bias-aware, reproducible, daily-frequency factor research system for US equities.

This project focuses on turning factor ideas into decision-grade research outputs with a consistent validation protocol, not one-off backtest screenshots.

## Recruiter Quick Link
- Start here: [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md)

## What This Project Does
- Builds rebalance-date-driven backtests for factor strategies
- Evaluates factors with segmented IC, fixed train/test, and walk-forward
- Supports Stage 1/Stage 2 signal processing for baseline vs institutional robustness
- Adds point-in-time (PIT) controls for fundamentals timing
- Handles delisted data paths to reduce survivorship bias
- Produces structured diagnostics (rolling IC, quantiles, turnover, cost sensitivity)

## Validation Framework
Each factor follows the same research gate:

1. Segmented backtest (2-year slices): stability across regimes
2. Fixed train/test: out-of-sample degradation check
3. Walk-forward: deployment-style rolling validation

If a factor fails step 1, it does not move forward.

## Current Research Snapshot (Updated 2026-02-15 UTC)
Stage 1 rerun (2-year segmented IC) is complete for all target factors:
- `value`: `ic_mean=0.054063`, `ic_std=0.021962`, `pos_ratio=0.8889`
- `momentum` (6-1): `ic_mean=0.012868`, `ic_std=0.022771`, `pos_ratio=0.6667`
- `reversal`: `ic_mean=0.003564`, `ic_std=0.010793`, `pos_ratio=0.4444`
- `low_vol`: `ic_mean=0.003209`, `ic_std=0.034677`, `pos_ratio=0.4444`
- `quality`: `ic_mean=0.000957`, `ic_std=0.008283`, `pos_ratio=0.4444`
- `pead`: `ic_mean=0.000766`, `ic_std=0.030426`, `pos_ratio=0.5556`

Current Stage 1 ranking (by `ic_mean`):
1. `value`
2. `momentum`
3. `reversal`
4. `low_vol`
5. `quality`
6. `pead`

Next policy:
- Run Stage 2 robustness on prioritized factors first (`value`, `momentum`, then `reversal`)
- Refresh fixed train/test under the same updated protocol

## Core Architecture
- `backtest/backtest_engine.py`: rebalance loop orchestration
- `backtest/universe_builder.py`: tradable universe filters
- `backtest/factor_engine.py`: factor computation and signal aggregation
- `backtest/factor_factory.py`: winsor/rank/zscore/neutralization/lag pipeline
- `backtest/execution_simulator.py`: execution and cost simulation
- `backtest/performance_analyzer.py`: IC and diagnostics

## Repository Structure
- `backtest/`: core engine modules
- `strategies/`: factor strategy entrypoints/configs
- `scripts/`: data and research utilities
- `configs/`: protocol and strategy YAML config
- `tests/`: no-lookahead / lag / factor processing tests
- `data/`: local data cache (excluded from public repo)
- `logs/`: local run logs (excluded from public repo)

## Quick Start
### 1) Environment
- Python 3.11 recommended
- Set project root as `PYTHONPATH`

```bash
cd quant_score/v4
export PYTHONPATH=$(pwd)
```

### 2) Run segmented factor validation
```bash
python scripts/run_segmented_factors.py --factors value --years 2
```

### 3) Run a strategy train/test
```bash
python -m strategies.value_v1.run
```

### 4) Run unified config entrypoint
```bash
python scripts/run_with_config.py --strategy configs/strategies/momentum_v1.yaml
```

### 5) Run tests
```bash
python -m pytest tests
```

## Public-Repo Notes
- Large local datasets, logs, and generated results are intentionally excluded.
- To reproduce full results, prepare your own data caches and API keys.
- Do not commit secrets (API tokens, credentials, private keys).

## Key Documents
- `RUNBOOK.md`: practical command reference
- `STATUS.md`: current progress and latest run status
- `SINGLE_FACTOR_BASELINE.md`: standardized single-factor evaluation checklist
- `FACTOR_NOTES.md`: implementation notes and caveats per factor
- `SYSTEM_OVERVIEW_CN.md`: Chinese system overview

## Interview-Ready Summary
Designed and implemented a modular, PIT-aware multi-factor research platform that standardizes factor validation and distinguishes robust alpha signals from unstable ones under institutional-style checks.

## Additional Public Summary
- `PROJECT_SUMMARY.md`: one-page interview-friendly project summary
