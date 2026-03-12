# WF17 Single-Factor Provisional Grading (L2 + L3)

As-of: 2026-03-11

## Scope
- This file summarizes the 17-factor single-factor gate after:
  - `SF-L2` fixed train/test run:
    - `runs/sf_l2_17_20260308_200146`
  - `SF-L3` walk-forward run:
    - `runs/sf_l3_wf_17_20260309_212116`
- `SF-L3` setup:
  - train `3y`, test `1y`, test years `2013..2025` (`13` windows per factor, `221` tasks total)
  - completion: `221/221`, all `rc=0`

## Rule Used (Provisional)
- `L2 pass`: `l2_test_ic > 0`
- `L3 pass`:
  - positive-window ratio `>= 60%`
  - max consecutive negative windows `< 3`
- Provisional grade (cost gate not applied yet):
  - `A`: L2 pass + L3 pass + `l2_test_ic >= 0.006`
  - `B`: L2 pass + L3 pass + `0 < l2_test_ic < 0.006`
  - `C`: otherwise

## Summary Counts
- `A=7`
- `B=5`
- `C=5`

## Factor Table
| factor | L2 test_ic | WF mean test_ic | WF pos_ratio | WF max_consec_neg | grade_provisional |
|---|---:|---:|---:|---:|:---:|
| ocf_yield_ttm | 0.010748 | 0.012937 | 84.62% | 1 | A |
| fcf_yield_ttm | 0.009918 | 0.010575 | 84.62% | 1 | A |
| shareholder_yield | 0.008559 | 0.009567 | 84.62% | 1 | A |
| value_rerating_trend | 0.008423 | 0.010488 | 100.00% | 0 | A |
| ebitda_ev_yield | 0.007641 | 0.009487 | 92.31% | 1 | A |
| smallcap_seasonality_proxy | 0.006803 | 0.005048 | 69.23% | 2 | A |
| failed_breakout_reversal | 0.006040 | 0.003736 | 61.54% | 2 | A |
| trend_regime_switch | 0.004599 | 0.011803 | 84.62% | 1 | B |
| ownership_dispersion_proxy | 0.003813 | 0.003890 | 92.31% | 1 | B |
| gap_fill_propensity | 0.001497 | 0.002927 | 84.62% | 2 | B |
| liquidity_regime_switch | 0.000749 | 0.003691 | 84.62% | 1 | B |
| earnings_gap_strength | 0.000411 | -0.003485 | 61.54% | 2 | B |
| ownership_acceleration | 0.002986 | -0.000125 | 46.15% | 3 | C |
| large_gap_reversal | 0.001938 | 0.000766 | 69.23% | 3 | C |
| fcf_growth_persistence | 0.000985 | 0.001438 | 76.92% | 3 | C |
| nwc_change_inverse | -0.000527 | 0.000642 | 46.15% | 3 | C |
| risk_on_off_breadth | -0.007821 | -0.003970 | 23.08% | 5 | C |

## Notes
- This is a provisional L2/L3 grading snapshot for combo admission prep.
- Cost-adjusted gate is still required before final promotion.
- Source JSON artifact (workstation runtime repo):
  - `runs/sf_l3_wf_17_20260309_212116/wf17_l2_l3_grade_provisional.json`
