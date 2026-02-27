# Batch A: 新100单因子逻辑草案（2026-02-27）

状态：`draft_only`（仅研究，不运行）

目标：
- 本批只做“新逻辑优先”，避免把同逻辑反复调参当新因子。
- 与当前 `V1=36`（`momentum_v2/reversal_v2/turnover_shock/vol_regime/low_vol_v2`）做逻辑去重。
- 组织方式：`25` 个逻辑家族，单家族建议 `3-5` 个参数变体，合计约 `100` 单因子候选。

数据边界：
- 默认可用：`factor_ready` / `factor_ready_with_lag`。
- 默认隔离：`research_only_high_leakage_guard`（仅研究，不进主排名）。
- 依据：`FMP_FACTOR_FACTORY_DATA_CONSTRAINTS_2026-02-23.md`。

当前已核对数据可用性（工作站）：
- core: `data/fmp/ratios/value/*.pkl`, `data/fmp/ratios/quality/*.pkl`, `data/fmp/earnings/*.csv`, `data/fmp/institutional/*.jsonl`, `data/fmp/owner_earnings/*.jsonl`
- research_only: `data/fmp/research_only/*.jsonl`

---

## A. Core（默认可进主排名）25个逻辑

1. `value_ey_cross`（估值-盈利收益率横截面）
- 公式：`score = z(earnings_yield)`
- 数据：`ratios/value: earnings_yield`
- 参数建议：winsor 分位、zscore 窗口、行业中性开关、lag 日数

2. `value_fcfy_cross`（估值-FCF收益率横截面）
- 公式：`score = z(fcf_yield)`
- 数据：`ratios/value: fcf_yield`
- 参数建议：同上

3. `value_ev_ebitda_cross`（估值-EV/EBITDA反向）
- 公式：`score = z(ev_ebitda_yield)`
- 数据：`ratios/value: ev_ebitda_yield`
- 参数建议：同上

4. `value_composite_v1`（三估值合成）
- 公式：`score = mean(z(earnings_yield), z(fcf_yield), z(ev_ebitda_yield))`
- 数据：`ratios/value`
- 参数建议：组合权重模板、最小有效字段数、行业中性开关

5. `quality_roe_cross`（ROE质量）
- 公式：`score = z(roe)`
- 数据：`ratios/quality: roe`
- 参数建议：winsor、zscore、lag、行业中性

6. `quality_roa_cross`（ROA质量）
- 公式：`score = z(roa)`
- 数据：`ratios/quality: roa`
- 参数建议：同上

7. `quality_gm_cross`（毛利率质量）
- 公式：`score = z(gross_margin)`
- 数据：`ratios/quality: gross_margin`
- 参数建议：同上

8. `quality_cfoa_cross`（现金流质量）
- 公式：`score = z(cfo_to_assets)`
- 数据：`ratios/quality: cfo_to_assets`
- 参数建议：同上

9. `safety_de_inverse`（负债安全因子）
- 公式：`score = z(-debt_to_equity)`
- 数据：`ratios/quality: debt_to_equity`
- 参数建议：极值截断、行业中性、缺失阈值

10. `quality_composite_v1`（质量合成）
- 公式：`score = mean(z(roe), z(roa), z(gross_margin), z(cfo_to_assets), z(-debt_to_equity))`
- 数据：`ratios/quality`
- 参数建议：组件最小数、权重模板、lag

11. `value_quality_blend`（价值+质量）
- 公式：`score = 0.5*z(value_composite) + 0.5*z(quality_composite)`
- 数据：`ratios/value + ratios/quality`
- 参数建议：权重模板（如 60/40, 50/50, 40/60）、行业中性

12. `profitability_minus_leverage`（盈利-杠杆质量差）
- 公式：`score = z(cfo_to_assets) - z(debt_to_equity)`
- 数据：`ratios/quality`
- 参数建议：标准化方式、缺失处理、lag

13. `roe_trend`（ROE改善趋势）
- 公式：`score = z(roe_t - roe_{t-k})`
- 数据：`ratios/quality: roe`
- 参数建议：lookback k、平滑窗口、winsor

14. `roa_trend`（ROA改善趋势）
- 公式：`score = z(roa_t - roa_{t-k})`
- 数据：`ratios/quality: roa`
- 参数建议：同上

15. `margin_trend`（毛利率趋势）
- 公式：`score = z(gross_margin_t - gross_margin_{t-k})`
- 数据：`ratios/quality: gross_margin`
- 参数建议：同上

16. `cfo_quality_trend`（现金流质量趋势）
- 公式：`score = z(cfo_to_assets_t - cfo_to_assets_{t-k})`
- 数据：`ratios/quality: cfo_to_assets`
- 参数建议：同上

17. `deleveraging_trend`（去杠杆趋势）
- 公式：`score = z(-(debt_to_equity_t - debt_to_equity_{t-k}))`
- 数据：`ratios/quality: debt_to_equity`
- 参数建议：同上

18. `value_re_rating_ey`（估值重定价-盈利收益率变化）
- 公式：`score = z(earnings_yield_t - earnings_yield_{t-k})`
- 数据：`ratios/value: earnings_yield`
- 参数建议：lookback、平滑、极值处理

19. `value_re_rating_fcfy`（估值重定价-FCF收益率变化）
- 公式：`score = z(fcf_yield_t - fcf_yield_{t-k})`
- 数据：`ratios/value: fcf_yield`
- 参数建议：同上

20. `sue_eps_basic`（EPS惊喜）
- 公式：`surprise = (epsActual-epsEstimated)/max(|epsEstimated|,eps_floor)`
- 数据：`earnings_calendar.csv` / `earnings_surprises_YYYY.csv`
- 参数建议：event_age 上限、eps_floor、最小覆盖门槛

21. `sue_revenue_basic`（收入惊喜）
- 公式：`surprise = (revenueActual-revenueEstimated)/max(|revenueEstimated|,rev_floor)`
- 数据：`earnings_calendar.csv`
- 参数建议：event_age、rev_floor、缺失处理

22. `pead_short_window`（财报后漂移短窗）
- 公式：`score = surprise * I(1<=event_age<=h)`
- 数据：`earnings_* + price`
- 参数建议：h、惊喜标准化、公告日对齐

23. `institutional_ownership_change`（机构持仓变化）
- 公式：`score = z(ownershipPercentChange)`
- 数据：`institutional-ownership__symbol-positions-summary.jsonl`
- 参数建议：最小样本行、平滑窗口、极值处理

24. `institutional_breadth_change`（机构覆盖广度变化）
- 公式：`score = z(investorsHoldingChange)`
- 数据：同上
- 参数建议：同上

25. `owner_earnings_yield_proxy`（Owner Earnings收益率代理）
- 公式：`score = z(ownersEarningsPerShare / price)`
- 数据：`owner-earnings.jsonl + price`
- 参数建议：price 对齐窗、lag、极值处理

---

## B. Research-only（不进主排名，放 Batch B 候选池）

- `analyst_revision_eps`：`epsAvg_t - epsAvg_{t-k}`（`analyst-estimates.jsonl`）
- `target_revision`：`targetConsensus_t - targetConsensus_{t-k}`（`price-target-consensus.jsonl`）
- `rating_diffusion`：`(strongBuy+buy)-(sell+strongSell)`（`grades-consensus.jsonl`）

说明：上述属于 `research_only_high_leakage_guard`，需要单独 PIT 校验后才可进入默认主流程。

---

## 组合计数建议（先逻辑后参数）

- 25 逻辑家族，每家族参数数建议：
  - 15 个家族 × 4 变体 = 60
  - 10 个家族 × 4 变体 = 40
- 合计：100
- 原则：优先给不同逻辑分配名额，不在少数逻辑上做密集调参。

---

## 参考依据（机构/论文）

- Fama & French (2015), Five-Factor Model: https://doi.org/10.1016/j.jfineco.2014.10.010
- Novy-Marx (2010/2013), Gross Profitability: https://www.nber.org/papers/w15940
- Asness, Moskowitz, Pedersen (2013), Value and Momentum Everywhere: https://www.aqr.com/insights/research/journal-article/value-and-momentum-everywhere
- Asness, Frazzini, Pedersen (2019), Quality Minus Junk: https://doi.org/10.1007/s11142-018-9470-2
- Ahmed, Bu, Tsvetanov (2019), Factor Model Comparison: https://doi.org/10.1017/S0022109018000947

注：执行时仍以你仓内 FMP 可用字段和 PIT 规则为最高约束。
