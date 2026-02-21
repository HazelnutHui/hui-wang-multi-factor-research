# Governance Audit Checker

Last updated: 2026-02-21

This document defines the post-run governance completeness check for official production gate runs.

## Purpose

Validate that one run has a complete, traceable artifact chain after sync/finalization.

## Script

- `scripts/governance_audit_checker.py`

## Required Inputs

1. `--run-dir audit/workstation_runs/<...>`
2. `--report-json gate_results/production_gates_<ts>/production_gates_report.json`
3. optional `--stage-log` (default `docs/production_research/STAGE_AUDIT_LOG.md`)
4. optional `--require-final-summary` to enforce `production_gates_final_summary.md`

## Checks Performed

1. required run artifacts exist:
   - `preflight.json`
   - `context.json`
   - `command.sh`
   - `run.log`
   - `result.json`
2. report artifacts exist:
   - `production_gates_report.json`
   - `production_gates_report.md`
3. run success:
   - `result.json.exit_code == 0`
4. decision consistency:
   - `context.json.decision_tag == report.inputs.decision_tag`
5. data quality control:
   - `skip_data_quality_check == false`
   - `data_quality_report_json` exists and `overall_pass == true`
6. stage ledger linkage:
   - decision tag appears in `STAGE_AUDIT_LOG.md`

## Outputs

Written to run dir:

- `governance_audit_check.json`
- `governance_audit_check.md`

Exit code:

- `0` when all checks pass
- `2` when any check fails

## Standard Usage

```bash
python scripts/governance_audit_checker.py \
  --run-dir audit/workstation_runs/<ts>_production_gates_<decision_tag> \
  --report-json gate_results/production_gates_<ts>/production_gates_report.json \
  --require-final-summary
```

## Integration

- Included in `scripts/post_run_sync_and_finalize.sh` after finalization.
- Serves as a final quality gate for audit completeness before governance commit/push.
