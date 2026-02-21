# Governance Remediation Plan Standard

Last updated: 2026-02-21

This standard defines how to convert failed governance audit checks into explicit fix actions.

## Script

- `scripts/governance_remediation_plan.py`

## Input

- `audit/workstation_runs/<...>/governance_audit_check.json`

## Output

- `audit/workstation_runs/<...>/governance_remediation_plan.json`
- `audit/workstation_runs/<...>/governance_remediation_plan.md`

## Behavior

The script reads failed checks and maps them into severity-tagged actions:

1. `High`:
   - data quality failures
   - missing critical artifacts
   - decision tag mismatch
   - non-zero run exit code
2. `Medium`:
   - stage ledger linkage gaps
   - uncategorized issues requiring manual resolution

## Standard Usage

```bash
python scripts/governance_remediation_plan.py \
  --audit-json audit/workstation_runs/<ts>_production_gates_<decision_tag>/governance_audit_check.json
```

## Integration

- `scripts/post_run_sync_and_finalize.sh` now runs this automatically after governance audit check.
- If governance audit fails, remediation plan is still generated before the script exits non-zero.
