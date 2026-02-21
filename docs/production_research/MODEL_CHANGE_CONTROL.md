# Model Change Control Standard

Last updated: 2026-02-21

This standard defines how factor/model changes move from research edits to production decision artifacts.

## 1) Change Classes

- `Class A (Major)`: objective function, factor set, risk gates, data source/path change.
- `Class B (Moderate)`: hyperparameter/bucket/window changes with same data contract.
- `Class C (Minor)`: documentation, observability, non-behavioral refactor.

## 2) Mandatory Inputs Before Approval

1. Change proposal with rationale and expected impact.
2. Baseline comparison against prior approved freeze.
3. Reproducible command block (local/workstation) with exact config/freeze.
4. Audit artifacts:
   - run manifest
   - gate report json/md
   - stage audit log update
5. Risk impact statement referencing `RISK_REGISTER.md`.

## 3) Approval Matrix

| class | required reviewers | gate scope | promotion eligibility |
|---|---|---|---|
| Class A | owner + second reviewer | full production gates + statistical + risk diagnostics | yes, if pass |
| Class B | owner | full production gates (same thresholds) | yes, if pass |
| Class C | owner | no gate rerun required if behavior proven unchanged | no direct promotion effect |

## 4) Change Ticket Template

```md
Change ID: CHG-YYYYMMDD-XX
Class: A/B/C
Owner:
Date:
Scope:
- files/configs changed:
- expected behavior delta:

Evidence:
- baseline decision_tag:
- new decision_tag:
- freeze file:
- key command:

Results:
- overall_pass:
- critical metrics:
- risk updates:

Decision:
- approved/rejected/deferred
- approver:
- decision time:
```

## 5) Hard Rejection Conditions

1. Missing freeze consistency.
2. Missing gate report artifacts.
3. Any required hard gate is `False`.
4. Skip flags used in a run claimed as official.

## 6) Linkage and Recordkeeping

- Update `docs/production_research/STAGE_AUDIT_LOG.md` per stage decision.
- If incident-linked, also record in `docs/production_research/INCIDENT_RESPONSE.md`.
- If data contract changed, update `docs/production_research/DATA_QUALITY_POLICY.md`.
