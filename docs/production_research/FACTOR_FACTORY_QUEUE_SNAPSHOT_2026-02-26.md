# Factor Factory Queue Snapshot (2026-02-26)

As-of: 2026-02-26 (cleanup completed, then de-duplicated next100 run restarted)

This is a historical snapshot kept for continuity. It is not the latest state and not an official production-gate verdict.

## 1) Final Retained Outputs

- Retained run directory:
  - `segment_results/factor_factory/2026-02-25_072539_p1_core_short_horizon`
- Completed candidate count: `16/16`
- Retained candidates:
  - `momentum_v2_core_001~004`
  - `reversal_v2_core_001~004`
  - `turnover_shock_core_001~004`
  - `vol_regime_core_001~004`

## 2) Cleanup Result

- Temporary stop/cleanup was completed for this cycle.
- Removed duplicated restarted lineage:
  - `segment_results/factor_factory/2026-02-26_010815_p1_core_short_horizon`
- Removed incomplete residual candidates under retained run:
  - `low_vol_v2_core_001~004`

## 3) Restarted Run State (Latest)

- Active queue on workstation:
  - `configs/research/factory_queue/queue_100_fastscreen_v2.json`
  - `--jobs 8`
- Active queue log:
  - `logs/queue_100_fastscreen_v2_2026-02-26_104024.log`
- Current p1 run directory:
  - `segment_results/factor_factory/2026-02-26_104024_p1_core_short_horizon_no_existing16`
  - candidate folders observed: `20`
- De-dup validation before restart:
  - total queue candidates: `100`
  - unique signatures: `100`
  - overlap with retained historical 16: `0`

## 4) Config Context

- First-round low-vol residual setting remains disabled:
  - `configs/research/factory_queue/policy_p1_core_short_horizon_no_existing16.json`
  - `configs/research/factory_queue/policy_p4_neutralized_core.json`
  - `LOW_VOL_USE_RESIDUAL=[false]`

## 5) Interpretation Boundary (Historical As-of 2026-02-26)

1. As-of 2026-02-26, the then-reference dataset was the retained `16` only.
2. Next100 run must use a new lineage and de-duplicated queue definition (do not mix with removed/stale restarted outputs).
3. Official gate status SSOT remains:
   - `docs/production_research/CURRENT_GATE_STATUS_2026-02-23.md`
4. V3 configs are draft-only in this cycle and must not be launched before:
   - V2 queue completion or explicit switch decision,
   - new-signal implementation and de-dup gate completion.
5. For current/latest state, use:
   - `docs/production_research/FACTOR_FACTORY_QUEUE_SNAPSHOT_2026-02-27.md`
6. Referenced queue/policy config files in this historical snapshot were retired and deleted on 2026-02-27.
