# V4 Project Status (Public English Edition)

Last updated: 2026-03-11 (combo L2 preregistered12 running on workstation)

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

## 2.1) Active Admission Standard (Locked)
- Authoritative policy docs:
  - `SINGLE_FACTOR_BASELINE.md` (Hard Rules v1.0)
  - `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md` (Locked v1.0 sections)
- Current hard gates:
  - `SF-L2`: `test_ic > 0` required for main combo
  - `SF-L3`: positive-window ratio `>= 60%`, no 3 consecutive negative windows
  - cost-adjusted out-of-sample must remain positive
- Grade rule:
  - `A`: `test_ic >= 0.006`
  - `B`: `0 < test_ic < 0.006`
  - `C`: `test_ic <= 0` or WF/cost fail
- Main combo admission: only grades `A/B`

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
- Round2 hold robustness (1/3/5 shortlist check):
  - `docs/production_research/BATCHA100_ROUND2_HOLD_ROBUSTNESS_2026-03-07.md`
  - `docs/production_research/BATCHA100_ROUND2_HOLD_ROBUSTNESS_2026-03-07.csv`
  - current snapshot: `20` shortlist tested, `17` robust-pass
- Post-fix note:
  - duplicate-logic fixes for `cash_conversion_improve`, `eps_growth_quality_adj`, and `capex_discipline` are integrated in canonical output.

## 9) Active Runtime Snapshot (Current)
- Completed job (workstation):
  - `SF-L3` full single-factor WF for 17 factors
  - run dir: `runs/sf_l3_wf_17_20260309_212116`
  - window design: train `3y`, test `1y`, test years `2013..2025` (total `221` tasks)
- Final execution snapshot:
  - `done=221`
  - `ok=221`
  - `fail=0`
  - `remaining=0`
- Provisional single-factor admission grading (L2 + L3 only; cost gate pending):
  - `A=7`
  - `B=5`
  - `C=5`
  - reference: `docs/production_research/WF17_SINGLE_FACTOR_GRADE_2026-03-11.md`
- Workstation repository topology (locked):
  - runtime repo (do not force pull while jobs run):
    - `~/projects/hui-wang-multi-factor-research`
  - clean sync repo (git-updated code mirror):
    - `~/projects/v4_clean`

## 10) Current Execution Boundary
- Combo preregistered set (cycle-1) is locked at 12 candidates:
  - `docs/production_research/COMBO_PREREGISTERED_SET_2026-03-11.md`
  - strategy configs: `configs/strategies/combo_p0_*` ... `combo_p11_*`
- Combo-layer baseline is now locked:
  - `docs/production_research/COMBO_RESEARCH_BASELINE_2026-03-11.md`
- Promotion boundary remains unchanged:
  - no combo result is official until governed run + gate artifacts are produced.

## 11) Active Combo Runtime Snapshot (Current)
- Running job (workstation, background):
  - stage: `Layer2` (fixed train/test)
  - scope: `12` preregistered combo candidates (`combo_p0..combo_p11`)
  - parallelism: `8`
  - runtime repo: `~/projects/hui-wang-multi-factor-research`
  - run dir: `runs/combo_l2_preregistered12_20260312_013348`
  - launcher pid: `103388`
- Monitoring files:
  - driver log: `runs/combo_l2_preregistered12_20260312_013348/batch_driver.log`
  - per-combo logs: `runs/combo_l2_preregistered12_20260312_013348/logs/*.log`
