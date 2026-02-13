# A 股迁移状态（给下次打开 Codex 的人）

更新时间：2026-02-05（无新增进展）

## 目标与意图
- 在保持美股框架不变的前提下，**隔离出 A 股协议与数据管线**，逐步迁移与验证。
- 先用 **免费数据源（AKShare）做最小验证**，确认框架能跑通。
- 若验证有效，再切换到 **Tushare Pro（付费）**，获取 PIT/停牌/退市等“实盘级”数据。

---

## 已完成的架构改造（A 股适配）

### 1) 新协议 + 最小验证策略
- 新协议：`configs/protocol_cn.yaml`
- 最小验证策略：`configs/strategies/cn_reversal_v1.yaml`
  - 只做多：`short_pct = 0.0`
  - 反转因子为第一优先验证

### 2) 市场规则扩展（引擎层）
已加入下列开关（可由协议配置）：
- **涨跌停过滤**：`apply_limit_up_down` + `limit_up_down_pct`
- **印花税**：`apply_stamp_tax` + `stamp_tax_rate`
- **成本倍数**：`cost_multiplier`

已改动文件：
- `backtest/execution_simulator.py`
- `backtest/backtest_engine.py`
- `scripts/run_with_config.py`（透传配置）

### 3) 黑名单隔离
虽然是美股遗留，但机制可复用：
- `UNIVERSE_EXCLUDE_SYMBOLS_PATH` 已支持
- A 股协议里预留：`../data/cn/blacklist_symbols.txt`

---

## 已新增 A 股数据脚本（AKShare）

### 股票池
- `scripts/akshare_stock_list.py`
  - 默认 `ak.stock_zh_a_spot_em()` + 自动重试
  - 失败后回退 `ak.stock_zh_a_spot()`

### 日线行情
- `scripts/akshare_download_daily.py`
  - 读取股票池 CSV
  - 下载复权日线（qfq）
  - 输出到 `data/cn/prices/`（按 symbol .pkl）

---

## 当前进度（A 股）

1) **AKShare 依赖已装**
- 使用 `qscore` 环境安装成功

2) **股票池拉取失败（待重试）**
- 错误：`RemoteDisconnected`（AKShare 源站断连）
- 已更新脚本支持重试 + fallback
- 尚未成功拉到 `data/cn/stock_list.csv`

3) **Tushare Pro 尚未接入**
- 用户计划购买 **2000 积分/年**（先试用）
- Token 未提供
- 数据管线尚未落地

---

## A 股最小验证的标准流程（待执行）

1) 拉股票池：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/akshare_stock_list.py
```

2) 下载日线：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/akshare_download_daily.py \
  --symbols-csv /Users/hui/quant_score/v4/data/cn/stock_list.csv
```

3) 跑最小验证（反转）：
```bash
/Users/hui/miniconda3/envs/qscore/bin/python /Users/hui/quant_score/v4/scripts/run_with_config.py \
  --protocol /Users/hui/quant_score/v4/configs/protocol_cn.yaml \
  --strategy /Users/hui/quant_score/v4/configs/strategies/cn_reversal_v1.yaml
```

---

## 接下来最重要的三件事

1) **成功拉取 AKShare 股票池**  
如果重复失败，考虑：
- 尝试不同时间段重试
- 改用 Tushare 作为股票池

2) **接入 Tushare Pro（付费后）**
需要：
- `TUSHARE_TOKEN`
- 确定数据范围（建议 2015–2025）

3) **A 股市场规则细化**
后续可加入：
- 停牌过滤（不可交易）
- ST 股票过滤
- 次新股过滤（上市<1年）

---

## 关键文件索引

- A 股协议：`configs/protocol_cn.yaml`
- A 股最小策略：`configs/strategies/cn_reversal_v1.yaml`
- AKShare 股票池：`scripts/akshare_stock_list.py`
- AKShare 日线：`scripts/akshare_download_daily.py`
- 执行规则：`backtest/execution_simulator.py`
- 统一入口：`scripts/run_with_config.py`
