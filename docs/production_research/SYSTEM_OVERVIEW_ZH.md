# V4 量化研究系统白皮书（中文）

Last updated: 2026-02-28

## 0. 文档定位与阅读顺序

本文档面向首次接触该系统的读者，目标是建立完整的结构认知与流程认知。

阅读顺序采用“先总后分”：

1. 先看系统全景（第 1-3 节）
2. 再看核心执行链（第 4-7 节）
3. 再看治理、自动化与审计（第 8-12 节）
4. 最后看运行边界与演进方向（第 13-15 节）

本文档为客观技术说明，不含主观叙述与人称指代。

当前运行快照（2026-02-28）：
1. 重置前历史结果：已退役（当前决策不作为正式结果使用）。
2. 当前在跑批次：`batchA100_logic100_formal_v1`（工作站运行中）。
   - run id：`2026-02-28_095939_batchA100_logic100_formal_v1`
3. formal 逻辑覆盖：`100/100` 已映射到运行入口（含原生/代理实现分类）。
4. 治理边界：
   - 后续新批次/新队列仍需人工审批后才能启动。
   - 审批门文件：`configs/research/factory_queue/run_approval.json`

---

## 1. 系统全景

V4 是一套面向美股日频因子研究的生产级研究系统。系统设计目标不是“单次回测”，而是“可持续研究流水线”，核心特征如下：

1. 研究流程标准化：单因子、组合、压力测试采用统一协议与统一入口。
2. 结果可复现：运行配置哈希、代码版本、输出路径全部落盘。
3. 风险可控：在执行前后设置数据质量、统计与治理门禁。
4. 过程可审计：每一阶段有对应 JSON/MD/CSV 产物。
5. 交接可连续：新会话可通过固定导读协议恢复上下文。

---

## 2. 系统分层架构

系统按职责划分为六层。

### 2.1 数据与基础设施层

核心模块：

- `backtest/data_engine.py`：价格与基础数据访问
- `backtest/delisting_handler.py`：退市情形处理
- `backtest/market_cap_engine.py`：市值历史数据读取
- `backtest/data_quality_filter.py`：执行阶段数据质量过滤

职责：

- 提供统一数据接口
- 控制退市与缺失数据带来的偏差
- 为上层因子计算、交易执行提供一致输入

### 2.2 因子计算与信号标准化层

核心模块：

- `backtest/factor_engine.py`
- `backtest/fundamentals_engine.py`
- `backtest/value_fundamentals_engine.py`
- `backtest/factor_factory.py`

职责：

- 计算动量、反转、价值、质量、低波、PEAD 等因子
- 处理因子发布日期与滞后控制（PIT/lag）
- 执行标准化流程：winsor / rank / zscore / 中性化

### 2.3 可交易股票池层

核心模块：

- `backtest/universe_builder.py`

职责：

- 基于价格、成交额、市值、波动率等约束构建可交易池
- 输出逐次调仓点的 universe 过滤审计记录

### 2.4 回测执行与成交模拟层

核心模块：

- `backtest/backtest_engine.py`
- `backtest/execution_simulator.py`
- `backtest/cost_model.py`

职责：

- 生成调仓日期（支持交易日频率与 month_end 模式）
- 进行建仓/平仓执行价格模拟与交易成本注入
- 计算持有期收益、前瞻收益及过滤统计

### 2.5 绩效评估层

核心模块：

- `backtest/performance_analyzer.py`
- `backtest/walk_forward_validator.py`

职责：

- 计算 IC、分期 IC、t 统计、收益分布与胜率
- 将“研究结论”转换为可比较指标体系

### 2.6 治理与自动化层

核心模块：

- 治理：`scripts/research_governance.py`、`scripts/governance_audit_checker.py`
- 自动化：`scripts/auto_research_orchestrator.py`、`scripts/auto_research_scheduler.py`
- 参数搜索：`scripts/build_search_v1_trials.py`

职责：

- 保障运行可追溯
- 把手工研究流程升级为可调度、可收敛的自动研究流程

---

## 3. 统一执行入口与配置体系

### 3.1 统一入口

系统统一入口：`scripts/run_research_workflow.py`

支持工作流：

1. `train_test`（固定训练/测试）
2. `segmented`（分段回测）
3. `walk_forward`（滚动前推）
4. `production_gates`（生产门禁评估）

统一入口的作用是把不同研究任务收敛到同一调度和审计框架。

### 3.2 配置结构

配置由“协议层 + 策略层”合并形成最终执行配置：

- 协议层：`configs/protocol.yaml`（全局默认约束）
- 策略层：`configs/strategies/*.yaml`（策略差异化参数）

组合策略生产配置示例：`configs/strategies/combo_v2_prod.yaml`

该配置体系的结果是：

- 同一协议可驱动不同策略
- 策略变更可被审计记录
- 运行命令可复用、可批量化

---

## 4. 单因子研究流程（从信号到评估）

### 4.1 单因子定义方式

单因子在 `scripts/run_segmented_factors.py` 中通过 `FACTOR_SPECS` 映射定义：

- 配置文件路径（`strategies/<factor>/config.py`）
- 因子权重（例如 value=1.0，其余为 0）

该映射使单因子实验具备一致执行接口与可比性。

### 4.2 单次回测内部链路

在 `BacktestEngine.run_backtest()` 中，单次回测按以下顺序执行：

1. 生成调仓日期序列
2. 每个调仓日构建可交易股票池（`UniverseBuilder`）
3. 计算截面信号（`FactorEngine.compute_signals`）
4. 信号平滑（可选）
5. 头寸构建（`build_positions`）
6. 成交与成本模拟（`ExecutionSimulator.execute_trades`）
7. 收益与前瞻收益计算
8. IC 与分期统计分析
9. 写出过滤统计与 universe audit

### 4.3 信号标准化机制

`factor_factory.standardize_signal()` 提供统一处理链：

1. 缺失值策略（drop/fill/keep）
2. 分位数 winsor（可选）
3. rank 或 zscore
4. 行业内中性化与多因子暴露中性化（可选）
5. z 范围截断（winsor_z）

该机制用于保证跨因子的信号可比性。

---

## 5. 三层验证框架（Layer1 -> Layer2 -> Layer3）

系统采用三层验证，不通过前层不进入后层。

### 5.1 Layer1：分段稳健性验证（Segmented）

入口：`scripts/run_segmented_factors.py`

特征：

- 按固定窗口切分（典型为 2 年段）
- 观察各阶段 IC 均值、波动、正收益占比
- 输出 `all_factors_summary.csv` 等分段汇总

目标：识别“跨时期不稳定”因子，过滤脆弱候选。

### 5.2 Layer2：固定训练/测试（Train/Test）

入口：`scripts/run_with_config.py` 或策略 `run.py`

特征：

- 使用固定 train/test 切分
- 对比样本内外性能衰减
- 输出 runs JSON、signals/returns CSV

目标：检验样本外退化，避免纯样本内拟合。

### 5.3 Layer3：滚动前推（Walk-Forward）

入口：`scripts/run_walk_forward.py`

特征：

- 滚动训练窗口 + 前推测试窗口
- 更接近真实部署时序
- 支持 `--wf-shards` 分片并行

目标：模拟持续再训练部署场景下的稳定性。

---

## 6. 组合因子系统（从单因子到组合）

### 6.1 组合构建逻辑

组合策略基线：`strategies/combo_v2/`

核心思想：

1. 先通过单因子三层验证筛选核心因子
2. 将通过因子纳入组合权重空间
3. 在组合层继续执行三层验证与门禁

当前组合配置采用 `value + momentum` 为核心结构。

### 6.2 组合公式机制

组合支持多公式模式（见 `strategies/combo_v2/config.py`）：

1. `linear`
2. `value_momentum_gated`
3. `value_momentum_two_stage`

该设计允许在同一输入数据与同一门禁下进行公式对比。

### 6.3 组合验证路径

组合遵循与单因子一致的三层路径：

1. Layer1 组合分段回测
2. Layer2 固定 train/test
3. Layer3 walk-forward

组合结果只有在三层均满足约束时，才进入生产门禁阶段。

---

## 7. 生产门禁系统（Production Gates）

入口：`scripts/run_production_gates.py`

### 7.1 门禁组成

生产门禁由四类检查组成：

1. 成本压力（cost multipliers）
2. 更严格股票池下的 walk-forward 压力测试
3. 风险诊断（beta、换手重叠、规模相关、行业覆盖）
4. 统计门禁（BH-FDR 多重检验）

### 7.2 结果产物

输出目录：`gate_results/production_gates_<ts>/`

关键产物：

- `production_gates_report.json/.md`
- `cost_stress_results.csv`
- `walk_forward_stress/...`
- 关联 registry 条目（可选）

### 7.3 决策意义

生产门禁将“研究指标良好”与“可部署风险可接受”区分开，避免直接由回测结果推导部署结论。

---

## 8. 治理与可追溯机制

### 8.1 Freeze 与 Manifest

核心脚本：`scripts/research_governance.py`

机制：

1. `build_manifest()`：记录运行范围、CLI 参数、配置哈希、代码版本
2. `enforce_freeze()`：校验当前运行与冻结配置一致

作用：确保复现实验时，配置与代码版本一致可验证。

### 8.2 Guardrails

在核心 runner 中默认启用：

- lag 非负检查
- 必需目录存在性检查
- PIT 相关数据路径检查

作用：在运行前阻断明显配置风险。

### 8.3 治理审计检查

脚本：`scripts/governance_audit_checker.py`

作用：检查阶段产物完整性、结构一致性与收尾状态。

---

## 9. 自动研究闭环

自动研究目标是把“候选筛选 -> 计划生成 -> 执行验证”系统化。

### 9.1 候选与计划链

1. `scripts/update_factor_experiment_registry.py`
2. `scripts/generate_candidate_queue.py`
3. `scripts/generate_next_run_plan.py`
4. `scripts/repair_next_run_plan_paths.py`
5. `scripts/execute_next_run_plan.py`

对应文档：

- `FACTOR_EXPERIMENT_REGISTRY.md`
- `CANDIDATE_QUEUE_POLICY.md`
- `NEXT_RUN_PLANNING.md`
- `NEXT_RUN_EXECUTION_STANDARD.md`

### 9.2 Orchestrator

脚本：`scripts/auto_research_orchestrator.py`

单轮步骤：

1. 生成候选队列
2. 生成 next-run plan
3. 修复 plan 路径与标签
4. dry-run 验证命令
5. （可选）真实执行

并支持预算控制、重试与停机条件（如 no-improvement）。

### 9.3 Scheduler

脚本：`scripts/auto_research_scheduler.py`

职责：

- 按周期触发 orchestrator
- 维护 lock/heartbeat/ledger
- 故障告警与去重

支持模式：

- `standard`
- `low-network`（低联网默认模式）

---

## 10. Search V1 参数搜索系统

### 10.1 目标

Search V1 用于在固定组合框架下进行参数网格/随机搜索，形成可追溯 trial 计划。

### 10.2 组件

- 策略：`configs/research/auto_research_search_v1_policy.json`
- 执行：`scripts/build_search_v1_trials.py`
- 规范：`docs/production_research/AUTO_RESEARCH_SEARCH_V1.md`

### 10.3 运行结果

每次运行输出：

- trial 计划 JSON/MD/CSV
- 每个 trial 派生策略 YAML
- 执行报告 JSON

路径：`audit/search_v1/<ts>_search_v1/`

作用：为后续批量重算与候选收敛提供结构化输入。

---

## 11. 审计产物体系（按目录）

### 11.1 研究与调度

- `audit/auto_research/`：编排与调度账本、心跳、健康摘要

### 11.2 候选与计划

- `audit/factor_registry/`：实验注册表、候选队列、计划文件

### 11.3 失败反馈

- `audit/failure_patterns/`：失败模式数据库与汇总

### 11.4 交接与收口

- `audit/session_handoff/`：会话交接可读性检查
- `audit/system_closure/`：阶段收口报告

### 11.5 结果门禁

- `gate_results/production_gates_<ts>/`：生产门禁报告

---

## 12. 会话连续性与知识传承机制

### 12.1 单入口导读协议

入口文件：`SESSION_CONTINUITY_PROTOCOL.md`

作用：

1. 固定新会话阅读顺序
2. 固定 completion checks
3. 固定冲突优先级（SSOT）

### 12.2 可读性门禁

脚本：`scripts/check_session_handoff_readiness.py`

检查项：

- 必读文件是否存在
- 索引文档是否可达
- completion references 是否可定位

该门禁保障“新会话可接管”。

---

## 13. 运行环境分工

### 13.1 本地环境职责

- 文档编制与治理规则维护
- 轻量调试与 dry-run 验证
- 提交与版本管理

### 13.2 工作站职责

- 重计算（walk-forward、分片并行）
- 长周期自动调度
- 官方运行执行与监控

推荐并行参数：

- `--threads 8`
- `--wf-shards 4`

---

## 14. 当前能力边界

### 14.1 已形成能力

1. 单因子 -> 组合 -> 三层验证 的完整路径
2. 生产门禁（成本、风险、统计）
3. 自动研究编排与调度
4. 低联网运行模式
5. 全链路审计与交接检查

### 14.2 待增强能力

1. Search trial 结果自动回写统一 leaderboard
2. 多目标自动收敛（收益、稳定性、容量联合优化）
3. 更细粒度策略版本对比与自动回滚机制

---

## 15. 总结

V4 的核心价值不在单次回测性能，而在“研究工程化能力”：

1. 结构清晰：模块边界明确，入口统一
2. 流程完整：单因子、组合、三层验证闭环
3. 风险可控：门禁前置，治理后置
4. 审计完备：关键动作可追踪、可复核、可交接

该结构使系统从“脚本集合”升级为“生产级研究基础设施”。
