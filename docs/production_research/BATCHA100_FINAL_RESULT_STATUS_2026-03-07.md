# BatchA100 Final Result Status (2026-03-07)

As-of: 2026-03-07

## Final Result
- Batch: `batchA100_logic100_formal_v1`
- Canonical run id: `2026-02-28_095939_batchA100_logic100_formal_v1`
- Final availability: `100/100` factors with valid `segment_summary.csv`
- Canonical output path:
  - `segment_results/factor_factory/2026-02-28_095939_batchA100_logic100_formal_v1`

## Interpretation Boundary
- Use canonical output path only.
- Do not use intermediate rerun paths for ranking or reporting.
- Row-level factor status is maintained in:
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`

## Cleanup Result
- Intermediate remediation run directories were retired.
- Intermediate remediation logs were removed.
- Only canonical formal output remains under:
  - `segment_results/factor_factory/`

## Integrity Check
- `accruals_inverse` and `cash_conversion_improve` are not identical in canonical output.
- `eps_growth_quality_adj` and `revenue_growth_quality_adj` are not identical in canonical output.
- `capex_discipline` and `fcf_growth_persistence` are not identical in canonical output.
- Exact duplicate IC-vector groups in canonical set: `0`.
