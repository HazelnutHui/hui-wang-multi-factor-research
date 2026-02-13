# Financial Modeling Prep (FMP)

Last checked: 2026-02-10

这份文档是 Financial Modeling Prep (FMP) 提供的 API 文档说明。

以下是文档中涉及的所有 API 接口及其对应内容的完整总结，按功能板块分类：

1. 公司搜索与基础信息 (Company Search & Directory)

Stock Symbol Search API: 搜索全球市场的股票代码。

Company Name Search API: 通过公司名称搜索股票代码。

CIK API: 获取上市公司的中央索引键 (CIK) 号码。

CUSIP API: 通过 CUSIP 号码检索证券信息。

ISIN API: 通过 ISIN 号码检索证券信息。

Stock Screener API: 根据市值、价格、行业、成交量等条件筛选股票。

Exchange Variants API: 查找某股票在哪些交易平台挂牌。

Company Symbols List API: 获取完整的证券代码列表。

Financial Statement Symbols List API: 具有财务报表数据的公司列表。

Symbol Changes List API: 跟踪公司更名、并购、拆分导致的符号变更。

ETF Symbol Search API: 专门搜索 ETF 的代码和名称。

Actively Trading List API: 列出当前正在交易的证券。

Earnings Transcript List API: 列出具有业绩说明会文本的公司。

Available (Exchanges/Sectors/Industries/Countries) API: 获取支持的所有交易所、板块、行业和国家列表。

2. 公司深度信息 (Company Information)

Company Profile Data API: 获取公司详细资料（市值、行业、首席执行官、描述等）。

Company Profile by CIK API: 通过 CIK 号码获取公司资料。

Company Notes API: 获取公司发行的票据/债券信息。

Stock Peer Comparison API: 检索同行业/同市值的对标公司。

Delisted Companies API: 检索从美国交易所退市的公司列表。

Company Employee Count (Historical) API: 获取公司当前及历史员工人数。

Company Market Cap (Historical/Batch) API: 获取公司当前、历史或批量市值数据。

Company Share Float & Liquidity (All) API: 获取公司流通股本及流动性数据。

Mergers & Acquisitions (Latest/Search) API: 检索最新或搜索特定的并购交易。

Company Executives API: 公司高管姓名、头衔、薪酬及背景资料。

Executive Compensation (Benchmark) API: 高管薪酬详情及行业基准对比。

3. 行情数据 (Quotes & Charts)

Stock Quote (Short/Batch) API: 实时股票行情（价格、涨跌幅、成交量）。

Aftermarket (Trade/Quote) API: 盘后交易的价格、规模和报价。

Stock Price Change API: 监测各时段（日、周、月、年）的价格变动百分比。

Exchange Stock Quotes API: 特定交易所内所有股票的实时报价。

Mutual Fund / ETF Price Quotes API: 共同基金和 ETF 的实时报价。

Commodities / Crypto / Forex / Index Quotes API: 商品、加密货币、外汇、指数的实时行情。

Stock Chart Light API: 简化的图表数据（价格、成交量）。

Stock Price and Volume Data API: 详细的历史收盘价及成交量。

Unadjusted / Dividend Adjusted Price Chart API: 未调整或经过股息调整的历史价格图。

Intraday Interval Stock Charts: 提供 1分钟、5分钟、15分钟、30分钟、1小时、4小时等不同频率的日内图表数据。

4. 财务报表与指标 (Statements & Metrics)

Income Statement / Balance Sheet / Cash Flow API: 详细的三大财务报表。

Latest Financial Statements API: 公司最新的财务报告数据。

TTM Financials (Income/Balance/Cashflow/Metrics) API: 滚动十二个月 (TTM) 的报表和指标。

Key Metrics API: 核心财务指标（市盈率、市净率、营收增长等）。

Financial Ratios API: 盈利能力、流动性、效率等各类财务比率。

Financial Scores API: 财务健康得分（如 Altman Z-Score, Piotroski Score）。

Owner Earnings API: 经过调整的股东盈余数据。

Enterprise Values API: 企业价值计算。

Financial Statement Growth API: 报表各项科目的增长率分析。

Financial Reports (Dates/JSON/XLSX) API: 10-K/10-Q 报告的归档日期、JSON 原文或 Excel 下载。

Revenue Segmentation (Product/Geographic) API: 按产品线或地理区域划分的营收数据。

As Reported Financial Statements API: 原始的、未经标准化的报表申报数据。

5. 宏观、股息与重大事件 (Economics, Dividends & Splits)

Treasury Rates API: 获取各期限的国债利率。

Economics Indicators API: GDP、失业率、通胀率等宏观经济指标。

Economic Data Releases Calendar API: 经济数据发布日历。

Market Risk Premium API: 市场风险溢价数据。

Dividends (Company/Calendar) API: 公司股息记录及未来派息日历。

Earnings (Report/Calendar) API: 业绩报告详情及业绩发布日历。

IPOs (Calendar/Disclosure/Prospectus) API: IPO 日历、披露文件及招股说明书。

Stock Splits (Details/Calendar) API: 股票拆分历史及未来拆分日历。

6. 业绩说明会与新闻 (Transcripts & News)

Earnings Transcript API (Latest/Search/Dates): 业绩发布会电话会议的文字记录。

FMP / General / Stock / Crypto / Forex News API: 来源于 FMP 或全球各大媒体的相关新闻。

Press Releases (Search) API: 搜索和获取官方新闻稿。

7. 机构持仓与分析师观点 (Institutional Ownership & Analyst)

Form 13F (Institutional Ownership) API: 机构持仓申报。

Filings Extract & Analytics API: 从申报文件中提取数据并进行分析。

Holder Performance / Industry Breakdown API: 机构持有人的表现及行业分布。

Financial Estimates API: 分析师对营收、EPS 等的预测。

Analyst Ratings (Snapshot/Historical) API: 综合分析师评级快照及历史变动。

Price Target (Summary/Consensus) API: 分析师目标价摘要及共识。

Stock Grades (Snapshot/Historical/Summary) API: 分析师对股票的评级（买入、持有、卖出等）。

8. 市场表现与技术指标 (Market Performance & Technicals)

Market/Industry Sector Performance API: 板块和行业表现快照及历史数据。

Sector/Industry PE Snapshot & Historical API: 板块和行业的市盈率估值情况。

Biggest Gainers / Losers / Top Traded API: 涨幅榜、跌幅榜及成交量排行榜。

Technical Indicators API: SMA (简单移动平均线)、EMA (指数平均线)、WMA、RSI、标准差、Williams %R、ADX 等技术分析指标。

9. 基金与 ETF (ETF & Mutual Funds)

ETF & Fund Holdings / Info API: ETF 及其持仓明细。

Country Allocation / Sector Weighting API: 基金的国家和行业分配权重。

ETF Asset Exposure API: 查看某股票被哪些 ETF 持有。

Mutual Fund & ETF Disclosures API: 基金披露文件搜索及持仓变动分析。

10. 合规与监管 (SEC Filings & Insider Trades)

SEC Filings (8-K, 10-K, 10-Q, Search) API: 实时检索 SEC 申报文件。

Industry Classification (SIC) API: 标准工业分类代码查询。

Insider Trading (Latest/Search/Statistics) API: 内部人士交易记录及统计。

Acquisition Ownership API: 收购导致的受益所有权变更记录。

11. 其它资产与市场 (Forex, Crypto, Commodities, DCF)

Forex / Crypto List, Quotes & Charts API: 外汇、加密货币的完整列表、报价和图表。

Commodities List, Quotes & Charts API: 商品（金、油、农产品等）列表、报价及图表。

DCF Valuation (Levered/Custom) API: 现金流折现 (DCF) 模型估值。

Market Hours / Holidays API: 全球交易所的营业时间及节假日。

12. 政治与社会责任 (Political & ESG)

Senate / House Financial Disclosures & Trading API: 美国参议院和众议院议员的财务披露及交易活动记录。

ESG Investment Search / Ratings / Benchmark API: 环境、社会和治理 (ESG) 得分及对比。

13. 其它特种 API (COT, Fundraisers, Bulk)

COT Report (Analysis/List) API: 持仓报告 (Commitment of Traders)。

Crowdfunding / Equity Offering API: 众筹项目及股权发行更新。

Bulk APIs: 针对公司资料、评级、DCF、财务指标、报表等提供 大批量数据下载 接口，适合大规模数据抓取。
