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

Examples:
- `gate_results/production_gates_<ts>/production_gates_report.json`
- `gate_results/production_gates_<ts>/production_gates_report.md`
- `gate_results/production_gates_<ts>/cost_stress_results.csv`
- `gate_results/gate_registry.csv`

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
