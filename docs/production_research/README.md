# Production Research Governance Docs

Last updated: 2026-03-04 (post-formal remediation runtime sync)

## Current Operating State
- No formal historical factor result is retained.
- First official research batch is `batchA100_logic100_formal_v1`.
- Formal run status: `closed` (`run_id=2026-02-28_095939_batchA100_logic100_formal_v1`).
- Current status: remediation reruns `running` on workstation (FMP/coverage + duplicate-implementation subsets).
- Any run launch requires manual approval.

## Primary Documents
- `RESET_STATE_2026-02-27.md`
- `FACTOR_BATCH_MASTER_TABLE.csv`
- `FACTOR_BATCH_MASTER_TABLE.md`
- `BATCHA100_LOGIC100_BLUEPRINT_2026-02-28.md`
- `BATCHA100_LOGIC100_FORMAL_V1_2026-02-28.md`
- `BATCHA100_LOGIC100_FORMAL_V1_2026-02-28.csv`
- `BATCHA100_GATE_REPORT_2026-02-28.md`
- `BATCHA100_PHASE1_RUNNABLE10_2026-02-28.csv`
- `BATCHA100_LOGIC100_IMPLEMENTATION_MAP_2026-02-28.md`
- `BATCHA100_LOGIC100_IMPLEMENTATION_MAP_2026-02-28.csv`
- `FACTOR_FACTORY_STANDARD.md`
- `FACTOR_PIPELINE_FREEZE_2026-02-25.md`
- `PIPELINE_COMPLETENESS_PATCH_2026-03-01.md`
- `OPS_PLAYBOOK.md`
- `STAGE_EXECUTION_STANDARD.md`
- `WORKSTATION_PRIMARY_MODE.md`
- `WORKSTATION_RUNNER_SPEC.md`
- `FACTOR_ENGINE_SNAPSHOT_2026-03-04.md`

## Data Readiness
- `FMP_NEXT100_DATA_PLAN_2026-02-26.md`
- `BATCHA100_DATA_READINESS_2026-02-27.md`
- `BATCHA100_FMP_DOWNLOAD_REQUIREMENTS_2026-02-28.md`

## Next Batch Design (Not Running)
- `BATCHB100_LOGIC100_DESIGN_V1_2026-03-01.md`
- `BATCHB100_LOGIC100_DESIGN_V1_2026-03-01.csv`
- `BATCHB100_FMP_DOWNLOAD_REQUIREMENTS_2026-03-01.md`

## Command Entry
- `scripts/ops_entry.sh`
- `scripts/run_factor_factory_batch.py`
- `scripts/run_segmented_factors.py`
- `scripts/run_factor_factory_queue.py`

## Runtime Mapping (Current)
- `configs/research/factor_factory_policy_batchA100_logic100_formal_v1.json`
- `docs/production_research/BATCHA100_LOGIC100_IMPLEMENTATION_MAP_2026-02-28.csv`
