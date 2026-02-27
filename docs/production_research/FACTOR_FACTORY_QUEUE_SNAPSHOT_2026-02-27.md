# Factor Factory Queue Snapshot (2026-02-27)

As-of: 2026-02-27 (workstation live verification)

This snapshot records current factor-factory continuity for this cycle. It is not an official production-gate verdict.

## 1) Verified Complete Outputs (Usable)

- `segment_results/factor_factory/2026-02-25_072539_p1_core_short_horizon`
  - `total=16`, `complete=16`
  - candidates:
    - `momentum_v2_core_001~004`
    - `reversal_v2_core_001~004`
    - `turnover_shock_core_001~004`
    - `vol_regime_core_001~004`
- `segment_results/factor_factory/2026-02-26_104024_p1_core_short_horizon_no_existing16`
  - `total=20`, `complete=20`
  - candidates:
    - `low_vol_v2_core_001~004`
    - `momentum_v2_core_new_001~004`
    - `reversal_v2_core_new_001~004`
    - `turnover_shock_core_new_001~004`
    - `vol_regime_core_new_001~004`
- merged usable set:
  - `36` complete candidates
  - signature-level duplicate check: `duplicate_groups=0` (`36/36` unique)

## 2) Non-Usable Lineages (Cleanup Applied)

The previously incomplete/stale lineages were removed from workstation storage to avoid accidental mixing:

- `segment_results/factor_factory/2026-02-26_103744_p1_core_short_horizon` (removed)
- `segment_results/factor_factory/2026-02-26_103804_p1_core_short_horizon` (removed)
- `segment_results/factor_factory/2026-02-27_033745_p2_quality_value_timing` (removed)

## 3) Runtime State

- V2 queue is currently stopped by operator decision.
- Current execution state is `review_required` for next batch planning.
- Any next queue execution requires explicit approval file update:
  - `configs/research/factory_queue/run_approval.json`

## 4) Execution Profile Boundary

- fixed profile baseline:
  - `REBALANCE_FREQ=5`
  - `HOLDING_PERIOD=3`
  - `REBALANCE_MODE=None`
  - `LOW_VOL_USE_RESIDUAL=false` (p1 + p4 policy configs)
- queue-level de-dup validation remained:
  - `new_total=100`, `new_unique=100`, `overlap_with_retained16=0`

## 5) Interpretation Boundary

1. Current cycle's usable factor-factory dataset is the merged complete `36` only (V1 frozen baseline).
2. Next batches (V2/V3/...) are blocked until manual review approval.
3. Official gate SSOT remains:
   - `docs/production_research/CURRENT_GATE_STATUS_2026-02-23.md`
4. `FACTOR_FACTORY_QUEUE_SNAPSHOT_2026-02-26.md` is retained as historical continuity context, not latest state.
