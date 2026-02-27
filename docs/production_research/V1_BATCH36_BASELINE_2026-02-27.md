# V1 Batch36 Baseline (2026-02-27)

As-of: 2026-02-27

This file is the single baseline reference for current factor-factory usable outputs.

## Baseline Definition

- V1 batch name: `batch36_frozen`
- Total usable candidates: `36`
- Signature-level duplicates: `0`
- Scope:
  - `segment_results/factor_factory/2026-02-25_072539_p1_core_short_horizon` (`16/16` complete)
  - `segment_results/factor_factory/2026-02-26_104024_p1_core_short_horizon_no_existing16` (`20/20` complete)

## Family Counts

- `momentum_v2`: `8`
- `reversal_v2`: `8`
- `turnover_shock`: `8`
- `vol_regime`: `8`
- `low_vol_v2`: `4`

## Execution Profile (Fixed)

- `REBALANCE_FREQ=5`
- `HOLDING_PERIOD=3`
- `REBALANCE_MODE=None`
- `EXECUTION_USE_TRADING_DAYS=True`
- `MARKET_CAP_STRICT=True`
- factor lag default in this batch: `LAG_DAYS=1`

## Governance Boundary

1. Treat this `36` as immutable V1 reference set.
2. Do not append incomplete or stale lineage outputs into this baseline.
3. Any next batch (V2/V3/...) requires explicit approval before execution.
