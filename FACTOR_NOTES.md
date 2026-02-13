# 因子笔记（逻辑与注意事项）

最后核查：2026-02-12

目的：记录每个因子的实现逻辑、关键参数与可能的偏差来源。

---

## 0) 因子状态总览（已完成 vs 候选/进行中）

**已完成验证（Stage 1/2 + Train/Test）**
- Value（通过）：`segment_results/2026-02-10_015525` / `segment_results/2026-02-10_222028`；`strategies/value_v1/runs/2026-02-12_163841.json`（新口径 Test IC ≈ 0.04176）
- Quality（未通过）：`segment_results/2026-02-10_135559` / `segment_results/2026-02-10_223438`；`strategies/quality_v1/runs/2026-02-12_135607.json`
- Low-vol（未通过）：`segment_results/2026-02-10_012143` / `segment_results/2026-02-10_213821`；`strategies/low_vol_v1/runs/2026-02-12_143900.json`

**候选/进行中**
- Momentum：未开始（已清理所有动量回测产物）
- Reversal：未开始分段/Train-Test
- PEAD：未开始分段/Train-Test

**执行口径（机构默认）**
- 交易日执行与动态成本为默认（`EXECUTION_USE_TRADING_DAYS = True`, `ENABLE_DYNAMIC_COST = True`）
 - 新口径结果未产出前，旧口径结果保留为参考

---

## 1) Momentum（动量）

当前实现（已修正）：
- 默认日频动量：`log(price[t-skip] / price[t-lookback-skip])`
- 参数：
  - `MOMENTUM_LOOKBACK = 126`
  - `MOMENTUM_SKIP = 21`
  - `MOMENTUM_VOL_LOOKBACK = None`
- `MOMENTUM_ZSCORE = False`（不做横截面标准化）
- `MOMENTUM_USE_MONTHLY = False`
- `MOMENTUM_LOOKBACK_MONTHS = 6`（保留配置，当前不启用）
- `MOMENTUM_SKIP_MONTHS = 1`（保留配置，当前不启用）
- `MOMENTUM_WINSOR_Z = None`（不做极值裁剪）
- `INDUSTRY_NEUTRAL = False`（不做行业中性化）
- `UNIVERSE_MAX_VOL = None`（不做波动率过滤）

注意：
- 历史分段 IC 多数为负，可能仍存在口径问题
- 如果反向动量显著转正，说明方向问题为主
- 后续可考虑“月度动量”口径（更标准）
- 备注：IC 现已按“全信号 forward returns”计算，旧口径（仅已建仓位）
  会低估/扭曲 IC
- 验证状态：
  - 分段 Stage 1 已完成：`segment_results/2026-02-12_150619`
  - 分段 Stage 2 未完成（已启动未产出结果）

---

## 2) Reversal（短期反转）

当前实现：
- 默认日内反转：`-(Close/Open - 1)`
- 参数：
  - `REVERSAL_LOOKBACK = 3`
  - `REVERSAL_MODE = "intraday"`
  - `REVERSAL_VOL_LOOKBACK = 20`
  - `REVERSAL_EARNINGS_FILTER_DAYS = 1`
- 日频调仓，持有 1 天

注意：
- 日频回测在 M1 上较慢
- 过滤财报日可减少噪声
- 验证状态：未开始分段/Train-Test

---

## 3) Quality（质量）

当前实现（组合口径 v2）：
- ROE + ROA + 毛利率 + CFO/资产 + 负债惩罚（debt_to_equity 负权重）
- 数据来自 `data/fmp/ratios/quality/`

注意：
- 若未重建 quality fundamentals，新字段（ROA / debt_to_equity）会缺失
- 信号取“截至 signal_date 的最新可用值”（PIT: available_date）
- Stage 2（机构版）建议：行业 + size/beta 中性后再做 zscore
- 验证状态：
  - 分段：Stage 1 `segment_results/2026-02-10_135559`；Stage 2 `segment_results/2026-02-10_223438`
  - Train/Test：`strategies/quality_v1/runs/2026-02-12_135607.json`（Test IC ≈ 0.00126）

---

## 4) Value（估值）

当前实现：
- Earnings Yield + FCF Yield + EV/EBITDA Yield 等权
- 数据来自 `data/fmp/ratios/value/`

注意：
- 与 Quality 类似，缓存质量影响信号数量
- Stage 2（机构版）建议：行业 + size/beta 中性后再做 zscore
- 验证状态：
  - 分段：Stage 1 `segment_results/2026-02-10_015525`；Stage 2 `segment_results/2026-02-10_222028`
  - Train/Test：`strategies/value_v1/runs/2026-02-12_133236.json`（Test IC ≈ 0.0405）

---

## 5) Low-vol（低波动）

当前实现：
- 残差 + 下行波动率（更接近机构低波口径）
- 关键开关：
  - `LOW_VOL_USE_RESIDUAL=True`（以 SPY 残差波动作为低波指标）
  - `LOW_VOL_DOWNSIDE_ONLY=True`（只统计下行波动）

注意：
- residual 模式更接近“风险调整”的低波口径
- Stage 2（机构版）建议：行业中性 + size/beta 中性（`SIGNAL_NEUTRALIZE_SIZE/BETA`）
- 验证状态：
  - 分段：Stage 1 `segment_results/2026-02-10_012143`；Stage 2 `segment_results/2026-02-10_213821`
  - Train/Test：`strategies/low_vol_v1/runs/2026-02-12_143900.json`（Test IC ≈ 0.0000836）

---

## 6) PEAD（盈利漂移）

当前实现：
- `ShiftedPEADFactor` 对齐
- 仅在 `earnings_date == signal_date + 1` 时触发
- 执行在 earnings_date 当日开盘

注意：
- 只在 rebalance date 扫描事件
- 调仓频率会影响事件捕捉覆盖
- 近期基于新 IC（全信号 forward returns）验证为弱正（2010-2016 三段）
- 验证状态：未开始分段/Train-Test
