# 质量策略 v1（ROE + 现金流质量 + 毛利率）

> 目标：选择盈利能力强、现金流真实的公司，作为长期稳健因子。

---

## 1. 策略逻辑概述

**核心假设**：高质量公司（高盈利能力+高现金流质量）在长期具有超额收益。

**质量分数定义**：
- 使用以下指标（来自财报/TTM 数据）：
  - ROE（净利润 / 股东权益）
  - 毛利率（毛利 / 营收）
  - 经营现金流 / 资产
- 质量分数：
  \[
  score = w_1 \cdot ROE + w_2 \cdot GrossMargin + w_3 \cdot CFO/Assets
  \]

**建仓与持有**：
- 每个调仓日生成质量分数并排序，取 top 20% 做多。
- 不做空。
- 次日开盘执行，持有 20 个交易日。

---

## 2. 时序与数据流

**流程顺序**：
1) 交易日历与 rebalance 日期生成
2) 构建当日可交易股票池（退市/价格/流动性过滤）
3) 读取最新可用的财报指标（不晚于信号日）
4) 计算质量分数 → 横截面排序 → 建仓
5) 次日开盘执行 → 持有 20 日 → 计算收益
6) 输出结果与报告

---

## 3. 模块结构与职责

### 3.1 FundamentalsEngine
- 读取本地财务指标缓存（每个 symbol 一个文件）
- 取信号日之前最近一期数据

### 3.2 FactorEngine
- 计算质量分数（加权和）
- 将质量分数作为 `quality` 因子

### 3.3 执行与收益（ExecutionSimulator）
- 次日开盘执行，持有 20 日

---

## 4. 配置与默认参数

位置：`strategies/quality_v1/config.py`

- `QUALITY_WEIGHTS = {roe:1, gross_margin:1, cfo_to_assets:1}`
- `HOLDING_PERIOD = 20`
- `REBALANCE_FREQ = 21`
- `EXECUTION_DELAY = 1`
- `TRANSACTION_COST = 0.0020`
- `USE_ADJ_PRICES = True`
- `FUNDAMENTALS_DIR = ../data/fmp/ratios/quality`

---

## 5. 数据口径说明

- 必须使用**点时数据**（信号日不晚于财报发布日期）。
- 财务指标为 TTM 或季度数据，建议季度更新。

---

## 6. 风险与注意事项

- 财务指标更新频率低，短期不敏感。
- 数据延迟或缺失会导致信号稀疏。
- 需避免 look-ahead（只用信号日前已公布的数据）。

---

## 7. 输出文件

目录：`strategies/quality_v1/results` 与 `strategies/quality_v1/runs`

- `train_signals_latest.csv`
- `train_returns_latest.csv`
- `test_signals_latest.csv`
- `test_returns_latest.csv`
- `runs/<timestamp>.json`

---

## 8. 运行方式

```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.quality_v1.run
```
