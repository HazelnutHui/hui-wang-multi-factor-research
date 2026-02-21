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

## Core scripts

- `scripts/run_research_workflow.py`
- `scripts/run_with_config.py`
- `scripts/run_segmented_factors.py`
- `scripts/run_walk_forward.py`
- `scripts/run_production_gates.py`
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
