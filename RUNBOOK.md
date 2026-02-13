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
