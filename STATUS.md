# V4 Project Status (Public English Edition)

Last updated: 2026-02-26 (next100 de-duplicated queue running on workstation)

## 1) Current Mode (Authoritative)
- Active pipeline: `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md`
- Factor discovery default: workstation `factory_queue` with fast-screen policy
  - queue: `configs/research/factory_queue/queue_100_fastscreen_v2.json`
  - parallelism: `--jobs 8`
  - fixed profile: `REBALANCE_FREQ=5`, `HOLDING_PERIOD=3`, `REBALANCE_MODE=None`
  - round-1 low-vol setting: `LOW_VOL_USE_RESIDUAL=false` (p1 + p4 policy configs)
- Single-factor validation policy:
  - `SF-L1` segmented strict: mandatory gate
  - `SF-L2` fixed train/test: mandatory before combo promotion
  - `SF-DIAG` segmented diagnostics: optional only

## 2) Execution Rules (Current)
1. Large-scale candidate generation in `S0` only.
2. `1/3/5` holding-period robustness only for shortlisted candidates.
3. Do not run combo validation before single-factor shortlist is frozen.
4. Heavy official runs remain workstation-only.

## 3) Gate Status Boundary
- Official gate pass/fail must be read from latest gate artifacts, not command exit codes.
- If workstation and local artifacts differ, local status is `pending_local_sync` until verified.
- Current local gate snapshot reference:
  - `docs/production_research/CURRENT_GATE_STATUS_2026-02-23.md`

## 4) Latest Factor-Factory Snapshot (2026-02-26)
- Snapshot note: `docs/production_research/FACTOR_FACTORY_QUEUE_SNAPSHOT_2026-02-26.md`
- Current retained outputs:
  - run dir: `segment_results/factor_factory/2026-02-25_072539_p1_core_short_horizon`
  - completed candidates: `16` (`momentum_v2/reversal_v2/turnover_shock/vol_regime`, each `core_001~004`)
- Current queue state:
  - active run on workstation: `queue_100_fastscreen_v2` (`--jobs 8`, single queue process)
  - p1 is switched to de-duplicated policy:
    - `configs/research/factory_queue/policy_p1_core_short_horizon_no_existing16.json`
  - runtime safeguards:
    - BLAS thread caps enabled (`OMP/MKL/OPENBLAS/NUMEXPR=1`) to avoid CPU oversubscription
    - queue `sleep_sec=0`
  - current next100 queue definition was validated before run:
    - `new_total=100`, `new_unique=100`, `overlap_with_retained16=0`
  - this snapshot does not override official gate status; gate SSOT remains `CURRENT_GATE_STATUS_2026-02-23.md`

## 5) FMP Next100 Data Readiness (2026-02-26)
- Plan note: `docs/production_research/FMP_NEXT100_DATA_PLAN_2026-02-26.md`
- Governance rule:
  - only `factor_ready_with_lag` data may enter default next100 factor generation
  - `research_only_high_leakage_guard` data stays in isolated research inputs until PIT checks pass
- Download status:
  - next100-required endpoint pull + 429 retry were completed on workstation
  - paths were normalized to `data/fmp/` and `data/fmp/research_only/`; legacy staging backup removed

## 6) Historical Records (Kept for Audit, Not Active Requirements)
- `PROJECT_SUMMARY.md`
- `COMBO_WEIGHT_EXPERIMENTS.md`
- `FACTOR_NOTES.md`
- historical gate snapshots in `docs/production_research/CURRENT_GATE_STATUS_2026-02-20.md` and `...2026-02-21.md`
