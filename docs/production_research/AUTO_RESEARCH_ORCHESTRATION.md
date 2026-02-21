# Auto Research Orchestration Standard

Last updated: 2026-02-21

Purpose:
- run continuous multi-round research loops from existing governance artifacts;
- enforce execution budget and validation gates before any official run command;
- keep full audit trail for each orchestration cycle.

## Components

- `scripts/auto_research_orchestrator.py`
- `configs/research/auto_research_policy.json`

## Loop Sequence (Per Round)

1. generate candidate queue
   - `scripts/generate_candidate_queue.py`
2. generate next-run plan
   - `scripts/generate_next_run_plan.py`
3. repair plan paths and normalize tags
   - `scripts/repair_next_run_plan_paths.py`
4. validate selected command in dry-run mode
   - `scripts/execute_next_run_plan.py --dry-run`
5. optional real execution (if enabled and within budget)
   - `scripts/execute_next_run_plan.py`

## Safety Defaults

Default policy is safe mode:
1. `execute_enabled=false`
2. hard pre-execution validation required
3. stop on validation failure
4. stop on empty plan

## Standard Usage

Safe audit run (no execution):
```bash
python scripts/auto_research_orchestrator.py
```

Note:
- default policy uses placeholder `dq_input_csv=data/your_input.csv`;
- if not changed to an existing path, validation stage will stop with `validation_failed`.

Controlled execution mode:
```bash
python scripts/auto_research_orchestrator.py --execute --max-rounds 2 --max-executions 1
```

## Audit Outputs

Per orchestrator run:
- `audit/auto_research/<timestamp>_orchestrator/auto_research_orchestrator_report.json`
- `audit/auto_research/<timestamp>_orchestrator/auto_research_orchestrator_report.md`

Each round includes:
1. return code and logs for queue/plan/repair/validate/execute
2. selected factor and decision tag
3. explicit stop reason for deterministic traceability

## Policy Keys (Current)

- `max_rounds`
- `max_executions`
- `execute_rank`
- `execute_enabled`
- `stop_on_validation_failure`
- `stop_on_empty_plan`
- `sleep_seconds_between_rounds`
- `dq_input_csv`
- `candidate_queue.*`
- `next_run_plan.*`

## Operational Rules

1. For unattended mode, use explicit budget (`max_rounds`, `max_executions`).
2. Keep `execute_enabled=false` unless current dataset/freeze path are verified.
3. Treat non-zero orchestrator exit as governance event; inspect round-level logs in report json.
