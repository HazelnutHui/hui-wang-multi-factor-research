# Factor Pipeline Freeze (2026-02-25)

Purpose:
- lock an unambiguous, compute-efficient, institution-style pipeline;
- remove stage naming ambiguity before any new large run;
- define what must run for all candidates vs shortlisted candidates only.

## Stage Terminology (Locked)

1. `S0` Factor Factory Pre-Screen
- large-scale candidate ranking under one fixed execution profile.

2. Single-factor validation stack:
- `SF-L1`: segmented strict robustness check (production-style constraints, mandatory).
- `SF-L2`: fixed train/test (single factor, mandatory).
- `SF-L3`: walk-forward (single factor; shortlist only).
- `SF-DIAG`: segmented diagnostic check (optional, non-gating).

3. Combo validation stack:
- `Layer1`: segmented combo validation.
- `Layer2`: fixed train/test combo validation.
- `Layer3`: walk-forward combo validation.

## Execution Profile Policy

Global screening baseline (must keep fixed for comparability):
- `REBALANCE_FREQ=5`
- `HOLDING_PERIOD=3`
- `REBALANCE_MODE=None`
- `EXECUTION_USE_TRADING_DAYS=True`

Fast-screen compute rule:
- first-round queue must avoid heavy residual momentum variants;
- `MOMENTUM_USE_RESIDUAL=False` in round-1 policy files.

## Required Workflow (Locked)

1. Round A: large-scale pre-screen (`S0`)
- target: `>=100` candidates
- output: leaderboard + ranked shortlist
- keep top `20-30`.

2. Round B: holding-period robustness (shortlist only)
- run `HOLDING_PERIOD=1/3/5` in parallel
- keep candidates stable across horizons.

3. Round C: single-factor formal validation
- run `SF-L1` + `SF-L2` as mandatory path
- run `SF-DIAG` only when diagnostics/parameter triage is needed
- run `SF-L3` only for top `<=5`.

4. Round D: combo validation
- combo `Layer1 -> Layer2 -> Layer3`.

5. Round E: production gates
- stress/risk/statistical gates + audit completeness.

## Single-Factor Admission Policy (Locked, v1.0)

1. `SF-L2` rule:
- `test_ic <= 0` means not eligible for main combo;
- `train_ic <= 0` and `test_ic <= 0` means direct fail;
- `train_ic <= 0` and `test_ic > 0` can stay only as low-priority candidate.

2. `SF-L3` rule:
- positive `test_ic` ratio across windows must be `>= 60%`;
- no `3` consecutive negative windows.

3. Cost rule:
- out-of-sample metric under current cost model must stay positive.

4. Grade mapping:
- `A`: `test_ic >= 0.006` and all gates pass;
- `B`: `0 < test_ic < 0.006` and all gates pass;
- `C`: `test_ic <= 0` or WF/cost gate fail.

Main combo input is restricted to grades `A` and `B`.

## Combo Construction Policy (Locked, v1.0)

1. Build order:
- intra-group sub-combo first, inter-group combo second.

2. Exposure control:
- initial single-factor max weight cap: `<= 15%`;
- if recent sample `|corr| > 0.7`, do not keep both at full weight.

3. Retention rule:
- a factor remains in combo only if it adds out-of-sample quality after cost.

## Regime Adaptation Policy (Locked, v1.0)

1. Long-history validation is the admission baseline.
2. Recent `2-3` year window can adjust weights only.
3. Relative weight tilt cap vs baseline: `+/-30%`.
4. Any tilt change requires a new fixed train/test and walk-forward record.

## Compute Allocation Rule

- heavy models are moved backward in the pipeline;
- no full-universe `1/3/5` or walk-forward in round A;
- no combo run before single-factor shortlist is frozen.
