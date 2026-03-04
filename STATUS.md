# V4 Project Status (Public English Edition)

Last updated: 2026-03-04 (post-formal remediation reruns in progress on workstation)

## 1) Current Mode (Authoritative)
- Active pipeline: `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md`
- First official post-reset batch: `batchA100_logic100_formal_v1`
- Runtime state: `formal batch finished; targeted remediation reruns running` (workstation)
- Formal batch run id (closed): `2026-02-28_095939_batchA100_logic100_formal_v1`
- Current active run family: 2026-03-04 remediation reruns
  - data-remediation reruns for FMP/coverage-affected factors
  - logic-remediation reruns for duplicate-implementation factors

## 2) What Is Frozen Now
- Comparison baseline remains fixed for round-1:
  - `REBALANCE_FREQ=5`
  - `HOLDING_PERIOD=3`
  - `REBALANCE_MODE=None`
- Candidate scope: 100 formal distinct logic factors (no pair/tri stacking as official logic)
- Source documents:
  - `docs/production_research/BATCHA100_LOGIC100_FORMAL_V1_2026-02-28.csv`
  - `docs/production_research/BATCHA100_LOGIC100_IMPLEMENTATION_MAP_2026-02-28.csv`

## 3) Current Batch Readiness Snapshot
- Formal logic coverage in runtime mapping: `100/100`
- Implementation split:
  - `native=75`
  - `alias_proxy=18`
  - `proxy=7`
- Current remediation scope (2026-03-04):
  - `21` factors queued/rerun as remediation set
  - expected unaffected set: `79` factors
- Master query table:
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.md`

## 4) Governance Boundary
- Heavy official runs are workstation-only.
- Queue/batch launch still requires manual approval path (`configs/research/factory_queue/run_approval.json`).
- Command success is not equal to gate pass; promotion relies on final gate artifacts.

## 5) Data Readiness (for this batch)
- Core FMP paths are prepared under `data/fmp/` and `data/fmp/research_only/`.
- Latest readiness references:
  - `docs/production_research/BATCHA100_DATA_READINESS_2026-02-27.md`
  - `docs/production_research/BATCHA100_FMP_DOWNLOAD_REQUIREMENTS_2026-02-28.md`

## 6) Historical Boundary
- Pre-reset outputs remain retired and are not used as official evidence.
- Deprecated pair/tri draft representation is kept only for traceability and not used for this batch decision.

## 7) Next Batch Planning (Design-Only)
- BatchB design draft prepared (not approved, not running):
  - `docs/production_research/BATCHB100_LOGIC100_DESIGN_V1_2026-03-01.md`
  - `docs/production_research/BATCHB100_LOGIC100_DESIGN_V1_2026-03-01.csv`
  - `docs/production_research/BATCHB100_FMP_DOWNLOAD_REQUIREMENTS_2026-03-01.md`

## 8) Pipeline Patch (Governance)
- Completeness patch drafted (docs-only; no runtime impact on current running batch):
  - `docs/production_research/PIPELINE_COMPLETENESS_PATCH_2026-03-01.md`

## 9) Rerun Risk Notes (2026-03-04)
- `crowding_turnover_x_inst` is marked as rerun-required after institutional data refresh.
  - prior formal run evidence: only `2/9` segments had non-zero signals (`segment_summary.csv` in run `2026-02-28_095939_batchA100_logic100_formal_v1`).
  - data dependency: price turnover + institutional ownership level (`data/fmp/institutional/institutional-ownership__symbol-positions-summary.jsonl`).
- Additional rerun candidates may still be added if low-coverage patterns persist after current remediation runs finish.
- Potential API redirection/download-path anomaly should be reviewed in FMP ingestion scripts/logs before rerun promotion.
