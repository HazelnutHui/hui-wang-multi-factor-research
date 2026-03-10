# OpenClaw Factor Research Playbook (V4)

Last updated: 2026-03-10

## Positioning
- OpenClaw: workflow runner + monitoring + reporting.
- Human researcher: factor logic decisions and portfolio decisions.
- Codex: code changes and repository maintenance when needed.

## Do We Need OpenClaw <-> Codex Direct Integration?
- No hard dependency.
- Recommended: keep them decoupled.
  - OpenClaw executes governed workflows through `agent_gateway.py`.
  - Codex edits code/docs and fixes pipeline issues.
- This separation reduces operational risk and keeps audit trails clean.

## Standard Operating Model
1. OpenClaw first runs `plan`.
2. Human checks plan + scope.
3. Open approval gate for a single execution window.
4. OpenClaw runs `execute`.
5. Close approval gate immediately.
6. Review `audit/agent_gateway/*` output and research results.

## Allowed Entrypoint
- `python3 agent/scripts/agent_gateway.py ...`

## Forbidden Pattern
- Direct calls to:
  - `scripts/run_with_config.py`
  - `scripts/run_segmented_factors.py`
  - `scripts/run_walk_forward.py`
  - `scripts/run_production_gates.py`
  - `scripts/run_statistical_gates.py`

## Minimum Acceptance Checks per Run
- Audit folder created with `request.json` and `result.json`.
- `blocked_flag_hits` is empty.
- Workflow name is in allowed list.
- Execute run has matched `approval_id`.

## Suggested Task Order for Your Current Stage
1. `train_test` on selected factors.
2. `walk_forward` on the screened set.
3. `production_gates`.
4. `statistical_gates`.
5. Consolidate ranking and eliminate unstable/negative factors.
