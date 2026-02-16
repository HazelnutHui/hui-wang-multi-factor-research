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

## Current Research Snapshot (Updated 2026-02-16 UTC)
Current rerun status under updated single-factor formula logic:
- Stage 1 completed (new run): `value`, `momentum` (6-1), `reversal`, `low_vol`, `quality`, `pead`
- Stage 1 ranking by `ic_mean`: `value` > `momentum` > `reversal` > `low_vol` > `quality` > `pead`

Latest Stage 1 metrics:
- `value`: `ic_mean=0.054227`, `ic_std=0.022106`, `pos_ratio=0.8889`, `valid_n=8/9`
- `momentum` (6-1): `ic_mean=0.012868`, `ic_std=0.022771`, `pos_ratio=0.6667`, `valid_n=8/9`
- `reversal`: `ic_mean=0.005325`, `ic_std=0.006380`, `pos_ratio=1.0000`, `valid_n=9/9`
- `low_vol`: `ic_mean=0.003209`, `ic_std=0.034677`, `pos_ratio=0.4444`, `valid_n=8/9`
- `quality`: `ic_mean=0.002387`, `ic_std=0.008456`, `pos_ratio=0.5556`, `valid_n=8/9`
- `pead`: `ic_mean=0.000766`, `ic_std=0.030426`, `pos_ratio=0.5556`, `valid_n=9/9`

Policy for this cycle:
- Prioritize Stage 2 rerun for `value`, `momentum`, `reversal`
- Then refresh fixed train/test under updated protocol assumptions

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
- `docs/public_factor_references/FACTOR_PUBLIC_FORMULAS_AND_EXECUTION_CONSTRAINTS_EN.md`: public factor formulas, execution constraints, and V4 defect audit (English)
- `docs/public_factor_references/FACTOR_PUBLIC_FORMULAS_AND_EXECUTION_CONSTRAINTS_CN.md`: 公开因子公式、执行约束与 V4 缺陷审查（中文）
- `SYSTEM_OVERVIEW_CN.md`: Chinese system overview

## Interview-Ready Summary
Designed and implemented a modular, PIT-aware multi-factor research platform that standardizes factor validation and distinguishes robust alpha signals from unstable ones under institutional-style checks.

## Additional Public Summary
- `PROJECT_SUMMARY.md`: one-page interview-friendly project summary
