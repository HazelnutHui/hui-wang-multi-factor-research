# Failure Pattern DB Standard

Last updated: 2026-02-21

This standard defines how governance failures are accumulated into a searchable failure-pattern dataset.

## Script

- `scripts/update_failure_pattern_db.py`

## Inputs

1. `governance_remediation_plan.json`
2. `governance_audit_check.json`

## Outputs

- `audit/failure_patterns/failure_patterns.csv`
- `audit/failure_patterns/failure_pattern_summary.md`

## Record Fields

- `decision_tag`
- `run_dir`
- `severity`
- `domain`
- `failure`
- `action`
- `pattern_key`

## Update Policy

1. append/update by `pattern_key` (`decision_tag|domain|failure`)
2. never delete historical failure patterns
3. maintain human-readable summary for quick trend review

## Standard Usage

```bash
python scripts/update_failure_pattern_db.py \
  --remediation-json audit/workstation_runs/<...>/governance_remediation_plan.json \
  --audit-json audit/workstation_runs/<...>/governance_audit_check.json
```

## Integration

- auto-invoked by `scripts/post_run_sync_and_finalize.sh`
- used by next-run planning to reduce repeated governance/control failures
