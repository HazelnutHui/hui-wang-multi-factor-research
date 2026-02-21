# Factor Experiment Registry Standard

Last updated: 2026-02-21

This standard defines the centralized registry used for continuous automated factor research.

## Purpose

1. unify experiment records across official production gate runs
2. provide stable scoring and ranking for candidate selection
3. preserve traceable links to run/report/governance artifacts

## Script

- `scripts/update_factor_experiment_registry.py`

## Outputs

- `audit/factor_registry/factor_experiment_registry.csv`
- `audit/factor_registry/factor_experiment_leaderboard.md`

## Input Sources

1. `gate_results/production_gates_*/production_gates_report.json`
2. matching run dir by `decision_tag` under:
   - `audit/workstation_runs/*<decision_tag>*/`
3. governance artifacts (if present):
   - `governance_audit_check.json`
   - `governance_remediation_plan.json`
   - `context.json` (for data quality report linkage)

## Scoring Model (v1)

Total score range: `0-100`

1. quality score (`0-80`):
   - cost stress component (`0-20`)
   - walk-forward component (`0-30`)
   - risk component (`0-20`)
   - statistical component (`0-10`)
2. governance score (`0-20`):
   - data quality pass
   - governance audit pass
   - stage ledger linkage
   - no high-severity remediation items

Rule:
- if `overall_pass=false`, score is capped to avoid accidental top ranking.

## Recommendation Labels

1. `promote_candidate`:
   - `overall_pass=true`
   - governance and data-quality checks pass
   - score >= 80
2. `watchlist_rerun`:
   - score >= 65 but not promotion-ready
3. `reject_or_research`:
   - score < 65

## Standard Usage

Single run update:

```bash
python scripts/update_factor_experiment_registry.py \
  --report-json gate_results/production_gates_<ts>/production_gates_report.json \
  --run-dir audit/workstation_runs/<ts>_production_gates_<decision_tag>
```

Full rebuild:

```bash
python scripts/update_factor_experiment_registry.py
```

## Integration

- auto-invoked by `scripts/post_run_sync_and_finalize.sh` after run review generation
- registry + leaderboard are SSOT inputs for automated candidate queueing
- queue refresh script:
  - `scripts/generate_candidate_queue.py`
  - outputs under `audit/factor_registry/factor_candidate_queue.*`
