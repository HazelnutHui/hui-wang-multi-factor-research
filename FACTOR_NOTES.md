# Factor Notes (Public English Edition)

Last updated: 2026-02-13

Purpose: summarize current implementation logic and practical caveats for major factors.

## Value
- Implementation: composite of earnings yield, FCF yield, and EV/EBITDA yield.
- Status: strongest validated factor among completed runs.
- Notes: dependent on fundamentals freshness and PIT filtering quality.

## Quality
- Implementation: composite quality score (profitability, margin, cashflow quality, leverage penalty).
- Status: weak out-of-sample in latest tests.
- Notes: sensitive to data coverage and specification details.

## Low-vol
- Implementation: residual/downside volatility style signal.
- Status: mixed stability across market regimes.
- Notes: robustness improves with stronger neutralization but remains inconsistent.

## Momentum
- Implementation: daily 6-1 style momentum setup.
- Status: pending full segmented + train/test rerun under current protocol.
- Notes: direction and rebalance convention should be validated first.

## Reversal
- Implementation: short-horizon reversal signal.
- Status: pending full protocol run.
- Notes: transaction-cost sensitivity is usually high.

## PEAD
- Implementation: event-driven earnings surprise alignment.
- Status: pending full protocol run.
- Notes: strict event-date alignment and execution timing assumptions are critical.
