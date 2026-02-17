# Factor Notes (Public English Edition)

Last updated: 2026-02-17 (combo_v2 Layer2/Layer3 completed under locked linear settings)

Purpose: summarize current implementation logic and practical caveats for major factors.

## Value
- Implementation: composite of earnings yield, FCF yield, and EV/EBITDA yield.
- Status (`v2.1` Stage 1): completed.
- Stage 1 metrics (`v2.1`): `ic_mean=0.047520`, `ic_std=0.015569`, `% positive segments=88.89%`, `valid_n=8/9`.
- Stage 2 top3 metrics (`v2.1`): `ic_mean=0.055206`, `ic_std=0.021952`, `% positive segments=88.89%`, `valid_n=8/9`.
- Stage 2 strict+cache core-pair metrics (`v2026_02_16c_vm`): `ic_mean=0.053457`, `ic_std=0.021938`, `% positive segments=100.00%`, `valid_n=8/9`.
- v2.1 update: keeps mainstream cross-sectional component zscore composite with industry-aware component normalization.
- Notes: dependent on fundamentals freshness and PIT filtering quality.

## Quality
- Implementation: composite quality score (profitability, margin, cashflow quality, leverage penalty).
- Status (`v2.1` Stage 1): completed.
- Stage 1 metrics (`v2.1`): `ic_mean=0.009247`, `ic_std=0.011422`, `% positive segments=55.56%`, `valid_n=8/9`.
- Stage 2 top3 metrics (`v2.1`): `ic_mean=-0.003500`, `ic_std=0.007554`, `% positive segments=44.44%`, `valid_n=8/9`.
- v2.1 update: keeps mainstream component-wise composite with strict min-component-count and missing handling.
- Notes: sensitive to data coverage and specification details; currently held out from core combo.

## Low-vol
- Implementation: residual/downside volatility style signal.
- Status (`v2.1` Stage 1): completed.
- Stage 1 metrics (`v2.1`): `ic_mean=0.009101`, `ic_std=0.033835`, `% positive segments=55.56%`, `valid_n=8/9`.
- v2.1 update: default switched to residual volatility + downside-only volatility.
- Notes: robustness improves with stronger neutralization but remains inconsistent.

## Momentum
- Implementation: daily 6-1 style momentum setup.
- Status (`v2.1` Stage 1): completed.
- Stage 1 metrics (`v2.1`): `ic_mean=0.012868`, `ic_std=0.022771`, `% positive segments=66.67%`, `valid_n=8/9`.
- Stage 2 top3 metrics (`v2.1`): `ic_mean=0.016483`, `ic_std=0.034164`, `% positive segments=66.67%`, `valid_n=8/9`.
- Stage 2 strict+cache core-pair metrics (`v2026_02_16c_vm`): `ic_mean=0.014055`, `ic_std=0.026392`, `% positive segments=75.00%`, `valid_n=8/9`.
- v2.1 update: added residual momentum branch (`MOMENTUM_USE_RESIDUAL=True`) against `SPY`.
- Notes: direction and rebalance convention should be validated first.

## Reversal
- Implementation: short-horizon reversal signal.
- Status (`v2.1` Stage 1): completed.
- Stage 1 metrics (`v2.1`): `ic_mean=0.005704`, `ic_std=0.004982`, `% positive segments=88.89%`, `valid_n=9/9`.
- v2.1 update: added max gap filter and minimum dollar-volume filter to reduce microstructure noise.
- Notes: transaction-cost sensitivity is usually high.

## PEAD
- Implementation: event-driven earnings surprise alignment.
- Status (`v2.1` Stage 1): completed.
- Stage 1 metrics (`v2.1`): `ic_mean=0.000766`, `ic_std=0.030426`, `% positive segments=55.56%`, `valid_n=9/9`.
- v2.1 update: keeps strict event-day alignment baseline (`event_max_age_days=0`).
- Notes: strict event-date alignment and execution timing assumptions are critical.

## Combo_v2 (new)
- Implementation: institutional baseline combination now using core pair `value + momentum` (quality held out after Stage2).
- Default static baseline weights (current): `value=0.90`, `momentum=0.10`, `quality=0.00`.
- Formula comparison result (segmented Stage2 strict):
  - Linear `0.90/0.10`: `ic_mean=0.066149`, `ic_std=0.047273`, `pos_ratio=0.857143`, `valid_n=7/9`.
  - `value_momentum_gated`: `ic_mean=0.038463`, `ic_std=0.070371`, `pos_ratio=0.571429`, `valid_n=7/9`.
  - `value_momentum_two_stage`: `ic_mean=0.048188`, `ic_std=0.081973`, `pos_ratio=0.714286`, `valid_n=7/9`.
  - Decision: keep linear formula.
- Layer2 fixed train/test (locked combo):
  - Train IC (overall): `0.080637`
  - Test IC (overall): `0.053038`
- Layer3 walk-forward (locked combo, test years 2013-2025, `REBALANCE_MODE=None`):
  - `test_ic`: `mean=0.057578`, `std=0.033470`, `pos_ratio=1.0000`, `n=13`
  - `test_ic_overall`: `mean=0.050814`, `std=0.032703`, `pos_ratio=1.0000`, `n=13`
- Supports adaptive suggestion via `scripts/derive_combo_weights.py` from merged segmented outputs.
- Status: locked combo passed Layer2 and Layer3 under current protocol and is now the primary combo candidate.
- Integrity update (2026-02-17):
  - Segmented runner previously used hardcoded combo defaults, which invalidated an early weight-grid batch for final selection.
  - Runner has been fixed: `combo_v2` now reads `COMBO_WEIGHTS` from `strategies/combo_v2/config.py`.
  - Corrected weight-grid and formula comparison are complete; final lock is linear `0.90/0.10`.
  - Walk-forward setting note: use `REBALANCE_MODE=None` for combo Layer3, otherwise yearly windows can collapse to one rebalance date and yield `test_ic=N/A`.
