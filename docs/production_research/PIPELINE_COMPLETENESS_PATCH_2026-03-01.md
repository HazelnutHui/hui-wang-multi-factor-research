# Pipeline Completeness Patch (2026-03-01)

As-of: 2026-03-01
Status: governance patch draft (documentation only; no runtime impact)

## Purpose
Patch the current factor workflow with missing hard rules while preserving the existing official run (`batchA100_logic100_formal_v1`) unchanged.

## Non-Impact Statement
- This patch does not change running workstation processes.
- This patch does not modify current batch policy/config/code.
- This patch only defines additional governance rules for subsequent batches.

## Patch-1: S0 -> Shortlist Hard Entry/Exit Rules

### S0 Entry (must all pass)
1. Candidate logic has explicit mechanism statement and formula.
2. Candidate has lag-safe data dependency map.
3. Candidate is not a pure parameter variant of an existing logic.

### S0 Exit (for shortlist eligibility)
Use fixed profile (`5/3/None`) outputs only:
1. `n_segments >= 8` valid segments.
2. `ic_mean > 0`.
3. `ic_pos_ratio >= 0.55`.
4. Not in top 80% pairwise correlation cluster among shortlisted candidates.

## Patch-2: Shortlist -> SF Stack Promotion Rules

### SF-L1 mandatory pass
1. Segmented strict run complete.
2. No long negative streak: max consecutive negative-IC segments <= 3.
3. Coverage floor respected (same data domain standard as batch peers).

### SF-L2 mandatory pass
1. Test IC remains positive.
2. Degradation guard: `test_ic / train_ic >= 0.5` when `train_ic > 0`.

### SF-L3 (top <= 5 only)
1. Walk-forward test mean IC positive.
2. Walk-forward positive-window ratio >= 0.6.

## Patch-3: Multiple Testing Control (new mandatory audit item)

For each S0 batch leaderboard:
1. Compute p-values for IC means across candidates.
2. Apply FDR control (Benjamini-Hochberg).
3. Store `q_value` in leaderboard exports.
4. Default shortlist requires `q_value <= 0.20` OR explicit committee override note.

Artifacts:
- `audit/factor_factory/<run>/leaderboard_fdr.csv`
- `audit/factor_factory/<run>/fdr_summary.md`

## Patch-4: Regime Gate as Official Combo Pre-Check

Before combo Layer1:
1. Build regime labels (volatility/liquidity/trend/event-density).
2. Report factor IC by regime bucket.
3. Reject factors that are unstable in all major buckets.

Regime package (minimum):
- volatility state: low/medium/high
- liquidity state: normal/stress
- trend state: risk-on/risk-off
- event state: earnings-season / non-earnings-season

Artifact:
- `audit/regime_gate/<run>/regime_factor_diagnostics.csv`
- `audit/regime_gate/<run>/regime_factor_diagnostics.md`

## Implementation Priority
1. Governance docs alignment (this patch + index + status) [now]
2. Add FDR post-process script to S0 outputs.
3. Add regime diagnostic script before combo Layer1.
4. Promote rules from patch to formal freeze doc when validated.

## Adoption Rule
This patch is effective for next approved batch after current running batch completes.
