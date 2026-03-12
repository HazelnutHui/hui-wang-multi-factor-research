# Session Continuity Protocol

Last updated: 2026-03-11 (WF17 completion synced)

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
10. `SINGLE_FACTOR_BASELINE.md`
11. `docs/production_research/WF17_SINGLE_FACTOR_GRADE_2026-03-11.md`

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
7. Confirm hard-rule baseline is active:
   - `SINGLE_FACTOR_BASELINE.md` includes Hard Rules v1.0
   - pipeline freeze doc includes matching locked admission policy
8. Confirm WF17 status is synchronized:
   - `runs/sf_l3_wf_17_20260309_212116` is completed (`221/221`, `fail=0`)
   - provisional grading reference: `docs/production_research/WF17_SINGLE_FACTOR_GRADE_2026-03-11.md`

## Runtime First Commands (Workstation)
```bash
cd ~/projects/hui-wang-multi-factor-research
pgrep -af "run_factor_factory_batch.py|run_segmented_factors.py" || true
ls -1 segment_results/factor_factory 2>/dev/null
ls -1 audit/factor_factory 2>/dev/null
```

## Workstation Topology (Locked)
- Runtime repo (active jobs, data, caches):
  - `~/projects/hui-wang-multi-factor-research`
- Clean sync repo (git mirror only):
  - `~/projects/v4_clean`
- Rule:
  - do not run risky sync operations in runtime repo when active runs exist.
