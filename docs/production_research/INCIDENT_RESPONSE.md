# Incident Response Standard

Last updated: 2026-02-21

This document defines incident severity, response timelines, and required audit outputs for production research operations.

## 1) Incident Levels

- `SEV-1`: incorrect promotion/live decision risk; active run integrity compromised.
- `SEV-2`: official run failure, reproducibility break, or audit artifact loss.
- `SEV-3`: non-blocking operational defect with workaround.

## 2) Target Timelines

| level | acknowledge | contain | initial report | closure report |
|---|---|---|---|---|
| SEV-1 | 15 minutes | 1 hour | 4 hours | 48 hours |
| SEV-2 | 1 hour | 4 hours | 1 business day | 3 business days |
| SEV-3 | 1 business day | planned | 3 business days | next sprint |

## 3) Immediate Actions

1. Preserve evidence: logs, manifests, report json/md, shell history snippets.
2. Freeze mutation: stop destructive cleanup and run overwrites.
3. Classify severity and owner on-call.
4. Open incident record (template below).

## 4) Incident Record Template

```md
Incident ID: INC-YYYYMMDD-XX
Level: SEV-1/2/3
Detected at:
Owner:
Status: open/contained/monitoring/closed

Impact:
- affected run_dir(s):
- affected decision_tag(s):
- data/model integrity impact:

Root cause hypothesis:

Containment actions:

Recovery actions:

Preventive controls:

Links:
- run.log
- context.json
- production_gates_report.json
- related change ticket
```

## 5) Typical Incident Classes

- Freeze mismatch at official run start.
- Mixed lineage due to stale concurrent processes.
- Data freshness/schema failure before gate execution.
- Missing or corrupted report artifacts.

## 6) Closure Requirements

1. Root cause confirmed with evidence.
2. Preventive action merged and documented.
3. `RISK_REGISTER.md` updated if risk profile changed.
4. Stage log notes added in `STAGE_AUDIT_LOG.md`.
