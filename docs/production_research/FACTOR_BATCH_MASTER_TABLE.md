# Factor Batch Master Table

As-of: 2026-03-07

- Scope: first official post-reset research batch (formal logic100)
- Batch ID: `batchA100_logic100_formal_v1`
- Formal run status: `closed`
- Run ID: `2026-02-28_095939_batchA100_logic100_formal_v1`
- Workstation log: `logs/batchA100_logic100_formal_v1_20260228_025939.log`
- Query CSV: `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
- Logic design SSOT: `docs/production_research/BATCHA100_LOGIC100_FORMAL_V1_2026-02-28.csv`
- Implementation map: `docs/production_research/BATCHA100_LOGIC100_IMPLEMENTATION_MAP_2026-02-28.csv`

## Snapshot

| item | value |
|---|---|
| total candidates | 100 |
| result_status | final_consolidated |
| priority split | P0=54, P1=42, P2=4 |
| implementation split | native=75, alias_proxy=18, proxy=7 |
| factors with valid outputs | 100 |
| canonical output path | segment_results/factor_factory/2026-02-28_095939_batchA100_logic100_formal_v1 |
| old pair/tri draft table | retired from master table view |

## Notes

- This master table intentionally avoids duplicating the full 100-row markdown list to reduce stale drift.
- Use the CSV for full row-level query/filter.
- Older `logic100_001..100` pair/tri draft representation is deprecated and not used for this official run.
- Final interpretation boundary:
  - use canonical output path only
  - treat intermediate rerun artifacts as retired workflow artifacts
