# Single-Factor Baseline (V4)

Last checked: 2026-02-25

Purpose: define a complete, modular baseline workflow for a new single factor before combination.

---

## 0) Scope

This baseline is for daily-frequency single-factor research using the V4 system.
It is intended to be a repeatable, professional-grade checklist with explicit steps and commands.
Default execution is now trading-day based with dynamic cost enabled (see `RUNBOOK.md` for toggles).

---

## 1) Factor Module Spec (Minimum Required)

Fill this once per new factor. This is the “module spec” that drives execution.

1. **Name**:  
2. **Family**: (risk/defensive, value, quality, behavior, event, liquidity, etc.)  
3. **Direction**: (higher = better / lower = better / absolute / conditional)  
4. **Data dependencies**: (prices, fundamentals, events, etc.)  
5. **PIT fields**: (available_date / acceptedDate / filingDate / none)  
6. **Formula (exact)**:  
7. **Lookback**:  
8. **Lag / delay**:  
9. **Winsor / clipping**:  
10. **Standardization**: (rank / zscore / none)  
11. **Neutralization**: (industry / sector / market / size / beta / none)  
12. **Update frequency**: (daily / weekly / monthly / quarterly)  
13. **Universe filters**: (min price, min dollar vol, min cap, max vol)  
14. **Execution**: (delay, entry/exit price)  
15. **Holding period**:  
16. **Costs**:  
17. **Validation lane**: (`SF-L1` / `SF-L2` / `SF-L3` / `SF-DIAG`)  

---

## 2) Baseline Workflow (Required Steps)

Precondition (required):
- candidate must come from `S0` factor-factory ranking shortlist (recommended top `20-30`);
- do not run full single-factor baseline stack on all raw candidates.

### Step 1. Data + PIT sanity
Goal: ensure data exists and PIT timing is valid.

1. Verify required data folders exist and are non-empty.  
2. Verify PIT availability (if fundamentals).  
3. Note reset-boundary risks in `docs/production_research/RESET_STATE_2026-02-27.md`.  

### Step 2. SF-L1 segmented strict backtest (mandatory)
Goal: production-style robustness check (primary single-factor segmented gate).

Command template:
```bash
PYTHONPATH=/Users/hui/quant_score/v4 /Users/hui/miniconda3/envs/qscore/bin/python3.11 \
  /Users/hui/quant_score/v4/scripts/run_segmented_factors.py --factors <factor> --years 2 \
  --set SIGNAL_ZSCORE=True --set SIGNAL_RANK=False --set INDUSTRY_NEUTRAL=True \
  --set SIGNAL_NEUTRALIZE_SIZE=True --set SIGNAL_NEUTRALIZE_BETA=True \
  |& tee /Users/hui/quant_score/v4/logs/<factor>_segment_sf_l1_YYYY-MM-DD.log
```

Outputs:
- `segment_results/<timestamp>/<factor>/segment_summary.csv`

### Step 3. SF-L2 Fixed Train/Test (mandatory)
Goal: check overfit and out-of-sample degradation.

Command template:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python3.11 /Users/hui/quant_score/v4/scripts/run_with_config.py \
  --strategy /Users/hui/quant_score/v4/configs/strategies/<factor>_v1.yaml
```

If not using configs, run the strategy entrypoint directly:
```bash
/Users/hui/miniconda3/envs/qscore/bin/python3.11 -m strategies.<factor>_v1.run
```

### Step 4. SF-DIAG segmented diagnostics (optional)
Goal: debug parameter sensitivity or abnormal behavior, non-gating.

Command template:
```bash
PYTHONPATH=/Users/hui/quant_score/v4 /Users/hui/miniconda3/envs/qscore/bin/python3.11 \
  /Users/hui/quant_score/v4/scripts/run_segmented_factors.py --factors <factor> --years 2 \
  |& tee /Users/hui/quant_score/v4/logs/<factor>_segment_sf_diag_YYYY-MM-DD.log
```

### Step 5. SF-L3 Walk-forward (shortlist only)
Goal: deployment-style rolling validation for top candidates only.

```bash
/Users/hui/miniconda3/envs/qscore/bin/python3.11 /Users/hui/quant_score/v4/scripts/run_walk_forward.py \
  --factors <factor> --train-years 3 --test-years 1 --start-year 2010 --end-year 2026
```

### Step 6. Professional factor report
Goal: quantiles, rolling IC, turnover, cost sensitivity.

```bash
/Users/hui/miniconda3/envs/qscore/bin/python3.11 /Users/hui/quant_score/v4/scripts/generate_factor_report.py \
  --strategy /Users/hui/quant_score/v4/configs/strategies/<factor>_v1.yaml \
  --quantiles 5 --rolling-window 60 --cost-multipliers 2,3
```

Outputs:
- `strategies/<factor>/reports/` (md/json/csv)

---

## 3) Robustness Extensions (Recommended)

### 3.1 Parameter sensitivity (±20% lookback)
Re-run `SF-DIAG` with lookback ±20% and compare IC.

Example:
```bash
... run_segmented_factors.py --factors <factor> --years 2 --set <LOOKBACK_PARAM>=<value>
```

### 3.2 Standardization swap (rank vs zscore)
Re-run `SF-DIAG` with rank/zscore variants to inspect sensitivity.

### 3.3 Sub-universe checks
At least one of:
1. Large cap only (raise `MIN_MARKET_CAP` if market cap history exists).  
2. High liquidity only (raise `MIN_DOLLAR_VOLUME`).  

---

## 4) Pass/Fail Baseline (Default Guidance)

Use this unless you override with your own standards.

1. Segmented IC: majority of segments > 0, no long negative streaks.  
2. Train/Test: test IC does not collapse to ~0.  
3. Cost sensitivity: still positive at 2x cost.  
4. Robustness: rank vs zscore does not flip sign.  
5. Sub-universe: at least one sub-universe remains positive.  

---

## 5) Record Keeping (Required)

1. Update `STATUS.md` with latest `SF-L1`/`SF-L2` results (`SF-DIAG` only if used).  
2. Update `docs/production_research/RESET_STATE_2026-02-27.md` and current batch master table with any logic changes or pitfalls.  
3. Keep report outputs in `strategies/<factor>/reports/`.  
