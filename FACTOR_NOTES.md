# Factor Notes (Public English Edition)

Last updated: 2026-02-16 (v2.1 Stage1 completed)

Purpose: summarize current implementation logic and practical caveats for major factors.

## Value
- Implementation: composite of earnings yield, FCF yield, and EV/EBITDA yield.
- Status (`v2.1` Stage 1): completed.
- Stage 1 metrics (`v2.1`): `ic_mean=0.047520`, `ic_std=0.015569`, `% positive segments=88.89%`, `valid_n=8/9`.
- v2.1 update: keeps mainstream cross-sectional component zscore composite with industry-aware component normalization.
- Notes: dependent on fundamentals freshness and PIT filtering quality.

## Quality
- Implementation: composite quality score (profitability, margin, cashflow quality, leverage penalty).
- Status (`v2.1` Stage 1): completed.
- Stage 1 metrics (`v2.1`): `ic_mean=0.009247`, `ic_std=0.011422`, `% positive segments=55.56%`, `valid_n=8/9`.
- v2.1 update: keeps mainstream component-wise composite with strict min-component-count and missing handling.
- Notes: sensitive to data coverage and specification details.

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
