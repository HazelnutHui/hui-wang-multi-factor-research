# Session Bootstrap (For New Codex)

Last updated: 2026-02-21

Use this exact read order for new sessions focused on production workflow.

## Mandatory read order

1. `CODEX_SESSION_GUIDE.md`
2. `RUNBOOK.md`
3. `STATUS.md`
4. `DOCS_INDEX.md`
5. `docs/production_research/README.md`
6. `docs/production_research/GATE_SPEC.md`
7. `docs/production_research/OPS_PLAYBOOK.md`
8. `docs/production_research/WORKSTATION_PRIMARY_MODE.md`
9. latest `gate_results/production_gates_*/production_gates_report.json`
10. `gate_results/gate_registry.csv`
11. `docs/production_research/TERMINOLOGY_POLICY.md`
12. `docs/production_research/RENAMING_AUDIT_2026-02-21.md`
13. `docs/production_research/STAGE_EXECUTION_STANDARD.md`
14. `docs/production_research/WORKSTATION_RUNNER_SPEC.md`
15. `docs/production_research/STAGE_AUDIT_LOG.md`
16. `docs/production_research/ARTIFACT_RETENTION_AND_CLEANUP.md`
17. `docs/production_research/DATA_QUALITY_POLICY.md`
18. `docs/production_research/RISK_REGISTER.md`
19. `docs/production_research/MODEL_CHANGE_CONTROL.md`
20. `docs/production_research/INCIDENT_RESPONSE.md`
21. `docs/production_research/SECURITY_AND_ACCESS_CONTROL.md`
22. `docs/production_research/GOVERNANCE_AUDIT_CHECKER.md`
23. `docs/production_research/GOVERNANCE_REMEDIATION_PLAN.md`
24. `docs/production_research/FACTOR_EXPERIMENT_REGISTRY.md`
25. `docs/production_research/CANDIDATE_QUEUE_POLICY.md`
26. `docs/production_research/NEXT_RUN_EXECUTION_STANDARD.md`
27. `docs/production_research/SESSION_HANDOFF_READINESS.md`
28. `docs/production_research/AUTO_RESEARCH_ORCHESTRATION.md`
29. `docs/production_research/AUTO_RESEARCH_SCHEDULER.md`
30. `docs/production_research/AUTO_RESEARCH_DEPLOYMENT.md`
31. `docs/production_research/LOW_NETWORK_MODE.md`
32. `docs/production_research/SYSTEM_CLOSURE_CHECK.md`

## Mandatory checks before editing/running

1. Confirm whether run is local or workstation official run.
2. Confirm freeze file path and whether it already exists.
3. Confirm no skip flags for official runs:
   - `--skip-guardrails`
   - `--skip-risk-diagnostics`
   - `--skip-statistical-gates`
4. Confirm output root and artifact retention path.
5. Confirm a passing data quality gate artifact exists (or run one before official gate execution).
6. After post-run finalization, confirm governance audit check artifacts are present for the run.

## Minimal new-session prompt

```text
Start with docs/production_research/SESSION_BOOTSTRAP.md and continue production gate workflow in workstation-primary mode.
```
