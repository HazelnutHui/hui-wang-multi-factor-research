# Renaming Audit (2026-02-21)

Audit date: 2026-02-21
Scope: full terminology migration from legacy `institutional` naming to `production` naming.

## Objective

Align governance and promotion workflow naming to a single professional vocabulary and remove mixed terminology from source, docs, scripts, and tracked audit artifacts.

## Executed migration

1. Governance docs namespace
- `docs/institutional/` -> `docs/production_research/`

2. Gate runner
- `scripts/run_institutional_gates.py` -> `scripts/run_production_gates.py`
- Workflow key updated in `scripts/run_research_workflow.py`:
  - `institutional_gates` -> `production_gates`

3. Checklist doc
- `POST_WF_INSTITUTIONAL_CHECKLIST.md` -> `POST_WF_PRODUCTION_CHECKLIST.md`

4. Strategy profile naming
- `configs/strategies/combo_v2_inst.yaml` -> `configs/strategies/combo_v2_prod.yaml`
- `runs/freeze/combo_v2_inst.freeze.json` -> `runs/freeze/combo_v2_prod.freeze.json`
- In-file strategy id updated to `combo_v2_prod`

5. Gate result artifacts
- `gate_results/institutional_gates_<ts>/` -> `gate_results/production_gates_<ts>/`
- `institutional_gates_report.{json,md}` -> `production_gates_report.{json,md}`
- Internal artifact path strings and registry references rewritten consistently.

6. Text replacement pass
- Replaced terminology in docs/scripts/config comments:
  - `Institutional` -> `Production`
  - `institutional` -> `production`

## Verification procedure

1. Global legacy term scan:

```bash
rg -n "institutional|Institutional|docs/institutional|institutional_gates|combo_v2_inst|POST_WF_INSTITUTIONAL_CHECKLIST" \
  --glob '!.git/**' \
  --glob '!docs/production_research/TERMINOLOGY_POLICY.md' \
  --glob '!docs/production_research/RENAMING_AUDIT_2026-02-21.md' \
  --glob '!docs/production_research/CHANGELOG.md'
```

2. Positive consistency scan:

```bash
rg -n "production_research|run_production_gates|production_gates_|production_gates_report|combo_v2_prod|POST_WF_PRODUCTION_CHECKLIST" --glob '!.git/**'
```

## Verification result

- Legacy scan: no remaining legacy-term hits outside dedicated migration/policy/changelog audit docs.
- Positive scan: all governance entrypoints and artifact naming aligned to production terminology.

## Audit notes

- This migration is nomenclature-only; no strategy logic or model math changes were introduced by this audit item.
- Historical timestamps remain unchanged to preserve chronological traceability.
