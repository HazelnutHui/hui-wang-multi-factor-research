# V4 Project Status (Public English Edition)

Last updated: 2026-02-27 (v2 queue still running; latest verified usable set is 36 unique candidates)

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

## 4) Latest Factor-Factory Snapshot (2026-02-27)
- Snapshot note: `docs/production_research/FACTOR_FACTORY_QUEUE_SNAPSHOT_2026-02-27.md`
- Current verified usable outputs:
  - run dir: `segment_results/factor_factory/2026-02-25_072539_p1_core_short_horizon` (`16/16` complete)
  - run dir: `segment_results/factor_factory/2026-02-26_104024_p1_core_short_horizon_no_existing16` (`20/20` complete)
  - merged usable set: `36` complete candidates, signature-level unique (`duplicate_groups=0`)
- Incomplete/non-usable lineages (not for ranking or gate input):
  - `segment_results/factor_factory/2026-02-26_103744_p1_core_short_horizon` (`0/20` complete)
  - `segment_results/factor_factory/2026-02-26_103804_p1_core_short_horizon` (`0/20` complete)
  - `segment_results/factor_factory/2026-02-27_033745_p2_quality_value_timing` (`0/20` complete)
- Current queue state:
  - active run on workstation: `queue_100_fastscreen_v2` (`--jobs 8`, single queue process)
  - active batch process observed: `policy_p2_quality_value_timing` (`--jobs 8 --max-candidates 20`)
  - runtime safeguards:
    - BLAS thread caps enabled (`OMP/MKL/OPENBLAS/NUMEXPR=1`) to avoid CPU oversubscription
    - queue `sleep_sec=0`
  - this snapshot does not override official gate status; gate SSOT remains `CURRENT_GATE_STATUS_2026-02-23.md`

## 5) FMP Next100 Data Readiness (2026-02-26)
- Plan note: `docs/production_research/FMP_NEXT100_DATA_PLAN_2026-02-26.md`
- Governance rule:
  - only `factor_ready_with_lag` data may enter default next100 factor generation
  - `research_only_high_leakage_guard` data stays in isolated research inputs until PIT checks pass
- Download status:
  - next100-required endpoint pull + 429 retry were completed on workstation
  - paths were normalized to `data/fmp/` and `data/fmp/research_only/`; legacy staging backup removed

## 6) Next100 V3 Draft Status (2026-02-26)
- Plan note: `docs/production_research/NEXT100_V3_PLAN_2026-02-26.md`
- Intent:
  - V3 is defined as **new-signal-first** expansion (expectation/event/inst-flow/owner-earnings/accounting structure), not repeated V2-style parameter tuning.
- Current state:
  - V3 queue/policies are written as draft config only.
  - V3 is not running while V2 queue is active.
- Launch prerequisites:
  - FMP support + code-level new factor implementation complete
  - signature-level overlap checks vs historical16 and V2 both equal `0`

## 7) Historical Records (Kept for Audit, Not Active Requirements)
- `PROJECT_SUMMARY.md`
- `COMBO_WEIGHT_EXPERIMENTS.md`
- `FACTOR_NOTES.md`
- historical gate snapshots in `docs/production_research/CURRENT_GATE_STATUS_2026-02-20.md` and `...2026-02-21.md`
