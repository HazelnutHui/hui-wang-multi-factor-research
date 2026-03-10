# Agent Gateway Integration (OpenClaw-like)

Last updated: 2026-03-10

## Goal
- Integrate external AI agents (OpenClaw-like) into V4 safely.
- Force all agent execution through `agent/scripts/agent_gateway.py`.

## Required Boundary
1. Agent must NOT call raw workflow scripts directly.
2. Agent must only call:
   - `python3 agent/scripts/agent_gateway.py ...`
3. Use `plan` first, then `execute`.

## Step 1: Policy Check
- Policy file:
  - `agent/configs/agent_policy.json`
- Default protections already enabled:
  - workflow allowlist
  - blocked dangerous flags in execute mode
  - approval required for execute mode
  - audit output enabled

## Step 2: Approval Gate (execute mode)
Edit:
- `configs/research/factory_queue/run_approval.json`

Minimum fields:
```json
{
  "approved": true,
  "approval_id": "2026-03-10-agent-001"
}
```

## Step 3: Plan Mode (Safe)
```bash
cd /Users/hui/quant_score/v4
python3 agent/scripts/agent_gateway.py \
  --mode plan \
  --workflow train_test \
  -- --strategy configs/strategies/combo_v2_prod.yaml
```

## Step 4: Execute Mode (Approved)
```bash
cd /Users/hui/quant_score/v4
python3 agent/scripts/agent_gateway.py \
  --mode execute \
  --approval-id 2026-03-10-agent-001 \
  --workflow train_test \
  -- --strategy configs/strategies/combo_v2_prod.yaml
```

## Audit Path
Each run writes:
- `audit/agent_gateway/<timestamp>_<workflow>_<mode>/request.json`
- `audit/agent_gateway/<timestamp>_<workflow>_<mode>/command.sh`
- `audit/agent_gateway/<timestamp>_<workflow>_<mode>/result.json`

## OpenClaw-like Adapter Rule
When configuring external agent tools, set a single execution command pattern:
- `python3 agent/scripts/agent_gateway.py --mode <plan|execute> ...`

Do not expose:
- `scripts/run_with_config.py`
- `scripts/run_segmented_factors.py`
- `scripts/run_walk_forward.py`
- `scripts/run_production_gates.py`
directly to the external agent.
