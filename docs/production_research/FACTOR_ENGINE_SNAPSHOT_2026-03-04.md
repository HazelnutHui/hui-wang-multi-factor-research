# Factor Engine Snapshot (Logic100 Remediation)

Date: 2026-03-04

## Purpose
Freeze a reproducible engine snapshot for the current Logic100 remediation cycle, so later engine updates do not break traceability.

## Snapshot File
- `backups/factor_engine/factor_engine_2026-03-04_logic100_remediation_snapshot.py`

## Integrity
- source file: `backtest/factor_engine.py`
- source SHA256: `edfc569f92a3c72d6548dd0a3f73fb7da58de81d634aaaf86c1cf40fbf4f417e`
- git short commit at snapshot time: `23633db`

## Scope Boundary
This snapshot is aligned to the current governance/logic docs:
- `BATCHA100_LOGIC100_FORMAL_V1_2026-02-28.csv`
- `BATCHA100_LOGIC100_IMPLEMENTATION_MAP_2026-02-28.csv`
- `BATCHA100_LOGIC100_BLUEPRINT_2026-02-28.md`
- `STATUS.md`

Implementation coverage check at snapshot time:
- formal logic factors: 100
- missing in `FACTOR_SPECS`: 0
- note: runtime supports additional non-formal/legacy factors; they are out of this snapshot scope.

## Usage Rule
- For all rerun/result interpretation tied to this cycle, use this snapshot as the reference engine.
- If engine logic changes later, create a new snapshot file + new dated note, do not overwrite this one.
