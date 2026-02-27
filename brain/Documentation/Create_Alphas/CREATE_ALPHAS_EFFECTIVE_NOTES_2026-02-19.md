# Create Alphas (4 Articles) Effective Notes

Source files:
- `brain/results/create_alphas_docs/21.txt`
- `brain/results/create_alphas_docs/22.txt`
- `brain/results/create_alphas_docs/23.txt`
- `brain/results/create_alphas_docs/24.txt`

Goal:
- Keep only practical, test-relevant, and submission-relevant information.

## 1) First-Simulation Baseline (Minimal Working Setup)
- Suggested starter expression from docs: `-ts_delta(close, 5)` (or `-delta(close, 5)` UI alias).
- Typical starter settings:
  - `Region/Universe`: `USA / TOP3000`
  - `Delay`: `1`
  - `Neutralization`: `Subindustry` or `Market` (docs show both contexts)
- Read first:
  - PnL curve stability (not only return magnitude).
  - Sharpe-through-time graph (consistency over time).

## 2) “Good Alpha” Criteria Mentioned in Docs
- Turnover: low but not below `1%`.
- Drawdown: `< 10%` (guidance context).
- Sharpe:
  - `> 2.0` for Delay-0
  - `> 1.25` for Delay-1

These are practical pass-quality signals for early filtering.

## 3) Test Period Feature (Train/Test Split Inside IS)
- Purpose: reduce overfitting by separating development and validation slices.
- Important behavior:
  - Simulation still runs on full IS window.
  - Stats/visualization are split into Train and Test sections.
  - Submission tests still evaluate full IS.
- Operational note in docs:
  - Test-period view must be revealed (`Show test period`) to submit.

## 4) Simulation Settings That Matter Most

### Delay
- `Delay=0`: trade using same-day available info assumption.
- `Delay=1`: trade next day using today’s data; generally more conservative.
- Delay is applied by platform mechanics (you do not manually lag fields for this purpose).

### Decay
- Linear smoothing:
  - combines current signal with previous `n` days.
- Constraints:
  - legal `n` is integer and `n >= 0`.
- Use:
  - lower turnover / reduce over-reactivity.
- Risk:
  - too large decay attenuates signal.

### Truncation
- Max per-instrument weight cap.
- Legal range: `0 <= truncation <= 1`.
- Practical recommendation: `0.05 ~ 0.1`.

### Neutralization
- Market neutralization: `alpha = alpha - mean(alpha)` on whole universe.
- Industry/Subindustry: same operation within each group bucket.
- Effect: reduce systematic market/group exposure.

### Pasteurize
- `On` (default): inputs outside selected universe become NaN.
- `Off`: keep broader available inputs; can manually apply `pasteurize(x)` where needed.

### NaN Handling
- `On`: platform fills/propagates according to operator-specific rules (higher coverage, but possible ambiguity).
- `Off` (default in docs examples): preserve NaNs; user handles explicitly.
- For clarity-sensitive alphas, explicit manual NaN logic is safer.

### Unit Handling
- Raises warnings for incompatible-unit operations (e.g., price + volume).
- Warning may not block run, but should trigger economic-sanity check.

## 5) How BRAIN Works (Execution Intuition You Should Keep)
Given an expression and settings, BRAIN repeatedly does:
1. Evaluate expression cross-sectionally for date `t` (with delay convention).
2. Neutralize (market/industry/subindustry).
3. Normalize weights so absolute-sum is 1.
4. Scale to book size (docs example uses fixed $20M).
5. Compute next-day PnL from positions and realized returns.
6. Repeat across IS dates.
7. Aggregate cumulative PnL and performance metrics.

Key portfolio implication:
- Daily traded dollars come from weight changes between `t-1` and `t`; this drives turnover.

## 6) Practical Build Loop (Actionable)
1. Start with simple thesis expression.
2. Ensure shape:
  - ranking/normalization to avoid concentration
  - truncation control
  - proper neutralization
3. Run Train/Test split checks in Test Period view.
4. Tune decay for turnover without killing edge.
5. Submit only when both stability and pass metrics are acceptable.

## 7) Immediate Application to Your Current Workflow
- Your current daily quant workflow already aligns with:
  - Delay-1 semantics (`T -> T+1`)
  - neutralization-first design
  - weight/risk controls
- When porting to BRAIN:
  - lock settings first (Delay/Neutralization/Truncation/Decay),
  - then iterate expression,
  - then verify train/test stability before submission.

