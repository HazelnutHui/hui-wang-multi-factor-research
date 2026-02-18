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

## Current Research Snapshot (Updated 2026-02-17 UTC)
Current status under updated single-factor formula logic:
- `v1` Stage 1 completed and kept as baseline reference
- `v2` has been overwritten to `v2.1` (institutional baseline upgrade, nontrivial formula changes)
- `v2.1` Stage 1 segmented validation completed (6 factors x 9 segments)
- `v2.1` Stage 1 ranking by `ic_mean`: `value_v2` > `momentum_v2` > `quality_v2` > `low_vol_v2` > `reversal_v2` > `pead_v2`
- Stage2 strict institutional rerun profile added: `v2026_02_16b` (`value_v2,momentum_v2,quality_v2`, 6-core parallel)
- Stage2 strict + cache core-pair run completed: `v2026_02_16c_vm` (`value_v2,momentum_v2`, 18/18)
- Stage2 signal cache layer is now implemented and verified (`395` cache files on workstation run)

Latest `v2.1` Stage 1 metrics:
- `value_v2`: `ic_mean=0.047520`, `ic_std=0.015569`, `pos_ratio=0.8889`, `valid_n=8/9`
- `momentum_v2`: `ic_mean=0.012868`, `ic_std=0.022771`, `pos_ratio=0.6667`, `valid_n=8/9`
- `quality_v2`: `ic_mean=0.009247`, `ic_std=0.011422`, `pos_ratio=0.5556`, `valid_n=8/9`
- `low_vol_v2`: `ic_mean=0.009101`, `ic_std=0.033835`, `pos_ratio=0.5556`, `valid_n=8/9`
- `reversal_v2`: `ic_mean=0.005704`, `ic_std=0.004982`, `pos_ratio=0.8889`, `valid_n=9/9`
- `pead_v2`: `ic_mean=0.000766`, `ic_std=0.030426`, `pos_ratio=0.5556`, `valid_n=9/9`

Current cycle policy:
- Keep `v1` results as baseline reference
- Run Stage 2 segmented first on `value_v2,momentum_v2,quality_v2`
- Then run full Layer2 (fixed train/test) and Layer3 (walk-forward)
- Use `scripts/compare_v1_v2.py` to decide keep/promote by factor
- Stage2 top3 result confirmed: `value_v2` and `momentum_v2` pass; `quality_v2` does not pass
- Promote passing factors into `combo_v2` with current core set `value+momentum`

Latest Stage2 top3 metrics:
- `value_v2`: `ic_mean=0.055206`, `ic_std=0.021952`, `pos_ratio=0.8889`, `valid_n=8/9`
- `momentum_v2`: `ic_mean=0.016483`, `ic_std=0.034164`, `pos_ratio=0.6667`, `valid_n=8/9`
- `quality_v2`: `ic_mean=-0.003500`, `ic_std=0.007554`, `pos_ratio=0.4444`, `valid_n=8/9`

Latest Stage2 strict + cache core-pair metrics:
- `value_v2`: `ic_mean=0.053457`, `ic_std=0.021938`, `pos_ratio=1.0000`, `valid_n=8/9`
- `momentum_v2`: `ic_mean=0.014055`, `ic_std=0.026392`, `pos_ratio=0.7500`, `valid_n=8/9`

Strict Stage2 runner:
- `scripts/run_stage2_strict_top3_parallel.sh`
- Default command (resume-safe): `bash scripts/run_stage2_strict_top3_parallel.sh 6 segment_results/stage2_v2026_02_16b_top3`

## Combination Layer
- `combo_v2` is implemented as institutional research baseline.
- Current core decision: `value + momentum` as main production-candidate pair, `quality` held out for rework.
- Weight-grid integrity note:
  - Early batch `combo_weight_grid_2026_02_17_p6` is not valid for final weight decision.
  - Cause: segmented runner previously used hardcoded combo defaults.
  - Fix applied: `scripts/run_segmented_factors.py` now reads `COMBO_WEIGHTS` from `strategies/combo_v2/config.py` for `combo_v2`.
  - Corrected rerun batch: `segment_results/combo_weight_grid_2026_02_17_fix`.
- Final combo selection (after nonlinear comparison):
  - Linear winner: `value=0.90`, `momentum=0.10`
  - `value_momentum_gated` and `value_momentum_two_stage` both underperformed the linear winner under identical Stage2 strict constraints.
- Final locked combo validation:
  - Layer2 fixed train/test (`configs/strategies/combo_v2_inst.yaml`):
    - Train IC (overall): `0.080637`
    - Test IC (overall): `0.053038`
  - Layer3 walk-forward (`REBALANCE_MODE=None`, test years 2013-2025):
    - `test_ic`: `mean=0.057578`, `std=0.033470`, `pos_ratio=1.0000`, `n=13`
    - `test_ic_overall`: `mean=0.050814`, `std=0.032703`, `pos_ratio=1.0000`, `n=13`
- Post-WF stress validation (passed):
  - Run profile: `COST_MULTIPLIER=1.5`, `MIN_MARKET_CAP=2e9`, `MIN_DOLLAR_VOLUME=5e6`
  - `test_ic`: `mean=0.053310`, `std=0.032486`, `pos_ratio=1.0000`, `n=13`
  - `test_ic_overall`: `mean=0.046618`, `std=0.032058`, `pos_ratio=1.0000`, `n=13`
- Strategy files:
  - `strategies/combo_v2/config.py`
  - `strategies/combo_v2/run.py`
  - `configs/strategies/combo_v2_inst.yaml`
- Weight derivation helper:
  - `scripts/derive_combo_weights.py`

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
- `docs/codex_bootstrap_pack/START_HERE.md`: recommended first file for new Codex session handoff
- `docs/codex_bootstrap_pack/`: curated minimal context pack for fast session synchronization
- `RUNBOOK.md`: practical command reference
- `STATUS.md`: current progress and latest run status
- `WEBSITE_HANDOFF.md`: website dashboard handoff and continuation notes
- `docs/hui_dashboard/README.md`: Hui dashboard deployment/runtime notes and operations guide
- `COMBO_WEIGHT_EXPERIMENTS.md`: combo weight experiments and final selection log
- `POST_WF_INSTITUTIONAL_CHECKLIST.md`: post walk-forward institutional validation gates before paper/live
- `SINGLE_FACTOR_BASELINE.md`: standardized single-factor evaluation checklist
- `FACTOR_NOTES.md`: implementation notes and caveats per factor
- `docs/public_factor_references/FACTOR_PUBLIC_FORMULAS_AND_EXECUTION_CONSTRAINTS_EN.md`: public factor formulas, execution constraints, and V4 defect audit (English)
- `docs/public_factor_references/FACTOR_PUBLIC_FORMULAS_AND_EXECUTION_CONSTRAINTS_CN.md`: 公开因子公式、执行约束与 V4 缺陷审查（中文）
- `SYSTEM_OVERVIEW_CN.md`: Chinese system overview

## Interview-Ready Summary
Designed and implemented a modular, PIT-aware multi-factor research platform that standardizes factor validation and distinguishes robust alpha signals from unstable ones under institutional-style checks.

## Additional Public Summary
- `PROJECT_SUMMARY.md`: one-page interview-friendly project summary
