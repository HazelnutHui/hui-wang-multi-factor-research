# Terminology Policy (Production Naming)

Last updated: 2026-02-21
Owner: Hui research workspace

## Purpose

Standardize governance terminology across code, docs, and audit artifacts to avoid ambiguous wording and reduce session handoff risk.

## Canonical terms

- Use `production` as the canonical adjective for governance-level workflows.
- Use `production_gates` for hard-gate workflow names, folders, and report filenames.
- Use `production_research` as the governance docs namespace.
- Use `combo_v2_prod` for production-grade combo strategy profile naming.

## Deprecated terms

The following are deprecated and should not be introduced in new commits:

- `institutional`
- `institutional_gates`
- `docs/institutional`
- `combo_v2_inst`

## Naming rules

- Script name pattern: `run_<workflow>.py`, e.g. `run_production_gates.py`.
- Gate result path pattern: `gate_results/production_gates_<timestamp>/`.
- Gate report file pattern:
  - `production_gates_report.json`
  - `production_gates_report.md`
- Strategy profile pattern for production freeze/runs:
  - `configs/strategies/combo_v2_prod.yaml`
  - `runs/freeze/combo_v2_prod.freeze.json`

## Compliance check

Run:

```bash
rg -n "institutional|Institutional|docs/institutional|institutional_gates|combo_v2_inst|POST_WF_INSTITUTIONAL_CHECKLIST" \
  --glob '!.git/**' \
  --glob '!docs/production_research/TERMINOLOGY_POLICY.md' \
  --glob '!docs/production_research/RENAMING_AUDIT_2026-02-21.md' \
  --glob '!docs/production_research/CHANGELOG.md'
```

Expected result:

- No hits in active source/docs paths.
- Any legacy hit outside excluded audit-policy files must be explicitly explained in audit notes.

## Change control

- Any deviation from this policy requires a changelog entry in `docs/production_research/CHANGELOG.md` and an explicit migration note.
