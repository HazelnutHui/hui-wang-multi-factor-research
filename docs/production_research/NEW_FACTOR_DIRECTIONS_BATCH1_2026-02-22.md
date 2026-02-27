# New Factor Directions Batch 1 (2026-02-22)

Purpose:
- expand beyond pure parameter tuning;
- keep daily tradability and interpretability;
- support immediate fast-screen execution.

## Factor Set

1. `turnover_shock`
- Definition: `log(ADV_20 / ADV_120)`, `ADV = close * volume`.
- Interpretation: recent liquidity/attention acceleration.
- Data: price + volume only.

2. `vol_regime`
- Definition: `(vol_120 - vol_20) / vol_120`, using daily log returns.
- Interpretation: short-term volatility regime vs long-run baseline.
- Data: close price only.

3. `quality_trend`
- Definition: `quality_score(t) - quality_score(t-252d)`.
- Interpretation: cross-sectional improvement/deterioration in quality.
- Data: existing quality fundamentals (`data/fmp/ratios/quality`).

## Implementation Scope

- Engine support added in `backtest/factor_engine.py`.
- Config pass-through added in `scripts/run_with_config.py`.
- Segmented single-factor entry added in `scripts/run_segmented_factors.py`:
  - `turnover_shock`
  - `vol_regime`
  - `quality_trend`

## Batch Research Flow

1. run segmented single-factor baseline on these three factors;
2. rank by stability + cost sensitivity;
3. promote top candidates into combo weights for fast batch;
4. send shortlisted variants to official gate.

