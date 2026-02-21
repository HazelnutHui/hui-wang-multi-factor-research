# Candidate Queue Policy

Last updated: 2026-02-21

This policy defines how the system selects next-run factor candidates from the experiment registry.

## Script

- `scripts/generate_candidate_queue.py`

## Input

- `audit/factor_registry/factor_experiment_registry.csv`

## Outputs

- `audit/factor_registry/factor_candidate_queue.csv`
- `audit/factor_registry/factor_candidate_queue.md`

## Selection Rules (v1)

1. start from latest row per factor
2. require `score_total >= min_score` (default `45`)
3. include recommendation classes:
   - `promote_candidate`
   - `watchlist_rerun`
   - `reject_or_research` (only when score >= 55)
4. compute `priority_score` from:
   - score_total
   - overall pass bonus
   - governance/data-quality pass bonus
   - high-severity remediation penalty

## Queue Actions

1. `promote_candidate` -> `paper_candidate_validation`
2. `watchlist_rerun` -> `official_rerun_with_targeted_adjustments`
3. `reject_or_research` -> `research_iteration_with_new_hypothesis`

## Standard Usage

```bash
python scripts/generate_candidate_queue.py
```

Optional tuning:

```bash
python scripts/generate_candidate_queue.py --top-n 30 --min-score 50
```

## Integration

- auto-invoked at the end of `scripts/post_run_sync_and_finalize.sh`
- queue markdown includes ready-to-run command templates for official wrapper execution
