# Single-Factor Baseline (V4)

Last checked: 2026-03-09

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

## 4) Pass/Fail Baseline (Hard Rules v1.0)

This section is mandatory and authoritative for single-factor admission.

### 4.1 SF-L2 gate (fixed train/test)

1. `test_ic <= 0`: fail for main-combo admission (move to observation pool).  
2. `train_ic <= 0` and `test_ic > 0`: do not fail immediately; keep as low-priority candidate only.  
3. `train_ic <= 0` and `test_ic <= 0`: fail (remove from combo candidate set).  

### 4.2 SF-L3 gate (walk-forward)

1. Positive-window ratio must satisfy: `test_ic > 0` in at least `60%` of windows.  
2. No `3` consecutive negative `test_ic` windows are allowed.  
3. If either rule fails: factor is not admitted to main combo.

### 4.3 Cost gate

1. Out-of-sample net metric under current cost model must stay positive.  
2. If cost-adjusted out-of-sample turns negative: fail for main combo.

### 4.4 Factor grade for combo input

1. Grade `A`: `SF-L2 test_ic >= 0.006` and all gates above pass.  
2. Grade `B`: `0 < SF-L2 test_ic < 0.006` and all gates above pass.  
3. Grade `C`: `SF-L2 test_ic <= 0` or WF/cost gate fails.

Only `A` and `B` are eligible for main combo construction.

---

## 5) Record Keeping (Required)

1. Update `STATUS.md` with latest `SF-L1`/`SF-L2` results (`SF-DIAG` only if used).  
2. Update `docs/production_research/RESET_STATE_2026-02-27.md` and current batch master table with any logic changes or pitfalls.  
3. Keep report outputs in `strategies/<factor>/reports/`.  

## 6) Combo Admission And Weighting Rules (Hard Rules v1.0)

1. Main combo candidate set: include only factors with grade `A` or `B`.
2. Correlation control:
   - if recent sample `|corr| > 0.7`, do not hold both at full weight;
   - either keep one or apply explicit down-weighting.
3. Initial single-factor max weight cap in combo: `<= 15%`.
4. Build order:
   - first intra-group sub-combo (equal weight or risk-balanced);
   - then inter-group combo (equal weight by default).
5. A new factor is retained only if it improves out-of-sample combo quality after cost.

## 7) Regime Adaptation Rule (Hard Rules v1.0)

1. Long-history validation remains admission baseline; do not bypass with recent-only performance.
2. Recent `2-3` years are for weight tilt only, not for admission override.
3. Weight tilt limit vs baseline weight: within `+/-30%` relative change.
4. Any tilt update must be followed by a fresh fixed train/test + walk-forward record.
