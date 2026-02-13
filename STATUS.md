# V4 Project Status (Public English Edition)

Last updated: 2026-02-13

## 1) Current Position
- Project focus: daily-frequency factor research and scoring
- Stage policy:
  - Stage 1 = baseline screening (winsor + rank)
  - Stage 2 = institutional robustness (industry + size/beta neutralization + zscore)
- Current runtime status: no active jobs

## 2) Factor Progress Snapshot
- Completed (segmented + train/test):
  - Value
  - Quality
  - Low-vol
- In queue:
  - Momentum
  - Reversal
  - PEAD

## 3) High-Level Findings
- Value is currently the strongest and most stable tested factor.
- Quality is weak in out-of-sample testing.
- Low-vol is mixed and regime-sensitive.

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
1. Run Momentum/Reversal/PEAD under the same validation protocol
2. Select 2-3 robust factors for multi-factor combination
3. Run combination-level robustness checks (cost, turnover, exposures, redundancy)
4. Execute walk-forward for deployment readiness
