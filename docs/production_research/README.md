# Production Research Governance Docs

Last updated: 2026-03-09 (hard-rule baseline sync)

## Canonical Set (Minimal)
- `../../STATUS.md` (project-level status SSOT)
- `BATCHA100_FINAL_RESULT_STATUS_2026-03-07.md` (row-level final status SSOT)
- `BATCHA100_ROUND2_HOLD_ROBUSTNESS_2026-03-07.md` (shortlist 1/3/5 robustness summary)
- `FACTOR_BATCH_MASTER_TABLE.csv` (row-level query source)
- `FACTOR_ENGINE_SNAPSHOT_2026-03-07.md` (frozen code snapshot reference)
- `FACTOR_PIPELINE_FREEZE_2026-02-25.md` (pipeline boundary)
- `../../SINGLE_FACTOR_BASELINE.md` (single-factor hard-rule baseline)
- `FACTOR_FACTORY_STANDARD.md` (execution/governance standard)
- `OPS_PLAYBOOK.md` (ops procedures)
- `FMP_CALLABLE_DATA_REFERENCE_2026-03-07.md` (FMP callable data single-file reference)
- `../../agent/docs/AGENT_INTEGRATION_READINESS_2026-03-10.md` (agent integration boundary and readiness audit)
- `../../agent/docs/AGENT_GATEWAY_INTEGRATION_2026-03-10.md` (external agent safe integration quickstart)

## Operating Constraint
- Any new run launch requires manual approval:
  - `configs/research/factory_queue/run_approval.json`

## Cleanup Policy
- Keep only docs with explicit active use in current workflow.
- Remove outdated/unused docs instead of keeping passive archive copies.
