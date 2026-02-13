# BRAIN Validation (External Sanity Check)

Purpose: store WorldQuant BRAIN factor formulas and results separately from V4 backtests.
BRAIN results are treated as *external sanity checks* (directional validation), not final system truth.

## Structure
- `brain/factors/`  : Factor formulas and notes (one file per factor)
- `brain/results/`  : BRAIN exports / screenshots / CSVs
- `brain/logs/`     : Summary log (`brain_factor_log.md`)

## Workflow
1. Add a factor formula under `brain/factors/`.
2. Test in BRAIN (document universe / delay / decay / neutralization / sample period).
3. Save exports to `brain/results/`.
4. Record summary in `brain/logs/brain_factor_log.md`.

## Notes
- Keep factor formulas aligned to V4 definitions where possible.
- Record any field/definition mismatch vs V4 in the log.
