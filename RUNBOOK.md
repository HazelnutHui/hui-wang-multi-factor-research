# V4 Runbook (Public English Edition)

Last updated: 2026-02-17

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

### 2.5 Combo baseline (institutional top3)
```bash
python scripts/run_with_config.py --strategy configs/strategies/combo_v2_inst.yaml
python scripts/run_segmented_factors.py --factors combo_v2 --years 2
python scripts/run_walk_forward.py --factors combo_v2 --train-years 3 --test-years 1 --start-year 2010 --end-year 2026
```

### 2.5b Combo final locked run (recommended)
```bash
# Layer2 fixed train/test
python3 scripts/run_with_config.py --strategy configs/strategies/combo_v2_inst.yaml

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
python scripts/derive_combo_weights.py --root . --out analysis/combo_v2_weights_suggested.csv
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

### 2.9 Stage2 strict top3 (institutional segmented, 6-core)
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

### 2.10 Post-WF institutional gates (must-pass before paper/live)
Use:
- `POST_WF_INSTITUTIONAL_CHECKLIST.md`

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
