# 短期反转策略 v1（3日反转 + 次日开盘 + 持有1日）

> 目标：在日频框架下捕捉短期价格过度反应后的回归效应；盘后计算信号，次日开盘执行。

---

## 1. 策略逻辑概述

**核心假设**：短期内市场存在过度反应，价格在短期极端波动后出现反转回归。

**信号定义**（日内反转）：
- 使用当日开盘-收盘的日内收益：
  \[
  r_{intra} = \frac{Close_t}{Open_t} - 1
  \]
- 反转信号取负：
  \[
  signal = -r_{intra}
  \]
- 解释：
  - 当日上涨越多 → signal 越负
  - 当日下跌越多 → signal 越正

**建仓与持有**：
- 每天（交易日）生成信号并排序，取 top 20% 做多。
- 不做空。
- 次日开盘执行，持有 1 个交易日。

---

## 2. 时序与数据流

**流程顺序**：
1) 交易日历与 rebalance 日期生成（默认 daily）
2) 构建当日可交易股票池（退市/价格/流动性过滤）
3) 计算因子信号（短期反转）
4) 横截面排序选股 → 建仓
5) 次日开盘执行 → 持有 1 日 → 计算收益
6) 输出结果与报告

**时序示意**：
- T 日收盘：计算日内反转信号
- T+1 日开盘：执行买入
- T+2 日开盘：卖出（持有 1 日）

---

## 3. 模块结构与职责

### 3.1 数据层（DataEngine）
- 读取本地价格数据（默认：`data/prices` 或 `data/prices_divadj`）
- 退市股票按退市日截断

### 3.2 股票池构建（UniverseBuilder）
- 动态过滤条件：
  - 退市过滤
  - 最低价格过滤（`MIN_PRICE`）
  - 最低成交额过滤（`MIN_DOLLAR_VOLUME`）

### 3.3 因子计算（FactorEngine）
- 计算短期反转因子：
  - 当日开收盘日内收益
  - 取负作为反转信号
- 支持波动缩放（`REVERSAL_VOL_LOOKBACK`）
- 支持财报日过滤（`REVERSAL_EARNINGS_FILTER_DAYS`）

### 3.4 建仓逻辑（FactorEngine.build_positions）
- 信号降序排序
- 取 top 20% 做多
- 不做空

### 3.5 执行与收益（ExecutionSimulator）
- 执行价：次日开盘价（或下一个可交易日开盘）
- 持有：1 天
- 交易成本：配置项 `TRANSACTION_COST`

### 3.6 输出与报告
- 输出信号与收益（带时间戳 + latest）
- 生成最小化报告 JSON（策略配置 + 绩效摘要）

---

## 4. 配置与默认参数

位置：`strategies/reversal_v1/config.py`

- `REVERSAL_MODE = \"intraday\"`
- `REVERSAL_VOL_LOOKBACK = 20`
- `REVERSAL_EARNINGS_FILTER_DAYS = 1`
- `HOLDING_PERIOD = 1`
- `REBALANCE_FREQ = 1`
- `EXECUTION_DELAY = 1`
- `TRANSACTION_COST = 0.0020`
- `MIN_PRICE = 5.0`
- `MIN_DOLLAR_VOLUME = 1e6`
- `USE_ADJ_PRICES = True`

---

## 5. 数据口径说明

- 信号计算建议使用复权价（`adjClose`），避免拆股/分红扭曲。
- 执行价默认使用开盘价（若数据为复权价则口径一致）。
- 若复权库未准备完整，会自动回退到原价库。

---

## 6. 风险与注意事项

- 短期反转对交易成本敏感，需关注实际滑点与费用。
- 若交易日内波动极大，短期反转可能失效。
- 分钟级/盘中信息不在模型中，属于日频框架的不可见风险。

---

## 7. 输出文件

目录：`strategies/reversal_v1/results` 与 `strategies/reversal_v1/runs`

- `train_signals_latest.csv`
- `train_returns_latest.csv`
- `test_signals_latest.csv`
- `test_returns_latest.csv`
- `runs/<timestamp>.json`

---

## 8. 运行方式

```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.reversal_v1.run
```

---

## 9. 后续可选优化

- 日内/隔夜拆分反转信号
- 波动缩放（signal / vol）
- 事件日过滤（财报日 ±1）
- 分位分层持仓
