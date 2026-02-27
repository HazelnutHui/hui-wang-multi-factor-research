# BatchA100 Data Readiness (2026-02-27)

As-of: 2026-02-27

Scope: `batchA100_logic25_v1` (`100` candidates / `25` factor families).

Workstation data root: `/home/hui/projects/hui-wang-multi-factor-research/data/fmp`

## Summary
- Families checked: `25`
- Families ready now: `25`
- Families ready with integration note: `0`
- Data download status for newly requested packages:
  - `earnings_history/earnings.jsonl`: 5372 symbols, 4122 non-empty payload
  - `statements/income-statement.jsonl`: 5372 symbols, 4688 non-empty payload
  - `statements/income-statement-ttm.jsonl`: 5372 symbols, 4679 non-empty payload

## Family-Level Check

| factor_family | count | data_package | readiness | note |
|---|---:|---|---|---|
| `value_ey_cross` | 4 | `ratios/value` | `ready_now` |  |
| `value_fcfy_cross` | 4 | `ratios/value` | `ready_now` |  |
| `value_ev_ebitda_cross` | 4 | `ratios/value` | `ready_now` |  |
| `value_composite_v1` | 4 | `ratios/value` | `ready_now` |  |
| `quality_roe_cross` | 4 | `ratios/quality` | `ready_now` |  |
| `quality_roa_cross` | 4 | `ratios/quality` | `ready_now` |  |
| `quality_gm_cross` | 4 | `ratios/quality` | `ready_now` |  |
| `quality_cfoa_cross` | 4 | `ratios/quality` | `ready_now` |  |
| `safety_de_inverse` | 4 | `ratios/quality` | `ready_now` |  |
| `quality_composite_v1` | 4 | `ratios/quality` | `ready_now` |  |
| `value_quality_blend` | 4 | `ratios/value + ratios/quality` | `ready_now` |  |
| `profitability_minus_leverage` | 4 | `ratios/quality` | `ready_now` |  |
| `roe_trend` | 4 | `ratios/quality` | `ready_now` |  |
| `roa_trend` | 4 | `ratios/quality` | `ready_now` |  |
| `margin_trend` | 4 | `ratios/quality` | `ready_now` |  |
| `cfo_quality_trend` | 4 | `ratios/quality` | `ready_now` |  |
| `deleveraging_trend` | 4 | `ratios/quality` | `ready_now` |  |
| `value_re_rating_ey` | 4 | `ratios/value` | `ready_now` |  |
| `value_re_rating_fcfy` | 4 | `ratios/value` | `ready_now` |  |
| `sue_eps_basic` | 4 | `earnings/calendar (+surprises for PEAD)` | `ready_now` |  |
| `sue_revenue_basic` | 4 | `earnings/calendar (+surprises for PEAD)` | `ready_now` |  |
| `pead_short_window` | 4 | `earnings/calendar (+surprises for PEAD)` | `ready_now` |  |
| `institutional_ownership_change` | 4 | `institutional/positions_summary` | `ready_now` |  |
| `institutional_breadth_change` | 4 | `institutional/positions_summary` | `ready_now` |  |
| `owner_earnings_yield_proxy` | 4 | `owner_earnings + price` | `ready_now` |  |

## Operational Note
- `sue_revenue_basic` now supports fallback from `earnings_calendar.csv` to `earnings_history/earnings.jsonl` in `backtest/factor_engine.py`.
- Verified on workstation with non-null outputs for symbols where calendar revenue fields are missing but earnings-history provides `revenueActual/revenueEstimated`.

## Machine-Readable Table
- `docs/production_research/BATCHA100_DATA_READINESS_2026-02-27.csv`
