# Production Research Governance Docs

Last updated: 2026-02-21

This folder documents the production-grade governance layer added on top of V4 research workflows.

## Scope

- governed entrypoint and freeze policy
- PIT/lag guardrails
- universe filter audit outputs
- production hard gates (cost + stress + risk)
- decision registry and audit trail

## Files

- `GATE_SPEC.md`: formal gate definitions, thresholds, pass/fail logic
- `OPS_PLAYBOOK.md`: practical run commands and interpretation flow
- `CHANGELOG.md`: governance-layer change log
- `WORKSTATION_PRIMARY_MODE.md`: workstation-first execution policy
- `SESSION_BOOTSTRAP.md`: mandatory read order for new Codex sessions
- `AUDIT_ARTIFACTS.md`: required artifact classes for audit/compliance
- `CURRENT_GATE_STATUS_2026-02-20.md`: current gate-state snapshot and rerun checklist
- `AUDIT_SNAPSHOT_2026-02-20.md`: path-level audit snapshot for handoff/reference
- `TERMINOLOGY_POLICY.md`: canonical naming policy for production governance terms
- `RENAMING_AUDIT_2026-02-21.md`: full migration audit record for legacy-term cleanup
- `STAGE_EXECUTION_STANDARD.md`: stage-by-stage production research execution standard
- `STAGE_AUDIT_LOG.md`: append-only stage-level audit ledger
- `WORKSTATION_RUNNER_SPEC.md`: wrapper-script specification for workstation official runs
- `ARTIFACT_RETENTION_AND_CLEANUP.md`: retention boundary and safe cleanup policy for audit vs temporary outputs
- `CURRENT_GATE_STATUS_2026-02-21.md`: active rerun status snapshot with verified execution context
- `PERFORMANCE_OPTIMIZATION_BACKLOG_2026-02-21.md`: verified performance bottlenecks and prioritized optimization backlog
- `POST_RUN_OPERATIONS.md`: standardized sync/finalize procedure after official run completion
- `GOVERNANCE_AUDIT_CHECKER.md`: post-run governance completeness checks and pass criteria
- `GOVERNANCE_REMEDIATION_PLAN.md`: failed governance checks to fix-action mapping standard
- `DATA_QUALITY_POLICY.md`: pre-gate data quality hard-check policy and thresholds
- `RISK_REGISTER.md`: active risk inventory with owners, mitigations, and review cadence
- `MODEL_CHANGE_CONTROL.md`: model/factor change classification, evidence requirements, and approvals
- `INCIDENT_RESPONSE.md`: incident level definitions, response SLA, and closure requirements
- `SECURITY_AND_ACCESS_CONTROL.md`: credential, access, and workstation security baseline
- `OFFICIAL_RUN_TEMPLATE.md`: copy-ready official run / monitor / close command templates
- `RUN_REVIEW_TEMPLATE.md`: standardized committee review template after run closure

## Core scripts

- `scripts/run_research_workflow.py`
- `scripts/run_with_config.py`
- `scripts/run_segmented_factors.py`
- `scripts/run_walk_forward.py`
- `scripts/run_production_gates.py`
- `scripts/workstation_preflight.sh`
- `scripts/workstation_official_run.sh`
- `scripts/monitor_gate_run.sh`
- `scripts/monitor_then_finalize.sh`
- `scripts/finalize_gate_run.py`
- `scripts/finalize_gate_run.sh`
- `scripts/post_run_sync_and_finalize.sh`
- `scripts/data_quality_gate.py`
- `scripts/governance_audit_checker.py`
- `scripts/governance_remediation_plan.py`
- `scripts/research_governance.py`

## Related outputs

- Run manifests:
  - `strategies/<strategy>/runs/*.manifest.json`
  - `<segment_or_wf_out>/run_manifest.json`
- Universe audit:
  - `*_universe_audit_*.csv`
  - `<out>/<factor>/universe_filter_audit.csv`
- Gate reports:
  - `gate_results/production_gates_<ts>/production_gates_report.json`
  - `gate_results/production_gates_<ts>/production_gates_report.md`
