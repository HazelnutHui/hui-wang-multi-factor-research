# FMP 可调用数据总览（研究版单文件）

Last updated: 2026-03-07  
Scope: 基于你提供的 FMP Stable API 清单，重组为量化研究可直接执行的“可调用数据地图”。

---

## 1) 目标与使用边界

本文件用于回答三个问题：

1. FMP 到底“能调什么数据”（按研究场景分类）
2. 每类数据“怎么落地到本地目录”
3. 研究时“哪些接口优先、哪些只做扩展”

边界说明：

- 本文件是“可调用能力 + 研究落地”说明，不是策略结论文件。
- 不同步原始数据内容，只同步可调用范围、接口规则与落地规范。

---

## 2) 鉴权与调用规范

### 2.1 鉴权方式

- Header 鉴权：`apikey: <YOUR_API_KEY>`
- Query 鉴权：`?apikey=<YOUR_API_KEY>`
- 若 URL 已有参数，使用：`&apikey=<YOUR_API_KEY>`

### 2.2 安全要求（必须）

- 不在代码、文档、日志中写死明文 key。
- 统一使用环境变量：
  - `FMP_API_KEY`
- 示例（shell）：

```bash
export FMP_API_KEY="***"
curl -s "https://financialmodelingprep.com/stable/quote?symbol=AAPL&apikey=${FMP_API_KEY}"
```

### 2.3 通用请求建议

- 优先用 `stable` 路径。
- 批量接口优先（降低请求次数）。
- 全部响应落盘原始 JSON/JSONL，再做清洗层。
- 对分页接口固定 `page/limit`，并记录最后抓取时间。

---

## 3) 口径定义（先看这个）

为避免“数量对不上”，本文件固定两套口径：

1. 全量可调用口径（接口层）  
   - 基线采用历史探测快照：`156` callable stable endpoints（2026-02-23）。
   - 用途：评估“FMP 能调多少类接口”。

2. 字段口径（数据项层）  
   - 历史字段统计：`824` unique sampled fields（默认可用 `751`）。
   - 用途：评估“可用特征面有多大”。

3. 研究执行口径（流程层）  
   - 本文按 A/B/C 优先级组织，强调“当前研究应先调用哪些接口”。
   - 不等于全量枚举口径。

结论：

- “156”与“824”是两种不同维度，均保留为有效口径。
- 本文默认先服务研究执行，再回看全量接口覆盖。

---

## 4) 全量可调用家族（官方目录对齐）

你给的官方清单已经覆盖下列家族，本文件按研究方式重组，不再逐字复制官网说明：

1. Company Search
2. Stock Directory
3. Company Information
4. Quote
5. Statements
6. Charts
7. Economics
8. Earnings / Dividends / Splits
9. Earnings Transcript
10. News
11. Form 13F
12. Analyst
13. Market Performance
14. Technical Indicators
15. ETF and Mutual Funds
16. SEC Filings
17. Insider Trades
18. Indexes
19. Market Hours
20. Commodity
21. Discounted Cash Flow
22. Forex
23. Crypto
24. Senate
25. ESG
26. Commitment of Traders
27. Fundraisers
28. Bulk

如果后续要做“逐 endpoint 全量字典”，统一以 `configs/research/fmp_probe_targets_coverage_v1.json` 为机器基线，不再手工维护多份清单。

---

## 5) 研究优先级分层（A/B/C）

### A 层（当前 100 因子核心）

1. Statements/TTM/Growth
2. Ratios / Key Metrics / Financial Scores
3. Earnings / Earnings Calendar / Earnings Surprises
4. Market Cap / Historical Market Cap
5. Institutional Ownership（13F核心）
6. EOD 价格（含复权/非复权版本）
7. Owner Earnings

### B 层（增强研究）

1. Analyst（estimates/grades/targets）
2. Transcript / News
3. ETF & Fund 持仓
4. SEC filings（8-K/10-K/10-Q检索）
5. Insider trading

### C 层（扩展宏观与跨资产）

1. Economics（GDP/利率/日历）
2. Crypto/Forex/Commodity
3. Senate/House/ESG/COT/Fundraisers

---

## 6) 核心域接口清单（按研究使用）

## 6.1 证券主数据 / 股票池构建

关键接口：

- `GET /stable/stock-list`
- `GET /stable/financial-statement-symbol-list`
- `GET /stable/actively-trading-list`
- `GET /stable/delisted-companies?page=0&limit=100`
- `GET /stable/search-symbol?query=AAPL`
- `GET /stable/search-name?query=AA`
- `GET /stable/search-cik?cik=320193`
- `GET /stable/search-cusip?cusip=037833100`
- `GET /stable/search-isin?isin=US0378331005`
- `GET /stable/company-screener?...`
- `GET /stable/search-exchange-variants?symbol=AAPL`

研究作用：

- 初始股票池、活跃交易过滤、退市过滤。
- 标识符映射（symbol/cik/cusip/isin）。
- 交易所和 share class 对齐。

本地建议目录：

- `data/fmp/security_master/`
- `data/fmp/universe/`

---

## 6.2 公司画像与横截面基本信息

关键接口：

- `GET /stable/profile?symbol=AAPL`
- `GET /stable/profile-cik?cik=320193`
- `GET /stable/stock-peers?symbol=AAPL`
- `GET /stable/company-notes?symbol=AAPL`
- `GET /stable/employee-count?symbol=AAPL`
- `GET /stable/historical-employee-count?symbol=AAPL`
- `GET /stable/key-executives?symbol=AAPL`
- `GET /stable/governance-executive-compensation?symbol=AAPL`

研究作用：

- 行业/公司属性扩展特征。
- peer group 参考与行业比较。

本地建议目录：

- `data/fmp/profile/`
- `data/fmp/corporate_governance/`

---

## 6.3 市值与流动性（容量相关）

关键接口：

- `GET /stable/market-capitalization?symbol=AAPL`
- `GET /stable/market-capitalization-batch?symbols=AAPL,MSFT,GOOG`
- `GET /stable/historical-market-capitalization?symbol=AAPL`
- `GET /stable/shares-float?symbol=AAPL`
- `GET /stable/shares-float-all?page=0&limit=1000`

研究作用：

- 可交易性过滤（市值门槛、容量约束）。
- 小盘暴露/流动性暴露控制。

本地建议目录：

- `data/fmp/market_cap_history/`
- `data/fmp/liquidity/`

---

## 6.4 财报与基本面（最核心）

关键接口（单标的）：

- `GET /stable/income-statement?symbol=AAPL`
- `GET /stable/balance-sheet-statement?symbol=AAPL`
- `GET /stable/cash-flow-statement?symbol=AAPL`
- `GET /stable/income-statement-ttm?symbol=AAPL`
- `GET /stable/balance-sheet-statement-ttm?symbol=AAPL`
- `GET /stable/cash-flow-statement-ttm?symbol=AAPL`
- `GET /stable/key-metrics?symbol=AAPL`
- `GET /stable/ratios?symbol=AAPL`
- `GET /stable/key-metrics-ttm?symbol=AAPL`
- `GET /stable/ratios-ttm?symbol=AAPL`
- `GET /stable/financial-scores?symbol=AAPL`
- `GET /stable/owner-earnings?symbol=AAPL`
- `GET /stable/enterprise-values?symbol=AAPL`
- `GET /stable/financial-growth?symbol=AAPL`

关键接口（增长拆分）：

- `GET /stable/income-statement-growth?symbol=AAPL`
- `GET /stable/balance-sheet-statement-growth?symbol=AAPL`
- `GET /stable/cash-flow-statement-growth?symbol=AAPL`

关键接口（as-reported）：

- `GET /stable/income-statement-as-reported?symbol=AAPL`
- `GET /stable/balance-sheet-statement-as-reported?symbol=AAPL`
- `GET /stable/cash-flow-statement-as-reported?symbol=AAPL`
- `GET /stable/financial-statement-full-as-reported?symbol=AAPL`

研究作用：

- 价值、质量、盈利、成长、稳健性、现金流因子主来源。
- TTM 与 as-reported 用于减少口径偏差。

本地建议目录：

- `data/fmp/statements/`
- `data/fmp/ratios/value/`
- `data/fmp/ratios/quality/`
- `data/fmp/owner_earnings/`

---

## 6.5 财报日期与事件时点（PIT关键）

关键接口：

- `GET /stable/financial-reports-dates?symbol=AAPL`
- `GET /stable/latest-financial-statements?page=0&limit=250`
- `GET /stable/earnings?symbol=AAPL`
- `GET /stable/earnings-calendar`
- `GET /stable/earnings-surprises-bulk?year=2025`

研究作用：

- PIT 对齐（公告日可得性）。
- earnings surprise / post-earnings drift 研究。

本地建议目录：

- `data/fmp/earnings/`
- `data/fmp/earnings_history/`

---

## 6.6 价格/成交量/行情

EOD/历史：

- `GET /stable/historical-price-eod/light?symbol=AAPL`
- `GET /stable/historical-price-eod/full?symbol=AAPL`
- `GET /stable/historical-price-eod/non-split-adjusted?symbol=AAPL`
- `GET /stable/historical-price-eod/dividend-adjusted?symbol=AAPL`
- `GET /stable/eod-bulk?date=2024-10-22`

实时与批量报价：

- `GET /stable/quote?symbol=AAPL`
- `GET /stable/quote-short?symbol=AAPL`
- `GET /stable/batch-quote?symbols=AAPL`
- `GET /stable/batch-quote-short?symbols=AAPL`
- `GET /stable/batch-exchange-quote?exchange=NASDAQ`

盘后：

- `GET /stable/aftermarket-trade?symbol=AAPL`
- `GET /stable/aftermarket-quote?symbol=AAPL`
- `GET /stable/batch-aftermarket-trade?symbols=AAPL`
- `GET /stable/batch-aftermarket-quote?symbols=AAPL`

研究作用：

- 收益构建、换手、波动、流动性代理、成本模拟输入。

本地建议目录：

- `data/prices*/`（你现有价格主路径）
- `data/fmp/quotes/`（可选）

---

## 6.7 分红、拆股、IPO、并购

关键接口：

- `GET /stable/dividends?symbol=AAPL`
- `GET /stable/dividends-calendar`
- `GET /stable/splits?symbol=AAPL`
- `GET /stable/splits-calendar`
- `GET /stable/ipos-calendar`
- `GET /stable/ipos-disclosure`
- `GET /stable/ipos-prospectus`
- `GET /stable/mergers-acquisitions-latest?page=0&limit=100`
- `GET /stable/mergers-acquisitions-search?name=Apple`

研究作用：

- 复权逻辑核验、事件研究、交易可得性变化。

---

## 6.8 13F 机构持仓（你当前重点）

关键接口：

- `GET /stable/institutional-ownership/latest?page=0&limit=100`
- `GET /stable/institutional-ownership/extract?cik=...&year=...&quarter=...`
- `GET /stable/institutional-ownership/dates?cik=...`
- `GET /stable/institutional-ownership/extract-analytics/holder?symbol=AAPL&year=2023&quarter=3&page=0&limit=10`
- `GET /stable/institutional-ownership/holder-performance-summary?cik=...`
- `GET /stable/institutional-ownership/holder-industry-breakdown?cik=...&year=...&quarter=...`
- `GET /stable/institutional-ownership/symbol-positions-summary?symbol=AAPL&year=2023&quarter=3`
- `GET /stable/institutional-ownership/industry-summary?year=2023&quarter=3`

研究作用：

- 机构拥挤度、持仓集中度、持仓变化、机构行为因子。
- `crowding_turnover_x_inst` 这类因子的关键输入域。

本地建议目录：

- `data/fmp/institutional/`

---

## 6.9 Analyst 与评级

关键接口：

- `GET /stable/analyst-estimates?symbol=AAPL&period=annual&page=0&limit=10`
- `GET /stable/ratings-snapshot?symbol=AAPL`
- `GET /stable/ratings-historical?symbol=AAPL`
- `GET /stable/price-target-summary?symbol=AAPL`
- `GET /stable/price-target-consensus?symbol=AAPL`
- `GET /stable/grades?symbol=AAPL`
- `GET /stable/grades-historical?symbol=AAPL`
- `GET /stable/grades-consensus?symbol=AAPL`

研究作用：

- 预期修正、分析师分歧、评级变更冲击。

本地建议目录：

- `data/fmp/research_only/analyst/`

---

## 6.10 Transcript 与 News

Transcript：

- `GET /stable/earning-call-transcript-latest`
- `GET /stable/earning-call-transcript?symbol=AAPL&year=2020&quarter=3`
- `GET /stable/earning-call-transcript-dates?symbol=AAPL`
- `GET /stable/earnings-transcript-list`

News：

- `GET /stable/fmp-articles?page=0&limit=20`
- `GET /stable/news/general-latest?page=0&limit=20`
- `GET /stable/news/press-releases-latest?page=0&limit=20`
- `GET /stable/news/stock-latest?page=0&limit=20`
- `GET /stable/news/stock?symbols=AAPL`

研究作用：

- 文本因子、事件驱动特征、情绪/主题扩展。

本地建议目录：

- `data/fmp/research_only/transcript/`
- `data/fmp/research_only/news/`

---

## 6.11 经济与宏观

关键接口：

- `GET /stable/treasury-rates`
- `GET /stable/economic-indicators?name=GDP`
- `GET /stable/economic-calendar`
- `GET /stable/market-risk-premium`

研究作用：

- 宏观 regime、风险溢价条件过滤。

本地建议目录：

- `data/fmp/research_only/macro/`

---

## 6.12 ETF/基金

关键接口：

- `GET /stable/etf/holdings?symbol=SPY`
- `GET /stable/etf/info?symbol=SPY`
- `GET /stable/etf/asset-exposure?symbol=AAPL`
- `GET /stable/etf/sector-weightings?symbol=SPY`
- `GET /stable/funds/disclosure?symbol=VWO&year=2023&quarter=4`
- `GET /stable/funds/disclosure-holders-latest?symbol=AAPL`

研究作用：

- 被动资金暴露、主题拥挤、成分再平衡冲击。

本地建议目录：

- `data/fmp/research_only/funds/`

---

## 6.13 SEC / Insider

SEC：

- `GET /stable/sec-filings-financials?...`
- `GET /stable/sec-filings-search/form-type?...`
- `GET /stable/sec-filings-search/symbol?...`
- `GET /stable/sec-profile?symbol=AAPL`

Insider：

- `GET /stable/insider-trading/latest?page=0&limit=100`
- `GET /stable/insider-trading/search?page=0&limit=100`
- `GET /stable/insider-trading/statistics?symbol=AAPL`

研究作用：

- 公司事件、合规披露、内部人交易扩展信号。

本地建议目录：

- `data/fmp/research_only/sec/`
- `data/fmp/research_only/insider/`

---

## 6.14 Bulk（工业化下载优先）

关键接口（高优先）：

- `GET /stable/key-metrics-ttm-bulk`
- `GET /stable/ratios-ttm-bulk`
- `GET /stable/income-statement-bulk?year=YYYY&period=Q1`
- `GET /stable/balance-sheet-statement-bulk?year=YYYY&period=Q1`
- `GET /stable/cash-flow-statement-bulk?year=YYYY&period=Q1`
- `GET /stable/income-statement-growth-bulk?year=YYYY&period=Q1`
- `GET /stable/balance-sheet-statement-growth-bulk?year=YYYY&period=Q1`
- `GET /stable/cash-flow-statement-growth-bulk?year=YYYY&period=Q1`
- `GET /stable/earnings-surprises-bulk?year=YYYY`
- `GET /stable/eod-bulk?date=YYYY-MM-DD`

研究作用：

- 覆盖面和速度显著高于逐 symbol 拉取。
- 适合 nightly backfill 与大规模补齐。

---

## 7) 与当前 v4 目录映射（你现有口径）

当前已确认（工作站）存在域：

- `data/fmp/earnings`
- `data/fmp/earnings_history`
- `data/fmp/institutional`
- `data/fmp/market_cap_history`
- `data/fmp/owner_earnings`
- `data/fmp/ratios`（含 `quality`、`value`）
- `data/fmp/research_only`
- `data/fmp/statements`

建议保持：

- 核心生产域：`data/fmp/<domain>/...`
- 扩展研究域：`data/fmp/research_only/<domain>/...`

---

## 8) PIT 与研究口径控制（必须）

1. 使用可得日期而非报告期做交易对齐。
2. 财报、机构持仓、分析师数据设置发布时间滞后。
3. 成分股、退市、交易状态用同一时点快照。
4. 价格复权口径固定（拆股/分红是否调整必须全流程一致）。
5. 成本模型与可交易池参数固定后再比 IC。

---

## 9) 数据质量检查最小清单

每次更新至少检查：

1. 覆盖率：`unique_symbols / target_symbols`
2. 时点完整性：最近 N 期是否连续
3. 主键重复：`(symbol, date|year|quarter)` 唯一性
4. 字段类型漂移：数值字段是否变字符串
5. 空值比例：关键字段（eps/revenue/marketCap/...）
6. 异常值：极端跳变与单位突变
7. 域间一致性：ratios 与 statements 关键字段方向一致

---

## 10) 研究下载建议（100 因子场景）

优先顺序：

1. `ratios-ttm-bulk`、`key-metrics-ttm-bulk`
2. `income/balance/cashflow`（含 growth）
3. `historical-market-capitalization` / batch
4. `earnings + earnings-calendar + earnings-surprises-bulk`
5. `institutional-ownership/*`（按 quarter）
6. `owner-earnings`
7. 扩展域（analyst/transcript/news）

补数策略：

- 先 bulk 全量，再 symbol 增量修补。
- 缺失集中在少数 symbol 时，用单标的接口补洞。
- 所有补数写 manifest（时间、接口、参数、文件数、成功率）。

---

## 11) 典型调用示例（可直接改造脚本）

### 9.1 symbol 搜索

```bash
curl -s "https://financialmodelingprep.com/stable/search-symbol?query=AAPL&apikey=${FMP_API_KEY}"
```

### 9.2 TTM ratios

```bash
curl -s "https://financialmodelingprep.com/stable/ratios-ttm?symbol=AAPL&apikey=${FMP_API_KEY}"
```

### 9.3 earnings surprises（批量）

```bash
curl -s "https://financialmodelingprep.com/stable/earnings-surprises-bulk?year=2025&apikey=${FMP_API_KEY}"
```

### 9.4 机构持仓摘要（symbol+季度）

```bash
curl -s "https://financialmodelingprep.com/stable/institutional-ownership/symbol-positions-summary?symbol=AAPL&year=2023&quarter=3&apikey=${FMP_API_KEY}"
```

---

## 12) 已知实现注意点

1. 部分接口字段可能存在拼写/编码异常（例如文档示例里的脏字符），落地时必须做字段白名单映射。
2. 同名接口在不同资产类（股票/指数/外汇/商品）参数含义可能不同，必须按资产域分开处理。
3. bulk 与单标的返回结构可能不一致，清洗层不要复用同一解析器。
4. 文档可调用不代表当下每个账号权限一致，运行前做 probe。

---

## 13) 本项目建议的“单文件使用方式”

研究人员只需要先看本文件，然后按顺序：

1. 选研究域（A/B/C）
2. 选对应接口
3. 对齐本地落地目录
4. 通过 PIT 与 DQ 清单
5. 再进入因子回测流程

本文件与以下文档联动：

- `docs/production_research/BATCHA100_FMP_DOWNLOAD_REQUIREMENTS_2026-02-28.md`
- `docs/production_research/BATCHA100_DATA_READINESS_2026-02-27.md`
- `STATUS.md`
