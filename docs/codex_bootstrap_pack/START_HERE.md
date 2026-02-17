# Codex Bootstrap Pack (Session Handoff)

Last updated: 2026-02-17

Purpose: provide the minimum high-signal docs so a new Codex session can sync project status quickly and start execution without re-reading the whole repo.

## Recommended Send Order (for a new session)
1. `docs/codex_bootstrap_pack/START_HERE.md`
2. `docs/codex_bootstrap_pack/STATUS.md`
3. `docs/codex_bootstrap_pack/README.md`
4. `docs/codex_bootstrap_pack/FACTOR_NOTES.md`
5. `docs/codex_bootstrap_pack/RUNBOOK.md`
6. `docs/codex_bootstrap_pack/PROJECT_SUMMARY.md`
7. `docs/codex_bootstrap_pack/REMOTE_WORKSTATION_USAGE.md`

Optional context (only if needed):
- `docs/codex_bootstrap_pack/FACTOR_PUBLIC_FORMULAS_AND_EXECUTION_CONSTRAINTS_EN.md`
- `docs/codex_bootstrap_pack/FACTOR_PUBLIC_FORMULAS_AND_EXECUTION_CONSTRAINTS_CN.md`
- `docs/codex_bootstrap_pack/SYSTEM_OVERVIEW_CN.md`
- `docs/codex_bootstrap_pack/DOCS_INDEX.md`

## Why These Files
- `STATUS.md`: source of truth for current phase, finished tasks, next actions.
- `README.md`: global system context and current research snapshot.
- `FACTOR_NOTES.md`: factor-level conclusions and pass/hold decisions.
- `RUNBOOK.md`: command conventions and operational workflow.
- `PROJECT_SUMMARY.md`: concise strategic summary for quick alignment.
- `REMOTE_WORKSTATION_USAGE.md`: connection and sync execution details.

## Maintenance Rule
Whenever major progress changes:
1. Update root docs first (`STATUS.md`, `README.md`, `FACTOR_NOTES.md`, `RUNBOOK.md`, `PROJECT_SUMMARY.md`).
2. Refresh this pack by copying updated root docs into `docs/codex_bootstrap_pack/`.
3. Keep this file's date current.
