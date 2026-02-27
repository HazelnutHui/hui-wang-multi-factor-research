# Session Continuity Protocol

Last updated: 2026-02-27 (V1 batch36 frozen + BatchA100 running on workstation: `segment_results/factor_factory/2026-02-27_204818_batchA100_logic25_v1`)

This file is the single-entry protocol for new sessions.
If a new session is opened with workspace access, following this file step-by-step must be sufficient to continue safely.

## 1) Protocol Contract

1. Read this file first.
2. Follow the mandatory read sequence exactly.
3. Use SSOT priority rules when documents disagree.
4. Do not perform destructive cleanup while any official run is active.
5. For heavy official runs, use workstation-only flow.
6. For official runs, require a passing data quality gate artifact before gate execution.
7. For factor-factory full batches, use workstation by default with `--jobs 8` (minimum acceptable `--jobs 4`; local default is dry-run only).

## 2) Session Objective (Primary Track)

- production-grade `combo_v2` gate workflow
- complete audit chain:
  - freeze consistency
  - run manifests
  - gate report json/md
  - append-only registry and stage ledger updates

## 3) Mandatory Read Sequence With Completion Checks

Read in order:
1. `README.md`
2. `RUNBOOK.md`
3. `STATUS.md`
4. `DOCS_INDEX.md`
5. `docs/production_research/README.md`
6. `docs/production_research/GATE_SPEC.md`
7. `docs/production_research/OPS_PLAYBOOK.md`
8. `docs/production_research/WORKSTATION_PRIMARY_MODE.md`
9. `docs/production_research/SESSION_BOOTSTRAP.md`
10. `docs/production_research/AUDIT_ARTIFACTS.md`
11. `docs/production_research/TERMINOLOGY_POLICY.md`
12. `docs/production_research/RENAMING_AUDIT_2026-02-21.md`
13. `docs/production_research/STAGE_EXECUTION_STANDARD.md`
14. `docs/production_research/WORKSTATION_RUNNER_SPEC.md`
15. `docs/production_research/STAGE_AUDIT_LOG.md`
16. `docs/production_research/ARTIFACT_RETENTION_AND_CLEANUP.md`
17. `docs/production_research/DATA_QUALITY_POLICY.md`
18. `docs/production_research/RISK_REGISTER.md`
19. `docs/production_research/MODEL_CHANGE_CONTROL.md`
20. `docs/production_research/INCIDENT_RESPONSE.md`
21. `docs/production_research/SECURITY_AND_ACCESS_CONTROL.md`
22. `docs/production_research/GOVERNANCE_AUDIT_CHECKER.md`
23. `docs/production_research/GOVERNANCE_REMEDIATION_PLAN.md`
24. `docs/production_research/FACTOR_EXPERIMENT_REGISTRY.md`
25. `docs/production_research/CANDIDATE_QUEUE_POLICY.md`
26. `docs/production_research/NEXT_RUN_EXECUTION_STANDARD.md`
27. `docs/production_research/SESSION_HANDOFF_READINESS.md`
28. `docs/production_research/AUTO_RESEARCH_ORCHESTRATION.md`
29. `docs/production_research/AUTO_RESEARCH_SCHEDULER.md`
30. `docs/production_research/AUTO_RESEARCH_DEPLOYMENT.md`
31. `docs/production_research/LOW_NETWORK_MODE.md`
32. `docs/production_research/SYSTEM_CLOSURE_CHECK.md`
33. `docs/production_research/AUTO_RESEARCH_SEARCH_V1.md`
34. `docs/production_research/FACTOR_FACTORY_STANDARD.md`
35. `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md`
36. `docs/production_research/FMP_INTERFACE_PROBE_STANDARD.md`
37. `docs/production_research/FMP_ENDPOINT_CATALOG_2026-02-23.md`
38. `docs/production_research/FMP_FAILED_ENDPOINT_RECHECK_2026-02-23.md`
39. `docs/production_research/FMP_API_CALLABILITY_SUMMARY_2026-02-23.md`
40. `docs/production_research/FMP_ENDPOINT_FIELD_DICTIONARY_STATUS_2026-02-23.md`
41. `docs/production_research/FMP_FIELD_SEMANTIC_CATALOG_2026-02-23.md`
42. `docs/production_research/FMP_FACTOR_FACTORY_DATA_CONSTRAINTS_2026-02-23.md`
43. `docs/production_research/FMP_CATEGORY_PLAYBOOK_2026-02-23.md`
44. `docs/production_research/FMP_MEANINGFUL_DATA_INVENTORY_2026-02-23.md`
45. `docs/production_research/CURRENT_GATE_STATUS_2026-02-23.md`
46. `docs/production_research/FACTOR_FACTORY_QUEUE_SNAPSHOT_2026-02-27.md`
47. `docs/production_research/V1_BATCH36_BASELINE_2026-02-27.md`
48. `docs/production_research/FACTOR_BATCH_MASTER_TABLE.md`
49. `docs/production_research/FMP_NEXT100_DATA_PLAN_2026-02-26.md`
50. `docs/production_research/BATCHA_100_FACTOR_LOGIC_DRAFT_2026-02-27.md`

Completion check after reading:
1. identify active `decision_tag`
2. identify active workstation `run_dir`
3. identify freeze file in use
4. identify whether run is `in_progress` or finished
5. identify latest data quality gate artifact path and pass/fail status (for official runs)
6. identify latest factor registry update and leaderboard status
7. identify latest factor candidate queue output and top candidate
8. identify active candidate queue policy config (`configs/research/candidate_queue_policy.json`)
9. identify latest `audit/factor_registry/next_run_plan.md` and planned command set
10. identify latest `audit/factor_registry/next_run_plan_fixed.md` and whether tags were normalized
11. identify latest failure pattern summary status (`audit/failure_patterns/failure_pattern_summary.md`)
12. identify active auto-research policy config (`configs/research/auto_research_policy.json`)
13. identify latest auto-research ledger status (`audit/auto_research/auto_research_ledger.md`)
14. identify latest weekly auto-research health summary (`audit/auto_research/auto_research_weekly_summary.md`)
15. identify scheduler liveness and last-cycle status (`audit/auto_research/auto_research_scheduler_heartbeat.json`)
16. identify scheduler service deployment status (systemd user service + env file on workstation)
17. identify active scheduler mode (low-network vs standard) and latest mode-switch audit note
18. identify active search-v1 policy config (`configs/research/auto_research_search_v1_policy.json`)
19. identify latest search-v1 trial plan output location under audit/search_v1 (if available)
20. identify latest FMP coverage probe artifact:
   - `audit/fmp_probe_coverage_v1/fmp_interface_probe_latest.json`
21. identify latest endpoint semantic map + allow/block lists:
   - `audit/fmp_probe_coverage_v1/fmp_endpoint_semantic_map_2026-02-23.csv`
   - `audit/fmp_probe_coverage_v1/fmp_factor_factory_allowlist_2026-02-23.csv`
   - `audit/fmp_probe_coverage_v1/fmp_high_leakage_blocklist_2026-02-23.csv`
22. identify latest field-level semantic catalog + meaningful inventory:
   - `audit/fmp_probe_coverage_v1/fmp_field_semantic_catalog_2026-02-23.csv`
   - `audit/fmp_probe_coverage_v1/fmp_meaningful_data_inventory_2026-02-23.json`
23. identify active factor-factory detached run status on workstation (PID + run_dir + log)
24. read `docs/production_research/FACTOR_PIPELINE_FREEZE_2026-02-25.md` before launching new large factor queues
25. identify latest gate snapshot conclusions (and whether they are locally verified vs workstation-only):
   - `docs/production_research/CURRENT_GATE_STATUS_2026-02-23.md`
   - latest `overall_pass` and failed gate keys (if any)
26. identify latest factor-factory queue continuity snapshot:
   - `docs/production_research/FACTOR_FACTORY_QUEUE_SNAPSHOT_2026-02-27.md`
27. identify current frozen single-factor baseline set:
   - `docs/production_research/V1_BATCH36_BASELINE_2026-02-27.md`
28. identify latest queryable batch master table (logic/formula/params/results):
   - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
   - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.md`
29. identify next100 FMP data-use boundary and endpoint tiers:
   - `docs/production_research/FMP_NEXT100_DATA_PLAN_2026-02-26.md`

## 4) SSOT Priority (Conflict Resolution)

When two sources conflict, use this priority:
1. runtime artifacts for current run:
   - `audit/workstation_runs/<...>/context.json`
   - `audit/workstation_runs/<...>/run.log`
   - `gate_results/production_gates_<ts>/production_gates_report.json`
2. governance spec docs:
   - `docs/production_research/GATE_SPEC.md`
   - `docs/production_research/STAGE_EXECUTION_STANDARD.md`
   - `docs/production_research/WORKSTATION_RUNNER_SPEC.md`
3. operational guides:
   - `RUNBOOK.md`
   - `docs/production_research/OPS_PLAYBOOK.md`
4. historical snapshots and summaries:
   - `STATUS.md`
   - `CURRENT_GATE_STATUS_*.md`

## 5) Runtime Handoff Procedure (Do This First)

On workstation:
```bash
cd ~/projects/hui-wang-multi-factor-research
RUN_DIR=$(ls -td audit/workstation_runs/* | head -n1)
echo "$RUN_DIR"
cat "$RUN_DIR/context.json"
tail -n 40 "$RUN_DIR/run.log"
pgrep -af "run_walk_forward.py --factors combo_v2" || true
```

Interpretation:
1. if `result.json` exists in `RUN_DIR`, run likely finished
2. if WF processes exist, run is active; do not clean artifacts
3. if no active process and no `result.json`, inspect `run.log` for failure cause

## 6) Official Execution Rules (Must Keep)

1. heavy official runs on workstation only
2. freeze required for official runs
3. never use skip flags in official runs:
   - `--skip-guardrails`
   - `--skip-risk-diagnostics`
   - `--skip-statistical-gates`
4. preferred performance profile for heavy gates:
   - `--threads 8`
   - `--cost-multipliers 1.5,2.0` (rerun speed profile)
   - `--wf-shards 4`
5. factor-factory full-batch default:
   - run on workstation
   - queue execution requires manual approval first:
     - update `configs/research/factory_queue/run_approval.json`
     - set `approved=true` and `approved_queue=<target queue json>`
   - then run:
     - `bash scripts/ops_entry.sh factory_queue --queue-json <approved_queue_json> --jobs 8`
   - use single-batch `factory --jobs 4 --max-candidates 20` only for targeted debugging
   - keep policy-level execution profile fixed for comparability:
     - `REBALANCE_FREQ=5`
     - `HOLDING_PERIOD=3`
     - `REBALANCE_MODE=None`
   - two-round rule (must keep):
     - round-1: large-scale screening under fixed `5/3/None`
     - round-2: shortlisted top `20-30` run `HOLDING_PERIOD=1/3/5` robustness checks (`REBALANCE_FREQ=5`, `REBALANCE_MODE=None`)

Official wrapper template:
```bash
python scripts/data_quality_gate.py \
  --input-csv data/your_input.csv \
  --required-columns date,ticker,score \
  --numeric-columns score \
  --key-columns date,ticker \
  --date-column date \
  --max-staleness-days 7 \
  --out-dir gate_results/data_quality

bash scripts/ops_entry.sh official \
  --workflow production_gates \
  --tag committee_YYYY-MM-DD_runN \
  --owner hui \
  --notes "official workstation gate run" \
  --threads 8 \
  --dq-input-csv data/your_input.csv \
  -- \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --factor combo_v2 \
  --cost-multipliers 1.5,2.0 \
  --wf-shards 4 \
  --freeze-file runs/freeze/combo_v2_prod_<date>_g<commit>.freeze.json \
  --stress-market-cap-dir data/fmp/market_cap_history \
  --out-dir gate_results
```

## 7) In-Progress Safety Rules (No Interference)

While active process exists:
1. do not delete `gate_results/production_gates_<active_ts>/...`
2. do not delete active `audit/workstation_runs/<active_run_dir>/...`
3. do not overwrite freeze used by active run
4. do not run destructive cleanup on workstation cache/results paths

## 8) Failure Playbooks (Known Cases)

1. `python not found` / dependency mismatch:
   - ensure wrapper uses `.venv/bin/python`
2. freeze mismatch (`config_hash` or `git_commit`):
   - create new commit-aligned freeze file
   - rerun with new `decision_tag`
3. runtime contention from old runs:
   - kill only stale process from old out_dir
   - keep current official run single-lineage
4. long WF runtime:
   - use `--wf-shards` and monitor shard processes

## 9) Completion Protocol (After Run Ends)

1. verify report exists:
   - `gate_results/production_gates_<ts>/production_gates_report.json`
   - `gate_results/production_gates_<ts>/production_gates_report.md`
2. finalize ledger + summary:
```bash
bash scripts/finalize_gate_run.sh --tag committee_YYYY-MM-DD_runN
```
3. run governance completeness check:
```bash
python scripts/governance_audit_checker.py \
  --run-dir audit/workstation_runs/<ts>_production_gates_<decision_tag> \
  --report-json gate_results/production_gates_<ts>/production_gates_report.json \
  --require-final-summary
```
4. confirm stage ledger row updated:
   - `docs/production_research/STAGE_AUDIT_LOG.md`
5. refresh factor experiment registry:
```bash
python scripts/update_factor_experiment_registry.py \
  --report-json gate_results/production_gates_<ts>/production_gates_report.json \
  --run-dir audit/workstation_runs/<ts>_production_gates_<decision_tag>
```
6. if governance check failed, inspect remediation outputs:
   - `audit/workstation_runs/<...>/governance_remediation_plan.json`
   - `audit/workstation_runs/<...>/governance_remediation_plan.md`
7. if failed, keep failed trail and create new rerun with new tag

If run is still active and you want hands-off closure:
```bash
bash scripts/monitor_then_finalize.sh --tag committee_YYYY-MM-DD_runN --interval 30
```

## 10) Commit/Sync Rule

Preferred flow:
1. local `git commit`
2. local `git push`
3. workstation `git pull --ff-only`
4. run handoff readiness checker after doc/protocol updates:
```bash
python scripts/check_session_handoff_readiness.py
```

Do not include unrelated local modifications in official governance commits.

## 11) Daily Validation Semantics (If Needed)

- `signal_date = T`
- `trade_date = T+1`
- run id format: `trade_YYYY-MM-DD_from_signal_YYYY-MM-DD`

## 12) Minimal Prompt For New Session

```text
Read SESSION_CONTINUITY_PROTOCOL.md and follow its protocol exactly. First detect active decision_tag/run_dir on workstation, then continue without interrupting active official runs.
```

## 13) FMP + Factory Continuity Addendum (2026-02-23)

Purpose:
1. preserve end-to-end traceability for FMP interface research and field-level semantics;
2. ensure new sessions can resume factor-factory work without rediscovery.

Primary artifacts to verify:
1. endpoint callability matrix:
   - `audit/fmp_probe_coverage_v1/fmp_api_callable_matrix_2026-02-23.csv`
2. endpoint field dictionary:
   - `audit/fmp_probe_coverage_v1/fmp_endpoint_field_dictionary_2026-02-23.csv`
3. endpoint semantic map:
   - `audit/fmp_probe_coverage_v1/fmp_endpoint_semantic_map_2026-02-23.csv`
4. field semantic catalog:
   - `audit/fmp_probe_coverage_v1/fmp_field_semantic_catalog_2026-02-23.csv`
5. meaningful inventory:
   - `audit/fmp_probe_coverage_v1/fmp_meaningful_data_inventory_2026-02-23.json`
6. factor-factory data constraints:
   - `audit/fmp_probe_coverage_v1/fmp_factor_factory_allowlist_2026-02-23.csv`
   - `audit/fmp_probe_coverage_v1/fmp_high_leakage_blocklist_2026-02-23.csv`
   - `configs/research/fmp_field_theme_seeds_2026-02-23.json`

Workstation runtime check for detached factor-factory batch:
```bash
cd ~/projects/hui-wang-multi-factor-research
pgrep -af "run_factor_factory_queue.py|run_factor_factory_batch.py" || true
pgrep -af "run_segmented_factors.py --factors" || true
ls -td audit/factor_factory/* | head -n 3
find audit/factor_factory -maxdepth 3 -name leaderboard.csv | tail -n 3
```

Notes:
1. do not hardcode active lineage from historical docs; always verify newest runtime lineage with the commands above.
2. local-only view can lag workstation; if a snapshot references run dirs missing locally, mark status as `pending_local_sync` until artifacts are synced.
3. do not launch duplicate factory batches with the same command unless explicitly intended.
4. if duplicate lineage appears, keep newest active run and terminate stale lineage by run_dir pattern only.
