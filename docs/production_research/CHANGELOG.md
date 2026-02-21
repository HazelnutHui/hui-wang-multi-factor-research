# Production Research Layer Changelog

## 2026-02-21

### Added
- stage governance docs:
  - `docs/production_research/STAGE_EXECUTION_STANDARD.md`
  - `docs/production_research/STAGE_AUDIT_LOG.md`
  - `docs/production_research/WORKSTATION_RUNNER_SPEC.md`
  - `docs/production_research/ARTIFACT_RETENTION_AND_CLEANUP.md`
  - `docs/production_research/CURRENT_GATE_STATUS_2026-02-21.md`
  - `docs/production_research/POST_RUN_OPERATIONS.md`
- workstation wrappers:
  - `scripts/workstation_preflight.sh`
  - `scripts/workstation_official_run.sh`
  - `scripts/monitor_gate_run.sh`
  - `scripts/finalize_gate_run.py`
  - `scripts/finalize_gate_run.sh`
  - `scripts/post_run_sync_and_finalize.sh`
  - wrapper supports `--threads` for BLAS/OpenMP thread controls
  - gate runner supports `--wf-shards` for WF shard parallelism
- governance controls:
  - `docs/production_research/DATA_QUALITY_POLICY.md`
  - `docs/production_research/RISK_REGISTER.md`
  - `docs/production_research/MODEL_CHANGE_CONTROL.md`
  - `docs/production_research/INCIDENT_RESPONSE.md`
  - `docs/production_research/SECURITY_AND_ACCESS_CONTROL.md`
- data quality checker:
  - `scripts/data_quality_gate.py`
- governance completeness checker:
  - `scripts/governance_audit_checker.py`
- governance remediation planner:
  - `scripts/governance_remediation_plan.py`
- monitor-and-close helper:
  - `scripts/monitor_then_finalize.sh`
  - fixed WF process counting to avoid counting monitor shell itself
- review/run templates:
  - `docs/production_research/OFFICIAL_RUN_TEMPLATE.md`
  - `docs/production_research/RUN_REVIEW_TEMPLATE.md`
- session handoff readiness:
  - `docs/production_research/SESSION_HANDOFF_READINESS.md`
  - `scripts/check_session_handoff_readiness.py`
  - `CODEX_SESSION_GUIDE.md` and `SESSION_BOOTSTRAP.md` read sequence extended with handoff readiness standard
  - `scripts/post_run_sync_and_finalize.sh` now auto-runs handoff readiness checker and emits `audit/session_handoff/*`
- review generator:
  - `scripts/generate_run_review.py`
- post-run flow extension:
  - `scripts/post_run_sync_and_finalize.sh` now auto-generates `production_gates_run_review.md`
- factor experiment registry:
  - `docs/production_research/FACTOR_EXPERIMENT_REGISTRY.md`
  - `scripts/update_factor_experiment_registry.py`
  - `scripts/post_run_sync_and_finalize.sh` now auto-updates registry + leaderboard
- candidate queue automation:
  - `docs/production_research/CANDIDATE_QUEUE_POLICY.md`
  - `scripts/generate_candidate_queue.py`
  - `scripts/post_run_sync_and_finalize.sh` now auto-refreshes candidate queue
  - `configs/research/candidate_queue_policy.json` added for versioned mixed-mode scheduling (`3 robust + 1 exploration`)
  - `scripts/generate_candidate_queue.py` now auto-avoids decision_tag collisions via incremental suffixing
- next-run plan automation:
  - `docs/production_research/NEXT_RUN_PLANNING.md`
  - `docs/production_research/NEXT_RUN_EXECUTION_STANDARD.md`
  - `scripts/generate_next_run_plan.py`
  - `scripts/execute_next_run_plan.py`
  - `scripts/repair_next_run_plan_paths.py`
  - `scripts/post_run_sync_and_finalize.sh` now auto-generates rerun command/hypothesis plan
  - `scripts/execute_next_run_plan.py` now includes pre-execution safety validation (tag/freeze/dq/workflow checks)
  - `scripts/repair_next_run_plan_paths.py` now supports decision-tag normalization (`committee_YYYY-MM-DD_runN`) with collision avoidance
- auto research orchestration:
  - `docs/production_research/AUTO_RESEARCH_ORCHESTRATION.md`
  - `docs/production_research/AUTO_RESEARCH_SCHEDULER.md`
  - `docs/production_research/AUTO_RESEARCH_DEPLOYMENT.md`
  - `scripts/auto_research_orchestrator.py`
  - `scripts/auto_research_scheduler.py`
  - `scripts/install_auto_research_scheduler_service.sh`
  - `scripts/manage_auto_research_scheduler_service.sh`
  - `scripts/test_scheduler_alert_channels.py`
  - `configs/research/auto_research_policy.json`
  - `configs/research/auto_research_scheduler_policy.json`
  - orchestration loop now emits per-cycle audit reports under `audit/auto_research/`
  - orchestration loop now appends run-level ledger outputs (`audit/auto_research/auto_research_ledger.csv/.md`)
  - orchestration loop now updates rolling health summary (`audit/auto_research/auto_research_weekly_summary.csv/.md`)
  - scheduler mode now supports singleton lock, heartbeat, scheduler ledger, webhook/command/email alerts, alert dedupe window, and structured alert payloads (with recent failure summary)
  - scheduler alert channels now have one-command selftest report output
  - orchestrator now supports retry/backoff for pre-execution generation stages
  - orchestrator now supports multi-metric stagnation stop (`priority_score`, `gate_failure_count`, `high_remediation_count`)
- failure pattern database:
  - `docs/production_research/FAILURE_PATTERN_DB.md`
  - `scripts/update_failure_pattern_db.py`
  - `scripts/post_run_sync_and_finalize.sh` now auto-updates failure pattern DB + summary
- runner hardening:
  - `scripts/workstation_official_run.sh` now supports and records mandatory DQ pre-check (`--dq-input-csv`)
  - `scripts/workstation_official_run.sh` now auto-injects `--decision-tag/--owner/--notes` when missing in workflow args
  - `scripts/post_run_sync_and_finalize.sh` now executes governance audit checker automatically
  - `scripts/post_run_sync_and_finalize.sh` now generates remediation plan even when governance check fails
- playbook/bootstrap updates:
  - `CODEX_SESSION_GUIDE.md` mandatory sequence extended with new governance controls
  - `docs/production_research/SESSION_BOOTSTRAP.md` mandatory sequence extended
  - `docs/production_research/OPS_PLAYBOOK.md` includes pre-gate data quality step

### Renamed
- governance namespace:
  - `docs/institutional/` -> `docs/production_research/`
- gate runner:
  - `scripts/run_institutional_gates.py` -> `scripts/run_production_gates.py`
- checklist:
  - `POST_WF_INSTITUTIONAL_CHECKLIST.md` -> `POST_WF_PRODUCTION_CHECKLIST.md`
- production profile:
  - `configs/strategies/combo_v2_inst.yaml` -> `configs/strategies/combo_v2_prod.yaml`
  - `runs/freeze/combo_v2_inst.freeze.json` -> `runs/freeze/combo_v2_prod.freeze.json`
- gate artifact naming:
  - `institutional_gates_*` -> `production_gates_*`
  - `institutional_gates_report.*` -> `production_gates_report.*`

### Added (naming migration)
- terminology governance:
  - `docs/production_research/TERMINOLOGY_POLICY.md`
- migration evidence:
  - `docs/production_research/RENAMING_AUDIT_2026-02-21.md`

### Policy impact
- `production` is now the only approved governance term in active workflows.

## 2026-02-20

### Added
- governed manifest/freeze utilities:
  - `scripts/research_governance.py`
- unified governed dispatcher:
  - `scripts/run_research_workflow.py`
- freeze + manifest support for:
  - `scripts/run_with_config.py`
  - `scripts/run_segmented_factors.py`
  - `scripts/run_walk_forward.py`
- universe filter audit plumbing:
  - `backtest/universe_builder.py`
  - `backtest/backtest_engine.py`
  - runner-level audit csv outputs
- PIT/lag guardrails in all core runners (default enabled)
- production hard-gate runner:
  - `scripts/run_production_gates.py`
- risk diagnostics integrated into hard-gate pass/fail
- production research docs folder:
  - `docs/production_research/README.md`
  - `docs/production_research/GATE_SPEC.md`
  - `docs/production_research/OPS_PLAYBOOK.md`

### Policy impact
- Core research now supports formal promotion gates and decision audit trail.
- Official runs should not use skip flags (`--skip-guardrails`, `--skip-risk-diagnostics`).
