# V4 Project Status (Public English Edition)

Last updated: 2026-02-27 (V1 batch36 frozen; no V2/V3 queue retained; any future batch must be newly reviewed and manually approved)

## 1) Current Mode (Authoritative)
- Active pipeline: `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md`
- Factor discovery current governance:
  - baseline reference: `docs/production_research/V1_BATCH36_BASELINE_2026-02-27.md`
  - execution state: `review_required`
  - queue runtime gate: `configs/research/factory_queue/run_approval.json` must approve target queue before any run
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
- Master query table:
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.md`
- Current verified usable outputs:
  - run dir: `segment_results/factor_factory/2026-02-25_072539_p1_core_short_horizon` (`16/16` complete)
  - run dir: `segment_results/factor_factory/2026-02-26_104024_p1_core_short_horizon_no_existing16` (`20/20` complete)
  - merged usable set: `36` complete candidates, signature-level unique (`duplicate_groups=0`)
- Incomplete/non-usable lineages (not for ranking or gate input):
  - `segment_results/factor_factory/2026-02-26_103744_p1_core_short_horizon` (`0/20` complete)
  - `segment_results/factor_factory/2026-02-26_103804_p1_core_short_horizon` (`0/20` complete)
  - `segment_results/factor_factory/2026-02-27_033745_p2_quality_value_timing` (`0/20` complete)
- Queue state:
  - active queue processes: none
  - baseline `36` is frozen as current clean reference (V1)
  - queue config directory currently keeps only:
    - `configs/research/factory_queue/run_approval.json`
  - this snapshot does not override official gate status; gate SSOT remains `CURRENT_GATE_STATUS_2026-02-23.md`

## 5) FMP Next100 Data Readiness (2026-02-27)
- Plan note: `docs/production_research/FMP_NEXT100_DATA_PLAN_2026-02-26.md`
- BatchA readiness table:
  - `docs/production_research/BATCHA100_DATA_READINESS_2026-02-27.md`
  - `docs/production_research/BATCHA100_DATA_READINESS_2026-02-27.csv`
- Governance rule:
  - only `factor_ready_with_lag` data may enter default next100 factor generation
  - `research_only_high_leakage_guard` data stays in isolated research inputs until PIT checks pass
- Download status:
  - next100-required endpoint pull + 429 retry were completed on workstation
  - paths were normalized to `data/fmp/` and `data/fmp/research_only/`; legacy staging backup removed
  - newly downloaded on workstation for BatchA support:
    - `data/fmp/earnings_history/earnings.jsonl` (`5372` symbols, `4122` non-empty payload)
    - `data/fmp/statements/income-statement.jsonl` (`5372` symbols, `4688` non-empty payload)
    - `data/fmp/statements/income-statement-ttm.jsonl` (`5372` symbols, `4679` non-empty payload)
  - BatchA coverage conclusion:
    - `25/25` logic families are data-ready for run
    - `sue_revenue_basic` fallback to `earnings_history/earnings.jsonl` is wired in `backtest/factor_engine.py` and workstation-verified

## 6) Next Batch Status
- V2/V3 drafts, queues, and policies were removed.
- Current policy: no pre-created next-batch queue; create only after review, then run with explicit approval in `configs/research/factory_queue/run_approval.json`.

## 7) Historical Records (Kept for Audit, Not Active Requirements)
- historical gate snapshots in `docs/production_research/CURRENT_GATE_STATUS_2026-02-20.md` and `...2026-02-21.md`
