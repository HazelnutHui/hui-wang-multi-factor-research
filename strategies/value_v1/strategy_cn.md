# 估值策略 v1（盈利收益率 + FCF 收益率 + EV/EBITDA 收益率）

> 目标：选择估值便宜（“收益率高”）的公司，作为长期价值因子。

---

## 1. 策略逻辑概述

**核心假设**：价格低估的公司具备长期回归与超额收益潜力。

**估值分数定义**：
- 使用以下指标（来自 TTM 比率）：
  - 盈利收益率：\(1 / PE\)
  - 自由现金流收益率：\(1 / (P/FCF)\)
  - EV/EBITDA 收益率：\(1 / (EV/EBITDA)\)

**组合方式**：
\[
score = w_1 \cdot EY + w_2 \cdot FCFY + w_3 \cdot EVEBITDAY
\]

**建仓与持有**：
- 每个调仓日生成估值分数并排序，取 top 20% 做多。
- 不做空。
- 次日开盘执行，持有 20 个交易日。

---

## 2. 时序与数据流

**流程顺序**：
1) 交易日历与 rebalance 日期生成
2) 构建当日可交易股票池（退市/价格/流动性过滤）
3) 读取最新可用的估值指标（不晚于信号日）
4) 计算估值分数 → 横截面排序 → 建仓
5) 次日开盘执行 → 持有 20 日 → 计算收益
6) 输出结果与报告

---

## 3. 模块结构与职责

### 3.1 ValueFundamentalsEngine
- 读取本地估值指标缓存（每个 symbol 一个文件）
- 取信号日前最近一期数据

### 3.2 FactorEngine
- 计算估值分数（加权和）
- 将估值分数作为 `value` 因子

---

## 4. 配置与默认参数

位置：`strategies/value_v1/config.py`

- `VALUE_WEIGHTS = {earnings_yield:1, fcf_yield:1, ev_ebitda_yield:1}`
- `HOLDING_PERIOD = 20`
- `REBALANCE_FREQ = 21`
- `EXECUTION_DELAY = 1`
- `TRANSACTION_COST = 0.0020`
- `USE_ADJ_PRICES = True`
- `VALUE_DIR = ../data/fmp/ratios/value`

---

## 5. 数据口径说明

- 必须使用**点时数据**（信号日不晚于财报发布日期）。
- TTM 比率建议季度更新。

---

## 6. 风险与注意事项

- 估值因子回归速度慢，短期内可能弱。
- 极端低估可能是基本面恶化。

---

## 7. 输出文件

目录：`strategies/value_v1/results` 与 `strategies/value_v1/runs`

- `train_signals_latest.csv`
- `train_returns_latest.csv`
- `test_signals_latest.csv`
- `test_returns_latest.csv`
- `runs/<timestamp>.json`

---

## 8. 运行方式

```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.value_v1.run
```
