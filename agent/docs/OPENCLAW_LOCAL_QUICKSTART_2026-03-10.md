# OpenClaw Local Quickstart (V4)

Last updated: 2026-03-10

## 1) Preconditions
- OpenClaw gateway is running on local loopback:
  - `http://127.0.0.1:18789/`
- V4 gateway exists:
  - `agent/scripts/agent_gateway.py`

## 2) Health Check
```bash
openclaw gateway status
cd /Users/hui/quant_score/v4
python3 agent/scripts/agent_gateway.py \
  --mode plan \
  --workflow train_test \
  -- --strategy configs/strategies/combo_v2_prod.yaml
```

## 3) Approval Gate (safe default)
Approval file:
- `configs/research/factory_queue/run_approval.json`
- Helper script:
  - `agent/scripts/approval_gate.py`

Recommended default (idle state):
```json
{
  "approved": false,
  "approval_id": ""
}
```

Only enable for a single execution window, then close it again.

Approval helper supports:
- `status`: read current gate state
- `open`: open one execution window and write `approval_id`
- `close`: close gate and clear approval fields

## 4) Execute Example
```bash
cd /Users/hui/quant_score/v4
python3 agent/scripts/agent_gateway.py \
  --mode execute \
  --approval-id 2026-03-10-agent-001 \
  --workflow train_test \
  -- --strategy configs/strategies/combo_v2_prod.yaml
```

## 5) Audit Output
- `audit/agent_gateway/<timestamp>_<workflow>_<mode>/request.json`
- `audit/agent_gateway/<timestamp>_<workflow>_<mode>/command.sh`
- `audit/agent_gateway/<timestamp>_<workflow>_<mode>/result.json`

## 6) OpenClaw Tool Boundary
Use only:
- `python3 agent/scripts/agent_gateway.py ...`

Do not expose direct workflow scripts to the agent.

## 7) Security Note
If your OpenClaw token has been exposed in terminal/chat history, rotate it before production use.
