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

What this does:
1. detect remote `run_dir` by `decision_tag`
2. detect latest remote `production_gates_report.json`
3. rsync remote gate folder + run audit folder to local
4. run local finalization (`scripts/finalize_gate_run.sh`) to update:
   - `docs/production_research/STAGE_AUDIT_LOG.md`
   - `production_gates_final_summary.md`
5. run local governance completeness check (`scripts/governance_audit_checker.py`)
6. generate remediation plan (`scripts/governance_remediation_plan.py`)
7. generate standardized run review (`scripts/generate_run_review.py`)

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
7. if needed, commit governance/docs updates and push.

## Notes

- This flow is non-destructive; it does not delete remote/local artifacts.
- Cleanup should follow `ARTIFACT_RETENTION_AND_CLEANUP.md` after decision closure.
