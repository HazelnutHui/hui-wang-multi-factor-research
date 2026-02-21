# Workstation Runner Spec

Last updated: 2026-02-21

## Purpose

Standardize heavy-run execution on workstation with auditable wrapper scripts.

## Scripts

1. `scripts/workstation_preflight.sh`
- checks CPU cores and memory against minimum thresholds;
- captures git branch/commit/dirty status;
- outputs JSON for audit.

2. `scripts/workstation_official_run.sh`
- wraps `scripts/run_research_workflow.py`;
- enforces preflight before execution;
- stores command/context/log/result under:
  - `audit/workstation_runs/<ts>_<workflow>_<decision_tag>/`

## Required Invocation Pattern

```bash
bash scripts/workstation_official_run.sh \
  --workflow production_gates \
  --tag committee_YYYY-MM-DD_xxx \
  --owner hui \
  --notes "official workstation run" \
  -- \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --factor combo_v2 \
  --freeze-file runs/freeze/combo_v2_prod.freeze.json \
  --out-dir gate_results
```

## Produced Audit Files

- `preflight.json`
- `context.json`
- `command.sh`
- `run.log`
- `result.json`

## Governance Notes

- Use `--require-clean` when committee requires clean working tree enforcement.
- Preflight default minimums:
  - cores >= 8
  - memory >= 60GB
- Any preflight failure blocks official execution.
