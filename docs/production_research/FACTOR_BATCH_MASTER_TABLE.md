# Factor Batch Master Table

As-of: 2026-02-27

- Query CSV: `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
- Scope: first official research batch only (post-reset).

## Batch Snapshot

| batch_id | status | rows | completed | not_run |
|---|---|---:|---:|---:|
| batchA100_logic100_v1 | ready_for_review | 100 | 0 | 100 |

## batchA100_logic100_v1 (100)

| candidate_id | family | logic_formula | params | result_status |
|---|---|---|---|---|
| logic100_001 | logic100_001 | `+1.00*momentum` | `{}` | not_run |
| logic100_002 | logic100_002 | `+1.00*reversal` | `{}` | not_run |
| logic100_003 | logic100_003 | `+1.00*low_vol` | `{}` | not_run |
| logic100_004 | logic100_004 | `-1.00*size` | `{}` | not_run |
| logic100_005 | logic100_005 | `+1.00*turnover_shock` | `{}` | not_run |
| logic100_006 | logic100_006 | `+1.00*vol_regime` | `{}` | not_run |
| logic100_007 | logic100_007 | `+1.00*quality_component` | `{}` | not_run |
| logic100_008 | logic100_008 | `+1.00*quality_component` | `{}` | not_run |
| logic100_009 | logic100_009 | `+1.00*quality_component` | `{}` | not_run |
| logic100_010 | logic100_010 | `+1.00*quality_component` | `{}` | not_run |
| logic100_011 | logic100_011 | `-1.00*quality_component` | `{}` | not_run |
| logic100_012 | logic100_012 | `+1.00*value_component` | `{}` | not_run |
| logic100_013 | logic100_013 | `+1.00*value_component` | `{}` | not_run |
| logic100_014 | logic100_014 | `+1.00*value_component` | `{}` | not_run |
| logic100_015 | logic100_015 | `+1.00*quality_metric_trend` | `{}` | not_run |
| logic100_016 | logic100_016 | `+1.00*quality_metric_trend` | `{}` | not_run |
| logic100_017 | logic100_017 | `+1.00*quality_metric_trend` | `{}` | not_run |
| logic100_018 | logic100_018 | `+1.00*quality_metric_trend` | `{}` | not_run |
| logic100_019 | logic100_019 | `-1.00*quality_metric_trend` | `{}` | not_run |
| logic100_020 | logic100_020 | `+1.00*value_metric_trend` | `{}` | not_run |
| logic100_021 | logic100_021 | `+1.00*value_metric_trend` | `{}` | not_run |
| logic100_022 | logic100_022 | `+1.00*value_quality_blend` | `{}` | not_run |
| logic100_023 | logic100_023 | `+1.00*profitability_minus_leverage` | `{}` | not_run |
| logic100_024 | logic100_024 | `+1.00*sue_eps_basic` | `{}` | not_run |
| logic100_025 | logic100_025 | `+1.00*sue_revenue_basic` | `{}` | not_run |
| logic100_026 | logic100_026 | `+1.00*pead_short_window` | `{}` | not_run |
| logic100_027 | logic100_027 | `+1.00*institutional_ownership_change` | `{}` | not_run |
| logic100_028 | logic100_028 | `+1.00*institutional_breadth_change` | `{}` | not_run |
| logic100_029 | logic100_029 | `+1.00*owner_earnings_yield_proxy` | `{}` | not_run |
| logic100_030 | logic100_030 | `+0.50*momentum +0.50*reversal` | `{}` | not_run |
| logic100_031 | logic100_031 | `+0.50*low_vol +0.50*momentum` | `{}` | not_run |
| logic100_032 | logic100_032 | `+0.50*momentum -0.50*size` | `{}` | not_run |
| logic100_033 | logic100_033 | `+0.50*momentum +0.50*turnover_shock` | `{}` | not_run |
| logic100_034 | logic100_034 | `+0.50*momentum +0.50*vol_regime` | `{}` | not_run |
| logic100_035 | logic100_035 | `+0.50*momentum +0.50*quality_component` | `{}` | not_run |
| logic100_036 | logic100_036 | `+0.50*momentum +0.50*quality_component` | `{}` | not_run |
| logic100_037 | logic100_037 | `+0.50*momentum +0.50*quality_component` | `{}` | not_run |
| logic100_038 | logic100_038 | `+0.50*momentum +0.50*quality_component` | `{}` | not_run |
| logic100_039 | logic100_039 | `+0.50*momentum -0.50*quality_component` | `{}` | not_run |
| logic100_040 | logic100_040 | `+0.50*momentum +0.50*value_component` | `{}` | not_run |
| logic100_041 | logic100_041 | `+0.50*momentum +0.50*value_component` | `{}` | not_run |
| logic100_042 | logic100_042 | `+0.50*momentum +0.50*value_component` | `{}` | not_run |
| logic100_043 | logic100_043 | `+0.50*momentum +0.50*quality_metric_trend` | `{}` | not_run |
| logic100_044 | logic100_044 | `+0.50*momentum +0.50*quality_metric_trend` | `{}` | not_run |
| logic100_045 | logic100_045 | `+0.50*momentum +0.50*quality_metric_trend` | `{}` | not_run |
| logic100_046 | logic100_046 | `+0.50*momentum +0.50*quality_metric_trend` | `{}` | not_run |
| logic100_047 | logic100_047 | `+0.50*momentum -0.50*quality_metric_trend` | `{}` | not_run |
| logic100_048 | logic100_048 | `+0.50*momentum +0.50*value_metric_trend` | `{}` | not_run |
| logic100_049 | logic100_049 | `+0.50*low_vol +0.50*reversal` | `{}` | not_run |
| logic100_050 | logic100_050 | `+0.50*reversal -0.50*size` | `{}` | not_run |
| logic100_051 | logic100_051 | `+0.50*reversal +0.50*turnover_shock` | `{}` | not_run |
| logic100_052 | logic100_052 | `+0.50*reversal +0.50*vol_regime` | `{}` | not_run |
| logic100_053 | logic100_053 | `+0.50*quality_component +0.50*reversal` | `{}` | not_run |
| logic100_054 | logic100_054 | `+0.50*quality_component +0.50*reversal` | `{}` | not_run |
| logic100_055 | logic100_055 | `+0.50*quality_component +0.50*reversal` | `{}` | not_run |
| logic100_056 | logic100_056 | `+0.50*quality_component +0.50*reversal` | `{}` | not_run |
| logic100_057 | logic100_057 | `-0.50*quality_component +0.50*reversal` | `{}` | not_run |
| logic100_058 | logic100_058 | `+0.50*reversal +0.50*value_component` | `{}` | not_run |
| logic100_059 | logic100_059 | `+0.50*reversal +0.50*value_component` | `{}` | not_run |
| logic100_060 | logic100_060 | `+0.50*reversal +0.50*value_component` | `{}` | not_run |
| logic100_061 | logic100_061 | `+0.50*quality_metric_trend +0.50*reversal` | `{}` | not_run |
| logic100_062 | logic100_062 | `+0.50*quality_metric_trend +0.50*reversal` | `{}` | not_run |
| logic100_063 | logic100_063 | `+0.50*quality_metric_trend +0.50*reversal` | `{}` | not_run |
| logic100_064 | logic100_064 | `+0.50*quality_metric_trend +0.50*reversal` | `{}` | not_run |
| logic100_065 | logic100_065 | `-0.50*quality_metric_trend +0.50*reversal` | `{}` | not_run |
| logic100_066 | logic100_066 | `+0.50*reversal +0.50*value_metric_trend` | `{}` | not_run |
| logic100_067 | logic100_067 | `+0.50*low_vol -0.50*size` | `{}` | not_run |
| logic100_068 | logic100_068 | `+0.50*low_vol +0.50*turnover_shock` | `{}` | not_run |
| logic100_069 | logic100_069 | `+0.50*low_vol +0.50*vol_regime` | `{}` | not_run |
| logic100_070 | logic100_070 | `+0.50*low_vol +0.50*quality_component` | `{}` | not_run |
| logic100_071 | logic100_071 | `+0.50*low_vol +0.50*quality_component` | `{}` | not_run |
| logic100_072 | logic100_072 | `+0.50*low_vol +0.50*quality_component` | `{}` | not_run |
| logic100_073 | logic100_073 | `+0.50*low_vol +0.50*quality_component` | `{}` | not_run |
| logic100_074 | logic100_074 | `+0.50*low_vol -0.50*quality_component` | `{}` | not_run |
| logic100_075 | logic100_075 | `+0.50*low_vol +0.50*value_component` | `{}` | not_run |
| logic100_076 | logic100_076 | `+0.50*low_vol +0.50*value_component` | `{}` | not_run |
| logic100_077 | logic100_077 | `+0.50*low_vol +0.50*value_component` | `{}` | not_run |
| logic100_078 | logic100_078 | `+0.50*low_vol +0.50*quality_metric_trend` | `{}` | not_run |
| logic100_079 | logic100_079 | `+0.50*low_vol +0.50*quality_metric_trend` | `{}` | not_run |
| logic100_080 | logic100_080 | `+0.50*low_vol +0.50*quality_metric_trend` | `{}` | not_run |
| logic100_081 | logic100_081 | `+0.50*low_vol +0.50*quality_metric_trend` | `{}` | not_run |
| logic100_082 | logic100_082 | `+0.50*low_vol -0.50*quality_metric_trend` | `{}` | not_run |
| logic100_083 | logic100_083 | `+0.50*low_vol +0.50*value_metric_trend` | `{}` | not_run |
| logic100_084 | logic100_084 | `-0.50*size +0.50*turnover_shock` | `{}` | not_run |
| logic100_085 | logic100_085 | `-0.50*size +0.50*vol_regime` | `{}` | not_run |
| logic100_086 | logic100_086 | `+0.50*quality_component -0.50*size` | `{}` | not_run |
| logic100_087 | logic100_087 | `+0.50*quality_component -0.50*size` | `{}` | not_run |
| logic100_088 | logic100_088 | `+0.50*quality_component -0.50*size` | `{}` | not_run |
| logic100_089 | logic100_089 | `+0.50*quality_component -0.50*size` | `{}` | not_run |
| logic100_090 | logic100_090 | `-0.50*quality_component -0.50*size` | `{}` | not_run |
| logic100_091 | logic100_091 | `-0.50*size +0.50*value_component` | `{}` | not_run |
| logic100_092 | logic100_092 | `-0.50*size +0.50*value_component` | `{}` | not_run |
| logic100_093 | logic100_093 | `-0.50*size +0.50*value_component` | `{}` | not_run |
| logic100_094 | logic100_094 | `+0.50*quality_metric_trend -0.50*size` | `{}` | not_run |
| logic100_095 | logic100_095 | `+0.50*quality_metric_trend -0.50*size` | `{}` | not_run |
| logic100_096 | logic100_096 | `+0.50*quality_metric_trend -0.50*size` | `{}` | not_run |
| logic100_097 | logic100_097 | `+0.50*quality_metric_trend -0.50*size` | `{}` | not_run |
| logic100_098 | logic100_098 | `-0.50*quality_metric_trend -0.50*size` | `{}` | not_run |
| logic100_099 | logic100_099 | `-0.50*size +0.50*value_metric_trend` | `{}` | not_run |
| logic100_100 | logic100_100 | `+0.50*turnover_shock +0.50*vol_regime` | `{}` | not_run |
