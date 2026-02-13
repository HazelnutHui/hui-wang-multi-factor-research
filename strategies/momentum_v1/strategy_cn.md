# 中期动量策略 v1（12-1 动量）

> 目标：捕捉中期趋势延续效应。盘后计算信号，按周期调仓，次日开盘执行。

---

## 1. 策略逻辑概述

**核心假设**：中期价格趋势具有延续性（动量效应）。

**信号定义（12-1 动量）**：
- 基于日频价格计算 12 个月累计收益率，并跳过最近 1 个月：
  \[
  mom_{12-1} = \frac{P_{t-21}}{P_{t-252}} - 1
  \]
- 解释：
  - 近 12 个月中期上涨更多 → signal 更高（偏多）
  - 近 12 个月中期表现更弱 → signal 更低（偏空，但当前为多头）

**建仓与持有**：
- 每个调仓日（默认月频）生成信号并排序，取 top 20% 做多。
- 不做空。
- 次日开盘执行，持有 21 个交易日。

---

## 2. 时序与数据流

**流程顺序**：
1) 交易日历与 rebalance 日期生成
2) 构建当日可交易股票池（退市/价格/流动性过滤）
3) 计算动量信号（12-1）
4) 横截面排序选股 → 建仓
5) 次日开盘执行 → 持有 21 日 → 计算收益
6) 输出结果与报告

**时序示意**：
- T 日收盘：计算动量信号
- T+1 日开盘：执行买入
- T+21 日开盘：卖出（持有 21 日）

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
  - 可选波动率过滤（`UNIVERSE_MAX_VOL`, `UNIVERSE_VOL_LOOKBACK`）

### 3.3 因子计算（FactorEngine）
- 计算 12-1 动量（日频）：
  - 使用 252 日窗口，跳过最近 21 日
- 参数：`MOMENTUM_LOOKBACK`、`MOMENTUM_SKIP`
- 可选极值裁剪：`MOMENTUM_WINSOR_Z`
- 可选行业中性化：`INDUSTRY_NEUTRAL`（需 `INDUSTRY_MAP_PATH`）

### 3.4 建仓逻辑（FactorEngine.build_positions）
- 信号降序排序
- 取 top 20% 做多
- 不做空

### 3.5 执行与收益（ExecutionSimulator）
- 执行价：次日开盘价（或下一个可交易日开盘）
- 持有：21 个交易日
- 交易成本：配置项 `TRANSACTION_COST`

### 3.6 输出与报告
- 输出信号与收益（带时间戳 + latest）
- 生成最小化报告 JSON（策略配置 + 绩效摘要）

---

## 4. 配置与默认参数

位置：`strategies/momentum_v1/config.py`

- `MOMENTUM_LOOKBACK = 252`
- `MOMENTUM_SKIP = 21`
- `MOMENTUM_VOL_LOOKBACK = 60`
- `MOMENTUM_WINSOR_Z = 3.0`
- `HOLDING_PERIOD = 21`
- `REBALANCE_FREQ = 21`
- `EXECUTION_DELAY = 1`
- `TRANSACTION_COST = 0.0020`
- `MIN_PRICE = 5.0`
- `MIN_DOLLAR_VOLUME = 1e6`
- `USE_ADJ_PRICES = True`
- `UNIVERSE_VOL_LOOKBACK = 60`
- `UNIVERSE_MAX_VOL = 0.08`

---

## 5. 数据口径说明

- 信号计算建议使用复权价（`adjClose`），避免拆股/分红扭曲。
- 执行价默认使用开盘价（若数据为复权价则口径一致）。
- 若复权库未准备完整，会自动回退到原价库。

---

## 6. 风险与注意事项

- 动量是中期因子，不适合高频换仓。
- 换手率较高时交易成本会侵蚀收益。
- 需注意市场风格切换（动量崩溃期）。

---

## 7. 输出文件

目录：`strategies/momentum_v1/results` 与 `strategies/momentum_v1/runs`

- `train_signals_latest.csv`
- `train_returns_latest.csv`
- `test_signals_latest.csv`
- `test_returns_latest.csv`
- `runs/<timestamp>.json`

---

## 8. 运行方式

```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.momentum_v1.run
```

---

## 9. 后续可选优化

- 波动调整动量（signal / vol）
- 多空构建（top/bottom 分位）
- 动量+质量因子组合
