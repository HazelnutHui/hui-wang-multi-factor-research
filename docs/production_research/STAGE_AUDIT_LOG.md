# Stage Audit Log

Last updated: 2026-02-24

Purpose:
- append-only stage-level audit ledger;
- quick handoff view for new sessions and committee review.

## Ledger

| date | stage | decision_tag | owner | objective | command_ref | artifact_ref | result | next_action |
|---|---|---|---|---|---|---|---|---|
| 2026-02-21 | S0/S3 Governance Rename | committee_2026-02-21_naming_migration | hui | unify production naming and audit docs | `scripts/run_research_workflow.py --workflow production_gates --help` | `docs/production_research/RENAMING_AUDIT_2026-02-21.md` | pass | continue S2/S3 official workstation rerun under new naming |
| 2026-02-21 | S3 Production Gates | committee_2026-02-21_run1_rerun4 | hui | official workstation gate run with wf shard parallelism | `audit/workstation_runs/2026-02-21_053448_production_gates_committee_2026-02-21_run1_rerun4/command.sh` | `gate_results/production_gates_2026-02-21_053448/production_gates_report.json` | superseded | superseded by finalized fail row for same decision_tag |
| 2026-02-21 | S3 Production Gates | committee_2026-02-21_run1_rerun4 | hui | S3 production gates official rerun | `/Users/hui/quant_score/v4/audit/workstation_runs/2026-02-21_053448_production_gates_committee_2026-02-21_run1_rerun4/command.sh` | `/Users/hui/quant_score/v4/gate_results/production_gates_2026-02-21_053448/production_gates_report.json` | fail | review failed gate components and rerun |
| 2026-02-22 | S3 Production Gates | committee_2026-02-22_run5 | hui | official workstation gate rerun (run5) | `audit/workstation_runs/2026-02-22_223843_production_gates_committee_2026-02-22_run5/command.sh` | `gate_results/production_gates_2026-02-22_223844/production_gates_report.json` | pending_local_sync | referenced in docs snapshot, but corresponding artifacts are not currently synced in local workspace |
| 2026-02-22 | S0 Factor Factory | factor_factory_2026-02-22_batch1 | hui | local factor-factory batch candidate planning | `python3 scripts/run_factor_factory_batch.py --policy-json configs/research/factor_factory_policy.json --jobs 4 --max-candidates 20 --dry-run` | `audit/factor_factory/2026-02-22_174534_factor_factory_v1/factor_factory_batch_report.json` | dry_run_complete | rerun without `--dry-run` to generate ranked leaderboard |

## Update Rule

- New row required for every official stage decision.
- `decision_tag` must match gate registry decision tag when S3 is involved.
- Never delete rows; use new rows for corrections.
