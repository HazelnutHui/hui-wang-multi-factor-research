# V4 Runbook (Public English Edition)

Last updated: 2026-02-18 (live trading eval + bilingual daily PDF report)

This runbook contains the minimal commands needed to run, validate, and inspect factors in this repository.

## 1) Environment
- Python 3.11 recommended
- Run from repository root

```bash
cd quant_score/v4
export PYTHONPATH=$(pwd)
```

## 2) Common Workflows

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

### 2.5b Combo final locked run (recommended)
```bash
# Layer2 fixed train/test
python3 scripts/run_with_config.py --strategy configs/strategies/combo_v2_prod.yaml

# Layer3 walk-forward (important: REBALANCE_MODE=None)
python3 scripts/run_walk_forward.py \
  --factors combo_v2 \
  --train-years 3 --test-years 1 --start-year 2010 --end-year 2025 \
  --set REBALANCE_MODE=None \
  --set COMBO_FORMULA=linear \
  --set SIGNAL_ZSCORE=True \
  --set SIGNAL_RANK=False \
  --set SIGNAL_WINSOR_PCT_LOW=0.01 \
  --set SIGNAL_WINSOR_PCT_HIGH=0.99 \
  --set SIGNAL_MISSING_POLICY=drop \
  --set INDUSTRY_NEUTRAL=True \
  --set INDUSTRY_MIN_GROUP=5 \
  --set SIGNAL_NEUTRALIZE_SIZE=True \
  --set SIGNAL_NEUTRALIZE_BETA=True \
  --set MIN_MARKET_CAP=1000000000 \
  --set MIN_DOLLAR_VOLUME=2000000 \
  --set MIN_PRICE=5
```

### 2.6 Derive combo weights from segmented outputs
```bash
python scripts/derive_combo_weights.py --root . --out segment_results/derived/combo_v2_weights_suggested.csv
```

### 2.6b Combo segmented weight-grid (corrected path)
Important:
- Use only corrected output path for weight selection:
  - `segment_results/combo_weight_grid_2026_02_17_fix`
- Do not use:
  - `segment_results/combo_weight_grid_2026_02_17_p6` (invalid for final selection due to old hardcoded combo defaults in segmented runner)

Current combo lock after formula comparison:
- Formula: `linear`
- Weights: `value=0.90`, `momentum=0.10`
- Nonlinear candidates (`gated`, `two_stage`) were tested and did not beat linear under Stage2 strict constraints.
- Layer2 fixed train/test (locked): `train_ic=0.080637`, `test_ic=0.053038`
- Layer3 walk-forward (2013-2025, `REBALANCE_MODE=None`):
  - `test_ic mean=0.057578`, `std=0.033470`, `pos_ratio=1.0000`, `n=13`
  - `test_ic_overall mean=0.050814`, `std=0.032703`, `pos_ratio=1.0000`, `n=13`

### 2.7 Factor report generation
```bash
python scripts/generate_factor_report.py --strategy configs/strategies/momentum_v1.yaml --quantiles 5 --rolling-window 60 --cost-multipliers 2,3
```

### 2.8 Tests
```bash
python -m pytest tests
```

### 2.9 Stage2 strict top3 (production segmented, 6-core)
```bash
chmod +x scripts/run_stage2_strict_top3_parallel.sh
bash scripts/run_stage2_strict_top3_parallel.sh 6 segment_results/stage2_v2026_02_16b_top3
```

Resume-safe behavior:
- Default mode skips already completed segments.
- Force rerun all 27 tasks:
```bash
bash scripts/run_stage2_strict_top3_parallel.sh 6 segment_results/stage2_v2026_02_16b_top3 1
```

### 2.10 Post-WF production gates (must-pass before paper/live)
Use:
- `POST_WF_PRODUCTION_CHECKLIST.md`

Includes:
- cost stress (`--cost-multiplier`)
- walk-forward stress (cost + stricter universe)
- post-hoc risk diagnostics (`scripts/posthoc_factor_diagnostics.py`)
- pass/fail criteria for promotion

Latest completed stress result (2026-02-17):
- Profile: `COST_MULTIPLIER=1.5`, `MIN_MARKET_CAP=2e9`, `MIN_DOLLAR_VOLUME=5e6`
- Output: `walk_forward_results/combo_v2_postwf_stress_x1_5_p6/combo_v2/walk_forward_summary.csv`
- `test_ic`: `mean=0.053310`, `std=0.032486`, `pos_ratio=1.0000`, `n=13`
- `test_ic_overall`: `mean=0.046618`, `std=0.032058`, `pos_ratio=1.0000`, `n=13`

### 2.11 Daily lightweight update pipeline (incremental, not full overwrite)
Three-step design:
1. Incremental pull (`latest/recent`, no full rebuild by default)
2. Run current combo strategy once in live-daily profile (refresh `test_signals_latest.csv`)
3. Sync minimal outputs to web side

Scripts:
- `scripts/daily_pull_incremental.sh`
- `scripts/daily_run_combo_current.sh`
- `scripts/daily_sync_web.sh`
- `scripts/daily_update_pipeline.sh` (orchestrator)

Default strategy config used by `daily_run_combo_current.sh`:
- `configs/strategies/combo_v2_live_daily.yaml`

Default run mode:
- `RUN_MODE=live_snapshot` (latest signal snapshot only, no full train/test rerun)
- Optional: `RUN_MODE=full_backtest` (if you explicitly want fresh IC/run json)

Examples:
```bash
# dry-run full pipeline
DRY_RUN=1 bash scripts/daily_update_pipeline.sh

# full daily run
bash scripts/daily_update_pipeline.sh

# run only strategy + sync (skip pull)
DO_PULL=0 bash scripts/daily_update_pipeline.sh
```

Operational notes (2026-02-18):
- `daily_pull_incremental.sh` now auto-selects Python in this order:
  1) `.venv/bin/python`
  2) `/Users/hui/miniconda3/bin/python3`
  3) `python3`
- If local DNS cannot resolve FMP, set:
```bash
export FMP_RESOLVE_IPS='34.194.189.88,52.202.201.64,107.21.126.193'
```
- Signal semantics for web publish:
  - `test_signals_latest.csv` with `date=T` means signal computed with data up to `T` and used for next trading day `T+1`.

Workstation fallback (when local DNS/network to FMP fails):
```bash
ssh hui@100.66.103.44
cd ~/projects/hui-wang-multi-factor-research
export FMP_API_KEY=...
bash scripts/daily_pull_incremental.sh
```
Then sync refreshed cache back to local if needed:
```bash
rsync -avh --progress hui@100.66.103.44:~/projects/hui-wang-multi-factor-research/data/prices_divadj/ /Users/hui/quant_score/v4/data/prices_divadj/
rsync -avh --progress hui@100.66.103.44:~/projects/hui-wang-multi-factor-research/data/fmp/earnings/ /Users/hui/quant_score/v4/data/fmp/earnings/
```

### 2.12 Live trading daily eval (T -> T+1) + readable PDF
Run ID convention:
- `trade_YYYY-MM-DD_from_signal_YYYY-MM-DD`

Daily evaluation from score snapshot and realized returns:
```bash
python scripts/live_trading_eval.py \
  --signals live_trading/scores/trade_2026-02-18_from_signal_2026-02-17/scores_full_ranked.csv \
  --signal-date 2026-02-17 \
  --trade-date 2026-02-18 \
  --realized-file live_trading/accuracy/trade_2026-02-18_from_signal_2026-02-17/accuracy_check_2026-02-18_symbol_returns.csv
```

Generate bilingual daily readable reports (PDF):
```bash
python scripts/generate_daily_live_report.py \
  --run-id trade_2026-02-18_from_signal_2026-02-17
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

First live-day archive (2026-02-18 trading):
- Local:
  - `live_trading/scores/trade_2026-02-18_from_signal_2026-02-17/`
  - `live_trading/accuracy/trade_2026-02-18_from_signal_2026-02-17/`
- Web-side:
  - `/home/ubuntu/Hui/data/quant_score/v4/live_trading/scores/trade_2026-02-18_from_signal_2026-02-17/`
  - `/home/ubuntu/Hui/data/quant_score/v4/live_trading/accuracy/trade_2026-02-18_from_signal_2026-02-17/`

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
