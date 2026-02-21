# Institutional Gate Specification

Last updated: 2026-02-20

This document defines hard gates for promotion decisions (`research -> paper -> live candidate`).

## 1) Mandatory prerequisites

1. Freeze consistency is enforced (`--freeze-file`).
2. PIT/lag guardrails are enabled (default; do not use `--skip-guardrails` in official runs).
3. Run manifests are generated and archived.

## 2) Cost stress gates

Runner:
- `scripts/run_institutional_gates.py`

Default multipliers:
- `1.0, 1.5, 2.0`

Hard conditions:
1. `test_ic(x1.5) > 0`
2. `test_ic(x2.0) > 0`

Gate keys:
- `cost_gate_x1_5_positive`
- `cost_gate_x2_0_positive`

## 3) Walk-forward stress gates

Stress profile defaults:
- `COST_MULTIPLIER=1.5`
- `MIN_MARKET_CAP=2e9`
- `MIN_DOLLAR_VOLUME=5e6`
- `MIN_PRICE=5`

Hard conditions:
1. `test_ic_mean > 0`
2. `test_ic_pos_ratio >= 0.70` (configurable by `--min-pos-ratio`)

Gate keys:
- `wf_gate_positive_mean`
- `wf_gate_pos_ratio`

## 4) Risk diagnostics gates

Source:
- `scripts/posthoc_factor_diagnostics.py`

Hard conditions (defaults):
1. `abs(beta_vs_spy) <= 0.50`
2. `turnover_top_pct_overlap >= 0.20`
3. `abs(size_signal_corr_log_mcap) <= 0.30`
4. `industry_coverage >= 0.70`

Gate keys:
- `risk_gate_beta_abs`
- `risk_gate_turnover_overlap`
- `risk_gate_size_corr_abs`
- `risk_gate_industry_coverage`

## 5) Overall pass rule

- `overall_pass=True` only when all enabled hard gates are `True`.
- If `--skip-risk-diagnostics` is used, risk gates are excluded from the final conjunction and run is non-official by policy.

## 6) Statistical gates (multiple testing control)

Runner:
- `scripts/run_statistical_gates.py`

Default method:
- Benjamini-Hochberg FDR (`q_value_bh`)

Factor-level pass defaults:
1. `q_value_bh <= 0.10`
2. `pos_ratio >= 0.60`
3. `ic_mean > 0.0`

In integrated institutional gates:
- `stat_gate_factor_pass=True` is required unless `--skip-statistical-gates` is explicitly set.

## 7) Outputs and audit

Per gate run:
- `cost_stress_results.csv`
- `institutional_gates_report.json`
- `institutional_gates_report.md`
- registry append entry in `gate_results/gate_registry.csv` (if enabled)

## 8) Promotion policy

Recommended:
1. `overall_pass=True` for at least one full official gate run under frozen config.
2. Promote to paper-trading candidate (4-8 weeks) without parameter drift.
3. Start live candidate only after paper metrics and kill-switch thresholds are pre-defined.
