# V4 Project Status (Public English Edition)

Last updated: 2026-02-16

## 1) Current Position
- Project focus: daily-frequency factor research and scoring
- Stage policy:
  - Stage 1 = baseline screening (winsor + rank)
  - Stage 2 = institutional robustness (industry + size/beta neutralization + zscore)
- Current runtime status:
  - `v1` Stage 1 rerun completed for six target factors
  - `v2` upgraded in-place to `v2.1`
  - `v2.1` Stage 1 segmented completed (54/54 segment tasks)
  - `v2.1` Stage 2 top3 completed (`value_v2,momentum_v2,quality_v2`)
  - `v2.1` full Train-Test / Walk-forward pending
  - `combo_v2` code implemented; core candidate currently `value+momentum`

## 2) Factor Progress Snapshot (New Protocol Rerun)
- Stage 1 completed (`v1` baseline):
  - Value
  - Momentum (6-1)
  - Reversal
  - Low-vol
  - Quality
  - PEAD
- Stage 1 completed (`v2.1`):
  - Value_v2
  - Momentum_v2
  - Reversal_v2
  - Low-vol_v2
  - Quality_v2
  - PEAD_v2
- Stage 2 status (`v2.1`):
  - Top3 completed: `value_v2,momentum_v2,quality_v2`
- Train/Test status (`v2.1`):
  - Not started
- Walk-forward status (`v2.1`):
  - Not started

- Combo status:
  - `combo_v2` strategy/config/tooling implemented
  - Local smoke checks passed (`segmented`, `walk-forward`, `run_with_config`)
  - Stage2 top3 conclusion: keep `value_v2` + `momentum_v2`, hold `quality_v2` for rework

## 3) Stage 1 Metrics (Completed, 2-Year Segments)
`v2.1` results:
- Value_v2: `ic_mean=0.047520`, `ic_std=0.015569`, `% positive segments=88.89%`, `valid_n=8/9`
- Momentum_v2: `ic_mean=0.012868`, `ic_std=0.022771`, `% positive segments=66.67%`, `valid_n=8/9`
- Quality_v2: `ic_mean=0.009247`, `ic_std=0.011422`, `% positive segments=55.56%`, `valid_n=8/9`
- Low-vol_v2: `ic_mean=0.009101`, `ic_std=0.033835`, `% positive segments=55.56%`, `valid_n=8/9`
- Reversal_v2: `ic_mean=0.005704`, `ic_std=0.004982`, `% positive segments=88.89%`, `valid_n=9/9`
- PEAD_v2: `ic_mean=0.000766`, `ic_std=0.030426`, `% positive segments=55.56%`, `valid_n=9/9`

`v1` baseline results:
- Value: `ic_mean=0.054227`, `ic_std=0.022106`, `% positive segments=88.89%`, `valid_n=8/9`
- Momentum: `ic_mean=0.012868`, `ic_std=0.022771`, `% positive segments=66.67%`, `valid_n=8/9`
- Reversal: `ic_mean=0.005325`, `ic_std=0.006380`, `% positive segments=100.00%`, `valid_n=9/9`
- Low-vol: `ic_mean=0.003209`, `ic_std=0.034677`, `% positive segments=44.44%`, `valid_n=8/9`
- Quality: `ic_mean=0.002387`, `ic_std=0.008456`, `% positive segments=55.56%`, `valid_n=8/9`
- PEAD: `ic_mean=0.000766`, `ic_std=0.030426`, `% positive segments=55.56%`, `valid_n=9/9`

Stage 1 ranking by `ic_mean` (`v2.1`):
1. Value
2. Momentum
3. Quality
4. Low-vol
5. Reversal
6. PEAD

## 4) Stage 2 Top3 Metrics (Completed, 2-Year Segments)
- Value_v2: `ic_mean=0.055206`, `ic_std=0.021952`, `% positive segments=88.89%`, `valid_n=8/9`
- Momentum_v2: `ic_mean=0.016483`, `ic_std=0.034164`, `% positive segments=66.67%`, `valid_n=8/9`
- Quality_v2: `ic_mean=-0.003500`, `ic_std=0.007554`, `% positive segments=44.44%`, `valid_n=8/9`

Stage 2 decision:
1. Keep: `value_v2`
2. Keep: `momentum_v2`
3. Rework/hold: `quality_v2`

## 5) v2.1 Formula Upgrade (Completed, Pending Validation)
- `momentum_v2`: added residual momentum option against benchmark (`MOMENTUM_USE_RESIDUAL=True`, `SPY`, 252-day beta estimation window)
- `reversal_v2`: added gap-risk and liquidity filters (`REVERSAL_MAX_GAP_PCT`, `REVERSAL_MIN_DOLLAR_VOL`)
- `low_vol_v2`: switched to residual + downside volatility baseline (`LOW_VOL_USE_RESIDUAL=True`, `LOW_VOL_DOWNSIDE_ONLY=True`)
- `value_v2` / `quality_v2`: keep mainstream component-wise cross-sectional composite logic
- `pead_v2`: keep strict event-day alignment baseline
- Runner pass-through updated for all three layers (`run_segmented_factors.py`, `run_with_config.py`, `run_walk_forward.py`)
- Local smoke run completed for `momentum_v2`, `reversal_v2`, `low_vol_v2` (single short segment)

## 6) Engineering Progress Completed
- Unified protocol + strategy override configuration system
- Stage 1/Stage 2 factor processing pipeline
- PIT fundamentals support (`available_date` as-of filtering)
- Delisting-aware data handling
- Market-cap-history support for universe constraints
- Forward-return IC as default research metric
- Report/diagnostics/checklist tooling for review workflow
- Test coverage for lag/no-lookahead/factor transformation behaviors

## 7) Next Steps
1. Update combo baseline to core pair `value+momentum`
2. Run `combo_v2` segmented / fixed train-test / walk-forward
3. Keep `quality_v2` in candidate pool and retest after targeted rework
4. Run `scripts/compare_v1_v2.py` and finalize keep/promote/rework decisions
