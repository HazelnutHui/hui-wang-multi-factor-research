# BatchA100 Data Readiness (Post-Reset, 2026-02-27)

As-of: 2026-02-27

Scope: `batchA100_logic100_formal_v1` (100 distinct logic candidates, one candidate per logic).

Workstation data root: `/home/hui/projects/hui-wang-multi-factor-research/data/fmp`

## Status

- Readiness status: `ready_now` for the current logic100 design.
- This file is data-availability boundary only; it does not imply any completed factor result.
- Current reset policy remains in force:
  - no pre-reset result is retained as formal reference,
  - no official result exists yet for post-reset batch.

## Core Data Packages Verified

- `ratios/value`
- `ratios/quality`
- `earnings_history/earnings.jsonl`
- `statements/income-statement.jsonl`
- `statements/income-statement-ttm.jsonl`
- `institutional-ownership__symbol-positions-summary.jsonl`
- `owner-earnings.jsonl`
- price data roots used by current protocol (`data/prices*` + PIT/market-cap filters)

## Execution Boundary

- First official post-reset batch: `batchA100_logic100_formal_v1`.
- Runtime status (as-of 2026-02-28): running on workstation.
- Master table SSOT:
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.md`
- Run launch still requires explicit manual approval.
