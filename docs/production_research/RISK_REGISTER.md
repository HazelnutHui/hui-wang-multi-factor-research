# Production Research Risk Register

Last updated: 2026-02-21

This register tracks key risks in the V4 production research workflow.
All entries are append-only except `status`, `last_reviewed_at`, and mitigation progress fields.

## Severity Scale

- `Critical`: immediate stop for promotion/live transition
- `High`: blocks official promotion decision until mitigated
- `Medium`: accepted temporarily with bounded exposure and deadline
- `Low`: monitor-only

## Probability Scale

- `H`: likely within current quarter
- `M`: possible within current quarter
- `L`: unlikely within current quarter

## Register

| risk_id | domain | description | severity | probability | owner | detection_signal | mitigation_plan | contingency_plan | status | opened_at | target_close_at | last_reviewed_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RISK-001 | Data Quality | PIT lag break, stale market cap path, or schema drift causes invalid factor inputs. | Critical | M | hui | `data_quality_gate` fail, guardrail errors, row count collapse | Enforce pre-run data gate + pinned upstream paths + schema contract checks in CI | Freeze current promotion, regenerate canonical inputs, rerun full gates with new decision tag | Open | 2026-02-21 | 2026-03-07 | 2026-02-21 |
| RISK-002 | Reproducibility | Freeze mismatch (`config_hash`/`git_commit`) between run and declared decision artifact. | High | M | hui | freeze mismatch in wrapper/preflight logs | Mandatory freeze file, commit-aligned freeze regeneration SOP | Mark run invalid, issue rerun with new tag and full audit trail | Open | 2026-02-21 | 2026-02-28 | 2026-02-21 |
| RISK-003 | Runtime Integrity | Concurrent stale WF processes contaminate timing/resources and may mix artifacts. | High | M | hui | `pgrep` finds > expected lineage, shard overlap anomalies | Active lineage check in preflight, explicit PID logging, kill stale lineage only | Preserve artifacts, relaunch clean official run directory | Open | 2026-02-21 | 2026-02-28 | 2026-02-21 |
| RISK-004 | Governance Drift | Use of skip flags in nominally official runs invalidates decision comparability. | High | L | hui | run context contains forbidden flags | Wrapper hard-block list + post-run audit checker | Downgrade run to non-official and require re-execution | Open | 2026-02-21 | 2026-03-07 | 2026-02-21 |
| RISK-005 | Access/Security | Over-shared credentials or permissive filesystem/network scope in remote workstation. | High | M | hui | unexpected key usage, unauthorized pull/push, audit gap | Least-privilege keys, rotation cadence, explicit access register | Revoke keys, rotate tokens, audit last known good commit/run | Open | 2026-02-21 | 2026-03-14 | 2026-02-21 |

## Review Cadence

1. Weekly review during active model iteration.
2. Mandatory review before promotion decision.
3. Immediate update after incident or control breach.

## Linked Controls

- `docs/production_research/MODEL_CHANGE_CONTROL.md`
- `docs/production_research/INCIDENT_RESPONSE.md`
- `docs/production_research/SECURITY_AND_ACCESS_CONTROL.md`
- `docs/production_research/DATA_QUALITY_POLICY.md`
