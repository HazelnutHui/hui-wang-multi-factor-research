# Config Audit (2026-02-24)

Scope:
- factor-factory execution chain (`ops_entry.sh` -> `run_factor_factory_batch.py` -> `run_segmented_factors.py`)
- strategy execution defaults (`configs/strategies/*.yaml`, `strategies/*/config.py`)
- protocol defaults (`configs/protocol*.yaml`)

## What Was Fixed

1. Factor-factory profile drift removed.
- Updated `configs/research/factor_factory_policy.json` `default_set`:
  - `REBALANCE_FREQ=5`
  - `HOLDING_PERIOD=3`
  - `REBALANCE_MODE=None`
  - `EXECUTION_USE_TRADING_DAYS=True`
- Result: all candidates in one batch are evaluated under the same weekly horizon profile.

2. Batch1 helper script aligned.
- Updated `scripts/run_new_factor_batch1.sh` with the same overrides.
- Result: manual batch helper and policy batch use the same execution horizon.

3. Python environment mismatch hardening.
- Updated `scripts/ops_entry.sh` to prefer `.venv/bin/python`, then `python3`, then `python`.
- Result: avoids local/system Python dependency mismatch (e.g., pandas missing in system python).

## Current Strategy Default Snapshot

1. Monthly-style defaults (legacy baseline family):
- `value_v2`, `quality_v2`, `combo_v2`: `holding_period` around `20`, `rebalance_freq` around `21` (or `month_end` behavior).
- `momentum_v1/v2`, `low_vol_v2`: often `month_end` mode with `holding_period=21`.

2. Short-horizon defaults:
- `reversal_v2`: `holding_period=1`, `rebalance_freq=1`.
- `pead_v2`: `holding_period=1`, `rebalance_freq=5`.

3. Protocol base:
- `configs/protocol.yaml`: `rebalance_freq=21`, `holding_period=21`.
- This remains unchanged to preserve historical baseline compatibility for non-factory workflows.

## Decision

- For factor-factory candidate screening, use fixed profile (`5/3`, non-`month_end`) as the standard comparison baseline.
- After round-1 ranking, run holding-period robustness on shortlisted top `20-30` with `HOLDING_PERIOD=1/3/5` (keep `REBALANCE_FREQ=5`, `REBALANCE_MODE=None`).
- Keep legacy strategy/protocol defaults unchanged unless an explicit major migration is approved (would impact historical comparability).
