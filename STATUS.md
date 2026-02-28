# V4 Project Status (Public English Edition)

Last updated: 2026-02-27 (Reset mode; no formal historical result retained; batchA100_logic100_v1 is first official batch and pending approval)

## 1) Current Mode (Authoritative)
- Active pipeline: `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md`
- Factor discovery current governance:
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
- Current local reset state keeps no official gate artifact snapshot as SSOT.

## 4) Current Factor-Factory State (Post-Reset)
- Reset declaration: `docs/production_research/RESET_STATE_2026-02-27.md`
- Master query table:
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.md`
- Verified usable outputs: none (all pre-reset result sets retired and deleted).
- Queue state:
  - active batch run: none
  - next prepared batch:
    - `batchA100_logic100_v1` (100 distinct logic candidates; one candidate per logic)
    - status: `ready_for_review` (not started)
  - current official reference set: none (pre-run state)
  - queue config directory currently keeps only:
    - `configs/research/factory_queue/run_approval.json`
  - no local official gate snapshot file is treated as SSOT in reset mode.

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
    - current target is `batchA100_logic100_v1` (`100` distinct logic factors), data path is ready for this logic100 run
    - parameter expansion is a later-stage step and is not part of current first-pass logic100 definition
    - `sue_revenue_basic` fallback to `earnings_history/earnings.jsonl` is wired in `backtest/factor_engine.py` and workstation-verified

## 6) Next Batch Status
- V2/V3 drafts, queues, and policies were removed.
- Current policy: no pre-created next-batch queue; create only after review, then run with explicit approval in `configs/research/factory_queue/run_approval.json`.

## 7) Historical Records
- pre-reset historical snapshots were retired during reset cleanup and are not part of current governance SSOT.
