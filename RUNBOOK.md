# V4 Runbook (Public English Edition)

Last updated: 2026-03-10 (workstation dual-repo sync policy)

This runbook contains the minimal commands needed to run, validate, and inspect factors in this repository.

Runtime status source:
- Authoritative project status: `STATUS.md`
- Row-level final status: `docs/production_research/BATCHA100_FINAL_RESULT_STATUS_2026-03-07.md`

Status boundary note:
- command execution success (`exit_code=0`) is not equal to gate pass.
- official status must be read from latest `production_gates_report.json` plus artifact availability.
- if a documented workstation run is not present in local paths, mark it as `pending_local_sync` until artifacts are synced and verified.
- factor-factory full-batch runs default to workstation with at least `--jobs 4` (local default is `--dry-run` planning).
- factor-factory ranking comparability baseline is fixed in policy `default_set`: `REBALANCE_FREQ=5`, `HOLDING_PERIOD=3`, `REBALANCE_MODE=None`.
- workstation code-sync safety:
  - keep runtime repo and clean sync repo separated on workstation:
    - runtime: `~/projects/hui-wang-multi-factor-research`
    - clean sync: `~/projects/v4_clean`
  - do not force sync (`reset/clean/pull with conflict risk`) in runtime repo during active runs.

Snapshot details are maintained only in:
- `STATUS.md`
- `docs/production_research/BATCHA100_FINAL_RESULT_STATUS_2026-03-07.md`

## 1) Environment
- Python 3.11 recommended
- Run from repository root

```bash
cd quant_score/v4
export PYTHONPATH=$(pwd)
```

## 2) Common Workflows

### 2.0 Current Queue Governance (required)
```bash
# Step 1: update approval gate after manual review
# edit configs/research/factory_queue/run_approval.json
# set:
#   "approved": true
#   "approved_queue": "configs/research/factory_queue/<target_queue>.json"
#
# Step 2: run approved queue on workstation
bash scripts/ops_entry.sh factory_queue \
  --queue-json configs/research/factory_queue/<target_queue>.json \
  --jobs 8
```

Policy notes:
- queue run is blocked unless approval gate matches target queue.
- single-factor `SF-L1` is the mandatory segmented gate.
- single-factor `SF-L2`/`SF-L3` hard admission rules follow `SINGLE_FACTOR_BASELINE.md`.
- single-factor `SF-DIAG` is diagnostic optional (use only for debugging/triage).
- after round-1 ranking, run shortlist robustness with `HOLDING_PERIOD=1/3/5`.

### 2.1 Segmented backtest (2-year slices)
```bash
python scripts/run_segmented_factors.py --factors value --years 2
```

### 2.2 Fixed train/test run (single strategy)
```bash
python -m strategies.value_v1.run
```

### 2.3 Unified config entrypoint (recommended)
```bash
python scripts/run_with_config.py --strategy configs/strategies/momentum_v1.yaml
```

### 2.4 Walk-forward validation
```bash
python scripts/run_walk_forward.py --factors momentum --train-years 3 --test-years 1 --start-year 2010 --end-year 2026
```

### 2.5 Combo baseline (production top3)
```bash
python scripts/run_with_config.py --strategy configs/strategies/combo_v2_prod.yaml
python scripts/run_segmented_factors.py --factors combo_v2 --years 2
python scripts/run_walk_forward.py --factors combo_v2 --train-years 3 --test-years 1 --start-year 2010 --end-year 2026
```

### 2.7 Factor report generation
```bash
python scripts/generate_factor_report.py --strategy configs/strategies/momentum_v1.yaml --quantiles 5 --rolling-window 60 --cost-multipliers 2,3
```

### 2.8 Tests
```bash
python -m pytest tests
```

### 2.10 Post-WF production gates (must-pass before paper/live)
Use:
- `POST_WF_PRODUCTION_CHECKLIST.md`

Includes:
- cost stress (`--cost-multiplier`)
- walk-forward stress (cost + stricter universe)
- post-hoc risk diagnostics (`scripts/posthoc_factor_diagnostics.py`)
- pass/fail criteria for promotion

### 2.11 Daily research orchestration (current)
Preferred entry:
```bash
bash scripts/ops_entry.sh daily
```

Dry-run validation only:
```bash
bash scripts/ops_entry.sh status
```

The `daily` flow now uses:
- `scripts/prepare_dq_input.py`
- `scripts/data_quality_gate.py`
- `scripts/generate_candidate_queue.py`
- `scripts/generate_next_run_plan.py`
- `scripts/repair_next_run_plan_paths.py`
- `scripts/execute_next_run_plan.py` (dry-run first; execute only when enabled)

### 2.12 Live trading daily eval (T -> T+1) + readable PDF
Run ID convention:
- `trade_YYYY-MM-DD_from_signal_YYYY-MM-DD`

Daily evaluation from score snapshot and realized returns:
```bash
python scripts/live_trading_eval.py \
  --signals live_trading/scores/trade_YYYY-MM-DD_from_signal_YYYY-MM-DD/scores_full_ranked.csv \
  --signal-date YYYY-MM-DD \
  --trade-date YYYY-MM-DD \
  --realized-file live_trading/accuracy/trade_YYYY-MM-DD_from_signal_YYYY-MM-DD/accuracy_check_YYYY-MM-DD_symbol_returns.csv
```

Generate bilingual daily readable reports (PDF):
```bash
python scripts/generate_daily_live_report.py \
  --run-id trade_YYYY-MM-DD_from_signal_YYYY-MM-DD
```

Outputs:
- Scores: `live_trading/scores/<run_id>/signals_T.csv`
- Accuracy:
  - `live_trading/accuracy/<run_id>/metrics_T_Tplus1.csv`
  - `live_trading/accuracy/<run_id>/deciles_T_Tplus1.csv`
  - `live_trading/accuracy/<run_id>/match_T_Tplus1.csv`
  - `live_trading/accuracy/metrics_panel.csv`
- Readable reports:
  - `live_trading/reports/daily/en/<run_id>/daily_report_en.pdf`
  - `live_trading/reports/daily/zh/<run_id>/daily_report_zh.pdf`

### 2.13 Governed unified entry + freeze (production-grade)
Single entrypoint:
```bash
python scripts/run_research_workflow.py --workflow train_test -- \
  --strategy configs/strategies/combo_v2_prod.yaml
python scripts/run_research_workflow.py --workflow segmented -- \
  --factors combo_v2 --years 2
python scripts/run_research_workflow.py --workflow walk_forward -- \
  --factors combo_v2 --train-years 3 --test-years 1 --start-year 2010 --end-year 2025
```

Freeze controls (supported in all three workflow scripts):
```bash
# first run: create freeze file
python scripts/run_with_config.py \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --freeze-file runs/freeze/combo_v2_prod.freeze.json \
  --write-freeze

# later runs: enforce same frozen config hash (+ commit when available)
python scripts/run_with_config.py \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --freeze-file runs/freeze/combo_v2_prod.freeze.json
```

Run-manifest outputs:
- `run_with_config`: `strategies/<strategy>/runs/<timestamp>.manifest.json` + `run_manifest_latest.json`
- `run_segmented_factors`: `<out_dir>/run_manifest.json` + `run_manifest_latest.json`
- `run_walk_forward`: `<out_dir>/run_manifest.json` + `run_manifest_latest.json`

PIT/lag guardrails:
- Default: enabled (lag non-negative checks + required PIT data-dir checks by active factors)
- Emergency bypass: add `--skip-guardrails` (not recommended for official runs)

Universe filter audit outputs:
- `run_with_config`:
  - `strategies/<strategy>/results/train_universe_audit_<ts>.csv`
  - `strategies/<strategy>/results/test_universe_audit_<ts>.csv`
- `run_segmented_factors`: `<out_dir>/<factor>/universe_filter_audit.csv`
- `run_walk_forward`: `<out_dir>/<factor>/universe_filter_audit.csv`

### 2.14 Production hard gates (cost + stress + pass/fail)
One-shot gate runner:
```bash
python scripts/run_production_gates.py \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --factor combo_v2 \
  --cost-multipliers 1.0,1.5,2.0 \
  --wf-train-years 3 --wf-test-years 1 --wf-start-year 2010 --wf-end-year 2025 \
  --stress-cost-multiplier 1.5 \
  --stress-min-market-cap 2000000000 \
  --stress-min-dollar-volume 5000000 \
  --stress-market-cap-dir data/fmp/market_cap_history \
  --out-dir gate_results
```

Outputs:
- `gate_results/production_gates_<ts>/cost_stress_results.csv`
- `gate_results/production_gates_<ts>/production_gates_report.json`
- `gate_results/production_gates_<ts>/production_gates_report.md`
- `gate_results/gate_registry.csv` (append-only decision ledger; disable with `--no-registry`)

Gate defaults:
- cost gate: `test_ic > 0` under `x1.5` and `x2.0`
- walk-forward stress gate:
  - `test_ic mean > 0`
  - `test_ic pos_ratio >= 0.70`
- risk diagnostics gate (from `posthoc_factor_diagnostics.py`):
  - `abs(beta_vs_spy) <= 0.50`
  - `turnover_top_pct_overlap >= 0.20`
  - `abs(size_signal_corr_log_mcap) <= 0.30`
  - `industry_coverage >= 0.70`

Optional:
- skip risk diagnostics in emergency runs: `--skip-risk-diagnostics`
- skip statistical gates in emergency runs: `--skip-statistical-gates`

Standalone statistical gates:
```bash
python scripts/run_statistical_gates.py \
  --factor combo_v2 \
  --alpha 0.10 \
  --min-pos-ratio 0.60 \
  --min-ic-mean 0.0 \
  --out-dir gate_results/statistical
```

### 2.15 Workstation-primary operation (official)
Use workstation for official heavy runs:
```bash
ssh hui@100.66.103.44
cd ~/projects/hui-wang-multi-factor-research
export PYTHONPATH=$(pwd)

python scripts/run_production_gates.py \
  --strategy configs/strategies/combo_v2_prod.yaml \
  --factor combo_v2 \
  --freeze-file runs/freeze/combo_v2_prod.freeze.json \
  --stress-market-cap-dir data/fmp/market_cap_history \
  --decision-tag committee_ws_official \
  --owner hui \
  --notes "workstation official run" \
  --out-dir gate_results
```

Pull artifacts back to local:
```bash
rsync -avh --progress \
  hui@100.66.103.44:~/projects/hui-wang-multi-factor-research/gate_results/ \
  /Users/hui/quant_score/v4/gate_results/

rsync -avh --progress \
  hui@100.66.103.44:~/projects/hui-wang-multi-factor-research/runs/freeze/ \
  /Users/hui/quant_score/v4/runs/freeze/
```

## 3) Where Outputs Go
- Segmented runs: `segment_results/<timestamp>/`
- Walk-forward runs: `walk_forward_results/<timestamp>/`
- Strategy outputs: `strategies/<strategy>/results/`
- Reports: `strategies/<strategy>/reports/`

## 4) Notes for Public Repo Users
- Large datasets and logs are intentionally excluded from this public repository.
- You need your own local data cache and API key to fully reproduce historical runs.
- Do not commit secrets or API credentials.

## 5) Code Sync Workflow (Local <-> Workstation)
- Recommended rule:
  - Code/docs: sync via Git (`push`/`pull`)
  - Data/results/logs: sync via `rsync`

If you configured local zsh helpers:

```bash
sync_push "docs: update runbook"
sync_pull_ws
sync_all "feat: update strategy config"
```

Without helper functions:

```bash
# local machine
cd /Users/hui/quant_score/v4
git add -A
git commit -m "your message"
git push

# workstation
cd ~/projects/hui-wang-multi-factor-research
git pull
```

Example data/result sync (run on local machine):

```bash
rsync -avh --progress /Users/hui/quant_score/v4/data/ hui@100.66.103.44:~/projects/hui-wang-multi-factor-research/data/
rsync -avh --progress hui@100.66.103.44:~/projects/hui-wang-multi-factor-research/segment_results/ /Users/hui/quant_score/v4/segment_results/
```
