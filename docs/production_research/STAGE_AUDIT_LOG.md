# Stage Audit Log

Last updated: 2026-02-28

Purpose:
- keep only active, post-reset stage decisions;
- avoid stale references to retired artifacts.

## Ledger

| date | stage | decision_tag | owner | objective | command_ref | artifact_ref | result | next_action |
|---|---|---|---|---|---|---|---|---|
| 2026-02-27 | S0 Reset | reset_2026-02-27_state_clear | hui | retire all pre-reset factor outputs and docs references | `scripts/run_segmented_factors.py --help` | `docs/production_research/RESET_STATE_2026-02-27.md` | pass | treat `batchA100_logic100_v1` as first official batch, pending approval |

## Update Rule

- Add a new row for each official post-reset stage decision.
- `artifact_ref` must point to an existing local file.
- If an old row becomes invalid after cleanup, replace by a new corrected row.
