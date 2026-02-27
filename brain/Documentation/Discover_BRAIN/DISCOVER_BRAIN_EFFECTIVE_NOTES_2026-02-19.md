# Discover BRAIN (7 Articles) Effective Notes

Source files:
- `brain/results/discover_brain_docs/1.txt` ... `brain/results/discover_brain_docs/7.txt`

Goal:
- Keep only actionable information for alpha building, evaluation, and challenge scoring.

## 1) BRAIN Simulation Core Mechanics
- Alpha expression is evaluated cross-sectionally each day and converted into portfolio weights.
- Positive weight = long, negative weight = short.
- Weights are scaled to book size; PnL is simulated day by day.
- Typical delay interpretation in examples: `Delay=1` uses prior-day data for next-day trade.

## 2) Fast Expression Practical Rules
- Fast Expression is the only official expression language for alpha simulation on platform.
- Expression components: data fields + operators + constants.
- `;` is used to separate statements; final statement is the alpha output used for positions.
- Use comments (`/* ... */`) for readability.

## 3) IS Metrics and Pass Thresholds (Most Useful)
- IS horizon in docs: 5-year in-sample.
- Main metrics to watch: `Sharpe`, `Turnover`, `Fitness`, `Returns`, `Drawdown`, `Margin`.
- Mentioned cutoffs:
  - `Sharpe > 1.25`
  - `Turnover in [1%, 70%]`
  - `Fitness > 1.0`

## 4) High-Frequency Failure Modes and Fixes
- Problem: weight concentration / too few instruments / max instrument weight too high.
  - Fixes:
    - apply cross-sectional normalization like `rank(...)`
    - set truncation around `0.1`
    - use `ts_backfill` to improve coverage
- Problem: low sub-universe Sharpe.
  - Practical mitigation in docs: increase universe size (e.g., `TOP3000`) and re-test robustness.
- Problem: syntax errors.
  - Check exact operator and field spellings from platform lists.
- Problem: unit warning (e.g., adding incompatible units).
  - Usually warning-level, but still verify economic meaning.

## 5) Settings That Most Affect Results
- `Universe`: liquidity-ranked instrument set; affects robustness and score profile.
- `Neutralization`: removes group-level mean exposure.
  - Docs state operation form: `Alpha = Alpha - mean(Alpha)` within chosen grouping.
  - Grouping options: Market / Industry / Sub-industry.
- `Truncation`: cap max weight per stock; docs recommend roughly `0.05 ~ 0.1`.
- `Decay`: linear smoothing over time; can reduce turnover, but too large may weaken signal.
- `Region`: alpha behavior and field coverage are region-dependent.

## 6) Operator Tips Repeated Across Docs
- Prefer cross-sectional stabilizers (`rank`) to reduce extreme concentration.
- Use time-series operators (`ts_rank`, `ts_delta`, `ts_backfill`) to improve stability/coverage.
- For first formulas, simple baseline + stable settings outperform over-complicated expressions.

## 7) Challenge Scoring: What Actually Matters
- Score is daily (EST), not per single alpha.
- Daily score cap: `2000`.
- Refresh time: `3 AM EST`.
- No negative score deduction.
- Quantity and quality both matter; quality depends on:
  - smaller universe preference in scoring component (as documented)
  - lower self-correlation
  - higher fitness
  - Delay effect (`D1` contributes more than `D0`, per docs)

## 8) Recommended Execution Workflow (From Docs, Trimmed)
1. Start with simple expressions and baseline settings.
2. Evaluate IS metrics against hard cutoffs (Sharpe/Turnover/Fitness).
3. Fix concentration first (`rank`, truncation, backfill).
4. Tune neutralization/decay for risk and turnover balance.
5. Improve quality before increasing quantity of submissions.

## 9) Immediate Application To Your Current Work
- Keep your current style of:
  - explicit delay convention
  - neutralization enabled
  - truncation control
  - coverage checks via backfill/missing handling
- When porting V4 logic to BRAIN:
  - verify field names first,
  - then enforce ranking/truncation to avoid concentration test failures.

