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

## Compute Allocation Rule

- heavy models are moved backward in the pipeline;
- no full-universe `1/3/5` or walk-forward in round A;
- no combo run before single-factor shortlist is frozen.
