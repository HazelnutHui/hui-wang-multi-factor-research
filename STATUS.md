# V4 Project Status (Public English Edition)

Last updated: 2026-02-15

## 1) Current Position
- Project focus: daily-frequency factor research and scoring
- Stage policy:
  - Stage 1 = baseline screening (winsor + rank)
  - Stage 2 = institutional robustness (industry + size/beta neutralization + zscore)
- Current runtime status: Stage 1 rerun complete (all six target factors)

## 2) Factor Progress Snapshot (New Protocol Rerun)
- Stage 1 completed:
  - Value
  - Quality
  - Low-vol
  - Momentum (6-1)
  - Reversal
  - PEAD
- Stage 2 status:
  - Not started for this rerun cycle
- Train/Test status:
  - Not started for this rerun cycle

## 3) Stage 1 Interim Metrics (Completed Factors)
- Value: `ic_mean=0.054063`, `ic_std=0.021962`, `% positive segments=88.89%`
- Momentum: `ic_mean=0.012868`, `ic_std=0.022771`, `% positive segments=66.67%`
- Reversal: `ic_mean=0.003564`, `ic_std=0.010793`, `% positive segments=44.44%`
- Quality: `ic_mean=0.000957`, `ic_std=0.008283`, `% positive segments=44.44%`
- Low-vol: `ic_mean=0.003209`, `ic_std=0.034677`, `% positive segments=44.44%`
- PEAD: `ic_mean=0.000766`, `ic_std=0.030426`, `% positive segments=55.56%`
- Stage 1 ranking by `ic_mean`: Value > Momentum > Reversal > Low-vol > Quality > PEAD.

## 4) Engineering Progress Completed
- Unified protocol + strategy override configuration system
- Stage 1/Stage 2 factor processing pipeline
- PIT fundamentals support (`available_date` as-of filtering)
- Delisting-aware data handling
- Market-cap-history support for universe constraints
- Forward-return IC as default research metric
- Report/diagnostics/checklist tooling for review workflow
- Test coverage for lag/no-lookahead/factor transformation behaviors

## 5) Next Steps
1. Run Stage 2 rerun for prioritized factors (`value`, `momentum`, then `reversal`)
2. Run refreshed fixed train/test with updated protocol assumptions
3. Decide 2-3 factor shortlist for combination after Stage 2
4. Run combination checks and then walk-forward
