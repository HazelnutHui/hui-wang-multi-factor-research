# Session Continuity Protocol

Last updated: 2026-02-28 (formal logic100 runtime sync)

## Session Contract
1. Start from reset declaration and master table.
2. Treat `batchA100_logic100_formal_v1` as first official batch.
3. Do not run any batch before manual approval.
4. Keep docs synchronized with real runtime state.

## Mandatory Read Order
1. `README.md`
2. `RUNBOOK.md`
3. `STATUS.md`
4. `DOCS_INDEX.md`
5. `docs/production_research/RESET_STATE_2026-02-27.md`
6. `docs/production_research/FACTOR_BATCH_MASTER_TABLE.md`
7. `docs/production_research/FACTOR_FACTORY_STANDARD.md`
8. `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md`
9. `docs/production_research/BATCHA100_DATA_READINESS_2026-02-27.md`
10. `docs/production_research/OPS_PLAYBOOK.md`

## Completion Checks
1. Confirm current active batch process status on workstation (running/finished).
2. Confirm current batch id is `batchA100_logic100_formal_v1`.
3. Confirm master table matches formal logic100 SSOT and implementation map.
4. Confirm run approval file path: `configs/research/factory_queue/run_approval.json`.
5. Confirm next-batch design status:
   - `docs/production_research/BATCHB100_LOGIC100_DESIGN_V1_2026-03-01.md/.csv` exist,
   - status is `design-only` (not approved, not running).

## Runtime First Commands (Workstation)
```bash
cd ~/projects/hui-wang-multi-factor-research
pgrep -af "run_factor_factory_batch.py|run_segmented_factors.py" || true
ls -1 segment_results/factor_factory 2>/dev/null
ls -1 audit/factor_factory 2>/dev/null
```
