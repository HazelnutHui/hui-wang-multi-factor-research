# Artifact Retention and Cleanup Policy

Last updated: 2026-02-21

## Purpose

Define what is audit evidence vs disposable runtime output, so cleanup does not break traceability.

## Classification

1. Must retain (audit evidence)
- `audit/workstation_runs/<ts>_<workflow>_<decision_tag>/`
- `gate_results/production_gates_<ts>/production_gates_report.json`
- `gate_results/production_gates_<ts>/production_gates_report.md`
- `gate_results/gate_registry.csv`
- freeze files actually used in official decisions

2. Retain until decision closes
- in-progress run folders for active `decision_tag`
- intermediate walk-forward shard outputs of active reruns

3. Cleanup candidates (after verification)
- aborted/failed temporary run folders not referenced by final decision row
- duplicate freeze files never referenced by official run
- temporary sync bundles/cache folders not required by current stage

## Safety rules

- Never delete artifacts for currently running processes.
- Never delete the latest successful official run for a decision tag.
- If deleting, record deleted paths and reason in stage audit notes.

## Suggested cleanup checklist

1. Identify active process list (`pgrep -af`).
2. Exclude active run directories from cleanup set.
3. Keep one complete failed trail + one successful trail per decision cycle.
4. Update `docs/production_research/STAGE_AUDIT_LOG.md` with cleanup note.

## Example monitor commands (non-destructive)

```bash
pgrep -af "run_walk_forward.py --factors combo_v2"
ls -td audit/workstation_runs/*committee_* | head -n 10
ls -td gate_results/production_gates_* | head -n 10
```
