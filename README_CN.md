# V4 - 多因子回测系统（中文说明）

最后核查：2026-02-12

本仓库记录多因子回测系统（动量、反转、价值、质量、低波动、PEAD 等）。本文档与英文版 `README.md` 对齐，重点强调数据流、时间对齐与诊断口径。

更新时间：2026-02-12

---

## 快速摘要

最新分段结果（Stage 1/Stage 2）统一记录在 `STATUS.md`。默认以 Stage 1（winsor + rank）作为新因子基线；Stage 2（机构版：行业 + size/beta 中性 + zscore，可选平滑）用于稳健性对照。
当前策略：先用 Stage 1 完成单因子筛选，组合阶段再用 Stage 2 做稳健性对照。

**当前研究意图（2026-02-12）**
- 先单因子稳定性（分段 IC + 固定 train/test）
- Stage 1 为默认基线；Stage 2 为机构版稳健性对照
- 至少 2–3 个稳定因子后再进入组合
- 已增加 post-hoc 诊断与投委级 checklist（不影响回测）
 - 交易日执行与动态成本已设为默认（`EXECUTION_USE_TRADING_DAYS` / `ENABLE_DYNAMIC_COST`）

---

## 回测标准（三层）

1. **分段回测（稳定性检查）**  
   - 固定窗口切分（如 2 年一段）计算 IC  
   - 目的：验证跨周期稳定性

2. **固定 train/test（过拟合检查）**  
   - 固定训练窗 + 固定测试窗  
   - 目的：检查 OOS 退化与信号数量

3. **Walk-forward（可部署性）**  
   - 滚动训练/测试  
   - 目的：近似真实滚动训练表现

如果分段回测不过关，后续两层不必推进。

---

## 0) 包含内容

单因子策略（`strategies/`）：
- PEAD（SUE）
- Momentum（12-1）
- Reversal（短期/日内）
- Quality（组合口径：ROE/ROA + 毛利率 + CFO/资产 + 负债惩罚）
- Value（EY + FCFY + EV/EBITDA）
- Low-vol（验证基线：`strategies/low_vol_v1/`）

工具脚本：
- 分段因子回测：`scripts/run_segmented_factors.py`
- Walk-forward：`scripts/run_walk_forward.py`
- FMP profile-bulk 转 CSV：`scripts/fmp_profile_bulk_to_csv.py`
- FMP 数据集索引：`data/fmp/DATASETS.md`
- 统一配置入口：`scripts/run_with_config.py`
- 专业因子报告：`scripts/generate_factor_report.py`

配置：
- 全局协议：`configs/protocol.yaml`
- 策略覆盖：`configs/strategies/*.yaml`

---

## 1) 系统概览（数据流 + 时间）

本系统 **按 rebalance date 驱动**，不是日频全量计算。信号与持仓仅在稀疏的调仓日生成。

高层流程：
1. 构建交易日历（SPY 或兜底）并生成 `rebalance_dates`
2. 对每个 rebalance date：
   - 构建可交易股票池  
   - 计算因子信号  
   - 构建持仓  
3. 按固定延迟与持有期执行交易  
4. 计算收益与诊断  
5. 保存输出（信号/收益 + 报告 JSON）

**重要**：系统以配置驱动。规范入口：
- `configs/protocol.yaml`（全局规则）
- `configs/strategies/<strategy>.yaml`（策略覆盖）

---

## 2) 核心回测模块

### 2.1 BacktestEngine（`backtest/backtest_engine.py`）
- **交易日历**：优先 SPY 数据，否则用其他符号或工作日兜底  
- **调仓日期**：每 `REBALANCE_FREQ` 个交易日  
- **主循环**：每个调仓日调用 `FactorEngine.compute_signals`、`FactorEngine.build_positions`，再执行与计算收益

关键点：
- `signals_df.date` 是 **rebalance date**（信号日期）  
- 策略只在 rebalance date 上“看见”事件

### 2.2 UniverseBuilder（`backtest/universe_builder.py`）
动态可交易股票池过滤：
- **退市过滤**：调仓日若已退市则跳过  
- **Lookback**：至少 `lookback` 条价格数据  
- **最低价格**：lookback 平均收盘价 >= `MIN_PRICE`  
- **最低成交额**：平均（收盘价 * 成交量）>= `MIN_DOLLAR_VOLUME`（若有成交量）

备注：当配置 `MarketCapEngine` 后，`MIN_MARKET_CAP` 会被执行（需要 PIT 市值历史数据）。

### 2.3 FactorEngine（`backtest/factor_engine.py`）
计算各因子并聚合信号：
- 已实现：momentum、reversal、low-vol、pead、value、quality  
- 信号计算：`signal = sum(weight_k * factor_k)`（仅使用非空因子）
- 默认输出列：`symbol`, `date`, `signal`
- 可选输出因子组件：`factors.include_components: true`

因子权重由策略定义。示例（`strategies/pead_v1/`）：
```
{'momentum': 0.0, 'reversal': 0.0, 'low_vol': 0.0, 'pead': 1.0}
```
因此该策略 `signal == pead`。

### 2.4 Position Builder（`FactorEngine.build_positions`）
- 按信号降序  
- Long 取 `floor(n * long_pct)`  
- Short 取 `floor(n * short_pct)`（当前未用）  
- 若 `long_pct > 0` 且有数据，至少保留 1 个多头

### 2.5 ExecutionSimulator（`backtest/execution_simulator.py`）
执行使用 **自然日偏移**，非交易日偏移。

- **执行日**：`signal_date + EXECUTION_DELAY`
- **退出日**：`signal_date + EXECUTION_DELAY + HOLDING_PERIOD`
- **进出场价格**：执行日或之后的首个可用 bar；优先 `open`，否则 `close`
- **成本**：默认 20 bps 或启用动态成本模型
- **缺失数据**：可回退到退市逻辑或保守损失

---

## 3) 事件因子示例：PEAD（SUE）与时间对齐

此处为事件因子对齐的示例。非事件因子（如动量、反转、价值、质量）不依赖财报日期对齐。

### 3.1 Cached PEAD（`backtest/pead_factor_cached.py`）
- 读取缓存的 Owner_Earnings 标注数据（来源：FMP `/stable/earnings`）  
- 计算 SUE：
  - `surprise = epsActual - epsEstimated`
  - 滚动标准差窗口 = `LOOKBACK_QUARTERS`（min periods = window）
  - `sue = surprise / (surprise_std + 1e-9)`，并裁剪到 [-10, 10]
- 旧式事件检测：**最近 5 日窗口**（当前策略未使用）

### 3.2 Shifted PEAD（`strategies/pead_v1/factor.py`）
当前启用的 PEAD 因子 **不使用 5 日窗口**，采用严格的 +1 天对齐。

**当前对齐逻辑**：
- 输入：`signal_date`（rebalance date）
- 内部目标：`target_date = signal_date + 1`
- 仅当 `earnings_date == target_date` 时触发
- 需满足 SUE 阈值：`abs(sue) > SUE_THRESHOLD`

**含义**：
```
earnings_date = signal_date + 1
signal_date   = earnings_date - 1
```

### 3.3 实际交易时间
给定 `EXECUTION_DELAY = 1`：
```
execution_date = signal_date + 1 = earnings_date
```
即策略 **在财报日开盘入场**。

---

## 4) 调仓效应（信号聚集）

系统只在 rebalance date 扫描事件。两次调仓之间发生的财报事件，会在满足对齐规则的最近调仓日被捕获，导致某些调仓日信号聚集。

---

## 5) 输出与诊断

### 5.1 主输出（策略运行示例：`strategies/pead_v1/run.py`）
- `train_signals_latest.csv` / `test_signals_latest.csv`
  - 列：`symbol, date, signal`（date 为 rebalance date）
- `train_returns_latest.csv` / `test_returns_latest.csv`
  - 进出场价格、收益、退出类型、持有期等
- 同名的带时间戳版本

### 5.2 报告 JSON（`strategies/*/runs/*.json`）
包含：
- 绩效指标（IC、robust IC、n_signals）
- 质量指标（退出类型、数据覆盖、过滤统计）
- 数据清单（文件 hash、git 信息）
- strategy_rules（对齐与执行）

### 5.3 研究/诊断产物（如有，PEAD 示例）
- `pead_full_cross_section_ic_input.csv` / `pead_fullcs_engine_ic_input.csv`
- `pead_ic_by_date_*.csv`
- `pead_top20_vs_all_by_date.csv`
- `pead_quantile_summary_tradableset.csv`
- `pead_quantile_portfolio_returns_tradableset.csv`
- `pead_quantile_equity_tradableset.csv`（含 PNG）

---

### IC 计算注意点（引擎）
IC 使用全信号 forward returns 计算（`forward_returns`）。旧口径（仅已建仓位）仍保留为 `ic_positions` 供参考。若需旧口径，使用 `analysis.ic_positions` / `analysis.ic_yearly_positions`。

---

## 9) 近期进展

旧结果目录已清理，待新一轮回测完成后补录。

---

## 5.4 验证基线（Low-Vol）

若某因子表现异常，先跑低波动基线验证引擎：
```bash
PYTHONPATH=/Users/hui/quant_score/v4 /Users/hui/miniconda3/envs/qscore/bin/python \
  /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --factors low_vol --max-segments 3
```

使用 `strategies/low_vol_v1/config.py` 与内置 low-vol 因子。

---

## 10) 行业/板块映射（行业中性化）

行业中性化可选，需要本地映射文件：
- `data/company_profiles.csv`（列：`symbol`, `industry`, `sector`）
- 通过 FMP profile-bulk 生成：
  - `scripts/fmp_profile_bulk_to_csv.py`

---

## 6) 默认参数（PEAD v1 示例）

来自 `strategies/pead_v1/config.py`：
- `SUE_THRESHOLD = 0.5`
- `LOOKBACK_QUARTERS = 8`
- `DATE_SHIFT_DAYS = 1`（注意：代码当前硬编码 +1，未读取常量）
- `REBALANCE_FREQ = 5`
- `EXECUTION_DELAY = 1`
- `HOLDING_PERIOD = 10`
- `MIN_PRICE = 5.0`
- `MIN_DOLLAR_VOLUME = 1e6`

---

## 7) 时间示意（当前实现）

```
          earnings_date（事件日）
                   ▲
                   │  当 earnings_date == signal_date + 1 时匹配
                   │
signal_date（调仓日）
      │
      └── execution_date = signal_date + 1 = earnings_date
```

---

## 8) 实际含义（PEAD 示例）

- 策略是 **事件驱动但受调仓门控**  
- PEAD 信号 **严格对齐** 到特定财报日  
- 执行是 **信号 T+1**，与财报日开盘一致

如需变更对齐（财报当天或次日），`ShiftedPEADFactor` 是唯一真相源。

---

## 9) 分段回测（2 年 IC 切片）

示例：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py
```

常用参数：
```bash
# 2010-2025，2 年一段
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --start-date 2010-01-01 --end-date 2025-12-31 --years 2

# 只跑 momentum + value
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --factors momentum,value --years 2

# 断点续跑
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --resume --out-dir /Users/hui/quant_score/v4/segment_results/<timestamp>

# 只跑前三段
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --max-segments 3

# 反向动量（方向验证）
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --factors momentum --invert-momentum --max-segments 3
```

输出目录：
`segment_results/<timestamp>/`

---

## 10) Walk-forward（滚动训练/测试）

示例：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py
```

常用参数：
```bash
# 3 年训练 + 1 年测试，2010-2026
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --train-years 3 --test-years 1 --start-year 2010 --end-year 2026

# 只跑 momentum + value
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --factors momentum,value

# 断点续跑
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --resume --out-dir /Users/hui/quant_score/v4/walk_forward_results/<timestamp>

# 只跑前三个窗口
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --max-windows 3

# 只跑指定年份（如 2018、2019）
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --only-years 2018,2019
```

输出目录：
`walk_forward_results/<timestamp>/`

---

## 11) 仓库结构（快速地图）

顶层目录：
- `backtest/` 核心引擎、数据处理、执行、分析
- `strategies/` 策略入口 + 配置 + 输出
- `data/` 价格、财报、退市列表、基本面缓存
- `scripts/` 数据下载与工具脚本
- `results/` 早期脚本输出
- `segment_results/` 分段回测输出
- `archive/` 历史归档

关键文件：
- `backtest/backtest_engine.py` 主引擎  
- `backtest/data_engine.py` 价格加载 + 退市处理  
- `backtest/universe_builder.py` 股票池过滤  
- `backtest/factor_engine.py` 因子计算  
- `backtest/execution_simulator.py` 执行与收益  
- `backtest/performance_analyzer.py` IC 与统计  

---

## 12) 数据依赖（必须存在）

价格数据（按股票一文件的 pickle）：
- Active：`data/prices_divadj/`（`USE_ADJ_PRICES=True` 时优先）
- Delisted：`data/prices_delisted_divadj/`
- 非复权兜底：`data/prices/` 和 `data/prices_delisted/`

**重要（数据来源说明）：**
- 本项目 **必须同时包含在交易与已退市股票** 的价格文件。
- 引擎会读取退市目录，并使用 `data/delisted_companies_2010_2026.csv` 在退市日截断价格序列。
- 若价格来源只包含“当前仍在交易”的股票，将产生 **幸存者偏差**，回测结果不可信。
- 请明确并可追溯 `data/prices*` 与 `data/prices_delisted*` 的真实数据来源。

退市清单：
- `data/delisted_companies_2010_2026.csv`（用于退市日截断）

覆盖率备注（最后核查：2026-02-05）：
- 退市清单已更新为 FMP 最新，合计 4718 个 symbol
- 退市复权价格覆盖 4256 个
- US-only 缺失复权 9 个
- 报告：`data/fmp/delisted_coverage_report.md`
 - US-only 缺失复权黑名单：`data/fmp/missing_delisted_adj_us_blacklist.txt`

价格来源说明：
- `data/fmp/price_provenance.md`

A 股启动（最小验证）：
1. 拉取股票列表：`scripts/akshare_stock_list.py`
2. 下载日线数据（复权）：`scripts/akshare_download_daily.py --symbols-csv /Users/hui/quant_score/v4/data/cn/stock_list.csv`
3. 用 A 股协议跑反转：`scripts/run_with_config.py --protocol /Users/hui/quant_score/v4/configs/protocol_cn.yaml --strategy /Users/hui/quant_score/v4/configs/strategies/cn_reversal_v1.yaml`

基本面缓存：
- Quality：`data/fmp/ratios/quality/`
- Value：`data/fmp/ratios/value/`

若基本面文件包含 `available_date`，引擎将优先使用该字段做时间过滤。

市值历史（用于 PIT 市值过滤，可选）：
- `data/fmp/market_cap_history/`（按 symbol 的 CSV）
- 当目录存在且有数据时，`MIN_MARKET_CAP` 才会生效；否则会跳过过滤避免空池。

PIT 状态（最后核查：2026-02-05）：
- 正在用 FMP `acceptedDate` / `fillingDate` 重建基本面数据（生成 `available_date`）
- 需重跑：
  - `scripts/download_quality_fundamentals.py --overwrite`
  - `scripts/download_value_fundamentals.py --overwrite`
PIT 复检：
- `data/fmp/fundamentals_available_date_coverage.md`（样本覆盖率 100%）

执行成本敏感性：
- `ExecutionSimulator` 支持 `cost_multiplier` 用于成本压力测试（如 2x/3x）

统一入口成本倍数：
- `scripts/run_with_config.py --cost-multiplier 2.0`

动量当前默认（2026-02-10，未变更）：
- 日频 6-1：`MOMENTUM_LOOKBACK=126`, `MOMENTUM_SKIP=21`
- `MOMENTUM_USE_MONTHLY=False`
- `REBALANCE_MODE="month_end"` + `REBALANCE_FREQ=1`

PEAD 时间风险说明：
- `data/fmp/pead_timing_risk.md`

策略入口：
- `strategies/pead_v1/run.py`
- `strategies/momentum_v1/run.py`
- `strategies/reversal_v1/run.py`
- `strategies/quality_v1/run.py`
