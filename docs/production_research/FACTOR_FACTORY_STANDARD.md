# Factor Factory Standard

Last updated: 2026-02-27

Purpose:
- industrialize new-factor generation and batch validation;
- avoid manual command stitching for large candidate sets;
- produce ranked candidates with reproducible artifacts.

## Components

- Entry:
  - `bash scripts/ops_entry.sh factory ...`
- Runner:
  - `scripts/run_factor_factory_batch.py`
- Policy:
  - `configs/research/factor_factory_policy.json`

## Default Behavior

1. build candidates from policy families/grid
2. run segmented single-factor backtests in parallel
3. aggregate metrics (`ic_overall`, stability, sharpe)
4. generate leaderboard + report under `audit/factor_factory/...`

Stage mapping (to avoid ambiguity):
- factor-factory batch is an `S0` pre-screen pipeline for candidate generation/ranking.
- only non-dry-run leaderboard outputs are eligible to enter the single-factor validation stack.
- `--dry-run` validates command wiring only and must not be treated as segmented/train-test evidence.

Execution default:
- official/primary factor-factory batch execution must run on workstation.
- local machine is for dry-run planning, code edits, and small smoke checks only.
- default parallelism is `--jobs 8` on workstation (minimum acceptable `--jobs 4`).

Current normalized execution profile (for cross-batch comparability):
- `REBALANCE_FREQ=5`
- `HOLDING_PERIOD=3`
- `REBALANCE_MODE=None`
- `EXECUTION_USE_TRADING_DAYS=True`
- profile is injected by `configs/research/factor_factory_policy.json` `default_set`.
- round-1 fast-screen rule: avoid heavy residual momentum variants (`MOMENTUM_USE_RESIDUAL=False`) in queue policies.

Holding-period robustness policy (saved decision):
1. round-1 screening:
  - run large-scale queue/batch with fixed `5/3/None` profile for strict comparability.
2. round-2 robustness:
  - only on shortlisted top candidates (recommended top `20-30`);
  - run parallel holding-period checks with `HOLDING_PERIOD in {1,3,5}` while keeping `REBALANCE_FREQ=5` and `REBALANCE_MODE=None`.
3. promotion:
  - prioritize candidates that remain stable across `1/3/5` instead of single-period winners.

Pipeline freeze reference:
- `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md`

## Standard Usage

Dry-run plan generation (local allowed):

```bash
bash scripts/ops_entry.sh factory --dry-run --jobs 4
```

Execute full batch (workstation default):

```bash
bash scripts/ops_entry.sh factory --jobs 8
```

Cap candidates (workstation default):

```bash
bash scripts/ops_entry.sh factory --jobs 8 --max-candidates 20
```

Queue multiple batches (approval required, workstation):

```bash
# 1) set approval file first:
# configs/research/factory_queue/run_approval.json
#   approved=true
#   approved_queue=<exact queue path>
#
# 2) run queue
bash scripts/ops_entry.sh factory_queue \
  --queue-json configs/research/factory_queue/<target_queue>.json \
  --jobs 8
```

Approval gate:
- enforced by `scripts/run_factor_factory_queue.py`
- default approval file: `configs/research/factory_queue/run_approval.json`
- queue run is blocked if:
  - `approved != true`, or
  - `approved_queue` does not exactly equal `--queue-json`.

## Artifacts

Per batch run:

- `audit/factor_factory/<ts>_<batch>/candidate_plan.csv`
- `audit/factor_factory/<ts>_<batch>/execution_results.csv`
- `audit/factor_factory/<ts>_<batch>/leaderboard.csv`
- `audit/factor_factory/<ts>_<batch>/factor_factory_batch_report.json`
- `audit/factor_factory/<ts>_<batch>/factor_factory_batch_report.md`

Per candidate runtime outputs:

- `segment_results/factor_factory/<ts>_<batch>/<candidate_id>/...`

## Policy Model

`factor_factory_policy.json` fields:

1. `batch_name`
2. `mode` (`grid` / `random`)
3. `years` (segment years)
4. `default_set` (global `--set` overrides)
5. `families[]`:
- `name`
- `factor`
- `max_candidates`
- `grid` (parameter search space)

## Promotion Rule (Recommended)

1. keep top candidates by leaderboard score
2. run fast combo integration for top-N
3. send shortlisted variants to `official` gate only
