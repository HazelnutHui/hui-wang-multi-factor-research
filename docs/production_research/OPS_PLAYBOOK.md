# Production Ops Playbook

Last updated: 2026-02-21

## 1) One-time setup

```bash
cd /Users/hui/quant_score/v4
export PYTHONPATH=$(pwd)
```

## 2) Create freeze (official baseline)

```bash
python scripts/run_with_config.py \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --freeze-file runs/freeze/combo_v2_prod.freeze.json \
  --write-freeze
```

## 3) Run data quality gate (mandatory for official runs)

```bash
python scripts/data_quality_gate.py \
  --input-csv data/your_input.csv \
  --required-columns date,ticker,score \
  --numeric-columns score \
  --key-columns date,ticker \
  --date-column date \
  --max-staleness-days 7 \
  --out-dir gate_results/data_quality
```

Proceed only when `overall_pass: true`.

## 4) Run production hard gates

```bash
python scripts/run_production_gates.py \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --factor combo_v2 \
  --freeze-file runs/freeze/combo_v2_prod.freeze.json \
  --out-dir gate_results
```

## 5) Unified entry alternative

```bash
python scripts/run_research_workflow.py --workflow production_gates -- \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --factor combo_v2 \
  --freeze-file runs/freeze/combo_v2_prod.freeze.json \
  --out-dir gate_results
```

## 6) Read outputs

1. Open latest:
   - `gate_results/production_gates_<ts>/production_gates_report.md`
2. Verify machine-readable:
   - `gate_results/production_gates_<ts>/production_gates_report.json`
3. Check registry:
   - `gate_results/gate_registry.csv`

## 7) Decision checklist

1. `overall_pass` is `True`.
2. No gate is bypassed (`skip_guardrails=False`, `skip_risk_diagnostics=False`).
3. Data quality report shows `overall_pass=True`.
4. Freeze file is present and unchanged.
5. Run artifacts are archived with manifest and gate report.

## 8) Workstation official wrapper (recommended)

```bash
bash scripts/workstation_official_run.sh \
  --workflow production_gates \
  --tag committee_YYYY-MM-DD_runN \
  --owner hui \
  --notes "official workstation gate run" \
  --threads 8 \
  --dq-input-csv data/your_input.csv \
  -- \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --factor combo_v2 \
  --cost-multipliers 1.5,2.0 \
  --wf-shards 4 \
  --freeze-file runs/freeze/combo_v2_prod_<date>_g<commit>.freeze.json \
  --out-dir gate_results
```

Artifacts are stored under:
- `audit/workstation_runs/<ts>_<workflow>_<decision_tag>/`

Post-run governance check (recommended):

```bash
python scripts/governance_audit_checker.py \
  --run-dir audit/workstation_runs/<ts>_production_gates_<decision_tag> \
  --report-json gate_results/production_gates_<ts>/production_gates_report.json \
  --require-final-summary
```

If governance check fails, generate remediation actions:

```bash
python scripts/governance_remediation_plan.py \
  --audit-json audit/workstation_runs/<ts>_production_gates_<decision_tag>/governance_audit_check.json
```

Update factor registry and leaderboard:

```bash
python scripts/update_factor_experiment_registry.py \
  --report-json gate_results/production_gates_<ts>/production_gates_report.json \
  --run-dir audit/workstation_runs/<ts>_production_gates_<decision_tag>
```

Generate next-run candidate queue:

```bash
python scripts/generate_candidate_queue.py
```
