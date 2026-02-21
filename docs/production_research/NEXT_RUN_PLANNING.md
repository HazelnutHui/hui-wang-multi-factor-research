# Next Run Planning Standard

Last updated: 2026-02-21

This standard defines how to produce an actionable rerun plan after each official run closure.

## Script

- `scripts/generate_next_run_plan.py`

## Inputs

1. `audit/factor_registry/factor_candidate_queue.csv`
2. latest `governance_remediation_plan.json`
3. latest `production_gates_report.json`

## Outputs

- `audit/factor_registry/next_run_plan.json`
- `audit/factor_registry/next_run_plan.md`

## Content Requirements

1. failed gate list from latest gate report
2. high-severity remediation items
3. explicit rerun hypotheses (domain-linked)
4. ranked execution commands for next official run

## Standard Usage

```bash
python scripts/generate_next_run_plan.py --dq-input-csv data/your_input.csv
```

## Integration

- recommended to run immediately after candidate queue refresh
- output markdown is committee-ready and can be used as next-run command checklist

## Optional One-Click Execution

```bash
python scripts/execute_next_run_plan.py --rank 1 --dry-run
python scripts/execute_next_run_plan.py --rank 1
```
