# Multi-Factor Alpha Research Platform (V4)

A bias-aware, reproducible, daily-frequency factor research system for US equities.

This project focuses on turning factor ideas into decision-grade research outputs with a consistent validation protocol, not one-off backtest screenshots.

## Recruiter Quick Link
- Start here: [`STATUS.md`](STATUS.md)

## White Paper
- English: [`docs/production_research/SYSTEM_OVERVIEW_EN.md`](docs/production_research/SYSTEM_OVERVIEW_EN.md)
- 中文: [`docs/production_research/SYSTEM_OVERVIEW_ZH.md`](docs/production_research/SYSTEM_OVERVIEW_ZH.md)

## What This Project Does
- Builds rebalance-date-driven backtests for factor strategies
- Evaluates factors with segmented IC, fixed train/test, and walk-forward
- Supports mandatory single-factor strict validation (`SF-L1`) plus optional diagnostics (`SF-DIAG`)
- Adds point-in-time (PIT) controls for fundamentals timing
- Handles delisted data paths to reduce survivorship bias
- Produces structured diagnostics (rolling IC, quantiles, turnover, cost sensitivity)

## Validation Framework
Each factor follows the same research gate:

1. Segmented strict backtest (2-year slices): robustness across regimes
2. Fixed train/test: out-of-sample degradation check
3. Walk-forward: deployment-style rolling validation (shortlist only)

Default single-factor path is `SF-L1 -> SF-L2`; `SF-DIAG` is optional and non-gating.

## Current Operating Mode (2026-03-04)
- authoritative pipeline is frozen in:
  - `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md`
- factor factory governance:
  - Reset declaration: `docs/production_research/RESET_STATE_2026-02-27.md`
  - all next batches require manual approval before run:
    - `configs/research/factory_queue/run_approval.json`
  - fixed comparability profile (for approved runs): `REBALANCE_FREQ=5`, `HOLDING_PERIOD=3`, `REBALANCE_MODE=None`
- round design:
  1. `S0` large-scale pre-screen
  2. shortlist `1/3/5` holding-period robustness
  3. single-factor validation (`SF-L1` mandatory + `SF-L2` mandatory; `SF-DIAG` optional)
  4. combo Layer1/Layer2/Layer3
  5. production gates

Current runtime status:
- formal run `2026-02-28_095939_batchA100_logic100_formal_v1` is closed
- active workstation jobs are targeted remediation reruns
  - FMP/coverage-affected subset
  - duplicate-implementation subset

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
- `live_trading/`: live daily score, accuracy, and readable reports
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

### 6) Unified ops entry (recommended for daily work)
```bash
bash scripts/ops_entry.sh daily
# fast status refresh only:
# bash scripts/ops_entry.sh status
```

## Public-Repo Notes
- Large local datasets, logs, and generated results are intentionally excluded.
- To reproduce full results, prepare your own data caches and API keys.
- Do not commit secrets (API tokens, credentials, private keys).

## Live Trading Daily Validation (T -> T+1)
- Daily score snapshot archive path:
  - `live_trading/scores/trade_YYYY-MM-DD_from_signal_YYYY-MM-DD/`
- Daily realized-accuracy archive path:
  - `live_trading/accuracy/trade_YYYY-MM-DD_from_signal_YYYY-MM-DD/`
- Daily readable reports path:
  - `live_trading/reports/daily/en/<run_id>/daily_report_en.pdf`
  - `live_trading/reports/daily/zh/<run_id>/daily_report_zh.pdf`

Core metrics (production-style, daily):
- IC: Pearson and Spearman
- Top/Bottom bucket mean return and spread
- Top/Bottom win rate
- Coverage (`n_matched / n_total`)
- Decile return table

## Key Documents
- `SESSION_CONTINUITY_PROTOCOL.md`: single-file handoff guide for new sessions (read this first)
- `RUNBOOK.md`: practical command reference
- `STATUS.md`: current progress and latest run status
- `WEBSITE_HANDOFF.md`: website dashboard handoff and continuation notes
- `docs/hui_dashboard/README.md`: Hui dashboard deployment/runtime notes and operations guide
- `POST_WF_PRODUCTION_CHECKLIST.md`: post walk-forward production validation gates before paper/live
- `SINGLE_FACTOR_BASELINE.md`: standardized single-factor evaluation checklist
- `docs/public_factor_references/FACTOR_PUBLIC_FORMULAS_AND_EXECUTION_CONSTRAINTS_EN.md`: public factor formulas, execution constraints, and V4 defect audit (English)
- `docs/public_factor_references/FACTOR_PUBLIC_FORMULAS_AND_EXECUTION_CONSTRAINTS_CN.md`: 公开因子公式、执行约束与 V4 缺陷审查（中文）

## Interview-Ready Summary
Designed and implemented a modular, PIT-aware multi-factor research platform that standardizes factor validation and distinguishes robust alpha signals from unstable ones under production-style checks.

## Additional Public Summary
- `docs/production_research/SYSTEM_OVERVIEW_EN.md`: concise architecture and governance summary
