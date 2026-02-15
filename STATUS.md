# V4 Project Status (Public English Edition)

Last updated: 2026-02-15

## 1) Current Position
- Project focus: daily-frequency factor research and scoring
- Stage policy:
  - Stage 1 = baseline screening (winsor + rank)
  - Stage 2 = institutional robustness (industry + size/beta neutralization + zscore)
- Current runtime status: Stage 1 rerun active (`reversal`/`low_vol`/`quality`/`pead` on 8-core parallel segments)

## 2) Factor Progress Snapshot (New Protocol Rerun)
- Stage 1 completed:
  - Value
  - Momentum (6-1)
- Stage 1 running:
  - Reversal
  - Low-vol
  - Quality
  - PEAD
- Stage 2 status:
  - Not started for this rerun cycle
- Train/Test status:
  - Not started for this rerun cycle

## 3) Stage 1 Metrics (Currently Completed)
- Value: `ic_mean=0.054063`, `ic_std=0.021962`, `% positive segments=88.89%`
- Momentum: `ic_mean=0.012868`, `ic_std=0.022771`, `% positive segments=66.67%`
- Remaining factors are being rerun after formula updates and cleanup.

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
1. Finish Stage 1 rerun for `reversal`, `low_vol`, `quality`, `pead`
2. Refresh Stage 1 ranking under unified latest formula logic
3. Run Stage 2 rerun for prioritized factors
4. Run refreshed fixed train/test under updated protocol assumptions
