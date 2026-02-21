# Official Run Template

Last updated: 2026-02-21

This file provides copy-ready templates for official production gate runs.

## 1) Workstation Official Run (Recommended)

```bash
cd ~/projects/hui-wang-multi-factor-research
export PYTHONPATH=$(pwd)

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
  --stress-market-cap-dir data/fmp/market_cap_history \
  --out-dir gate_results
```

## 2) Active-Run Monitor Then Auto-Close (Local)

```bash
cd /Users/hui/quant_score/v4
bash scripts/monitor_then_finalize.sh --tag committee_YYYY-MM-DD_runN --interval 30
```

## 3) Direct Post-Run Close (When Run Already Ended)

```bash
cd /Users/hui/quant_score/v4
bash scripts/post_run_sync_and_finalize.sh --tag committee_YYYY-MM-DD_runN
```

## 4) Naming Rules

1. `decision_tag` format: `committee_YYYY-MM-DD_runN`
2. freeze file should include commit suffix: `_g<commit>`
3. reruns must use a new tag suffix (for example `_rerun2`)

## 5) Minimum Pre-Submission Checks

1. run dir has `result.json`
2. gate dir has `production_gates_report.json` and `.md`
3. governance outputs exist:
   - `governance_audit_check.json/.md`
   - `governance_remediation_plan.json/.md`
