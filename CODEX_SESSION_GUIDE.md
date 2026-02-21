# CODEX Session Guide

Last updated: 2026-02-21

This file is the single-entry protocol for new Codex sessions.
If a new session is opened with workspace access, following this file step-by-step must be sufficient to continue safely.

## 1) Protocol Contract

1. Read this file first.
2. Follow the mandatory read sequence exactly.
3. Use SSOT priority rules when documents disagree.
4. Do not perform destructive cleanup while any official run is active.
5. For heavy official runs, use workstation-only flow.

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
17. `docs/production_research/CURRENT_GATE_STATUS_2026-02-21.md`

Completion check after reading:
1. identify active `decision_tag`
2. identify active workstation `run_dir`
3. identify freeze file in use
4. identify whether run is `in_progress` or finished

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

Official wrapper template:
```bash
bash scripts/workstation_official_run.sh \
  --workflow production_gates \
  --tag committee_YYYY-MM-DD_runN \
  --owner hui \
  --notes "official workstation gate run" \
  --threads 8 \
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
3. confirm stage ledger row updated:
   - `docs/production_research/STAGE_AUDIT_LOG.md`
4. if failed, keep failed trail and create new rerun with new tag

## 10) Commit/Sync Rule

Preferred flow:
1. local `git commit`
2. local `git push`
3. workstation `git pull --ff-only`

Do not include unrelated local modifications in official governance commits.

## 11) Daily Validation Semantics (If Needed)

- `signal_date = T`
- `trade_date = T+1`
- run id format: `trade_YYYY-MM-DD_from_signal_YYYY-MM-DD`

## 12) Minimal Prompt For New Codex

```text
Read CODEX_SESSION_GUIDE.md and follow its protocol exactly. First detect active decision_tag/run_dir on workstation, then continue without interrupting active official runs.
```
