# Public Factor Formula Library and Execution Constraints (V4)

Last updated: 2026-02-16 (US)
Purpose: provide a decision-grade, implementation-oriented public factor library and audit it against V4.

## 1) Scope and Evidence Standard

This document is not a marketing list of factor names. It is a practical reference for:
- formula-level implementation;
- execution constraints that determine net alpha;
- failure modes and minimum acceptance tests.

Evidence hierarchy:
- Tier A: primary academic/index methodology/factor library definitions;
- Tier B: large open-source framework implementations;
- Tier C: secondary summaries only for context.

Primary public sources (checked 2026-02-16):
- Ken French Data Library (FF factors, momentum, reversal definitions)
- MSCI methodology and index-family pages (Momentum/Quality/Min Vol/Enhanced Value)
- AQR dataset pages (QMJ/BAB)
- arXiv `101 Formulaic Alphas`
- Microsoft Qlib `Alpha158/Alpha360` code

## 2) Formula Conventions (for comparability)

Use consistent notation:
- `P_t`: close price at date `t`
- `r_t = ln(P_t / P_{t-1})` or simple return (must fix one convention)
- `z(x)`: cross-sectional z-score at rebalance date
- `rank(x)`: cross-sectional percentile rank at rebalance date
- `winsor(x, ql, qh)`: cross-sectional percentile winsorization
- all fundamentals must use PIT as-of filtering (`available_date <= signal_date`)

Default cross-sectional pipeline (baseline):
1. raw factor value
2. missing handling
3. winsorization
4. rank or z-score
5. optional neutralization (industry/size/beta)
6. portfolio construction

## 3) Extended Public Formula Library (Detailed)

Each factor includes: formula, expected sign, typical parameter range, and implementation caveats.

### 3.1 Value Family

1. `Earnings Yield (EP)`
- Formula: `EP = Earnings / MarketCap` or `1 / PE`
- Signal direction: higher is better
- Typical update: quarterly with PIT delay
- Caveats: negative earnings treatment must be explicit

2. `Book-to-Price (B/P)`
- Formula: `B/P = BookEquity / MarketCap`
- Direction: higher is better
- Caveats: financials accounting differences; stale book values

3. `Sales-to-Price (S/P)`
- Formula: `S/P = Sales / MarketCap`
- Direction: higher is better
- Caveats: low-margin businesses may look cheap but low quality

4. `Cashflow-to-Price (CF/P)`
- Formula: `OperatingCashflow / MarketCap`
- Direction: higher is better
- Caveats: one-off working-capital effects

5. `Free-cashflow Yield (FCFY)`
- Formula: `FCF / MarketCap`
- Direction: higher is better
- Caveats: capex cycle distortions

6. `EV/EBITDA Yield`
- Formula: `EBITDA / EV` (or inverse EV/EBITDA)
- Direction: higher yield is better
- Caveats: EV components freshness and debt timing

7. `Gross Profitability to Price`
- Formula: `GrossProfit / Assets` or `/MarketCap`
- Direction: higher is better
- Caveats: sector comparability

Recommended composite:
- `ValueComposite = mean(z(EP), z(B/P), z(FCFY), z(EBITDA/EV))`
- apply metric-level clipping before aggregation.

### 3.2 Quality / Profitability / Safety

8. `ROE`
- Formula: `NetIncome / BookEquity`
- Direction: higher better
- Caveats: leverage can inflate ROE

9. `ROA`
- Formula: `NetIncome / TotalAssets`
- Direction: higher better

10. `Gross Margin`
- Formula: `GrossProfit / Revenue`
- Direction: higher better

11. `CFO-to-Assets`
- Formula: `OperatingCashflow / TotalAssets`
- Direction: higher better

12. `Debt-to-Equity`
- Formula: `TotalDebt / BookEquity`
- Direction: lower better

13. `Earnings Variability`
- Formula: rolling std of EPS growth or profitability metrics
- Direction: lower better

14. `Accruals (quality drag)`
- Formula: `(NetIncome - CFO) / Assets`
- Direction: lower better

15. `Asset Growth` (often anti-quality / anti-value)
- Formula: `(Assets_t - Assets_{t-1}) / Assets_{t-1}`
- Direction: lower often better in cross-section

Recommended quality composite:
- `QualityComposite = z(ROE)+z(ROA)+z(GrossMargin)+z(CFO/Assets)-z(Debt/Equity)-z(Accruals)`

### 3.3 Momentum / Reversal / Trend

16. `Medium-term Momentum 6-1`
- Formula: `ln(P[t-21]/P[t-126])`
- Direction: higher better
- Common rebalance: monthly

17. `Medium-term Momentum 12-1`
- Formula: `ln(P[t-21]/P[t-252])`

18. `Risk-adjusted Momentum`
- Formula: `Mom / std(r, lookback)`

19. `Residual Momentum`
- Formula: momentum on residual return after market/industry beta removal
- Caveat: requires robust regression and enough history

20. `Short-term Reversal`
- Formula: `-sum(r_{t-1..t-k})`, `k=1..5`

21. `Intraday Reversal Proxy`
- Formula: `-mean((close/open)-1, k)`

22. `Long-term Reversal`
- Formula (proxy): `-(P[t-12m]/P[t-60m] - 1)` or FF-style long-horizon loser-minus-winner

### 3.4 Risk / Volatility / Defensive

23. `Historical Volatility`
- Formula: `-std(r, 20/60/120/252)`

24. `Downside Volatility`
- Formula: `-std(min(r,0), window)`

25. `Residual Volatility`
- Formula: `-std(r_i - beta_i r_m, window)`

26. `Beta`
- Formula: `cov(r_i,r_m)/var(r_m)`
- Direction in BAB context: lower beta preferred (with leverage scaling)

27. `Idiosyncratic Vol`
- Formula: residual std from multifactor regression

28. `Max Drawdown (rolling)`
- Formula: negative rolling max drawdown score
- Caveat: unstable for short windows

### 3.5 Size / Liquidity / Trading Frictions

29. `Size`
- Formula: `-ln(MarketCap)`

30. `Dollar Volume`
- Formula: `log(mean(price*volume, window))`
- Usually used as filter, not alpha signal

31. `Turnover`
- Formula: `volume / shares_outstanding`
- Direction: context-dependent (attention/liquidity effects)

32. `Amihud Illiquidity`
- Formula: `mean(|r_t| / dollar_volume_t, window)`
- Direction: generally lower liquidity premium is context-dependent; often used as risk control

33. `Bid-Ask Spread Proxy`
- Formula: Corwin-Schultz or high-low based proxies
- Mostly execution/cost model input

34. `Zero-trade / zero-volume frequency`
- Formula: `% days volume==0 over window`
- Usually exclusion/risk control

### 3.6 Earnings / Event / Analyst-related

35. `PEAD (SUE-based)`
- Formula: `SUE = (EPS_actual - EPS_est)/std(surprise over trailing N quarters)`
- Signal: `SUE` if `|SUE| > threshold`

36. `Analyst Revision`
- Formula: change in consensus EPS forecast over 1-3 months

37. `Earnings Announcement Return Drift`
- Formula: post-event cumulative abnormal return over fixed window

38. `Revenue Surprise`
- Formula: `(Revenue_actual - Revenue_est)/scale`

39. `Guidance Surprise` (if available)
- Formula: standardized management guidance change

### 3.7 Shareholder Yield / Capital Structure

40. `Dividend Yield`
- Formula: `dividend_per_share / price`

41. `Buyback Yield`
- Formula: `-(shares_outstanding_growth)` or repurchase amount / market cap

42. `Net Issuance`
- Formula: `% change in shares outstanding`
- Direction: lower issuance (or buyback) generally better

43. `Debt Issuance`
- Formula: `% change in total debt`
- Direction context-dependent, often lower better

### 3.8 Growth / Investment / Efficiency

44. `Sales Growth`
- Formula: `YoY sales growth`

45. `Earnings Growth`
- Formula: `YoY EPS growth`

46. `Investment (CMA-style proxy)`
- Formula: `asset_growth`

47. `Capex Intensity`
- Formula: `capex / assets` or `capex / sales`

48. `Inventory Growth`
- Formula: `Δinventory / assets`

49. `Receivables Growth`
- Formula: `Δreceivables / assets`

### 3.9 Price-Volume Formulaic Alpha Templates (AI generation pool)

50. `Price trend slope`
- Formula: OLS slope of log-price over window

51. `Distance to moving average`
- Formula: `(P - MA_n)/MA_n`

52. `Breakout strength`
- Formula: `(P - rolling_max_n)/rolling_max_n`

53. `Volume surprise`
- Formula: `volume / mean(volume,n)`

54. `Price-volume correlation`
- Formula: `corr(r, volume_change, n)`

55. `Volatility regime switch`
- Formula: `std_short/std_long`

56. `RSV/Stochastic`
- Formula: `(P - rolling_low)/(rolling_high-rolling_low)`

57. `Decay-weighted return`
- Formula: weighted sum of lagged returns with decay

58. `Rank interaction`
- Formula: `rank(mom)*rank(liquidity)` and variants

59. `Range-based reversal`
- Formula: negative normalized close location value in daily range

60. `Gap continuation/reversal`
- Formula: open-to-prev-close gap signal with conditional follow-through

## 4) Execution Constraint Framework (Detailed)

### 4.1 Time alignment and leakage control

Checklist:
- define signal timestamp exactly (`T close` vs `T+1 open`);
- use PIT as-of filtering for all fundamentals/events;
- enforce factor-specific lag when field semantics are uncertain;
- validate no-lookahead with synthetic lag tests.

### 4.2 Universe and tradability constraints

Minimum practical constraints:
- `MIN_PRICE` (e.g., $5)
- `MIN_DOLLAR_VOLUME` (e.g., $1M)
- `MIN_MARKET_CAP` (e.g., $500M)
- optional volatility and exclusion list controls

Critical note:
- if market-cap engine not loaded, `MIN_MARKET_CAP` may be nominal only.

### 4.3 Rebalance and holding

- choose rebalance schedule by half-life:
  - momentum/value/quality: monthly/3-4 weeks;
  - reversal/PEAD: higher frequency but stricter costs;
- holding period must align with signal decay profile.

### 4.4 Cost model realism

Minimum components:
- commissions/fees
- spread proxy
- market impact (`trade_size / dollar_volume`)
- volatility-linked widening
- short borrow fee when shorting is active

Required stress tests:
- 2x and 3x cost multipliers
- liquidity bucket stress

### 4.5 Portfolio construction

Minimum controls:
- explicit long/short selection fractions
- max name weight or risk budget
- turnover cap
- exposure checks (industry, beta, size)

### 4.6 Data-quality and delisting handling

- reject broken quotes and impossible prints;
- define delisting/no-data exit policy;
- report drop diagnostics by category.

## 5) V4 Mapping: Current Formulas and Constraints

Current V4 formulas (code):
- `momentum`: `backtest/factor_engine.py:123`
- `reversal`: `backtest/factor_engine.py:184`
- `low_vol`: `backtest/factor_engine.py:260`
- `quality`: `backtest/factor_engine.py:380`
- `value`: `backtest/factor_engine.py:401`
- `pead`: `backtest/pead_factor_cached.py:22`, `strategies/pead_v1/factor.py:107`

Current execution/control points (code):
- simulator/cost/delay: `backtest/execution_simulator.py:11`
- rebalance calendar generation: `backtest/backtest_engine.py:133`
- universe filters: `backtest/universe_builder.py:36`
- transform/neutralization: `backtest/factor_factory.py:154`

## 6) Defects in Current V4 (Prioritized)

Severity: `H` high, `M` medium, `L` low.

1. `H` Segmented workflow may not enforce market-cap filter
- Evidence: `scripts/run_segmented_factors.py:245`, `backtest/universe_builder.py:88`
- Root issue: `MIN_MARKET_CAP` needs a loaded market-cap engine.

2. `H` Entry-point drift across workflows
- Evidence:
  - rich parameter pass-through: `scripts/run_segmented_factors.py:138`
  - leaner strategy entrypoints: `strategies/value_v1/run.py:86`, `strategies/quality_v1/run.py:86`, `strategies/reversal_v1/run.py:85`
- Impact: Stage1/Stage2 comparability risk.

3. `M` Rank branch exits before residual neutralization path
- Evidence: `backtest/factor_factory.py:193`
- Impact: rank+neutralization expectation mismatch.

4. `M` Cost model still simplified for production net-alpha certainty
- Evidence: `backtest/cost_model.py:16`

5. `M` PEAD timing still coarse at date-level assumption
- Evidence: `strategies/pead_v1/config.py` alignment rules, `strategies/pead_v1/factor.py:72`

6. `M` Universe construction is serial and I/O-heavy
- Evidence: `backtest/universe_builder.py:51`

7. `L` Default position sizing remains binary (1/0/-1)
- Evidence: `backtest/factor_engine.py:568`

## 7) Minimum Validation Gates for Any New Factor

A candidate factor should pass all of:
1. Segmented stability: majority positive segments, no long negative streak.
2. OOS persistence: test IC not collapsing near zero.
3. Cost resilience: still positive under 2x costs.
4. Spec robustness: no sign flip under rank/zscore switch.
5. Sub-universe sanity: remains positive in at least one tighter liquidity/size subset.
6. Combination value: adds incremental portfolio IR after correlation control.

## 8) Ready-to-Use Research Card Template

Use this one-page card per factor:
- Factor ID / family / economic rationale
- Exact formula (with all transforms)
- Data fields + PIT logic
- Rebalance/holding/execution delay
- Universe constraints
- Cost model assumptions
- Segmented IC table
- Train/Test and Walk-forward summary
- Failure modes observed
- Decision (`reject/keep/combine/revisit`)

## 9) Sources (links)

- Ken French 5-factor:
  - https://mba.tuck.dartmouth.edu/pages/faculty/Ken.french/Data_Library/f-f_5_factors_2x3.html
- Ken French momentum:
  - https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html
- Ken French short-term reversal:
  - https://mba.tuck.dartmouth.edu/pages/Faculty/ken.french/Data_Library/det_st_rev_factor_daily.html
- Ken French long-term reversal:
  - https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_lt_rev_factor_daily.html
- Ken French OP definition:
  - https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/six_portfolios_me_op.html
- Ken French Inv definition:
  - https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/six_portfolios_me_inv.html
- MSCI Momentum methodology:
  - https://www.msci.com/indexes/documents/methodology/2_MSCI_Momentum_Indexes_Methodology_20250417.pdf
- MSCI Quality indexes:
  - https://www.msci.com/indexes/group/quality-indexes
- MSCI Minimum Volatility indexes:
  - https://www.msci.com/indexes/group/minimum-volatility-indexes
- MSCI Enhanced Value indexes:
  - https://www.msci.com/indexes/group/enhanced-value-indexes
- AQR datasets:
  - https://www.aqr.com/insights/datasets
- AQR QMJ:
  - https://www.aqr.com/Insights/Datasets/Quality-Minus-Junk-Factors-Daily
- AQR BAB:
  - https://www.aqr.com/insights/datasets/betting-against-beta-equity-factors-daily
- Formulaic Alphas:
  - https://arxiv.org/abs/1601.00991
- Qlib loader (Alpha feature definitions):
  - https://raw.githubusercontent.com/microsoft/qlib/main/qlib/contrib/data/loader.py
