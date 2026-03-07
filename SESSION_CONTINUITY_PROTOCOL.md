# Session Continuity Protocol

Last updated: 2026-03-07 (logic100 final consolidated baseline)

## Session Contract
1. Start from reset declaration and master table.
2. Treat `batchA100_logic100_formal_v1` as first official batch.
3. Do not run any batch before manual approval.
4. Keep docs synchronized with real runtime state.
5. Current active reference is the single final consolidated logic100 output.

## Mandatory Read Order
1. `README.md`
2. `STATUS.md`
3. `RUNBOOK.md`
4. `DOCS_INDEX.md`
5. `docs/production_research/BATCHA100_FINAL_RESULT_STATUS_2026-03-07.md`
6. `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
7. `docs/production_research/FACTOR_ENGINE_SNAPSHOT_2026-03-07.md`
8. `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md`
9. `docs/production_research/FACTOR_FACTORY_STANDARD.md`

## Completion Checks
1. Confirm canonical final output path exists and is complete (100 factors with summaries).
2. Confirm formal batch id is `batchA100_logic100_formal_v1`.
3. Confirm master table matches formal logic100 SSOT and implementation map.
4. Confirm run approval file path: `configs/research/factory_queue/run_approval.json`.
5. Confirm row-level 100-factor status from:
   - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
   - `docs/production_research/BATCHA100_FINAL_RESULT_STATUS_2026-03-07.md`
6. Confirm SSOT rule:
   - only `STATUS.md` stores project-level runtime snapshot
   - only `BATCHA100_FINAL_RESULT_STATUS_2026-03-07.md` stores row-level final status snapshot

## Runtime First Commands (Workstation)
```bash
cd ~/projects/hui-wang-multi-factor-research
pgrep -af "run_factor_factory_batch.py|run_segmented_factors.py" || true
ls -1 segment_results/factor_factory 2>/dev/null
ls -1 audit/factor_factory 2>/dev/null
```
