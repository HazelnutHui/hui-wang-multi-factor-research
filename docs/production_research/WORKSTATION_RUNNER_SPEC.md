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
- enforces data quality gate before `production_gates` execution (unless explicitly skipped with audit trace);
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
  --dq-input-csv data/your_input.csv \
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
- `data_quality_command.sh` (if DQ executed)
- `data_quality.log` (if DQ executed)
- `context.json`
- `command.sh`
- `run.log`
- `result.json`

## Monitoring / Finalization

Live monitor (non-destructive):

```bash
bash scripts/monitor_gate_run.sh --tag committee_YYYY-MM-DD_runN --host hui@100.66.103.44 --interval 30
```

Monitor-until-complete then auto-finalize:

```bash
bash scripts/monitor_then_finalize.sh --tag committee_YYYY-MM-DD_runN --interval 30
```

Post-run ledger finalization:

```bash
bash scripts/finalize_gate_run.sh --tag committee_YYYY-MM-DD_runN
```

Post-run sync + finalization (recommended local command):

```bash
bash scripts/post_run_sync_and_finalize.sh --tag committee_YYYY-MM-DD_runN
```

Governance completeness check (auto-invoked by post-run sync script):

```bash
python scripts/governance_audit_checker.py \
  --run-dir audit/workstation_runs/<...> \
  --report-json gate_results/production_gates_<ts>/production_gates_report.json \
  --require-final-summary
```

Remediation plan (auto-invoked after governance check):

```bash
python scripts/governance_remediation_plan.py \
  --audit-json audit/workstation_runs/<...>/governance_audit_check.json
```

Run review generation (auto-invoked in post-run sync flow):

```bash
python scripts/generate_run_review.py \
  --run-dir audit/workstation_runs/<...> \
  --report-json gate_results/production_gates_<ts>/production_gates_report.json
```

Factor registry update (auto-invoked in post-run sync flow):

```bash
python scripts/update_factor_experiment_registry.py \
  --report-json gate_results/production_gates_<ts>/production_gates_report.json \
  --run-dir audit/workstation_runs/<...>
```

Candidate queue refresh (auto-invoked in post-run sync flow):

```bash
python scripts/generate_candidate_queue.py
```

## Governance Notes

- Use `--require-clean` when committee requires clean working tree enforcement.
- Use `--threads` to set BLAS/OpenMP thread env vars for heavy workloads.
- Use `--wf-shards` to run walk-forward stress in parallel shards by test-year buckets.
- Preflight default minimums:
  - cores >= 8
  - memory >= 60GB
- Any preflight failure blocks official execution.
- Any data quality gate failure blocks official execution.
