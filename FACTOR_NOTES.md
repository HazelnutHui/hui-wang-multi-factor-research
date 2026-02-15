# Factor Notes (Public English Edition)

Last updated: 2026-02-15

Purpose: summarize current implementation logic and practical caveats for major factors.

## Value
- Implementation: composite of earnings yield, FCF yield, and EV/EBITDA yield.
- Status (new protocol Stage 1 rerun): completed.
- Interim metrics: `ic_mean=0.054063`, `ic_std=0.021962`, `% positive segments=88.89%`.
- Notes: dependent on fundamentals freshness and PIT filtering quality.

## Quality
- Implementation: composite quality score (profitability, margin, cashflow quality, leverage penalty).
- Status (new protocol Stage 1 rerun): completed.
- Interim metrics: `ic_mean=0.000957`, `ic_std=0.008283`, `% positive segments=44.44%`.
- Notes: sensitive to data coverage and specification details.

## Low-vol
- Implementation: residual/downside volatility style signal.
- Status (new protocol Stage 1 rerun): completed.
- Interim metrics: `ic_mean=0.003209`, `ic_std=0.034677`, `% positive segments=44.44%`.
- Notes: robustness improves with stronger neutralization but remains inconsistent.

## Momentum
- Implementation: daily 6-1 style momentum setup.
- Status (new protocol Stage 1 rerun): completed.
- Interim metrics: `ic_mean=0.012868`, `ic_std=0.022771`, `% positive segments=66.67%`.
- Notes: direction and rebalance convention should be validated first.

## Reversal
- Implementation: short-horizon reversal signal.
- Status (new protocol Stage 1 rerun): completed.
- Interim metrics: `ic_mean=0.003564`, `ic_std=0.010793`, `% positive segments=44.44%`.
- Notes: transaction-cost sensitivity is usually high.

## PEAD
- Implementation: event-driven earnings surprise alignment.
- Status (new protocol Stage 1 rerun): completed.
- Interim metrics: `ic_mean=0.000766`, `ic_std=0.030426`, `% positive segments=55.56%`.
- Notes: strict event-date alignment and execution timing assumptions are critical.
