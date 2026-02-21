# Run Review Template

Last updated: 2026-02-21

Use this template to produce a standardized committee-ready run review after official run closure.

Auto-generation helper:

```bash
python scripts/generate_run_review.py \
  --run-dir audit/workstation_runs/<ts>_production_gates_<decision_tag> \
  --report-json gate_results/production_gates_<ts>/production_gates_report.json
```

## Header

- decision_tag:
- run_date:
- owner:
- run_dir:
- gate_report_json:
- overall_pass:

## 1) Executive Decision

- recommendation: approve / reject / rerun
- reason summary:
- blocking issues:

## 2) Cost Stress Summary

- x1.5 test_ic:
- x2.0 test_ic:
- pass/fail:
- notes:

## 3) Walk-Forward Stress Summary

- wf_test_ic_mean:
- wf_test_ic_pos_ratio:
- wf_test_ic_n:
- pass/fail:
- notes:

## 4) Risk Diagnostics Summary

- beta_vs_spy:
- turnover_top_pct_overlap:
- size_signal_corr_log_mcap:
- industry_coverage:
- pass/fail:

## 5) Statistical Gates Summary

- q_value_bh:
- factor_gate_pass:
- n_factors:
- n_pass:

## 6) Governance and Audit Completeness

- stage ledger updated: yes/no
- governance audit pass: yes/no
- remediation items count:
- highest severity remediation:

## 7) Required Follow-Up

1. short-term actions (24h)
2. medium-term actions (this week)
3. next official rerun trigger (if needed)

## 8) Evidence Paths

- `audit/workstation_runs/<...>/context.json`
- `audit/workstation_runs/<...>/run.log`
- `audit/workstation_runs/<...>/governance_audit_check.json`
- `audit/workstation_runs/<...>/governance_remediation_plan.json`
- `gate_results/production_gates_<ts>/production_gates_report.json`
- `gate_results/production_gates_<ts>/production_gates_final_summary.md`
