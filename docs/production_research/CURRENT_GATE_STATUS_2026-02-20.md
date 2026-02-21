# Current Gate Status Snapshot (2026-02-20)

This file records observed gate behavior during the current production-grade governance cycle.

## 1) What is stable

1. Cost stress branch runs successfully under freeze:
   - `x1.0`, `x1.5`, `x2.0` all execute and produce positive `test_ic`.
2. Freeze + manifest + registry pipelines are operational.
3. Risk diagnostics and statistical gate scripts execute and produce reports.

## 2) What still needs follow-up

1. Walk-forward stress runtime is long under full-window setup.
2. Statistical gate for `combo_v2` may fail if latest segmented summary does not include `combo_v2` rows.
3. Risk diagnostics may return `beta_vs_spy=None` or `size_signal_corr_log_mcap=NaN` when data alignment/coverage is insufficient.

## 3) Required interpretation rule

If `overall_pass=False`, always inspect:
1. `wf_stress` fields (`test_ic_n`, `test_ic_mean`, `test_ic_overall_mean`)
2. `risk_diagnostics` null fields
3. `statistical_gates.focus.found`

Do not treat `overall_pass=False` as a single-cause failure without component review.

## 4) Next-action checklist for committee-grade rerun

1. Run on workstation as official environment.
2. Ensure `REBALANCE_MODE=None` for combo WF stress.
3. Ensure `MARKET_CAP_DIR` absolute path is passed in WF stress branch.
4. Ensure segmented summary source includes `combo_v2` for statistical gate or explicitly set `--stat-summary-csv`.
5. Record `decision-tag` and `notes` in registry on every rerun.
