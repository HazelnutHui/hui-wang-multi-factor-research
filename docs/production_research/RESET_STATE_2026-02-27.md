# Reset State (2026-02-27)

As-of: 2026-02-27

Historical note (2026-02-28):
- this file records reset-day snapshot only;
- current runtime state is tracked in `STATUS.md` and `FACTOR_BATCH_MASTER_TABLE.*`.

This project has been reset for formal factor research restart.

## Authoritative Reset

- All prior single-factor result sets are retired and deleted from active use.
- No pre-existing formal factor result is considered valid for current decision-making.
- The first official post-reset batch is:
  - `batchA100_logic100_formal_v1`
  - `100` distinct logic candidates
  - one candidate per logic (no family parameter duplication policy)

## Execution Boundary

- Reset-day status snapshot: `ready_for_review` (not started on 2026-02-27).
- Current live status is maintained in `STATUS.md` and `FACTOR_BATCH_MASTER_TABLE.*`.
- Any run launch still requires explicit manual approval.
- Master table SSOT:
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv`
  - `docs/production_research/FACTOR_BATCH_MASTER_TABLE.md`
