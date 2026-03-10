# OpenClaw V4 Agent Setup (Completed)

Last updated: 2026-03-10

## What Was Configured
1. Added dedicated OpenClaw agent:
   - `agent id`: `v4`
   - model: `openai/gpt-5`
2. Added dedicated workspace:
   - `/Users/hui/quant_score/v4/agent/openclaw_v4_workspace`
3. Added V4-specific instruction pack:
   - `AGENTS.md`
   - `USER.md`
   - `V4_CONTEXT.md`

## Why Dedicated Agent
- Avoid mixing generic personal assistant context with quant-research governance.
- Keep v4 execution boundaries strict and reproducible.
- Make startup behavior deterministic (SSOT read order + hard boundaries).

## Runtime Boundary
- Entrypoint:
  - `agent/scripts/agent_gateway.py`
- Approval:
  - `configs/research/factory_queue/run_approval.json`
- Audit:
  - `audit/agent_gateway/`

## Verification Notes
- Agent creation and model binding are successful.
- Local CLI runtime probe had intermittent model timeout; this is transport/runtime quality, not policy/workspace config failure.
- If web dashboard is responsive, use the `v4` agent profile/session for normal operation.
