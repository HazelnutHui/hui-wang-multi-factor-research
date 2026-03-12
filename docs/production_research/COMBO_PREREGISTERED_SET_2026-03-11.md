# Combo Preregistered Set (Cycle-1, 2026-03-11)

Last updated: 2026-03-11

Purpose:
- define a fixed combo candidate set before execution;
- avoid post-hoc tuning by locking candidate identities and weight logic.

Baseline:
- all candidates use the same execution shell:
  - `REBALANCE_FREQ=5`
  - `HOLDING_PERIOD=3`
  - `REBALANCE_MODE=None`
- all candidates use the same universe and neutralization settings from strategy yaml.

Input factor pool:
- AB-only from WF17 provisional grading:
  - `ocf_yield_ttm`
  - `fcf_yield_ttm`
  - `shareholder_yield`
  - `value_rerating_trend`
  - `ebitda_ev_yield`
  - `smallcap_seasonality_proxy`
  - `failed_breakout_reversal`
  - `trend_regime_switch`
  - `ownership_dispersion_proxy`
  - `gap_fill_propensity`
  - `liquidity_regime_switch`
  - `earnings_gap_strength`

Candidate set (12 total):
1. `combo_p0_ab12_equal_v1`  
   - file: `configs/strategies/combo_p0_ab12_equal_v1.yaml`
   - logic: equal-weight baseline over AB12.
2. `combo_p1_cluster_equal_v1`  
   - file: `configs/strategies/combo_p1_cluster_equal_v1.yaml`
   - logic: cluster-balance (valuation/cashflow vs behavior/regime vs specialty sleeves).
3. `combo_p2_value_quality_bias_v1`  
   - file: `configs/strategies/combo_p2_value_quality_bias_v1.yaml`
   - logic: valuation/cashflow tilted with moderate regime diversification.
4. `combo_p3_behavior_regime_bias_v1`  
   - file: `configs/strategies/combo_p3_behavior_regime_bias_v1.yaml`
   - logic: behavior/regime dominant, valuation kept as anchor.
5. `combo_p4_cashflow_dual_core_v1`  
   - file: `configs/strategies/combo_p4_cashflow_dual_core_v1.yaml`
   - logic: dual cashflow core (`ocf + fcf`) with valuation/risk overlays.
6. `combo_p5_low_turnover_conservative_v1`  
   - file: `configs/strategies/combo_p5_low_turnover_conservative_v1.yaml`
   - logic: emphasize slower-moving valuation/cashflow factors, lower fast-signal weights.
7. `combo_p6_robust_min_corr_v1`  
   - file: `configs/strategies/combo_p6_robust_min_corr_v1.yaml`
   - logic: more even spread to reduce concentration and pairwise dependency risk.
8. `combo_p7_no_earnings_gap_v1`  
   - file: `configs/strategies/combo_p7_no_earnings_gap_v1.yaml`
   - logic: excludes `earnings_gap_strength` to test event-field dependency sensitivity.
9. `combo_p8_value_light_behavior_v1`  
   - file: `configs/strategies/combo_p8_value_light_behavior_v1.yaml`
   - logic: valuation-first with light behavior sleeve.
10. `combo_p9_behavior_cashflow_barbell_v1`  
    - file: `configs/strategies/combo_p9_behavior_cashflow_barbell_v1.yaml`
    - logic: barbell between behavior cluster and cashflow cluster.
11. `combo_p10_defensive_stability_v1`  
    - file: `configs/strategies/combo_p10_defensive_stability_v1.yaml`
    - logic: defensive stability with low event-signal exposure.
12. `combo_p11_sparse_low_corr_v1`  
    - file: `configs/strategies/combo_p11_sparse_low_corr_v1.yaml`
    - logic: sparse diversified subset to reduce overlapping bet structure.

Design constraints satisfied:
- every configured factor weight is `<= 0.20`;
- every combo weight sum is `1.00`;
- no non-AB factor is introduced in cycle-1.

Execution policy for this set:
1. run `Layer2` for all 12;
2. remove `Layer2` fails;
3. run `Layer3` for survivors;
4. run production gates on top `<=3`;
5. promote only one primary + one backup.

Authoritative combo protocol:
- `COMBO_RESEARCH_BASELINE_2026-03-11.md`

