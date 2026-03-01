# V4 Project Status (Public English Edition)

Last updated: 2026-02-28 (formal logic100 run in progress on workstation)

## 1) Current Mode (Authoritative)
- Active pipeline: `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md`
- First official post-reset batch: `batchA100_logic100_formal_v1`
- Runtime state: `running` (workstation)
- Current run id: `2026-02-28_095939_batchA100_logic100_formal_v1`
- No official performance conclusion yet (run not finished)

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
