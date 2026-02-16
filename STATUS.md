# V4 Project Status (Public English Edition)

Last updated: 2026-02-16

## 1) Current Position
- Project focus: daily-frequency factor research and scoring
- Stage policy:
  - Stage 1 = baseline screening (winsor + rank)
  - Stage 2 = institutional robustness (industry + size/beta neutralization + zscore)
- Current runtime status: Stage 1 rerun completed for six target factors; Stage 2 not started yet.

## 2) Factor Progress Snapshot (New Protocol Rerun)
- Stage 1 completed:
  - Value
  - Momentum (6-1)
  - Reversal
  - Low-vol
  - Quality
  - PEAD
- Stage 1 running:
  - None
- Stage 2 status:
  - Not started for this rerun cycle
- Train/Test status:
  - Not started for this rerun cycle

## 3) Stage 1 Metrics (Completed, 2-Year Segments)
- Value: `ic_mean=0.054227`, `ic_std=0.022106`, `% positive segments=88.89%`, `valid_n=8/9`
- Momentum: `ic_mean=0.012868`, `ic_std=0.022771`, `% positive segments=66.67%`, `valid_n=8/9`
- Reversal: `ic_mean=0.005325`, `ic_std=0.006380`, `% positive segments=100.00%`, `valid_n=9/9`
- Low-vol: `ic_mean=0.003209`, `ic_std=0.034677`, `% positive segments=44.44%`, `valid_n=8/9`
- Quality: `ic_mean=0.002387`, `ic_std=0.008456`, `% positive segments=55.56%`, `valid_n=8/9`
- PEAD: `ic_mean=0.000766`, `ic_std=0.030426`, `% positive segments=55.56%`, `valid_n=9/9`

Stage 1 ranking by `ic_mean`:
1. Value
2. Momentum
3. Reversal
4. Low-vol
5. Quality
6. PEAD

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
1. Start Stage 2 rerun for prioritized factors: `value`, `momentum`, `reversal`
2. Re-check cost sensitivity and robustness for `reversal` before promotion
3. Run refreshed fixed train/test under updated protocol assumptions
4. Proceed to combination candidate construction after Stage 2 results are finalized
