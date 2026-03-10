# AGENTS.md - V4 Quant Research Agent

This workspace is dedicated to `/Users/hui/quant_score/v4` only.

## Session Startup (Required)
Read in this exact order before proposing or executing work:
1. `/Users/hui/quant_score/v4/SESSION_CONTINUITY_PROTOCOL.md`
2. `/Users/hui/quant_score/v4/STATUS.md`
3. `/Users/hui/quant_score/v4/RUNBOOK.md`
4. `/Users/hui/quant_score/v4/SINGLE_FACTOR_BASELINE.md`
5. `/Users/hui/quant_score/v4/docs/production_research/BATCHA100_FINAL_RESULT_STATUS_2026-03-07.md`
6. `/Users/hui/quant_score/v4/docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
7. `/Users/hui/quant_score/v4/agent/openclaw_v4_workspace/V4_CONTEXT.md`

## Scope
- Primary goal: execute and monitor governed factor-research workflows.
- Do not make autonomous investment decisions.
- Keep all status claims consistent with SSOT docs.

## Hard Boundaries
1. Use only governed entrypoint:
   - `python3 agent/scripts/agent_gateway.py ...`
2. Never call raw workflow scripts directly for execution decisions.
3. Always run `--mode plan` first.
4. Only run `--mode execute` when approval gate is open and `approval_id` matches.
5. Do not use skip/bypass flags in execute mode.

## SSOT Rule
- Project-level status: `/Users/hui/quant_score/v4/STATUS.md`
- Row-level final status: `/Users/hui/quant_score/v4/docs/production_research/BATCHA100_FINAL_RESULT_STATUS_2026-03-07.md`

## Reporting Format (Every Run)
Output must include:
1. What was run (workflow + args).
2. Audit path.
3. Exit status.
4. Failures/remaining tasks (if batch).
5. Next action suggestion.

## Safety
- Ask before destructive operations.
- Keep execution evidence in audit artifacts.
- Do not overwrite canonical conclusions with intermediate run outputs.
