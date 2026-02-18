# V4 Project Status (Public English Edition)

Last updated: 2026-02-18 (daily pipeline hardened for incremental live publish)

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
  - `v2.1` Stage 2 strict core-pair rerun completed (`value_v2,momentum_v2`, 18/18)
  - Stage2 signal cache pipeline implemented and verified on workstation (`395` cache files generated)
  - Combo segmented runner bug fixed: `combo_v2` now reads `COMBO_WEIGHTS` from strategy config (previous hardcoded weights removed from effective path)
  - `combo_v2` Layer1 segmented completed with locked linear settings
  - `combo_v2` Layer2 fixed train/test completed (`train_ic=0.080637`, `test_ic=0.053038`)
  - `combo_v2` Layer3 walk-forward completed (2013-2025 windows, `REBALANCE_MODE=None`)
  - `combo_v2` post-WF stress validation completed (`COST_MULTIPLIER=1.5` + stricter universe), passed
  - `combo_v2` now locked as core candidate (`value+momentum`, linear)

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
  - Core pair strict+cache run completed: `value_v2,momentum_v2`
- Train/Test status (`v2.1`):
  - Not started
- Walk-forward status (`v2.1`):
  - Not started

  - Combo status:
  - `combo_v2` strategy/config/tooling implemented
  - Full three-layer validation completed (`segmented`, `run_with_config`, `walk-forward`)
  - Stage2 top3 conclusion: keep `value_v2` + `momentum_v2`, hold `quality_v2` for rework
  - Stage2 strict rerun profile added: `v2026_02_16b` (institutional stricter universe + neutralization config)
  - Weight-grid note:
    - Previous `combo_weight_grid_2026_02_17_p6` batch is invalid for final selection due to segmented-runner hardcoded combo weights.
    - Corrected batch `combo_weight_grid_2026_02_17_fix` completed.
    - Linear weight ranking: `w090_m010` > `w080_m020` > `w070_m030`.
    - Provisional linear winner: `value=0.90, momentum=0.10`.
  - Formula research status:
    - Added formula-level combo options in engine/config (`COMBO_FORMULA`): `value_momentum_gated`, `value_momentum_two_stage`.
    - Segmented Stage2 strict comparison completed:
      - `two_stage`: `ic_mean=0.048188`, `ic_std=0.081973`, `pos_ratio=0.714286`, `valid_n=7/9`
      - `gated`: `ic_mean=0.038463`, `ic_std=0.070371`, `pos_ratio=0.571429`, `valid_n=7/9`
    - Final combo lock: linear formula with `value=0.90`, `momentum=0.10`.
  - Layer2/Layer3 final metrics (locked combo):
    - Layer2 fixed train/test:
      - Train IC (overall): `0.080637`
      - Test IC (overall): `0.053038`
    - Layer3 walk-forward (`start-year=2010`, `end-year=2025`, `REBALANCE_MODE=None`):
      - `test_ic`: `mean=0.057578`, `std=0.033470`, `pos_ratio=1.0000`, `n=13`
      - `test_ic_overall`: `mean=0.050814`, `std=0.032703`, `pos_ratio=1.0000`, `n=13`
    - Important implementation note:
      - Without `REBALANCE_MODE=None`, walk-forward degenerated to one rebalance date per year and produced `test_ic=N/A`.
      - Correct production research setting for this combo walk-forward run is `REBALANCE_MODE=None`.
  - Post-WF stress validation metrics (6-core shard run, merged):
    - Path: `walk_forward_results/combo_v2_postwf_stress_x1_5_p6/combo_v2/walk_forward_summary.csv`
    - `test_ic`: `mean=0.053310`, `std=0.032486`, `pos_ratio=1.0000`, `n=13`
    - `test_ic_overall`: `mean=0.046618`, `std=0.032058`, `pos_ratio=1.0000`, `n=13`
    - Verdict: pass (stress scenario remains positive and stable)

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

## 4) Stage 2 Metrics (Completed, 2-Year Segments)
- Value_v2: `ic_mean=0.055206`, `ic_std=0.021952`, `% positive segments=88.89%`, `valid_n=8/9`
- Momentum_v2: `ic_mean=0.016483`, `ic_std=0.034164`, `% positive segments=66.67%`, `valid_n=8/9`
- Quality_v2: `ic_mean=-0.003500`, `ic_std=0.007554`, `% positive segments=44.44%`, `valid_n=8/9`

Stage 2 decision:
1. Keep: `value_v2`
2. Keep: `momentum_v2`
3. Rework/hold: `quality_v2`

Core-pair strict+cache rerun (`v2026_02_16c_vm`):
- Value_v2: `ic_mean=0.053457`, `ic_std=0.021938`, `% positive segments=100.00%`, `valid_n=8/9`
- Momentum_v2: `ic_mean=0.014055`, `ic_std=0.026392`, `% positive segments=75.00%`, `valid_n=8/9`
- Output segments completed: `18/18`
- Stage2 cache files generated: `395`

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
- Stage2 signal cache layer:
  - BacktestEngine cache read/write via config flags
  - CLI support: `--use-cache --cache-dir --refresh-cache`
  - Verified on workstation in strict segmented rerun

## 7) Next Steps
1. Keep locked combo (`linear`, `value=0.90`, `momentum=0.10`) as current primary candidate
2. Compare combo walk-forward against single-factor baselines under identical constraints
3. Start paper-trading candidate phase (4-8 weeks, frozen research config)
4. Define live kill-switch thresholds and capital ramp plan

## 8) Daily Pipeline Runtime Notes (2026-02-18)
- Daily pipeline remains: `pull -> run -> sync` via `scripts/daily_update_pipeline.sh`
- Run mode default is live snapshot (`RUN_MODE=live_snapshot`) and updates:
  - `strategies/combo_v2/results/test_signals_latest.csv`
- Signal date interpretation:
  - `date=T` means data up to `T`, for next trading day `T+1`
- Recent ops issue observed:
  - Some local environments fail DNS resolution to FMP host.
  - Mitigation added: `FMP_RESOLVE_IPS` for direct resolve fallback in incremental dividend-adjusted pull.
