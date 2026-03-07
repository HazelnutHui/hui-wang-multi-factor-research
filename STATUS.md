# V4 Project Status (Public English Edition)

Last updated: 2026-03-07 (logic100 final consolidated baseline)

## 1) Current Mode (Authoritative)
- Active pipeline: `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md`
- First official post-reset batch: `batchA100_logic100_formal_v1`
- Runtime state: `final consolidated result ready` (workstation canonical path)
- Formal batch run id (closed): `2026-02-28_095939_batchA100_logic100_formal_v1`
- Canonical final result path:
  - `segment_results/factor_factory/2026-02-28_095939_batchA100_logic100_formal_v1`

## SSOT Rule (Status Maintenance)
- This file is the only project-level runtime status source of truth.
- Do not duplicate "current status snapshot" in other markdown files.
- Other docs should reference this file and the row-level result file:
  - `docs/production_research/BATCHA100_FINAL_RESULT_STATUS_2026-03-07.md`

## 2) What Is Frozen Now
- Comparison baseline remains fixed for round-1:
  - `REBALANCE_FREQ=5`
  - `HOLDING_PERIOD=3`
  - `REBALANCE_MODE=None`
- Candidate scope: 100 formal distinct logic factors (no pair/tri stacking as official logic)
- Source documents:
  - `docs/production_research/BATCHA100_LOGIC100_FORMAL_V1_2026-02-28.csv`
  - `docs/production_research/BATCHA100_LOGIC100_IMPLEMENTATION_MAP_2026-02-28.csv`

## 3) Final Batch Snapshot
- Formal logic coverage in runtime mapping: `100/100`
- Implementation split:
  - `native=75`
  - `alias_proxy=18`
  - `proxy=7`
- Final consolidated status:
  - total factors with valid outputs: `100/100`
  - all 21 targeted replacements are integrated into canonical path
  - exact duplicate IC-vector groups in canonical set: `0`
  - final interpretation boundary: use canonical path only (ignore intermediate rerun paths)
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
  - `docs/production_research/FMP_CALLABLE_DATA_REFERENCE_2026-03-07.md`
- FMP callable metrics boundary:
  - endpoint-level baseline: `156` callable stable endpoints (2026-02-23 probe baseline)
  - field-level baseline: `824` sampled unique fields (`751` default-allow)

## 6) Historical Boundary
- Pre-reset outputs remain retired and are not used as official evidence.
- Deprecated pair/tri draft representation is kept only for traceability and not used for this batch decision.

## 7) Pipeline Patch (Governance)
- Completeness patch drafted (docs-only; no runtime impact on current running batch):
  - `docs/production_research/PIPELINE_COMPLETENESS_PATCH_2026-03-01.md`

## 8) Final Result Reference
- Canonical row-level status:
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
- Canonical summary:
  - `docs/production_research/BATCHA100_FINAL_RESULT_STATUS_2026-03-07.md`
- Post-fix note:
  - duplicate-logic fixes for `cash_conversion_improve`, `eps_growth_quality_adj`, and `capex_discipline` are integrated in canonical output.
