# Post-WF Institutional Checklist (Combo Strategy)

Last updated: 2026-02-17

Purpose: standardized post-walk-forward validation gates before paper/live deployment.

Applies to current locked combo:
- `COMBO_FORMULA=linear`
- `value=0.90`, `momentum=0.10`
- Stage2 strict neutralization and universe filters

## 1) Freeze Research Version
- Do not change factor formulas or combo weights during this checklist.
- Record commit hash:

```bash
git rev-parse --short HEAD
```

## 2) Cost Stress (Fixed Train/Test)
Run same strategy config with multiple cost multipliers.

```bash
python3 scripts/run_with_config.py --strategy configs/strategies/combo_v2_inst.yaml --cost-multiplier 1.0 |& tee logs/combo_postwf_cost_x1.0.log
python3 scripts/run_with_config.py --strategy configs/strategies/combo_v2_inst.yaml --cost-multiplier 1.5 |& tee logs/combo_postwf_cost_x1.5.log
python3 scripts/run_with_config.py --strategy configs/strategies/combo_v2_inst.yaml --cost-multiplier 2.0 |& tee logs/combo_postwf_cost_x2.0.log
```

Minimum expectation:
- Test IC remains positive under `x1.5` and `x2.0`.
- Degradation is controlled (not collapsing to near-zero).

## 3) Cost + Universe Stress (Walk-Forward)
Run rolling validation under stricter liquidity/cap constraints.

```bash
python3 scripts/run_walk_forward.py \
  --factors combo_v2 \
  --train-years 3 --test-years 1 --start-year 2010 --end-year 2025 \
  --out-dir walk_forward_results/combo_v2_postwf_stress_x1_5 \
  --set REBALANCE_MODE=None \
  --set COMBO_FORMULA=linear \
  --set COST_MULTIPLIER=1.5 \
  --set SIGNAL_ZSCORE=True \
  --set SIGNAL_RANK=False \
  --set SIGNAL_WINSOR_PCT_LOW=0.01 \
  --set SIGNAL_WINSOR_PCT_HIGH=0.99 \
  --set SIGNAL_MISSING_POLICY=drop \
  --set INDUSTRY_NEUTRAL=True \
  --set INDUSTRY_MIN_GROUP=5 \
  --set SIGNAL_NEUTRALIZE_SIZE=True \
  --set SIGNAL_NEUTRALIZE_BETA=True \
  --set MIN_MARKET_CAP=2000000000 \
  --set MIN_DOLLAR_VOLUME=5000000 \
  --set MIN_PRICE=5 \
  |& tee logs/combo_postwf_stress_x1_5.log
```

Optional harsher scenario:
- `COST_MULTIPLIER=2.0`
- `MIN_DOLLAR_VOLUME=10000000`

## 4) Post-Hoc Risk Diagnostics
Generate non-invasive diagnostics on latest strategy outputs.

```bash
python3 scripts/posthoc_factor_diagnostics.py --strategy strategies/combo_v2 --top-pct 0.2
```

Check:
- `beta_vs_spy` not unintentionally extreme
- turnover overlap not too low (avoid excessive churn)
- size exposure not unintentionally one-sided

## 5) Walk-Forward Aggregate Check
Print aggregate metrics from the stress run summary.

```bash
python3 - <<'PY'
import pandas as pd
p='walk_forward_results/combo_v2_postwf_stress_x1_5/combo_v2/walk_forward_summary.csv'
df=pd.read_csv(p)
x=pd.to_numeric(df['test_ic'], errors='coerce').dropna()
y=pd.to_numeric(df['test_ic_overall'], errors='coerce').dropna()
print('rows=', len(df))
print('test_ic mean=', x.mean() if len(x)>0 else None, 'std=', x.std(ddof=1) if len(x)>1 else None, 'pos_ratio=', (x>0).mean() if len(x)>0 else None, 'n=', len(x))
print('test_ic_overall mean=', y.mean() if len(y)>0 else None, 'std=', y.std(ddof=1) if len(y)>1 else None, 'pos_ratio=', (y>0).mean() if len(y)>0 else None, 'n=', len(y))
PY
```

## 6) Pass/Fail Gates (Recommended)
Pass if all hold:
1. Walk-forward `test_ic` mean remains positive and `pos_ratio >= 0.70`.
2. Stress scenario (`x1.5`) still positive on aggregate IC.
3. No obvious risk concentration from diagnostics (beta/industry/size).
4. Turnover profile is acceptable for planned capital and holding horizon.

Fail if any holds:
1. Stress scenario collapses (IC near zero or negative).
2. Beta/industry/size exposure dominates alpha signal.
3. Turnover too high for real execution constraints.

## 7) Promotion Rule
Only after pass:
1. Promote to paper-trading candidate for 4-8 weeks.
2. Keep research config frozen during paper period.
3. Define kill-switch thresholds before first live trade.
