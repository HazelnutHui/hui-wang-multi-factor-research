# Combo Research Baseline (V4)

Last updated: 2026-03-11

Purpose:
- lock a professional, reproducible combo-research protocol before new combo backtests;
- prevent post-hoc parameter tuning;
- define admission, execution, and promotion standards at combo layer.

---

## 1) Scope (Current Phase)

- This baseline applies to combo research after WF17 single-factor completion.
- Single-factor upstream baseline remains:
  - `../../SINGLE_FACTOR_BASELINE.md`
  - `FACTOR_PIPELINE_FREEZE_2026-02-25.md`

Current combo input pool (AB only from WF17 provisional grading):
- Grade A:
  - `ocf_yield_ttm`
  - `fcf_yield_ttm`
  - `shareholder_yield`
  - `value_rerating_trend`
  - `ebitda_ev_yield`
  - `smallcap_seasonality_proxy`
  - `failed_breakout_reversal`
- Grade B:
  - `trend_regime_switch`
  - `ownership_dispersion_proxy`
  - `gap_fill_propensity`
  - `liquidity_regime_switch`
  - `earnings_gap_strength`
- Grade C (not admitted to main combo in this phase):
  - `ownership_acceleration`
  - `large_gap_reversal`
  - `fcf_growth_persistence`
  - `nwc_change_inverse`
  - `risk_on_off_breadth`

Reference:
- `WF17_SINGLE_FACTOR_GRADE_2026-03-11.md`

---

## 2) Locked Research Principles

1. Pre-register combo candidates before execution; no mid-run config changes.
2. Use one comparability baseline for all candidates:
   - `REBALANCE_FREQ=5`
   - `HOLDING_PERIOD=3`
   - `REBALANCE_MODE=None`
3. Apply identical universe/neutralization/cost assumptions across candidates.
4. Hard gates first, ranking second.
5. Only one canonical winner and one backup are promoted.

---

## 3) Combo Candidate Design (Required)

1. Candidate count per cycle: `12-18` combos.
2. Candidate families must be declared up front (example):
   - value-core
   - cashflow-core
   - balanced
   - low-turnover conservative
3. Each candidate must have:
   - unique strategy config path
   - unique strategy id/name
   - deterministic run id
4. Single-factor weight constraints:
   - max weight per factor `<= 0.20`
   - if pairwise recent `|corr| > 0.70`, both cannot stay at full intended weight

---

## 4) Execution Sequence (Locked)

1. `Layer2` fixed train/test for all pre-registered combos.
2. Apply `Layer2` hard gate and remove failures.
3. `Layer3` walk-forward for survivors.
4. Apply `Layer3` hard gate and remove failures.
5. Run production gates on top `<=3` by pre-defined ranking score.
6. Promote only combos passing all production gates.

No skip/bypass flags for official promotion runs.

---

## 5) Hard Gates (Combo Layer)

## 5.1 Layer2 gate

- `test_ic > 0` required.

## 5.2 Layer3 gate

- walk-forward mean `test_ic > 0`
- positive-window ratio `>= 60%`
- no `3` consecutive negative windows

## 5.3 Cost gate

- under `x1.5` and `x2.0` cost multipliers, out-of-sample metric must stay positive.

## 5.4 Risk diagnostics gate

- use current production gate defaults from:
  - `../../POST_WF_PRODUCTION_CHECKLIST.md`
  - `../../RUNBOOK.md` (`run_production_gates.py` section)

---

## 6) Ranking Rule After Gates

For candidates that pass all hard gates, use a fixed composite score:

\[
S = 0.35 \cdot Z(\text{Layer2 test\_ic})
  + 0.35 \cdot Z(\text{WF mean test\_ic})
  + 0.20 \cdot Z(\text{Cost x1.5 test\_ic})
  + 0.10 \cdot Z(-\text{turnover})
\]

Interpretation:
- prefer stronger OOS signal (`Layer2` + `WF`)
- require cost robustness
- penalize high-turnover structures

Tie-break order:
1. higher `WF pos_ratio`
2. lower max drawdown
3. lower turnover

---

## 7) Promotion Output (Required)

At cycle end, must produce:
1. full candidate leaderboard with pass/fail reasons;
2. one `primary` combo;
3. one `backup` combo;
4. frozen config artifact for promoted combo;
5. updates to:
   - `../../STATUS.md`
   - `../../DOCS_INDEX.md` (if canonical entry changes)

---

## 8) Cleanup Rule

- remove intermediate invalid run outputs and stale comparison notes;
- keep only:
  - canonical promoted combo evidence
  - full leaderboard table (for audit traceability)

