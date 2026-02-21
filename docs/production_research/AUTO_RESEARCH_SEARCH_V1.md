# Auto Research Search V1 Standard

Last updated: 2026-02-21

Purpose:
- standardize parameter-search trial generation for `combo_v2`;
- produce executable/dry-run command plans with full audit trace;
- keep default behavior safe (`execute=false`, `dry_run=true`).

## Components

- `configs/research/auto_research_search_v1_policy.json`
- `scripts/build_search_v1_trials.py`

## Trial Policy (Current)

- `mode`: `grid` or `random`
- `max_trials`: cap on selected trials from search space
- `seed`: deterministic random-mode selection
- `execute`: whether to run generated commands
- `dry_run`: whether generated commands include `--dry-run`
- `base_strategy`: base strategy yaml template
- `workflow.*`: production gates defaults (`factor`, `cost_multipliers`, `wf_shards`, `out_dir`)
- `space.*`:
  - `value_weight`
  - `momentum_lookback`
  - `rebalance_freq`
  - `min_dollar_volume`

## Strategy Override Mapping

Each trial generates one derived strategy yaml from `base_strategy`:

1. `space.value_weight` -> `factors.weights.value`
2. `1 - value_weight` -> `factors.weights.momentum`
3. `space.momentum_lookback` -> `factors.momentum.lookback`
4. `space.rebalance_freq` -> `execution.rebalance_freq`
5. `space.min_dollar_volume` -> `universe.min_dollar_volume`

Other factor weights are fixed to `0.0` for this search profile.

## Standard Usage

Build plan only (recommended default):

```bash
python scripts/build_search_v1_trials.py
```

Build with random mode and smaller budget:

```bash
python scripts/build_search_v1_trials.py --mode random --max-trials 6
```

Execute generated trial commands in dry-run mode:

```bash
python scripts/build_search_v1_trials.py --execute --dry-run
```

## Audit Outputs

Per search build run:

- `audit/search_v1/<timestamp>_search_v1/search_v1_trial_plan.json`
- `audit/search_v1/<timestamp>_search_v1/search_v1_trial_plan.md`
- `audit/search_v1/<timestamp>_search_v1/search_v1_trial_plan.csv`
- `audit/search_v1/<timestamp>_search_v1/search_v1_execution_report.json`
- `audit/search_v1/<timestamp>_search_v1/strategies/trial_*.yaml`

## Operational Rules

1. Keep `execute=false` in policy unless workstation resources and monitoring are prepared.
2. Keep `dry_run=true` for unattended scheduling until strategy/freeze/DQ paths are verified.
3. If promoting to official execution, use new decision tags and preserve append-only audit history.
4. Do not reuse trial strategy files across different search runs; each run directory is immutable.
