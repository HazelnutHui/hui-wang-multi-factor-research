# Next Run Execution Standard

Last updated: 2026-02-21

Purpose:
- turn `next_run_plan` into a safe, executable official run command;
- enforce deterministic tag naming and preflight validation;
- keep full audit trace from plan to execution.

## Standard Sequence

1. Generate candidate queue:
```bash
python scripts/generate_candidate_queue.py
```
2. Generate next-run plan:
```bash
python scripts/generate_next_run_plan.py --dq-input-csv data/your_input.csv
```
3. Repair command paths and normalize tags:
```bash
python scripts/repair_next_run_plan_paths.py \
  --plan-json audit/factor_registry/next_run_plan.json \
  --out-json audit/factor_registry/next_run_plan_fixed.json \
  --out-md audit/factor_registry/next_run_plan_fixed.md \
  --dq-input-csv data/your_input.csv
```
4. Validate command only (no execution):
```bash
python scripts/execute_next_run_plan.py \
  --plan-json audit/factor_registry/next_run_plan_fixed.json \
  --rank 1 \
  --dry-run
```
5. Execute selected command:
```bash
python scripts/execute_next_run_plan.py \
  --plan-json audit/factor_registry/next_run_plan_fixed.json \
  --rank 1
```

## Tag Naming Policy

When `scripts/repair_next_run_plan_paths.py` runs with default settings:
- decision tags are normalized to `committee_YYYY-MM-DD_runN`;
- `runN` auto-increments to avoid collisions with:
  - existing `audit/workstation_runs/*` directories;
  - tags already assigned in the same fixed plan.

## Validation Gates Before Execute

`scripts/execute_next_run_plan.py` enforces:
1. command uses `scripts/workstation_official_run.sh`
2. workflow is `--workflow production_gates`
3. `--tag` is new (no collision)
4. `--freeze-file` exists
5. `--dq-input-csv` is non-placeholder and path exists

## Audit Artifacts

After step 3-5, retain:
- `audit/factor_registry/next_run_plan.json`
- `audit/factor_registry/next_run_plan.md`
- `audit/factor_registry/next_run_plan_fixed.json`
- `audit/factor_registry/next_run_plan_fixed.md`

These artifacts are the execution intent trail and must be kept with run-level governance outputs.
