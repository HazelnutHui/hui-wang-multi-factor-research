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
  --threads 8 \
  -- \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --factor combo_v2 \
  --cost-multipliers 1.5,2.0 \
  --wf-shards 4 \
  --freeze-file runs/freeze/combo_v2_prod_<date>_g<commit>.freeze.json \
  --out-dir gate_results
```

## Produced Audit Files

- `preflight.json`
- `context.json`
- `command.sh`
- `run.log`
- `result.json`

## Monitoring / Finalization

Live monitor (non-destructive):

```bash
bash scripts/monitor_gate_run.sh --tag committee_YYYY-MM-DD_runN --host hui@100.66.103.44 --interval 30
```

Post-run ledger finalization:

```bash
bash scripts/finalize_gate_run.sh --tag committee_YYYY-MM-DD_runN
```

Post-run sync + finalization (recommended local command):

```bash
bash scripts/post_run_sync_and_finalize.sh --tag committee_YYYY-MM-DD_runN
```

## Governance Notes

- Use `--require-clean` when committee requires clean working tree enforcement.
- Use `--threads` to set BLAS/OpenMP thread env vars for heavy workloads.
- Use `--wf-shards` to run walk-forward stress in parallel shards by test-year buckets.
- Preflight default minimums:
  - cores >= 8
  - memory >= 60GB
- Any preflight failure blocks official execution.
