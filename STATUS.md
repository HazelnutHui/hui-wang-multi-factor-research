# V4 当前状态（更新日期：2026-02-12）

最后核查：2026-02-12

目的：让下一次打开 Codex 的人能快速理解当前进度、运行中的任务、如何继续。

---

## 1) 当前运行中的任务

**定位（更新）：日频评分/分析为主**
- 目标是日频量化评分与回测（基于常规交易时段 open/close 日线）
- 不做高频日内交易/逐笔级别
- 执行时点可灵活建模，但核心信号来自日频数据
 - Stage 1 = baseline screening；Stage 2 = 机构版（行业 + size/beta 中性 + zscore）

**当前任务**
- 无正在运行的任务

**Size 验证前置数据（Market Cap History）下载已完成**
- 全量历史（2010-01-01 → 2026-02-08）已下载，覆盖率：5370 / 5372
- 缺失：`BCF`, `LBDKV`（接口返回空数据）
- 已加入黑名单：`data/fmp/missing_delisted_adj_us_blacklist.txt`

---

## 1.1) 因子进度总览（简表）

说明：细节见 `FACTOR_NOTES.md`。

| 因子 | 分段 Stage 1 | 分段 Stage 2 | Train/Test | 组合/检验 |
|---|---|---|---|---|
| Value | 已完成 | 已完成 | 已完成 | 未进入组合 |
| Quality | 已完成 | 已完成 | 已完成 | 未进入组合 |
| Low-vol | 已完成 | 已完成 | 已完成 | 未进入组合 |
| Momentum | 未开始 | 未开始 | 未开始 | 未进入组合 |
| Reversal | 未开始 | 未开始 | 未开始 | 未进入组合 |
| PEAD | 未开始 | 未开始 | 未开始 | 未进入组合 |

---

## 2) 关键改动（本次已完成）

0) **统一协议配置 + 策略覆盖（新）**
- 全局协议：`configs/protocol.yaml`
- 策略覆盖：`configs/strategies/*.yaml`
- 统一入口：`scripts/run_with_config.py`

1) **因子工厂完成标准化链（新）**
- `backtest/factor_factory.py`
- 支持：rank/zscore/winsor/missing 处理
- 支持：全局与单因子滞后（`factors.lag_days` & `<factor>.lag_days`）
- 可选输出因子组件（用于相关性面板）

2) **专业因子报告（新）**
- `scripts/generate_factor_report.py`
- 输出：Markdown + JSON + CSV（rolling IC / quantile cum / factor corr）
- 可选：成本敏感性（`--cost-multipliers`）

2.1) **Post-hoc 诊断（新增，不影响回测）**
- `scripts/posthoc_factor_diagnostics.py`
- 输出：beta/行业暴露/size 暴露/换手统计（写入 `strategies/<factor>/reports/`）

2.2) **执行口径（已切换为机构默认）**
- 交易日偏移默认启用：`EXECUTION_USE_TRADING_DAYS = True`
- 动态成本模型默认启用：`ENABLE_DYNAMIC_COST = True`
- 容量/冲击成本参数：`TRADE_SIZE_USD`（默认 10000）

2.3) **投委级检查清单（新增，不影响回测）**
- `scripts/committee_checklist.py`
- 输出：`reports/committee_checklist_<ts>.md/.json`

3) **测试补齐（新）**
- `tests/` 下新增 no-lookahead & lag 测试
- 已安装 `pytest` 并通过全部测试

4) **动量基线更新为“月末调仓 + 日频 6-1 动量”**
- `MOMENTUM_USE_MONTHLY = False`
- `MOMENTUM_LOOKBACK = 126`, `MOMENTUM_SKIP = 21`
- `MOMENTUM_ZSCORE = False`
- `REBALANCE_MODE = "month_end"`
- `REBALANCE_FREQ = 1`

5) **因子处理管线已切换为阶段化（Stage 1/Stage 2）**
- Stage 1 默认：winsor（分位裁剪）+ rank 标准化
- Stage 2（机构版）：行业中性化 + size/beta 中性 + zscore（可选平滑）
 - 新增：beta 计算 + size/beta 中性化开关（`SIGNAL_NEUTRALIZE_SIZE/BETA`）

6) **行业映射数据已生成**
- `data/company_profiles.csv`（88646 行；industry/sector 非空率约 96%）
- 来源：FMP profile-bulk（parts 0-3）
- 脚本：`scripts/fmp_profile_bulk_to_csv.py`

6.1) **退市清单更新 + 覆盖率核查（新增）**
- 退市清单更新为 FMP `delisted-companies`（4741 行）
- 覆盖率报告：`data/fmp/delisted_coverage_report.md`
- US-only 缺失复权价格：9 个 symbol

6.2) **PIT 风险审计（新增）**
- 基本面数据缺少 filing/publish 日期字段，仅有 `date`
- 风险：若 `date` 为期间结束日而非公布日，存在前视偏差
- 报告：`data/fmp/fundamentals_pit_report.md`

6.3) **PIT 修复（已完成）**
- fundamentals 下载脚本已支持 `available_date`（acceptedDate/fillingDate 优先）
- 已重跑：
  - `scripts/download_quality_fundamentals.py`
  - `scripts/download_value_fundamentals.py`
- 引擎会优先用 `available_date` 进行 as-of 过滤

6.4) **退市缺口黑名单（新增）**
- US-only 缺失复权 9 个 symbol
- 黑名单：`data/fmp/missing_delisted_adj_us_blacklist.txt`

6.5) **PEAD 时间风险说明（新增）**
- 说明文档：`data/fmp/pead_timing_risk.md`

6.6) **执行成本敏感性（新增）**
- `ExecutionSimulator` 支持 `cost_multiplier`

6.7) **PIT available_date 覆盖率报告（新增）**
- 报告：`data/fmp/fundamentals_available_date_coverage.md`
- 复检结果：样本覆盖率 100%（2026-02-05）

6.8) **统一入口成本倍数（新增）**
- `scripts/run_with_config.py --cost-multiplier`

6.9) **数据可信度总览（新增）**
- `data/fmp/data_integrity_summary.md`

6.10) **价格来源说明已补全**
- `data/fmp/price_provenance.md`

6.11) **FMP 数据集索引**
- 统一命名与路径索引：`data/fmp/DATASETS.md`

6.16) **因子处理管线（阶段 1/2）已落地**
- 阶段 1：去极值（分位裁剪）+ Rank 标准化
- 阶段 2：可选行业中性与信号平滑（SMA/EMA）

6.17) **Quality 口径更新为组合版（v2）**
- 组合字段：ROE + ROA + Gross Margin + CFO/Assets + Debt/Equity（负权重）
- 需要重建 `data/fmp/ratios/quality/` 才能完全生效（未重建时新字段为空）

6.18) **Stage 1 作为默认配置**
- `low_vol_v1` / `value_v1` / `quality_v1` 已切回 Stage 1（winsor + rank）
- Stage 2 作为对照，需手动切换策略配置
- Value 公式未改动，已有 Stage 1 结果可直接复用：`segment_results/2026-02-10_015525`

6.12) **Market Cap PIT 过滤支持（新增）**
- 新增 `MarketCapEngine`（PIT 市值过滤）
- 新增下载脚本：`scripts/fmp_market_cap_history.py`
- 统一入口支持：`configs/protocol.yaml` 增加 `market_cap_dir` + `market_cap_strict`
- 已完成 market cap 历史数据下载（见下方 6.13）

6.13) **Market Cap 下载现状（2026-02-09）**
- FMP 历史市值接口单次最大 5000 行，已将脚本改为分段拉取（`--chunk-years`）。
- Python 下载在本机出现 DNS/连接不稳定（`NameResolutionError` / `Network is unreachable`）。
- 临时解决：新增 `scripts/fmp_market_cap_history_curl.sh` 使用 curl 分段下载。
- 当前下载已完成；`data/fmp/market_cap_history/` 共有 5370 个文件（缺 `BCF` / `LBDKV`）。
- 若网络稳定后恢复下载：
  - curl 版命令：`/Users/hui/quant_score/v4/scripts/fmp_market_cap_history_curl.sh`
  - 推荐运行（记录日志）：
    - `/Users/hui/quant_score/v4/scripts/fmp_market_cap_history_curl.sh |& tee /Users/hui/quant_score/v4/logs/market_cap_history_curl_YYYY-MM-DD.log`
  - 恢复/重跑判断（覆盖率检查）：
    - `ls /Users/hui/quant_score/v4/data/fmp/market_cap_history | wc -l`
    - `python3 - <<'PY'\nimport pandas as pd\np='/Users/hui/quant_score/v4/data/fmp/market_cap_history/A.csv'\ndf=pd.read_csv(p)\nprint(df['date'].min(), df['date'].max(), len(df))\nPY`
  - 补拉备忘：断网后曾出现 `empty MPG`，后续需确认并补拉该 symbol。

7) **A 股最小验证（新增）**
- 协议：`configs/protocol_cn.yaml`
- 策略：`configs/strategies/cn_reversal_v1.yaml`
- AKShare 脚本：
  - `scripts/akshare_stock_list.py`
  - `scripts/akshare_download_daily.py`
 - 详细状态：`A_SHARE_STATUS.md`
 - A 股数据目录说明：`data/cn/README.md`

8) **分段回测最新结果（当前保留目录）**
注：2026-02-12 之前的结果为自然日执行口径；当前默认已切换到交易日执行 + 动态成本。
在新口径结果未产出前，暂时保留并沿用旧口径结果作为参考。
**Stage 1（rank + winsor）**
- Low-vol（2010-01-04 → 2012-01-03）：IC ≈ 0.01248，IC_raw ≈ 0.01076，n=24601
- Low-vol（2012-01-04 → 2014-01-03）：IC ≈ -0.01582，IC_raw ≈ -0.02001，n=33849
- Low-vol（2014-01-04 → 2016-01-03）：IC ≈ 0.04445，IC_raw ≈ 0.04658，n=38499
- Low-vol（2016-01-04 → 2018-01-03）：IC ≈ -0.02770，IC_raw ≈ -0.02778，n=42227
- Low-vol（2018-01-04 → 2020-01-03）：IC ≈ 0.01091，IC_raw ≈ 0.01167，n=42563
- Low-vol（2020-01-04 → 2022-01-03）：IC ≈ 0.01497，IC_raw ≈ 0.01387，n=48121
- Low-vol（2022-01-04 → 2024-01-03）：IC ≈ 0.04587，IC_raw ≈ 0.04553，n=49422
- Low-vol（2024-01-04 → 2026-01-03）：IC ≈ -0.05011，IC_raw ≈ -0.04776，n=41930
- Low-vol（2026-01-04 → 2026-01-28）：IC = N/A，IC_raw = N/A，n=0
- 目录：`segment_results/2026-02-10_012143`

- Value（2010-01-04 → 2012-01-03）：IC ≈ 0.06569，IC_raw ≈ 0.06508，n=25240
- Value（2012-01-04 → 2014-01-03）：IC ≈ 0.05183，IC_raw ≈ 0.05080，n=30293
- Value（2014-01-04 → 2016-01-03）：IC ≈ 0.03307，IC_raw ≈ 0.03100，n=36470
- Value（2016-01-04 → 2018-01-03）：IC ≈ 0.04352，IC_raw ≈ 0.04357，n=40043
- Value（2018-01-04 → 2020-01-03）：IC ≈ 0.03629，IC_raw ≈ 0.03551，n=39085
- Value（2020-01-04 → 2022-01-03）：IC ≈ 0.01767，IC_raw ≈ 0.01712，n=45008
- Value（2022-01-04 → 2024-01-03）：IC ≈ 0.09652，IC_raw ≈ 0.09594，n=46193
- Value（2024-01-04 → 2026-01-03）：IC ≈ 0.01717，IC_raw ≈ 0.01539，n=39955
- Value（2026-01-04 → 2026-01-28）：IC = N/A，IC_raw = N/A，n=1528
- 目录：`segment_results/2026-02-10_015525`

- Quality（2010-01-04 → 2012-01-03）：IC ≈ -0.00719，IC_raw ≈ -0.00587，n=23569
- Quality（2012-01-04 → 2014-01-03）：IC ≈ -0.01316，IC_raw ≈ -0.01249，n=30259
- Quality（2014-01-04 → 2016-01-03）：IC ≈ 0.02684，IC_raw ≈ 0.02557，n=36445
- Quality（2016-01-04 → 2018-01-03）：IC ≈ 0.00275，IC_raw ≈ 0.00056，n=40051
- Quality（2018-01-04 → 2020-01-03）：IC ≈ 0.01490，IC_raw ≈ 0.01606，n=39137
- Quality（2020-01-04 → 2022-01-03）：IC ≈ 0.01557，IC_raw ≈ 0.01439，n=44753
- Quality（2022-01-04 → 2024-01-03）：IC ≈ 0.00783，IC_raw ≈ 0.00993，n=46238
- Quality（2024-01-04 → 2026-01-03）：IC ≈ 0.00426，IC_raw ≈ 0.00363，n=39954
- Quality（2026-01-04 → 2026-01-28）：IC = N/A，IC_raw = N/A，n=1533
- 目录：`segment_results/2026-02-10_135559`

**Quality 最新分段（Stage 1）**
- Quality（2010-01-04 → 2012-01-03）：IC ≈ -0.00513，IC_raw ≈ -0.00426，n=23569
- Quality（2012-01-04 → 2014-01-03）：IC ≈ -0.01236，IC_raw ≈ -0.01146，n=30259
- Quality（2014-01-04 → 2016-01-03）：IC ≈ 0.01464，IC_raw ≈ 0.01450，n=36445
- Quality（2016-01-04 → 2018-01-03）：IC ≈ 0.01110，IC_raw ≈ 0.01144，n=40041
- Quality（2018-01-04 → 2020-01-03）：IC ≈ 0.01204，IC_raw ≈ 0.01225，n=39137
- Quality（2020-01-04 → 2022-01-03）：IC ≈ 0.00277，IC_raw ≈ 0.00237，n=44753
- Quality（2022-01-04 → 2024-01-03）：IC ≈ 0.00188，IC_raw ≈ 0.00321，n=46238
- Quality（2024-01-04 → 2026-01-03）：IC ≈ 0.00250，IC_raw ≈ 0.00135，n=39954
- Quality（2026-01-04 → 2026-01-28）：IC = N/A，IC_raw = N/A，n=1533
- 目录：`segment_results/2026-02-10_135559`

**Momentum 分段（Stage 1）**
- 未开始（已清理所有动量回测产物）

**Stage 2（industry neutral + smoothing + zscore）**
- Low-vol（2010-01-04 → 2012-01-03）：IC ≈ 0.02265，IC_raw ≈ 0.02159，n=24601
- Low-vol（2012-01-04 → 2014-01-03）：IC ≈ -0.00579，IC_raw ≈ -0.01398，n=33849
- Low-vol（2014-01-04 → 2016-01-03）：IC ≈ 0.04918，IC_raw ≈ 0.05705，n=38499
- Low-vol（2016-01-04 → 2018-01-03）：IC ≈ -0.02629，IC_raw ≈ -0.02824，n=42227
- Low-vol（2018-01-04 → 2020-01-03）：IC ≈ 0.02464，IC_raw ≈ 0.02462，n=42563
- Low-vol（2020-01-04 → 2022-01-03）：IC ≈ 0.03225，IC_raw ≈ 0.03017，n=48122
- Low-vol（2022-01-04 → 2024-01-03）：IC ≈ 0.06576，IC_raw ≈ 0.06563，n=49423
- Low-vol（2024-01-04 → 2026-01-03）：IC ≈ -0.02947，IC_raw ≈ -0.02466，n=41930
- Low-vol（2026-01-04 → 2026-01-28）：IC = N/A，IC_raw = N/A，n=0
- 目录：`segment_results/2026-02-10_213821`

- Value（2010-01-04 → 2012-01-03）：IC ≈ 0.06540，IC_raw ≈ 0.06467，n=25240
- Value（2012-01-04 → 2014-01-03）：IC ≈ 0.03636，IC_raw ≈ 0.03381，n=30293
- Value（2014-01-04 → 2016-01-03）：IC ≈ 0.05599，IC_raw ≈ 0.05398，n=36470
- Value（2016-01-04 → 2018-01-03）：IC ≈ 0.04013，IC_raw ≈ 0.04123，n=40043
- Value（2018-01-04 → 2020-01-03）：IC ≈ 0.04720，IC_raw ≈ 0.04466，n=39085
- Value（2020-01-04 → 2022-01-03）：IC ≈ 0.03183，IC_raw ≈ 0.03120，n=45008
- Value（2022-01-04 → 2024-01-03）：IC ≈ 0.09301，IC_raw ≈ 0.09276，n=46193
- Value（2024-01-04 → 2026-01-03）：IC ≈ 0.03525，IC_raw ≈ 0.03181，n=39955
- Value（2026-01-04 → 2026-01-28）：IC = N/A，IC_raw = N/A，n=1528
- 目录：`segment_results/2026-02-10_222028`

- Quality（2010-01-04 → 2012-01-03）：IC ≈ -0.02441，IC_raw ≈ -0.02480，n=23569
- Quality（2012-01-04 → 2014-01-03）：IC ≈ -0.01213，IC_raw ≈ -0.01163，n=30259
- Quality（2014-01-04 → 2016-01-03）：IC ≈ 0.00028，IC_raw ≈ -0.00057，n=36445
- Quality（2016-01-04 → 2018-01-03）：IC ≈ -0.00298，IC_raw ≈ -0.00216，n=40041
- Quality（2018-01-04 → 2020-01-03）：IC ≈ 0.00126，IC_raw ≈ 0.00197，n=39137
- Quality（2020-01-04 → 2022-01-03）：IC ≈ -0.00349，IC_raw ≈ -0.00346，n=44753
- Quality（2022-01-04 → 2024-01-03）：IC ≈ 0.00668，IC_raw ≈ 0.00869，n=46238
- Quality（2024-01-04 → 2026-01-03）：IC ≈ 0.00284，IC_raw ≈ 0.00241，n=39954
- Quality（2026-01-04 → 2026-01-28）：IC = N/A，IC_raw = N/A，n=1533
- 目录：`segment_results/2026-02-10_223438`

9) **Train/Test（单因子）最新状态**
- Value：已完成（新口径：`strategies/value_v1/runs/2026-02-12_163841.json`，Test IC ≈ 0.04176）
- Quality：已完成（最新：`strategies/quality_v1/runs/2026-02-12_135607.json`）
- Low-vol：已完成（最新：`strategies/low_vol_v1/runs/2026-02-12_143900.json`）

**Stage 0（旧口径，已归档）**
- `segment_results_stage0/2026-02-09_190913`（low-vol）
- `segment_results_stage0/2026-02-09_213832`（value）
- `segment_results_stage0/2026-02-10_003847`（quality）

9) **Momentum 新配置（日频 6-1 + 月末调仓）**
- `MOMENTUM_LOOKBACK=126`, `MOMENTUM_SKIP=21`
- `MOMENTUM_USE_MONTHLY=False`
- `REBALANCE_FREQ=1`（month_end 模式下每月 rebalance）

7) **引擎与过滤支持扩展**
- `backtest/universe_builder.py`：新增波动率过滤
- `backtest/factor_engine.py`：行业中性化 + winsorize

8) **新增低波动验证基线**
- `strategies/low_vol_v1/config.py`
- 可用于 sanity check（验证框架是否能跑出稳定信号）

9) **IC 计算修正**
- 使用全信号 forward returns 计算 IC（非仅已建仓位）
- 保留 `ic_positions` 作为旧口径参考
- 新增 `ic_raw`（不走质量过滤）用于对照

10) **Size 健康检查准备（进行中）**
- 目标：用 Size 因子验证框架健康（市值历史为前置数据）。
- 已修正：`scripts/fmp_market_cap_history.py` 使用 `stable/historical-market-capitalization` 端点。
- 当前进度：`symbols_us_basic.csv` 已生成；历史市值下载在跑（可能需下次续跑）。
- 注意：运行命令请使用 `iterm_commands.txt` 中的顺序与指令。

10) **Low-vol 简化基线（新增，用于框架健康验证）**
- 新增策略配置：`strategies/low_vol_simple_v1/config.py`
- 分段跑法：`--factors low_vol_simple --years 2 --max-segments 5`
- 最新进度（已完成 1 段）：
  - 2010-01-04 → 2012-01-03：IC ≈ 0.0403，IC_raw ≈ -0.0038，n=28384

---

## 3) 已完成的结果（历史）
- 引擎收益与极简收益相关性：约 0.83（方向一致）
- 启示：引擎 IC 是基于“已选仓位”计算，非全市场横截面，可能低估/扭曲真实 IC

**IC 计算已修正**
- `backtest/execution_simulator.py`：新增 `calculate_forward_returns`
- `backtest/backtest_engine.py`：默认 IC 使用全信号 forward returns

## 4) BRAIN 外部验证（新增）

- 已建立隔离目录：`brain/`（`factors/`, `results/`, `logs/`）
- `brain/logs/brain_factor_log.md` 已记录 `rank(cap)` 的 BRAIN 测试结果（USA / TOP3000 / Delay 1 / Neutralization None / Decay 0 / 5y）
- BRAIN 语法草稿：`brain/BRAIN_SYNTAX.md`
- `scripts/run_segmented_factors.py`：分段 IC 使用 forward returns

---

## 5) 2026-02-09 Low-vol 分段回测（历史记录）
低波回测已修复 dtype 问题并加入日志输出，旧的“崩溃前输出”仅作历史参考。

---

## 4) 下一步建议（当前）

1) **重建 Quality fundamentals（组合口径 v2）**  
2) **新因子先跑 Stage 1 分段回测**（winsor + rank 作为默认基线）  
3) **稳定因子再进入组合**（至少 2–3 个稳定因子）  
4) **固定 train/test 与 walk-forward 放在组合稳定之后**  

常用命令统一维护在 `RUNBOOK.md`。

---

## 5) 机器限制提醒

- 当前机器：MacBook Pro M1, 16GB
- 建议一次只跑一个因子
- 优先用分段/断点续跑
