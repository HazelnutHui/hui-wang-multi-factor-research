# Session Continuity Protocol

Last updated: 2026-02-27 (reset mode; no formal historical result retained)

## Session Contract
1. Start from reset declaration and master table.
2. Treat `batchA100_logic100_v1` as first official batch.
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
1. Confirm there is no active batch process.
2. Confirm current batch id is `batchA100_logic100_v1`.
3. Confirm master table has only current post-reset candidates.
4. Confirm run approval file path: `configs/research/factory_queue/run_approval.json`.

## Runtime First Commands (Workstation)
```bash
cd ~/projects/hui-wang-multi-factor-research
pgrep -af "run_factor_factory_batch.py|run_segmented_factors.py" || true
ls -1 segment_results/factor_factory 2>/dev/null
ls -1 audit/factor_factory 2>/dev/null
```
