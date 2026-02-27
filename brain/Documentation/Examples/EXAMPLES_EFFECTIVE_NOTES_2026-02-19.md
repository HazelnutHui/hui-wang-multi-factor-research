# Examples (1 Article) Effective Notes

Source:
- `brain/results/examples_docs/3-.txt`
- Article title: `Alpha Examples for Beginners`

Goal:
- Extract reusable alpha-construction patterns and practical upgrade directions.

## 1) Reusable Pattern Library From Examples

### Pattern A: Event/Fundamental signal + backfill for coverage
- Example idea: momentum after news.
- Core expression style:
  - `ts_backfill(vec_avg(nws12_prez_4l), 504)`
- Why it matters:
  - sparse fundamentals/event fields often need backfill to pass coverage/sub-universe checks.

### Pattern B: Time-series ranking for firm-relative trend
- Examples:
  - `ts_rank(pretax_income, 250)`
  - `ts_rank(operating_income, 252)`
- Why it matters:
  - compares each stock to its own history, reducing scale mismatch across firms.

### Pattern C: Ratio normalization by firm size
- Example:
  - `ts_backfill(fnd6_drc, 252) / assets` (deferred revenue scaled by assets)
- Why it matters:
  - raw accounting levels are hard to compare cross-sectionally; size-scaling improves comparability.

### Pattern D: Directional sign flip to align hypothesis
- Examples:
  - `-ts_rank(fn_liab_fair_val_l1_a, 252)` (liability value rising is bearish)
  - `-ts_quantile(debt, 126)` (debt reduction hypothesis)
- Why it matters:
  - many fields need explicit sign inversion to match long/short thesis.

### Pattern E: Leverage-style structural ratio
- Example:
  - `liabilities / assets`
- Why it matters:
  - simple ratio factors can work as baseline; then refine by risk controls and filters.

## 2) Common Improvement Levers Repeated in Article
- Add liquidity conditioning (e.g., favor liquid names) to improve sub-universe robustness.
- Add complementary business-strength fields (e.g., sales) to strengthen base signal.
- Replace raw values with cross-sectional transforms (`rank`, `quantile`) to reduce concentration.
- Use group-based comparisons for heterogeneous industries (sector/industry/subindustry-aware).
- Test shorter/alternative lookback windows instead of fixed annual windows.
- Tune operator distribution/driver settings where available (e.g., quantile variants).

## 3) Settings Tendencies in the Examples
- Delay: mostly `1`.
- Pasteurization: `On`.
- NaN handling: often `Off` (implies manual NaN treatment is expected in stronger versions).
- Truncation: frequently around `0.01` to `0.08`, with one loose example at `1`.
- Neutralization varied by idea:
  - `Market`, `Industry`, `Subindustry`, `Sector`.
- Practical takeaway:
  - neutralization choice is signal-dependent and should be tested, not fixed by habit.

## 4) Immediate Build Checklist (Using This Article)
1. Start from one clear hypothesis and write a minimal expression.
2. Fix coverage first (`ts_backfill`, avoid sparse raw fields).
3. Fix comparability (`/assets`, `rank`, `quantile`, group operators).
4. Align sign with economic intuition (`-` where needed).
5. Tune settings in this order:
   - neutralization -> truncation -> decay -> universe.
6. Re-check sub-universe robustness after each change.

## 5) Direct Relevance to Your Current Workflow
- Your value/momentum framework can reuse these tactics directly:
  - coverage hardening for sparse fundamentals,
  - size-scaling before cross-sectional blending,
  - neutralization choice by factor family,
  - sign checks per component before weighted combination.

