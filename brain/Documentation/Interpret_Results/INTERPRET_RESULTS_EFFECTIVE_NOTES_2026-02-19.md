# Interpret Results (2 Articles) Effective Notes

Source files:
- `brain/results/interpret_results_docs/41.txt`
- `brain/results/interpret_results_docs/42.txt`

Goal:
- Keep submission-critical thresholds, formulas, and decision rules.

## 1) Submission-Critical Cutoffs (Alpha)
- `Sharpe`:
  - Delay-0: `> 2.0`
  - Delay-1: `> 1.25`
- `Fitness`:
  - Delay-0: `> 1.3`
  - Delay-1: `> 1.0`
- `Turnover`: `1% < Turnover < 70%`
- `Weight test`:
  - max weight on any instrument `< 10%`
  - and sufficient breadth (not too few instruments carrying weight)
- `Self-correlation`:
  - `< 0.7`, or
  - if correlated alpha exists, new alpha Sharpe should be at least `10%` higher.
- `Sub-universe test`: must clear threshold.

## 2) Sub-Universe Test (Most Important Robustness Formula)
- Published threshold:
  - `subuniverse_sharpe >= 0.75 * sqrt(subuniverse_size / alpha_universe_size) * alpha_sharpe`
- Interpretation:
  - alpha should remain effective in a more liquid/smaller universe (e.g., TOP3000 -> TOP1000 check).
- Practical fixes mentioned:
  - avoid heavy size/illiquidity multipliers that over-shift weight distribution;
  - liquidity-aware decay mixes;
  - re-check changes step-by-step (improvements can accidentally break sub-universe robustness).

## 3) Test Failure Message Order (What to Fix First)
When checking submission, failures are surfaced roughly in this sequence:
1. Weight test
2. Correlation test
3. Fitness test
4. Delay-0 check against Delay-1 suitability
5. Sub-universe test

Operational takeaway:
- solve concentration/breadth first, then correlation, then pure performance tuning.

## 4) Core Metrics Definitions (BRAIN)
- `IR = mean(PnL) / stdev(PnL)`
- `Sharpe = sqrt(252) * IR`
- `Returns = AnnualizedPnL / (0.5 * BookSize)`
- `Fitness = Sharpe * sqrt(abs(Returns) / max(Turnover, 0.125))`
- `Margin = PnL / TotalDollarsTraded`
- `Drawdown = largest peak-to-trough PnL gap / (0.5 * BookSize)`

Book size convention in docs:
- fixed daily book (example: $20M), with performance normalized on half-book notion.

## 5) Fitness Rating Bands (from results panel doc)
- Delay-1:
  - Spectacular `> 2.5`
  - Excellent `> 2.0`
  - Good `> 1.5`
  - Average `> 1.0`
  - Needs Improvement `<= 1.0`
- Delay-0:
  - Spectacular `> 3.25`
  - Excellent `> 2.6`
  - Good `> 1.95`
  - Average `> 1.3`
  - Needs Improvement `<= 1.3`

## 6) IS / Semi-OS / OS Interpretation
- Rolling IS window in docs:
  - starts ~7 years ago, ends ~2 years ago.
- Latest 2 years are hidden (semi-OS style) for scoring/test robustness.
- OS stats appear progressively after submission.
- Practical use:
  - do not trust IS-only excellence if robustness and correlation are weak.

## 7) Portfolio Construction Intuition to Keep
- Weight vector diversity is as important as Sharpe.
- High return with concentrated weights is fragile and often non-submittable.
- Correlation diversification can be more valuable than marginal Sharpe gain on similar ideas.

## 8) Decision Rules For Real Workflow
1. Gate by hard cutoffs (`Sharpe/Fitness/Turnover`).
2. Gate by implementation robustness (`Weight/Sub-universe/Self-correlation`).
3. Prefer lower-correlation new ideas over over-optimizing one correlated idea.
4. Submit only when both performance and robustness are jointly acceptable.

