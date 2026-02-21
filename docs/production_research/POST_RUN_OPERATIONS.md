# Post-Run Operations (Sync + Finalize)

Last updated: 2026-02-21

Purpose:
- standardize what to do immediately after an official workstation run finishes;
- avoid manual path mistakes when syncing artifacts and updating stage ledger.

## Preconditions

1. Official run has ended (`result.json` exists in run dir).
2. `production_gates_report.json` exists under the target gate folder.
3. No active process is writing into that gate folder.

## One-command flow (local machine)

```bash
cd /Users/hui/quant_score/v4
bash scripts/post_run_sync_and_finalize.sh --tag committee_YYYY-MM-DD_runN
```

## Wait-then-finalize flow (recommended while run is still active)

```bash
cd /Users/hui/quant_score/v4
bash scripts/monitor_then_finalize.sh --tag committee_YYYY-MM-DD_runN --interval 30
```

What this does:
1. monitor remote `run_dir` and `run.log`
2. wait for `result.json` existence
3. verify no active WF process remains
4. auto-call `scripts/post_run_sync_and_finalize.sh`

Post-run sync/finalize actions:
1. detect remote `run_dir` by `decision_tag`
2. detect latest remote `production_gates_report.json`
3. rsync remote gate folder + run audit folder to local
4. run local finalization (`scripts/finalize_gate_run.sh`) to update:
   - `docs/production_research/STAGE_AUDIT_LOG.md`
   - `production_gates_final_summary.md`
5. run local governance completeness check (`scripts/governance_audit_checker.py`)
6. generate remediation plan (`scripts/governance_remediation_plan.py`)
7. generate standardized run review (`scripts/generate_run_review.py`)
8. update factor experiment registry (`scripts/update_factor_experiment_registry.py`)
9. refresh factor candidate queue (`scripts/generate_candidate_queue.py`)
10. generate next-run execution plan (`scripts/generate_next_run_plan.py`)
11. update failure pattern database (`scripts/update_failure_pattern_db.py`)
12. generate session handoff readiness audit (`scripts/check_session_handoff_readiness.py`)

## Explicit-path mode

```bash
bash scripts/post_run_sync_and_finalize.sh \
  --run-dir-remote audit/workstation_runs/<ts>_production_gates_<decision_tag> \
  --report-json-remote gate_results/production_gates_<ts>/production_gates_report.json \
  --tag committee_YYYY-MM-DD_runN
```

## Validation checklist

1. local report exists:
- `gate_results/production_gates_<ts>/production_gates_report.json`
2. local final summary exists:
- `gate_results/production_gates_<ts>/production_gates_final_summary.md`
3. stage ledger has final row (pass/fail, not in_progress):
- `docs/production_research/STAGE_AUDIT_LOG.md`
4. governance check outputs exist and pass:
- `audit/workstation_runs/<...>/governance_audit_check.json`
- `audit/workstation_runs/<...>/governance_audit_check.md`
5. remediation plan exists (especially if check failed):
- `audit/workstation_runs/<...>/governance_remediation_plan.json`
- `audit/workstation_runs/<...>/governance_remediation_plan.md`
6. run review markdown exists:
- `gate_results/production_gates_<ts>/production_gates_run_review.md`
7. factor registry artifacts updated:
- `audit/factor_registry/factor_experiment_registry.csv`
- `audit/factor_registry/factor_experiment_leaderboard.md`
8. candidate queue artifacts updated:
- `audit/factor_registry/factor_candidate_queue.csv`
- `audit/factor_registry/factor_candidate_queue.md`
9. next-run plan artifacts updated:
- `audit/factor_registry/next_run_plan.json`
- `audit/factor_registry/next_run_plan.md`
10. failure pattern artifacts updated:
- `audit/failure_patterns/failure_patterns.csv`
- `audit/failure_patterns/failure_pattern_summary.md`
11. handoff readiness artifacts updated:
- `audit/session_handoff/handoff_readiness.json`
- `audit/session_handoff/handoff_readiness.md`
12. if needed, commit governance/docs updates and push.

## Notes

- This flow is non-destructive; it does not delete remote/local artifacts.
- Cleanup should follow `ARTIFACT_RETENTION_AND_CLEANUP.md` after decision closure.
