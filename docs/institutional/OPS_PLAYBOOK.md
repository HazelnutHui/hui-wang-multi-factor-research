# Institutional Ops Playbook

Last updated: 2026-02-20

## 1) One-time setup

```bash
cd /Users/hui/quant_score/v4
export PYTHONPATH=$(pwd)
```

## 2) Create freeze (official baseline)

```bash
python scripts/run_with_config.py \
  --strategy configs/strategies/combo_v2_inst.yaml \
  --freeze-file runs/freeze/combo_v2_inst.freeze.json \
  --write-freeze
```

## 3) Run institutional hard gates

```bash
python scripts/run_institutional_gates.py \
  --strategy configs/strategies/combo_v2_inst.yaml \
  --factor combo_v2 \
  --freeze-file runs/freeze/combo_v2_inst.freeze.json \
  --out-dir gate_results
```

## 4) Unified entry alternative

```bash
python scripts/run_research_workflow.py --workflow institutional_gates -- \
  --strategy configs/strategies/combo_v2_inst.yaml \
  --factor combo_v2 \
  --freeze-file runs/freeze/combo_v2_inst.freeze.json \
  --out-dir gate_results
```

## 5) Read outputs

1. Open latest:
   - `gate_results/institutional_gates_<ts>/institutional_gates_report.md`
2. Verify machine-readable:
   - `gate_results/institutional_gates_<ts>/institutional_gates_report.json`
3. Check registry:
   - `gate_results/gate_registry.csv`

## 6) Decision checklist

1. `overall_pass` is `True`.
2. No gate is bypassed (`skip_guardrails=False`, `skip_risk_diagnostics=False`).
3. Freeze file is present and unchanged.
4. Run artifacts are archived with manifest and gate report.
