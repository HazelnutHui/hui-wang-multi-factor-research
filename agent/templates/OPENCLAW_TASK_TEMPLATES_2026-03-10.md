# OpenClaw Task Templates (V4)

Last updated: 2026-03-10

Use these templates directly in OpenClaw chat.  
All execution must go through `agent/scripts/agent_gateway.py`.

## Template A: Data/Run Health Check
```text
You are operating in /Users/hui/quant_score/v4.
Goal: perform a safe pre-run health check.
Constraints:
1) Only use agent/scripts/agent_gateway.py.
2) First run mode=plan.
3) No execute.
4) Summarize expected command and audit output path.
Workflow:
- workflow=train_test
- args: --strategy configs/strategies/combo_v2_prod.yaml
Output:
- planned command
- latest audit folder
- pass/fail checklist
```

## Template B: Single Execution Window
```text
You are operating in /Users/hui/quant_score/v4.
Goal: run one approved execution and close the gate afterwards.
Constraints:
1) Use agent/scripts/approval_gate.py to open/close approval.
2) Use agent/scripts/agent_gateway.py for plan then execute.
3) approval_id must match exactly.
4) Summarize exit code and audit files.
Workflow:
- workflow=train_test
- args: --strategy configs/strategies/combo_v2_prod.yaml
Output:
- approval_id used
- execute exit code
- audit folder path
- gate status after close
```

## Template C: WF Batch Progress Tracking
```text
You are operating in /Users/hui/quant_score/v4.
Goal: track walk-forward batch progress and generate concise status.
Constraints:
1) Do not modify factor logic.
2) Do not run raw scripts; use agent gateway only.
3) Report started/ended/running/failures/remaining.
Workflow:
- workflow=walk_forward
- args: strategy/factor set as provided by operator
Output:
- progress table
- failed task list (if any)
- next action recommendation
```

## Template D: Post-run Summary for Research Decisions
```text
You are operating in /Users/hui/quant_score/v4.
Goal: summarize completed results for human decision making.
Constraints:
1) No new execute jobs.
2) Read existing outputs and audit logs only.
3) Focus on IC ranking, coverage, stability, and anomalies.
Output:
- top factors by IC
- negative/unstable candidates
- duplicate-signal suspects
- shortlist for next portfolio research step
```
