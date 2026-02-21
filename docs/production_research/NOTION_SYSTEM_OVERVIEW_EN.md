# V4 Quant Research System | Detailed Notion Version (English)

Last updated: 2026-02-21

## 0. Document Purpose

This document is a full-structure system description for readers with no prior context of the V4 stack.

Primary goals:
1. explain system architecture end-to-end;
2. explain research logic from single-factor testing to portfolio promotion;
3. explain governance gates, audit evidence, and automation loop;
4. provide an operational map for continuation and review.

This is a technical system description, not a strategy marketing note.

---

## 1. System Definition

V4 is a production-grade quantitative equity research system designed for repeatable, auditable, and governable factor research.

It is intentionally built as a research operating system rather than a set of ad-hoc backtest scripts.

Core properties:
- unified workflow entry;
- layered validation framework;
- strict pre/post-run governance checks;
- append-only audit artifacts;
- continuity protocol for new-session handoff.

---

## 2. Architectural Layers

The platform is organized into six functional layers.

### 2.1 Data and Infrastructure Layer

Main components:
- `backtest/data_engine.py`
- `backtest/market_cap_engine.py`
- `backtest/delisting_handler.py`
- `backtest/data_quality_filter.py`

Responsibilities:
- load price/fundamental/market-cap data under a unified interface;
- handle delisting-aware paths to reduce survivorship bias;
- provide consistency checks for downstream execution.

### 2.2 Factor and Signal Layer

Main components:
- `backtest/factor_engine.py`
- `backtest/fundamentals_engine.py`
- `backtest/value_fundamentals_engine.py`
- `backtest/factor_factory.py`

Responsibilities:
- compute factors (momentum, reversal, value, quality, low-vol, PEAD, etc.);
- enforce point-in-time timing via lag/date-resolution logic;
- standardize cross-sectional signals (winsor/rank/zscore/neutralization).

### 2.3 Tradable Universe Layer

Main component:
- `backtest/universe_builder.py`

Responsibilities:
- construct tradable universe by min price, dollar volume, market cap, and optional volatility filters;
- generate universe filter audit records at each rebalance date.

### 2.4 Backtest and Execution Layer

Main components:
- `backtest/backtest_engine.py`
- `backtest/execution_simulator.py`
- `backtest/cost_model.py`

Responsibilities:
- generate rebalance calendars (trading-day stepping and month-end mode);
- build positions from standardized signals;
- simulate execution costs/slippage controls;
- compute realized and forward returns.

### 2.5 Performance and Validation Layer

Main components:
- `backtest/performance_analyzer.py`
- `backtest/walk_forward_validator.py`

Responsibilities:
- compute IC/t-statistics/win-rate style diagnostics;
- evaluate cross-period stability and deployment-style behavior.

### 2.6 Governance and Automation Layer

Main components:
- governance: `scripts/research_governance.py`, `scripts/governance_audit_checker.py`
- orchestration: `scripts/auto_research_orchestrator.py`
- scheduling: `scripts/auto_research_scheduler.py`
- search: `scripts/build_search_v1_trials.py`

Responsibilities:
- enforce reproducibility and gate completeness;
- turn manual research iteration into an auditable automated cycle.

---

## 3. Unified Entry and Configuration Contract

### 3.1 Unified Entry

Entrypoint:
- `scripts/run_research_workflow.py`

Supported workflow dispatch:
1. `train_test`
2. `segmented`
3. `walk_forward`
4. `production_gates`

This design keeps execution semantics stable while allowing strategy-specific changes in config only.

### 3.2 Protocol + Strategy Merge

Configuration is merged from:
- global protocol: `configs/protocol.yaml`
- strategy overlay: `configs/strategies/*.yaml`

Examples:
- baseline protocol: `configs/protocol.yaml`
- production combo profile: `configs/strategies/combo_v2_prod.yaml`

Operational effect:
- global constraints remain consistent;
- strategy-level adjustments are explicit and versioned;
- run reproducibility is improved through manifest/freeze checks.

---

## 4. Single-Factor Research Flow

### 4.1 Factor Registry in Runner

`run_segmented_factors.py` defines factor entries via `FACTOR_SPECS`, each with:
- factor config path;
- effective factor weights.

This gives a deterministic mapping from factor name to executable test config.

### 4.2 Backtest Internal Sequence

Inside `BacktestEngine.run_backtest()`:
1. generate rebalance dates;
2. build tradable universe;
3. compute factor signals;
4. apply optional signal smoothing;
5. build long/short positions;
6. simulate execution and costs;
7. compute returns + forward returns;
8. compute IC diagnostics;
9. export filter stats + universe audit records.

This pipeline is identical across factors, improving comparability.

### 4.3 Signal Standardization Controls

`factor_factory.standardize_signal()` supports:
- missing handling policy;
- percentile winsorization;
- rank transform or zscore;
- industry and exposure neutralization;
- z-bound clipping.

This standardization stage is central to stage-specific robustness rules.

---

## 5. Three-Layer Validation Framework

The platform uses a strict 3-layer validation path. Later layers are meaningful only after earlier-layer survival.

### 5.1 Layer 1: Segmented Stability

Runner:
- `scripts/run_segmented_factors.py`

Purpose:
- test regime stability over segmented windows (typically 2-year slices);
- filter unstable factors before heavier tests.

### 5.2 Layer 2: Fixed Train/Test

Runner:
- `scripts/run_with_config.py`

Purpose:
- inspect out-of-sample degradation under fixed period splits;
- preserve consistent comparison across candidate strategies.

### 5.3 Layer 3: Walk-Forward

Runner:
- `scripts/run_walk_forward.py`

Purpose:
- simulate rolling deployment behavior;
- evaluate whether performance survives rolling re-estimation.

This layer can be sharded (`--wf-shards`) for parallel compute.

---

## 6. Portfolio Construction Logic (Single Factor -> Combination)

### 6.1 Promotion Logic

Combination research is downstream from single-factor validation:
1. rank and filter single factors by Layer1/Layer2/Layer3 evidence;
2. compose candidate factor set;
3. run combination under same validation structure;
4. pass production gates before any deployment decision.

### 6.2 Combination Strategy Family

Main combination baseline:
- `strategies/combo_v2/config.py`
- `configs/strategies/combo_v2_prod.yaml`

Formula options include:
- linear weighted combination;
- gated value-momentum form;
- two-stage value-then-momentum filtering.

This enables formula-level A/B comparison under identical constraints.

### 6.3 Combination Validation Path

Combination strategies follow the same 3-layer path:
1. segmented validation;
2. fixed train/test;
3. walk-forward;
then production gates.

This enforces parity between single-factor and portfolio promotion standards.

---

## 7. Production Gates (Promotion Barrier)

Runner:
- `scripts/run_production_gates.py`

Gate blocks:
1. cost stress (`--cost-multipliers`);
2. stricter-universe walk-forward stress;
3. risk diagnostics (beta/turnover overlap/size correlation/industry coverage);
4. statistical control gates (BH-FDR path via `run_statistical_gates.py`).

Outputs:
- `gate_results/production_gates_<ts>/production_gates_report.json`
- `gate_results/production_gates_<ts>/production_gates_report.md`
- stress and diagnostics sub-artifacts.

Production gates separate "research-positive" from "promotion-ready" outcomes.

---

## 8. Governance, Freeze, and Reproducibility

### 8.1 Manifest and Freeze

Utility:
- `scripts/research_governance.py`

Core primitives:
- `build_manifest()`: run scope + CLI + config hash + git commit;
- `enforce_freeze()`: reject mismatched config hash or commit against freeze file.

### 8.2 Guardrails

Core runners include default checks for:
- non-negative lag constraints;
- required path existence for PIT-sensitive factors;
- unsafe run flags (by policy for official runs).

### 8.3 Post-Run Governance Audit

Checkers:
- `scripts/governance_audit_checker.py`
- `scripts/governance_remediation_plan.py`

Purpose:
- verify artifact completeness;
- produce explicit remediation instructions if governance checks fail.

---

## 9. Automation Loop (Registry -> Queue -> Plan -> Execute)

Main chain:
1. `scripts/update_factor_experiment_registry.py`
2. `scripts/generate_candidate_queue.py`
3. `scripts/generate_next_run_plan.py`
4. `scripts/repair_next_run_plan_paths.py`
5. `scripts/execute_next_run_plan.py`

Policy references:
- `configs/research/candidate_queue_policy.json`
- `configs/research/auto_research_policy.json`

This chain turns scattered experiment outputs into a ranked and executable decision flow.

---

## 10. Orchestrator and Scheduler

### 10.1 Orchestrator

Component:
- `scripts/auto_research_orchestrator.py`

Per-round behavior:
1. build candidate queue;
2. build next-run plan;
3. repair/normalize paths and tags;
4. dry-run validate selected command;
5. optional execution with budget controls.

Additional controls:
- retry/backoff for pre-execution stages;
- no-improvement stop criteria.

### 10.2 Scheduler

Component:
- `scripts/auto_research_scheduler.py`

Scheduler features:
- singleton lock;
- heartbeat;
- scheduler ledger;
- alert channels with dedupe logic.

Modes:
- standard profile;
- low-network profile (`auto_research_scheduler_policy.low_network.json`).

---

## 11. Search V1 (Parameterized Trial Planning)

### 11.1 Scope

Search V1 explores parameter spaces for combo_v2 through structured trial plans.

### 11.2 Components

- policy: `configs/research/auto_research_search_v1_policy.json`
- builder: `scripts/build_search_v1_trials.py`
- standard: `docs/production_research/AUTO_RESEARCH_SEARCH_V1.md`

### 11.3 Output Contract

Each search run writes:
- trial plan json/md/csv;
- derived per-trial strategy YAMLs;
- execution status report.

Output root:
- `audit/search_v1/<ts>_search_v1/`

This is the bridge between parameter exploration and governed batch execution.

---

## 12. Audit Artifact Topology

Primary audit roots:
- `audit/auto_research/`
- `audit/factor_registry/`
- `audit/failure_patterns/`
- `audit/search_v1/`
- `audit/session_handoff/`
- `audit/system_closure/`

Promotion gate outputs:
- `gate_results/production_gates_<ts>/`

The artifact topology is intentionally append-oriented for traceability.

---

## 13. Session Continuity and Handoff

Single-entry protocol:
- `SESSION_CONTINUITY_PROTOCOL.md`

Bootstrap sequence:
- `docs/production_research/SESSION_BOOTSTRAP.md`

Readiness checker:
- `scripts/check_session_handoff_readiness.py`

Closure checker:
- `scripts/run_system_closure_check.py`

These controls ensure that a fresh session can recover context without hidden assumptions.

---

## 14. Operating Model (Local + Remote Workstation)

Local environment:
- code changes;
- docs updates;
- smoke checks and dry-runs.

Remote workstation:
- heavy/parallel walk-forward and stress runs;
- unattended scheduler operation.

Typical heavy-run profile:
- `--threads 8`
- `--wf-shards 4`

---

## 15. Current Maturity and Next Upgrades

### 15.1 Mature Areas

- strong workflow standardization;
- governance and audit infrastructure;
- automated orchestration scaffold;
- low-network operational mode.

### 15.2 Next-Step Enhancements

- automatic trial-result feedback into unified leaderboard;
- multi-objective convergence logic (return, stability, capacity);
- stronger automated promotion/rejection policies.

---

## 16. Practical Reading Path for New Stakeholders

Recommended order:
1. `SESSION_CONTINUITY_PROTOCOL.md`
2. `DOCS_INDEX.md`
3. this document (`NOTION_SYSTEM_OVERVIEW_EN.md`)
4. `docs/production_research/GATE_SPEC.md`
5. `docs/production_research/AUTO_RESEARCH_ORCHESTRATION.md`
6. latest `audit/system_closure/*/system_closure_report.json`

This path provides architecture understanding first, then operational confidence.
