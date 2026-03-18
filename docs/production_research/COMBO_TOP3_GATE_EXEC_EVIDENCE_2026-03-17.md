# Combo Top3 Gate Execution Evidence (2026-03-17)

Last updated: 2026-03-18

Purpose:
- record the actual execution evidence for the 2026-03-17 top3 combo gate cycle;
- avoid ambiguity between "official `run_production_gates.py` artifacts" and customized batch execution artifacts.

## 1) Top3 Baseline Runs (completed)

The three top combos have completed baseline runs at `2026-03-17_051049`:

1. `strategies/combo_p2_value_quality_bias_v1/runs/2026-03-17_051049.json`
2. `strategies/combo_p6_robust_min_corr_v1/runs/2026-03-17_051049.json`
3. `strategies/combo_p7_no_earnings_gap_v1/runs/2026-03-17_051049.json`

## 2) Top3 Custom Batch Scaffold (exists)

Top3 custom gate scaffold directory:

- `runs/combo_pg_top3_20260317_050839/`

Contains:
- `cost_matrix.csv`
- `wf_matrix.csv`
- `combos.txt`
- `tmp_strategies/` (generated strategy variants)

Note:
- this directory is an execution scaffold and mapping layer;
- it is not the standard output shape of `run_production_gates.py`.

## 3) Missing-Item Recovery (the "+1" rerun)

Recovery run directory:

- `runs/recover_p2_x2_20260317_205256/`

Recovered item:
- `combo_p2_value_quality_bias_v1` under `--cost-multiplier 2.0`

Execution log evidence:
- `runs/recover_p2_x2_20260317_205256/run.log`

Observed result snapshot in log:
- `Train IC (overall): 0.020265086430811697`
- `Test  IC (overall): 0.013968756782888508`

## 4) Interpretation Boundary

This cycle corresponds to user-directed custom top3 gate execution with "8/9 done + 1 recovered".

Therefore:
- completion evidence exists in run JSON + recovery log artifacts;
- this cycle should not be interpreted as a complete standard `gate_results/production_gates_<ts>/production_gates_report.json` chain unless such report artifacts are explicitly generated.

