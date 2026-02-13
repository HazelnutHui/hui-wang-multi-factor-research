# V4 操作手册（快速上手）

最后核查：2026-02-12

面向：下一次打开 Codex 能快速上手并继续回测/分析。

---

## 1) 环境

- Python：`/Users/hui/miniconda3/envs/qscore/bin/python`
- 工作目录：`/Users/hui/quant_score/v4`
- 注意：脚本用到 `PYTHONPATH` 时建议在命令前加：
  - `PYTHONPATH=/Users/hui/quant_score/v4`

## 1.1) 定位（日频，不做高频）
- 目标：**日频量化评分与回测**
- 数据口径：常规交易时段 **open/close** 的日线级别
- 不支持高频日内信号或逐笔交易级别
- 执行时点可灵活建模，但核心信号来自日频数据

## 1.1.1) 当前研究意图（2026-02-10）
- 先单因子稳定性（分段 IC + 固定 train/test）
- Stage 1 作为默认基线；Stage 2 为机构版稳健性对照
- 至少 2–3 个稳定因子后再进入组合

## 1.2) 因子验证流程（推荐）
1. **分段回测（Stage 1 基线）**
   - 默认口径：winsor（1%/99%）+ rank 标准化
   - Stage 2（行业中性 + 平滑 + zscore）仅作稳健性对照
2. **固定 train/test**
   - 仅对“分段稳定”的因子执行
3. **多因子组合**
   - 至少 2–3 个因子稳定后再做组合
4. **Walk-forward**
   - 成本高，放在组合稳定之后

## 1.2.1) 单因子完整基线（新增）
- 完整清单见：`SINGLE_FACTOR_BASELINE.md`
- 覆盖：Stage 1 → Stage 2 → Train/Test → 专业报告 → 鲁棒性/成本/子样本

## 1.3) 路径与数据分类（统一命名）
**FMP 数据集索引**
- `data/fmp/DATASETS.md`（API 名称 ↔ 端点 ↔ 输出目录）

**核心数据目录**
- 价格：`data/prices/`, `data/prices_divadj/`, `data/prices_delisted/`, `data/prices_delisted_divadj/`
- FMP 比率（Value）：`data/fmp/ratios/value/`
- FMP 比率（Quality）：`data/fmp/ratios/quality/`（组合口径 v2：含 ROA 与 debt_to_equity）
- Earnings（PEAD）：`data/Owner_Earnings/`
- 市值历史：`data/fmp/market_cap_history/`

**回测输出目录**
- 分段：`segment_results/<timestamp>/`
- Walk-forward：`walk_forward_results/<timestamp>/`
- 单策略：`strategies/<name>/results/`（旧脚本）

## 1.4) 因子处理管线（阶段 1 / 2）

**阶段 1（最小可用）**
- 数据清洗：`DataQualityFilter`
- 去极值：`SIGNAL_WINSOR_PCT_LOW/HIGH`（默认 1%/99%）
- 标准化：`SIGNAL_RANK = true`

**阶段 2（机构版）**
- 行业中性：`INDUSTRY_NEUTRAL = true`（需要 `industry_map_path`）
- size/beta 中性：`SIGNAL_NEUTRALIZE_SIZE=True`、`SIGNAL_NEUTRALIZE_BETA=True`（`BETA_LOOKBACK` 可调）
- 平滑（可选）：`SIGNAL_SMOOTH_WINDOW`（SMA）或 `SIGNAL_SMOOTH_METHOD=ema` + `SIGNAL_SMOOTH_ALPHA`
- PIT：已完成（`available_date`）
- 波动/流动性过滤：`UNIVERSE_MAX_VOL`, `MIN_DOLLAR_VOLUME`, `MIN_PRICE`
 - 启用方式：在对应策略 `config.py` 中将 `SIGNAL_ZSCORE=True`，`SIGNAL_RANK=False`，`INDUSTRY_NEUTRAL=True`，并设置 `SIGNAL_NEUTRALIZE_SIZE/BETA=True`（可选平滑）

## 1.5) 执行口径（交易日 vs 自然日）
**默认改为交易日偏移**（更接近机构执行口径）：
- `EXECUTION_USE_TRADING_DAYS = True`
- 使用交易日历（`CALENDAR_SYMBOL` 优先，默认 SPY）

容量/冲击成本（默认启用动态成本模型，参数可调）：
- `ENABLE_DYNAMIC_COST = True`
- `TRADE_SIZE_USD`：单笔成交金额假设（仅在动态成本模型启用时生效）

---

## 2) 最常用命令

### 2.1 分段回测（两年一段）
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --factors momentum --years 2
```

PEAD / Low-vol 分段：
```bash
PYTHONPATH=/Users/hui/quant_score/v4 /Users/hui/miniconda3/envs/qscore/bin/python \
  /Users/hui/quant_score/v4/scripts/run_segmented_factors.py --factors pead --years 2
```
```bash
PYTHONPATH=/Users/hui/quant_score/v4 /Users/hui/miniconda3/envs/qscore/bin/python \
  /Users/hui/quant_score/v4/scripts/run_segmented_factors.py --factors low_vol --years 2
```

只跑前三段：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --factors momentum --years 2 --max-segments 3
```

断点续跑：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --factors momentum --years 2 --resume --out-dir /Users/hui/quant_score/v4/segment_results/<timestamp>
```

反向动量（方向验证）：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_segmented_factors.py \
  --factors momentum --invert-momentum --max-segments 3
```

### 2.1.1 重建 Quality fundamentals（组合口径 v2）
```bash
FMP_API_KEY="$FMP_API_KEY" /Users/hui/miniconda3/envs/qscore/bin/python \
  /Users/hui/quant_score/v4/scripts/download_quality_fundamentals.py --overwrite
```

### 2.2 固定 train/test 回测（单策略）
```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m strategies.momentum_v1.run
```
可选交易日执行口径（不改变默认结果）：
```bash
PYTHONPATH=/Users/hui/quant_score/v4 /Users/hui/miniconda3/envs/qscore/bin/python3.11 \
  -m strategies.value_v1.run --exec-trading-days
```

### 2.2.1 统一协议入口（推荐）
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_with_config.py \
  --strategy /Users/hui/quant_score/v4/configs/strategies/momentum_v1.yaml
```

### 2.3 Walk-forward（滚动训练/测试）
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --factors momentum --train-years 3 --test-years 1 --start-year 2010 --end-year 2026
```

只跑前 3 个窗口：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --factors momentum --max-windows 3
```

断点续跑：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --factors momentum --resume --out-dir /Users/hui/quant_score/v4/walk_forward_results/<timestamp>
```

### 2.4 拉取行业映射（FMP profile-bulk）
生成 `data/company_profiles.csv`（含 `symbol/sector/industry`）：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/fmp_profile_bulk_to_csv.py \
  --api-key "<FMP_API_KEY>" \
  --out /Users/hui/quant_score/v4/data/company_profiles.csv
```

### 2.4.1 拉取市值历史（FMP market-capitalization）
生成 `data/fmp/market_cap_history/*.csv`（PIT 市值过滤用）：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/fmp_market_cap_history.py \
  --api-key "$FMP_API_KEY" \
  --symbols-csv /Users/hui/quant_score/v4/data/fmp/historical_stock_list.csv \
  --out-dir /Users/hui/quant_score/v4/data/fmp/market_cap_history \
  --from-date 2010-01-01 \
  --limit 1000 \
  --sleep 0.25
```
注意：不要把 `<FMP_API_KEY>` 当作字面值传入，会触发 401。

更新（最后核查：2026-02-08）：
- FMP 历史市值接口单次最大 5000 行，建议分段拉取：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/fmp_market_cap_history.py \
  --api-key "$FMP_API_KEY" \
  --symbols-csv /Users/hui/quant_score/v4/data/fmp/symbols_us_basic.csv \
  --out-dir /Users/hui/quant_score/v4/data/fmp/market_cap_history \
  --from-date 2010-01-01 --to-date 2026-01-28 \
  --chunk-years 2 --limit 5000 --sleep 0.25 \
  --retries 3 --retry-sleep 1 --overwrite
```
- 如果 Python DNS 不稳定，可改用 curl 脚本：
```bash
/Users/hui/quant_score/v4/scripts/fmp_market_cap_history_curl.sh
```

### 2.5 专业因子报告（Markdown + JSON + CSV）
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/generate_factor_report.py \
  --strategy /Users/hui/quant_score/v4/configs/strategies/momentum_v1.yaml \
  --quantiles 5 --rolling-window 60 --cost-multipliers 2,3
```

### 2.6 测试（look-ahead / lag / 标准化）
```bash
/Users/hui/miniconda3/envs/qscore/bin/python -m pytest /Users/hui/quant_score/v4/tests
```

### 2.7 Post-hoc 诊断（不影响回测）
读取 `*_latest.csv` 与最新 `runs/*.json`，输出到 `strategies/<factor>/reports/`。
```bash
# 全部因子（有 results 的）
/Users/hui/miniconda3/envs/qscore/bin/python3.11 /Users/hui/quant_score/v4/scripts/posthoc_factor_diagnostics.py --all

# 单个因子
/Users/hui/miniconda3/envs/qscore/bin/python3.11 /Users/hui/quant_score/v4/scripts/posthoc_factor_diagnostics.py \
  --strategy strategies/value_v1
```

### 2.8 投委级检查清单（汇总报告，不影响回测）
生成跨因子汇总的 checklist（含稳定性、Train/Test、暴露与换手）。
```bash
/Users/hui/miniconda3/envs/qscore/bin/python3.11 /Users/hui/quant_score/v4/scripts/committee_checklist.py
```

---

## 3) 输出路径速查

- 分段回测输出：
  - `segment_results/<timestamp>/factor/segment_summary.csv`
- Walk-forward 输出：
  - `walk_forward_results/<timestamp>/factor/walk_forward_summary.csv`
- 单策略回测输出：
  - `strategies/<name>/results/`
- 专业因子报告：
  - `strategies/<name>/reports/`

---

## 4) 常见问题

- 分段结果迟迟不出来？
  - 先看 `ps aux | grep "run_segmented_factors.py" | grep -v grep` 是否在跑
  - 再看日志

- IC 为 None？
  - 样本过少或信号过少（n_dates 很小）
  - 目前 IC 使用全信号 forward returns（非仅建仓位）

- 为什么新入口和旧入口结果不同？
  - 确认使用同一份协议与策略覆盖（`configs/`）
  - 确认 `factors.lag_days` 与各因子 `lag_days` 设置一致
