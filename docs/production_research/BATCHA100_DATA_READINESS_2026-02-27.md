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

## Workstation Download Snapshot (Observed 2026-03-07)

Source host: `hui@100.66.103.44`  
Source root: `/home/hui/projects/hui-wang-multi-factor-research/data/fmp`

- `data/fmp/earnings` (files=18, latest=2026-03-04 06:38:21)
- `data/fmp/earnings_history` (files=1, latest=2026-02-27 08:40:17)
- `data/fmp/institutional` (files=2, latest=2026-03-02 22:54:16)
- `data/fmp/market_cap_history` (files=5659, latest=2026-02-28 08:12:28)
- `data/fmp/owner_earnings` (files=1, latest=2026-02-28 07:54:35)
- `data/fmp/ratios` (files=9642, latest=2026-03-04 07:08:09)
  - `data/fmp/ratios/quality` (files=4799, latest=2026-03-04 07:08:09)
  - `data/fmp/ratios/value` (files=4843, latest=2026-02-28 08:08:04)
- `data/fmp/research_only` (files=4, latest=2026-02-26 10:24:22)
- `data/fmp/statements` (files=4, latest=2026-02-28 08:04:35)

## Execution Boundary

- First official post-reset batch: `batchA100_logic100_formal_v1`.
- Runtime final status (as-of 2026-03-07): final consolidated result ready (`100/100`) at canonical output path.
- Master table SSOT:
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.md`
- Run launch still requires explicit manual approval.
