# BatchA100 Logic100 Blueprint (2026-02-28)

As-of: 2026-02-28  
Status: historical draft (deprecated for runtime SSOT)

> Deprecated note (2026-02-28): this draft contains pair/tri-style constructions and is kept only for traceability.
> Use `BATCHA100_LOGIC100_FORMAL_V1_2026-02-28.md/.csv` as current design SSOT.

Purpose:
- define 100 distinct single-factor logics (not parameter variants),
- maximize cross-dimension coverage under current v4 process,
- align with FMP callable data and lag-safe implementation.

## Design Rules

- 100 entries are formula-distinct logics.
- no "same formula with minor parameter change" counted as new logic.
- each logic is first run in one canonical spec; parameter expansion only after fast-screen ranking.
- all fundamental/event signals must apply explicit lag guard.

## Logic Set (100)

### A. Price/Trend/Reversal (1-20)

1. `ret_12_1`: `log(P[t-21]/P[t-252])`
2. `ret_6_1`: `log(P[t-21]/P[t-126])`
3. `ret_3_1`: `log(P[t-5]/P[t-63])`
4. `st_rev_5d`: `-sum(r[t-5:t-1])`
5. `st_rev_2d`: `-sum(r[t-2:t-1])`
6. `intramonth_rev`: `-sum(r[t-10:t-1])`
7. `trend_tstat_60`: `slope(log(P),60)/stderr`
8. `trend_tstat_120`: `slope(log(P),120)/stderr`
9. `breakout_252`: `(P[t]-rolling_max(252))/rolling_max(252)`
10. `distance_ma_200`: `(P[t]-MA200)/MA200`
11. `distance_ma_50`: `(P[t]-MA50)/MA50`
12. `ma_cross_strength`: `(MA50-MA200)/MA200`
13. `vol_adj_mom`: `ret_12_1 / vol_63`
14. `idio_mom`: residual-return momentum vs benchmark
15. `overnight_mom`: `sum(overnight_ret,63)`
16. `intraday_reversal_proxy`: `sum(close_to_close - overnight,20)`
17. `gap_reversion`: `-zscore(open_gap_20d)`
18. `momentum_crash_guard`: `ret_12_1 * (1 - tail_risk_21)`
19. `52w_high_proximity`: `P[t]/max(P,252)`
20. `52w_low_distance`: `P[t]/min(P,252)`

### B. Liquidity/Turnover/Capacity (21-35)

21. `turnover_shock`: `log(ADV20/ADV120)`
22. `turnover_trend`: `zscore(diff(log(ADV),20),252)`
23. `amihud_illiquidity`: `mean(|r|/dollar_volume,20)`
24. `liquidity_recovery`: `-delta(amihud,20)`
25. `dollar_volume_rank`: `rank(log(ADV60))`
26. `volume_surprise`: `(vol - MA20(vol))/std20(vol)`
27. `volume_price_divergence`: `zscore(vol_chg_20 - |ret_20|)`
28. `high_low_spread_proxy`: `mean((H-L)/C,20)`
29. `liquidity_beta_proxy`: beta to market liquidity proxy
30. `turnover_vol_ratio`: `ADV20 / vol_20`
31. `capacity_penalized_mom`: `ret_12_1 - lambda*illiquidity`
32. `small_liquid_interaction`: `(-size_z) * liquidity_z`
33. `flow_persistence_proxy`: `autocorr(dollar_flow,20)`
34. `crowding_proxy`: `zscore(turnover)+zscore(inst_holders_pct)`
35. `liquidity_regime_switch`: regime state from turnover+vol

### C. Volatility/Risk/Downside (36-50)

36. `low_vol_20`: `-std(r,20)`
37. `low_vol_60`: `-std(r,60)`
38. `downside_vol_60`: `-std(min(r,0),60)`
39. `semi_variance_ratio`: `downside_var/total_var`
40. `idiosyncratic_vol`: `-std(residual_r,63)`
41. `beta_252`: `-beta(stock,market,252)`
42. `beta_instability`: `-std(beta_rolling,126)`
43. `skewness_60`: `skew(r,60)`
44. `kurtosis_60`: `-kurtosis(r,60)`
45. `left_tail_5pct`: `-ES_5%(r,126)`
46. `max_drawdown_126`: `-MDD(126)`
47. `drawdown_recovery_speed`: recovery slope after drawdown
48. `vol_of_vol`: `-std(rolling_std_20,126)`
49. `crash_sensitivity_proxy`: downside beta to market crashes
50. `risk_parity_signal`: `ret_63 / vol_63`

### D. Value/Multiple Re-rating (51-65)

51. `earnings_yield_ttm`: `EBIT_or_EPS / MarketCap`
52. `fcf_yield_ttm`: `FCF / MarketCap`
53. `ocf_yield_ttm`: `OCF / MarketCap`
54. `sales_yield_ttm`: `Revenue / EnterpriseValue`
55. `ebitda_yield_ttm`: `EBITDA / EV`
56. `book_to_market`: `BookEquity / MarketCap`
57. `tangible_bm`: `TangibleBook / MarketCap`
58. `shareholder_yield`: `buyback_yield + dividend_yield - dilution`
59. `dividend_yield`: `DPS / Price`
60. `net_payout_yield`: `(buyback-dividend-adjusted)/MarketCap`
61. `value_composite_q`: robust z-score composite of value metrics
62. `value_trend_4q`: `delta(value_composite,4q)`
63. `cheap_quality`: `value_z + quality_z`
64. `deep_value_safety`: `value_z - leverage_z`
65. `relative_value_sector_neutral`: sector-neutral value z-score

### E. Quality/Profitability/Balance Sheet (66-80)

66. `gross_profitability`: `GrossProfit / Assets`
67. `operating_profitability`: `OperatingIncome / Equity`
68. `roa_ttm`: `NetIncome / Assets`
69. `roe_ttm`: `NetIncome / Equity`
70. `roic_ttm`: `NOPAT / InvestedCapital`
71. `cfo_to_assets`: `OCF / Assets`
72. `accruals_total`: `(NI-OCF)/Assets` (negative preferred)
73. `asset_turnover`: `Revenue / Assets`
74. `gross_margin`: `GrossProfit / Revenue`
75. `margin_stability`: `-std(gross_margin,12q)`
76. `earnings_stability`: `-std(NI_margin,12q)`
77. `leverage_inverse`: `-Debt/Equity`
78. `interest_coverage`: `EBIT / InterestExpense`
79. `piotroski_fscore_proxy`: additive accounting quality score
80. `quality_composite_qmj_proxy`: profitability+growth+safety+payout

### F. Growth/Revision/Fundamental Trend (81-90)

81. `revenue_growth_yoy`: `Rev_ttm / Rev_ttm_1y - 1`
82. `eps_growth_yoy`: `EPS_ttm / EPS_ttm_1y - 1`
83. `fcf_growth_yoy`: `FCF_ttm / FCF_ttm_1y - 1`
84. `asset_growth_anomaly`: `-(Assets_t / Assets_t-1 - 1)`
85. `capex_intensity_change`: `delta(CAPEX/Assets)`
86. `working_capital_change`: `-delta(NWC/Assets)`
87. `profitability_trend`: `delta(ROA,4q)`
88. `margin_trend`: `delta(GrossMargin,4q)`
89. `deleveraging_trend`: `-delta(Debt/Equity,4q)`
90. `investment_conservatism`: `-(asset_growth + capex_growth)`

### G. Event/Expectation/Ownership (91-100)

91. `sue_eps`: standardized unexpected EPS
92. `sue_revenue`: standardized unexpected revenue
93. `pead_short`: post-earnings drift score (1-20 trading days)
94. `pead_medium`: post-earnings drift score (21-60 trading days)
95. `earnings_gap_strength`: opening gap around earnings vs history
96. `institutional_ownership_delta`: change in institutional ownership pct
97. `institutional_breadth_delta`: change in holder count breadth
98. `owner_earnings_yield`: owner earnings / market cap
99. `ownership_value_interaction`: ownership_delta * value_z
100. `event_quality_interaction`: sue_eps * quality_z

## Mapping To Literature / Institutional Practice

- Value/size/profitability/investment backbone: Fama-French style factor literature.
- Quality block: QMJ-style profitability/safety/payout construction.
- Liquidity block: Amihud/Pastor-Stambaugh style liquidity pricing ideas.
- Momentum/reversal/event: broad practitioner and academic evidence across medium-term momentum, short-term reversal, and PEAD.

## Reference Links

- Fama/French factor construction (Ken French data library):  
  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library/f-f_factors.html
- Fama/French five-factor description:  
  https://mba.tuck.dartmouth.edu/pages/faculty/Ken.french/Data_Library/f-f_5_factors_2x3.html
- Fama and French (2015) five-factor model entry:  
  https://econpapers.repec.org/RePEc:eee:jfinec:v:116:y:2015:i:1:p:1-22
- Quality Minus Junk (AQR working paper page):  
  https://www.aqr.com/Insights/Research/Working-Paper/Quality-Minus-Junk
- Novy-Marx gross profitability premium (NBER):  
  https://www.nber.org/papers/w15940
- Liquidity risk and expected returns (NBER):  
  https://www.nber.org/papers/w8462
- Amihud illiquidity revisit (EconPapers):  
  https://econpapers.repec.org/RePEc:now:jnlcfr:104.00000073
- Momentum strategy evidence (NBER):  
  https://www.nber.org/papers/w7159
- Momentum strategies (NBER):  
  https://www.nber.org/papers/w5375

## Implementation Note

This blueprint is SSOT for logic intent only.  
Execution specs (actual factor keys, lag gates, and run policy) must be generated from this file into:
- `configs/research/factor_factory_policy_batchA100_logic100_v1.json`
- `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
