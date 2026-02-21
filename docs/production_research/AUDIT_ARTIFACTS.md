# Audit Artifacts Specification

Last updated: 2026-02-20

This file defines mandatory artifact classes for production-grade auditability.

## 1) Run identity

Required:
- freeze file
- run manifest(s)
- strategy/protocol references

Examples:
- `runs/freeze/*.freeze.json`
- `strategies/<strategy>/runs/*.manifest.json`
- `<segment_or_wf_out>/run_manifest.json`

## 2) Execution outputs

Required:
- core result csv/json from runner
- latest snapshots where applicable

Examples:
- `strategies/<strategy>/runs/*.json`
- `segment_results/<run_id>/all_factors_summary.csv`
- `walk_forward_results/<run_id>/all_factors_walk_forward.csv`

## 3) Universe tradability audits

Required:
- universe filter audit files per run family

Examples:
- `strategies/<strategy>/results/*_universe_audit_*.csv`
- `segment_results/<run_id>/<factor>/universe_filter_audit.csv`
- `walk_forward_results/<run_id>/<factor>/universe_filter_audit.csv`

## 4) Production gate decisions

Required:
- gate report json/md
- cost stress table
- registry append row
- data quality report json/md (official runs)

Examples:
- `gate_results/production_gates_<ts>/production_gates_report.json`
- `gate_results/production_gates_<ts>/production_gates_report.md`
- `gate_results/production_gates_<ts>/cost_stress_results.csv`
- `gate_results/gate_registry.csv`
- `audit/workstation_runs/<ts>_production_gates_<tag>/data_quality/data_quality_<ts>/data_quality_report.json`
- `audit/workstation_runs/<ts>_production_gates_<tag>/data_quality/data_quality_<ts>/data_quality_report.md`

## 5) Diagnostics + statistical controls

Required:
- risk diagnostics json
- statistical gates table/report

Examples:
- `strategies/<strategy>/reports/diagnostics_*.json`
- `gate_results/production_gates_<ts>/statistical/*/statistical_gates_table.csv`
- `gate_results/production_gates_<ts>/statistical/*/statistical_gates_report.json`

## 6) Retention policy (recommended)

1. Keep all official gate report folders permanently.
2. Keep gate registry append-only; never rewrite old decision rows.
3. Keep freeze files versioned and human-labeled by strategy and date.

## 7) Post-run governance completeness

Required after official sync/finalization:
- governance completeness report json/md
- remediation plan json/md
- standardized run review markdown
- factor experiment registry row + leaderboard refresh
- factor candidate queue refresh
- handoff readiness report json/md (for session continuity)

Examples:
- `audit/workstation_runs/<ts>_production_gates_<tag>/governance_audit_check.json`
- `audit/workstation_runs/<ts>_production_gates_<tag>/governance_audit_check.md`
- `audit/workstation_runs/<ts>_production_gates_<tag>/governance_remediation_plan.json`
- `audit/workstation_runs/<ts>_production_gates_<tag>/governance_remediation_plan.md`
- `gate_results/production_gates_<ts>/production_gates_run_review.md`
- `audit/factor_registry/factor_experiment_registry.csv`
- `audit/factor_registry/factor_experiment_leaderboard.md`
- `audit/factor_registry/factor_candidate_queue.csv`
- `audit/factor_registry/factor_candidate_queue.md`
- `audit/session_handoff/handoff_readiness.json`
- `audit/session_handoff/handoff_readiness.md`

## 8) Auto research orchestration

Required when automated multi-round orchestration is used:
- orchestrator report json/md per cycle
- policy config snapshot reference in report metadata

Examples:
- `audit/auto_research/<ts>_orchestrator/auto_research_orchestrator_report.json`
- `audit/auto_research/<ts>_orchestrator/auto_research_orchestrator_report.md`
- `configs/research/auto_research_policy.json`
