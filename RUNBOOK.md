# V4 Runbook (Public English Edition)

Last updated: 2026-02-13

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

### 2.5 Factor report generation
```bash
python scripts/generate_factor_report.py --strategy configs/strategies/momentum_v1.yaml --quantiles 5 --rolling-window 60 --cost-multipliers 2,3
```

### 2.6 Tests
```bash
python -m pytest tests
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
