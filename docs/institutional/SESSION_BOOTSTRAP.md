# Session Bootstrap (For New Codex)

Last updated: 2026-02-20

Use this exact read order for new sessions focused on institutional workflow.

## Mandatory read order

1. `CODEX_SESSION_GUIDE.md`
2. `RUNBOOK.md`
3. `STATUS.md`
4. `DOCS_INDEX.md`
5. `docs/institutional/README.md`
6. `docs/institutional/GATE_SPEC.md`
7. `docs/institutional/OPS_PLAYBOOK.md`
8. `docs/institutional/WORKSTATION_PRIMARY_MODE.md`
9. latest `gate_results/institutional_gates_*/institutional_gates_report.json`
10. `gate_results/gate_registry.csv`

## Mandatory checks before editing/running

1. Confirm whether run is local or workstation official run.
2. Confirm freeze file path and whether it already exists.
3. Confirm no skip flags for official runs:
   - `--skip-guardrails`
   - `--skip-risk-diagnostics`
   - `--skip-statistical-gates`
4. Confirm output root and artifact retention path.

## Minimal new-session prompt

```text
Start with docs/institutional/SESSION_BOOTSTRAP.md and continue institutional gate workflow in workstation-primary mode.
```
