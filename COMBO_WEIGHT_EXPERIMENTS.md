# Combo Weight Experiments (value_v2 + momentum_v2)

Last updated: 2026-02-17 (linear selection + Layer2/Layer3 + stress confirmation completed)

## 1) Objective
- Find a robust `value_v2 / momentum_v2` weight split for `combo_v2` under the same Stage2 strict constraints.
- Goal is stability first, not single-run peak IC.

## 2) Fixed Conditions
- Factors: `value_v2`, `momentum_v2`
- Processing: Stage2 strict (zscore, winsor, missing policy, industry + size/beta neutralization, liquidity/price filters)
- Validation layer (for weight screening): segmented 2-year slices (9 segments)
- Data window: 2010-01-04 to 2026-01-28

## 3) Candidate Weights
- `0.90 / 0.10`
- `0.80 / 0.20`
- `0.70 / 0.30`
- `0.60 / 0.40`
- `0.50 / 0.50`

Important correction:
- A previous grid batch under `segment_results/combo_weight_grid_2026_02_17_p6` is invalid for weight selection.
- Root cause: `scripts/run_segmented_factors.py` had `combo_v2` hardcoded weights (`value=0.50,momentum=0.30,quality=0.20`), so edits in `strategies/combo_v2/config.py` were not applied.
- Fix: `combo_v2` now reads `COMBO_WEIGHTS` from `strategies/combo_v2/config.py`.
- Corrected rerun path: `segment_results/combo_weight_grid_2026_02_17_fix`.

## 4) Results Table
| run_id | w_value | w_momentum | ic_mean | ic_std | pos_ratio | valid_n | note |
|---|---:|---:|---:|---:|---:|---:|---|
| grid_fix_2026_02_17_w090_m010 | 0.90 | 0.10 | 0.066149 | 0.047273 | 0.857143 | 7 | best linear candidate |
| grid_fix_2026_02_17_w080_m020 | 0.80 | 0.20 | 0.055354 | 0.045034 | 0.857143 | 7 | second |
| grid_fix_2026_02_17_w070_m030 | 0.70 | 0.30 | 0.045395 | 0.045466 | 0.857143 | 7 | third |
| formula_gated_2026_02_17 | 0.90 | 0.10 | 0.038463 | 0.070371 | 0.571429 | 7 | worse than best linear |
| formula_two_stage_2026_02_17 | 0.90 | 0.10 | 0.048188 | 0.081973 | 0.714286 | 7 | worse than best linear |

## 5) Selection Rule
1. Keep only candidates with acceptable `pos_ratio` (recommended >= 0.60).
2. Among survivors, prioritize higher `ic_mean`.
3. Use lower `ic_std` as tie-breaker.
4. Lock one weight, then run Layer2/Layer3 without further weight changes.

## 6) Decision Log
- 2026-02-17: Created template. Baseline combo segmented run exists; detailed weight grid pending.
- 2026-02-17: Filled baseline (`0.70/0.30`) from `combo_v2` segmented output.
- 2026-02-17: Identified weight-source bug in segmented runner; previous grid marked invalid.
- 2026-02-17: Patched segmented runner to read `COMBO_WEIGHTS` from config; corrected grid rerun completed.
- 2026-02-17: Linear-grid provisional winner = `0.90 / 0.10`.
- 2026-02-17: Baseline combo config updated to `value=0.90, momentum=0.10` for formula-comparison runs.
- 2026-02-17: Enabled formula-level testing in engine (`COMBO_FORMULA`): `value_momentum_gated`, `value_momentum_two_stage`.
- 2026-02-17: Nonlinear formula comparison completed; both formulas underperform best linear candidate.
- 2026-02-17: Final combo decision locked: `linear + weights(value=0.90, momentum=0.10)`.

## 7) Next Actions
1. Keep combo formula as `linear`.
2. Keep combo weights as `value=0.90`, `momentum=0.10`.
3. Move to cost/turnover stress and baseline-vs-combo comparison without changing locked formula/weights.

## 8) Formula Candidates (After Current Weight Grid)
Formula-level candidates were tested in the same Stage2 strict framework:

1. Core-linear (value-dominant):
- `score = 0.85 * z(value) + 0.15 * z(momentum)`

2. Gated value (momentum as amplifier/dampener):
- `score = z(value) * (1 + 0.25 * clip(z(momentum), -1, 1))`
- Interpretation:
  - value is primary driver
  - momentum only adjusts exposure within +/-25%
  - clip prevents momentum extremes from dominating

3. Two-stage filter:
- Step A: rank by value, keep top candidate slice
- Step B: use momentum as filter to remove weakest momentum names
- Final scoring remains value-dominant

Formula comparison outcome:
- `gated`: lower mean IC and lower positive-ratio than linear winner.
- `two_stage`: lower mean IC and materially higher IC std than linear winner.
- Decision: keep linear formula.

## 9) Layer2/Layer3 Confirmation (Locked Combo)
- Layer2 fixed train/test (`configs/strategies/combo_v2_inst.yaml`):
  - Train IC (overall): `0.080637`
  - Test IC (overall): `0.053038`
- Layer3 walk-forward (test years 2013-2025, `REBALANCE_MODE=None`):
  - `test_ic`: `mean=0.057578`, `std=0.033470`, `pos_ratio=1.0000`, `n=13`
  - `test_ic_overall`: `mean=0.050814`, `std=0.032703`, `pos_ratio=1.0000`, `n=13`
- Operational note:
  - For combo Layer3, `REBALANCE_MODE=None` is required in current setup to avoid one-date-per-year degeneration (`test_ic=N/A`).

## 10) Post-WF Stress Confirmation
- Run profile:
  - `COST_MULTIPLIER=1.5`
  - `MIN_MARKET_CAP=2e9`
  - `MIN_DOLLAR_VOLUME=5e6`
- Output path:
  - `walk_forward_results/combo_v2_postwf_stress_x1_5_p6/combo_v2/walk_forward_summary.csv`
- Aggregate result:
  - `test_ic`: `mean=0.053310`, `std=0.032486`, `pos_ratio=1.0000`, `n=13`
  - `test_ic_overall`: `mean=0.046618`, `std=0.032058`, `pos_ratio=1.0000`, `n=13`
- Verdict:
  - Locked combo remains positive and stable under stress; promotion to paper-trading candidate is justified.
