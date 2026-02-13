# 策略总览（中文）

本文档简洁说明当前各策略的设计思路、结构与组合思路。所有策略默认 **盘后计算信号，次日开盘执行**。

---

## 1) 策略列表与逻辑

### 1.1 PEAD（`pead_v1`）
- **逻辑**：基于财报 SUE（盈利惊喜）捕捉公告后漂移。
- **关键点**：事件型因子；对公告时点敏感；信号稀疏。
- **当前设定**：`DATE_SHIFT_DAYS=0`，`HOLDING=1`。
- **数据类型**：Earnings Report（EPS 实际/预期）、日频价格。
- **核心公式**：  
  - Surprise = EPS_actual − EPS_est  
  - SUE = Surprise / rolling_std(Surprise, 8q)  
  - 信号：若 |SUE| > 阈值，signal = SUE

### 1.2 短期反转（`reversal_v1`）
- **逻辑**：日内反转（当日涨多的次日回落、跌多的次日反弹）。
- **信号**：`-(Close/Open - 1)`，并做波动缩放。
- **特性**：日频更新、成本敏感。
- **数据类型**：日频 OHLCV。
- **核心公式**：  
  - 日内收益 = Close_t / Open_t − 1  
  - signal = − 日内收益  
  - 可选缩放：signal / vol_20

### 1.3 中期动量（`momentum_v1`）
- **逻辑**：12-1 动量（12 个月趋势，跳过最近 1 个月）。
- **信号**：`(P_{t-21}/P_{t-252}-1)`，波动缩放。
- **特性**：慢因子，月度调仓。
- **数据类型**：复权日频价格。
- **核心公式**：  
  - mom_12-1 = P_{t-21} / P_{t-252} − 1  
  - 可选缩放：mom_12-1 / vol_60

### 1.4 质量（`quality_v1`）
- **逻辑**：盈利能力 + 现金流质量。
- **指标**：ROE、毛利率、CFO/资产。
- **特性**：季度更新，稳健。
- **数据类型**：财务报表/TTM（利润表、资产负债表、现金流量表）。
- **核心公式**：  
  - ROE = NetIncome / Equity  
  - GrossMargin = GrossProfit / Revenue  
  - CFO/Assets = OperatingCashFlow / TotalAssets  
  - score = w1·ROE + w2·GrossMargin + w3·CFO/Assets

### 1.5 估值（`value_v1`）
- **逻辑**：便宜公司长期回归。
- **指标**：盈利收益率（1/PE）、FCF收益率（1/PFCF）、EV/EBITDA收益率。
- **特性**：季度更新，慢因子。
- **数据类型**：TTM 比率（PE、P/FCF、EV/EBITDA）。
- **核心公式**：  
  - EY = 1 / PE  
  - FCFY = 1 / (P/FCF)  
  - EVEBITDAY = 1 / (EV/EBITDA)  
  - score = w1·EY + w2·FCFY + w3·EVEBITDAY

---

## 2) 结构与模块

- `strategies/<strategy_name>/run.py`：策略入口（生成 signals/returns/report）
- `strategies/<strategy_name>/config.py`：策略参数
- `backtest/`：统一回测引擎、执行器、因子计算
- `data/`：价格/财务/事件数据缓存

---

## 3) 策略组合思路（推荐）

**组合原则**：互补性优先、时间尺度分层。

### 推荐组合（稳健起步）
- **动量（中期）**：主因子
- **反转（短期）**：补充短期回归
- **质量/估值**：作为慢变量稳定器

### 组合方式
1) **线性加权**（最简单）：
   - 先对各因子横截面标准化（z-score 或 rank）
   - 再按权重求和
2) **分层筛选**：
   - 先筛质量/估值优良，再在其中选动量或反转信号

---

## 4) 使用建议

- PEAD 对时点敏感，建议先作为观察策略。
- 反转适合日频，但注意交易成本。
- 动量适合月度调仓，稳健性高。
- 质量/估值因子是长期稳定器。

---

## 5) 运行方式

示例：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.reversal_v1.run
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.momentum_v1.run
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.quality_v1.run
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.value_v1.run
```
