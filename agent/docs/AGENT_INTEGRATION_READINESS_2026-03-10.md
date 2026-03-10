# Agent Integration Readiness (V4)

Last updated: 2026-03-10

## Scope
- Audit whether V4 can safely connect to OpenClaw-like agents.
- Focus on execution boundary, approval gate, audit trail, and workflow consistency.

## Conclusion
- V4 is architecturally ready for agent integration.
- Do not use direct unrestricted agent execution.
- Use a controlled gateway model: allowlist tools + approval gate + immutable audit logs.

## What Is Already Strong
1. Unified workflow dispatch exists:
   - `scripts/run_research_workflow.py`
2. Official workstation wrapper with audit output exists:
   - `scripts/workstation_official_run.sh`
   - writes `audit/workstation_runs/<ts>_<workflow>_<tag>/...`
3. Queue approval gate exists for factor-factory queue:
   - `configs/research/factory_queue/run_approval.json`
   - enforced by `scripts/run_factor_factory_queue.py`
4. SSOT and governance docs are clear:
   - `STATUS.md`
   - `SINGLE_FACTOR_BASELINE.md`
   - `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md`

## Critical Findings (Must Address Before Agent Autonomy)
1. Approval bypass path exists:
   - `scripts/run_factor_factory_batch.py` can run directly without queue approval.
   - This is acceptable for manual local research, but unsafe for autonomous agent execution.
2. Workflow dispatch itself has no policy gate:
   - `scripts/run_research_workflow.py` forwards args directly.
   - Agent can pass sensitive flags unless restricted at gateway level.
3. Walk-forward implementation scope mismatch:
   - `scripts/run_walk_forward.py` supports built-in factor presets; custom logic100-style factor names are not first-class inputs.
   - Current custom-factor WF requires orchestrated `run_with_config` rolling windows.
4. Destructive maintenance scripts are callable:
   - e.g. cleanup utilities with apply mode.
   - Must be excluded from agent allowlist.

## Required Agent Boundary (Minimal Professional Standard)
1. Command allowlist only:
   - allow:
     - `scripts/run_with_config.py`
     - `scripts/run_segmented_factors.py`
     - `scripts/run_production_gates.py`
     - `scripts/run_walk_forward.py` (only for supported built-in factors)
     - `scripts/run_factor_factory_queue.py` (not direct batch)
   - deny by default all other scripts.
2. Approval gate required for execution mode:
   - for queue/factory jobs, require `run_approval.json` approved+matched.
3. Two-stage operation:
   - `plan` mode: generate commands only.
   - `execute` mode: requires explicit approval token.
4. Immutable run audit:
   - every execution writes:
     - command
     - resolved parameters
     - git commit
     - start/end time
     - exit code
     - artifact paths
5. Canonical write policy:
   - only approved result paths can be promoted to SSOT docs.

## Recommended Next Step (Implementation)
1. Add `agent/scripts/agent_gateway.py` with:
   - strict allowlist
   - parameter schema validation
   - approval enforcement hooks
   - run audit record output
2. Add `agent/configs/agent_policy.json`:
   - allowed workflows
   - blocked flags (`--skip-guardrails`, destructive apply flags) for execute mode
3. Keep agent as execution assistant, not decision authority:
   - factor admission and promotion remain human-approved.

## Notes On Current WF17 Run
- Full 17-factor WF is currently running through controlled rolling `run_with_config` orchestration on workstation.
- This is valid operationally, but should be productized into a first-class script for repeatability.
