# Production Research Governance Docs

Last updated: 2026-02-27 (v2 queue still running; factor-factory latest usable set verified as 36 unique candidates)

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
- `COMMAND_SURFACE.md`: primary/internal command boundary and deprecation policy
- `DAILY_DEV_RESEARCH_FLOW.md`: daily dual-track dev/research SOP with anti-loop data-boundary expansion rules
- `CHANGELOG.md`: governance-layer change log
- `WORKSTATION_PRIMARY_MODE.md`: workstation-first execution policy
- `SESSION_BOOTSTRAP.md`: mandatory read order for new sessions
- `AUDIT_ARTIFACTS.md`: required artifact classes for audit/compliance
- `CURRENT_GATE_STATUS_2026-02-20.md`: historical gate-state snapshot and rerun checklist
- `AUDIT_SNAPSHOT_2026-02-20.md`: path-level audit snapshot for handoff/reference
- `TERMINOLOGY_POLICY.md`: canonical naming policy for production governance terms
- `RENAMING_AUDIT_2026-02-21.md`: full migration audit record for legacy-term cleanup
- `STAGE_EXECUTION_STANDARD.md`: stage-by-stage production research execution standard
- `STAGE_AUDIT_LOG.md`: append-only stage-level audit ledger
- `WORKSTATION_RUNNER_SPEC.md`: wrapper-script specification for workstation official runs
- `ARTIFACT_RETENTION_AND_CLEANUP.md`: retention boundary and safe cleanup policy for audit vs temporary outputs
- `CURRENT_GATE_STATUS_2026-02-21.md`: historical rerun status snapshot with verified execution context
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
- `FACTOR_EXPERIMENT_REGISTRY.md`: central experiment registry and scoring/ranking standard
- `CANDIDATE_QUEUE_POLICY.md`: auto-prioritized next-run candidate queue policy
- `NEXT_RUN_PLANNING.md`: generation standard for rerun command/hypothesis plan
- `NEXT_RUN_EXECUTION_STANDARD.md`: standard sequence from next-run plan repair to safe execution
- `AUTO_RESEARCH_ORCHESTRATION.md`: multi-round automated research orchestration standard
- `AUTO_RESEARCH_SEARCH_V1.md`: parameter-search trial planning/execution standard for combo_v2
- `FACTOR_FACTORY_STANDARD.md`: batch new-factor factory standard (candidate build/execute/rank)
- `CONFIG_AUDIT_2026-02-24.md`: consolidated config audit and normalized execution-profile decision
- `FACTOR_PIPELINE_FREEZE_2026-02-25.md`: locked end-to-end factor pipeline and stage terminology
- `FACTOR_FACTORY_QUEUE_SNAPSHOT_2026-02-27.md`: latest factor-factory continuity snapshot (verified complete usable 36-candidate set; incomplete/stale lineages explicitly excluded)
- `FACTOR_FACTORY_QUEUE_SNAPSHOT_2026-02-26.md`: historical continuity snapshot kept for audit trail
- `FMP_NEXT100_DATA_PLAN_2026-02-26.md`: next100 FMP data classification and download/use boundary (core vs research-only vs hold)
- `NEXT100_V3_PLAN_2026-02-26.md`: next100 v3 draft (new-signal-first logic, FMP support matrix, launch de-dup gate, not started while v2 is active)
- `FMP_INTERFACE_PROBE_STANDARD.md`: small-sample FMP endpoint probe standard and ambiguity log
- `FMP_ENDPOINT_CATALOG_2026-02-23.md`: probed endpoint availability/status snapshot and ingestion boundary
- `FMP_FAILED_ENDPOINT_RECHECK_2026-02-23.md`: full recheck of batch1/batch2 failed endpoints with doc-aligned replacements
- `FMP_API_CALLABILITY_SUMMARY_2026-02-23.md`: full stable endpoint callability coverage summary (156 endpoints)
- `FMP_ENDPOINT_FIELD_DICTIONARY_STATUS_2026-02-23.md`: endpoint-field dictionary status and remaining semantic gap
- `FMP_FACTOR_FACTORY_DATA_CONSTRAINTS_2026-02-23.md`: enforceable allowlist/blocklist constraints for factor factory
- `FMP_CATEGORY_PLAYBOOK_2026-02-23.md`: per-category practical usage guide for factor factory data sources
- `FMP_FIELD_SEMANTIC_CATALOG_2026-02-23.md`: field-level semantic catalog status (`824` fields, `751` default-allow)
- `FMP_MEANINGFUL_DATA_INVENTORY_2026-02-23.md`: practical field-level meaningful data counts and theme pools
- `SYSTEM_OVERVIEW_EN.md`: end-to-end English white paper (architecture, validation flow, governance, and audit)
- `SYSTEM_OVERVIEW_ZH.md`: end-to-end Chinese system overview (architecture, gates, audit, operations)
- `NOTION_SYSTEM_OVERVIEW_ZH.md`: Notion-ready Chinese summary for project communication
- `NOTION_SYSTEM_OVERVIEW_EN.md`: concise English Notion summary for architecture and research logic
- `AUTO_RESEARCH_SCHEDULER.md`: unattended scheduler standard for orchestrator cadence/heartbeat/alerts
- `AUTO_RESEARCH_DEPLOYMENT.md`: workstation deployment standard for scheduler service operations
- `LOW_NETWORK_MODE.md`: low-network operation profile and mode switch standard
- `SYSTEM_CLOSURE_CHECK.md`: one-command end-of-phase acceptance/closure check standard
- `FAILURE_PATTERN_DB.md`: searchable failure-pattern database standard
- `SESSION_HANDOFF_READINESS.md`: pre-handoff readiness check standard for new session continuity

Active-flow note:
- historical snapshots are retained for audit, but current execution mode is defined by:
  - `FACTOR_PIPELINE_FREEZE_2026-02-25.md`
  - `FACTOR_FACTORY_STANDARD.md`

## Core scripts

- Primary unified entrypoint:
  - `scripts/ops_entry.sh` (`daily` / `fast` / `factory` / `status` / `official` / `check` / `cleanup` / `hygiene`)
- Daily pipeline internals:
  - `scripts/daily_research_run.sh`
  - `scripts/generate_daily_research_brief.py`
  - `scripts/prepare_dq_input.py`
  - `scripts/data_quality_gate.py`
  - `scripts/fast_research_run.sh`
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
- `scripts/governance_audit_checker.py`
- `scripts/governance_remediation_plan.py`
- `scripts/generate_run_review.py`
- `scripts/update_factor_experiment_registry.py`
- `scripts/generate_candidate_queue.py`
- `scripts/generate_next_run_plan.py`
- `scripts/execute_next_run_plan.py`
- `scripts/repair_next_run_plan_paths.py`
- `scripts/auto_research_orchestrator.py`
- `scripts/build_search_v1_trials.py`
- `scripts/run_factor_factory_batch.py`
- `scripts/fmp_interface_probe.py`
- `scripts/auto_research_scheduler.py`
- `scripts/test_scheduler_alert_channels.py`
- `scripts/switch_auto_research_mode.sh`
- `scripts/run_system_closure_check.py`
- `scripts/install_auto_research_scheduler_service.sh`
- `scripts/manage_auto_research_scheduler_service.sh`
- `scripts/update_failure_pattern_db.py`
- `scripts/check_session_handoff_readiness.py`
- `scripts/check_command_surface.py`
- `scripts/check_script_surface.py`
- `scripts/safe_artifact_cleanup.py`
- `scripts/research_governance.py`

## Related config

- `configs/research/candidate_queue_policy.json`
- `configs/research/auto_research_policy.json`
- `configs/research/auto_research_search_v1_policy.json`
- `configs/research/factor_factory_policy.json`
- `configs/research/auto_research_scheduler_policy.json`
- `configs/research/auto_research_scheduler_policy.low_network.json`

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
