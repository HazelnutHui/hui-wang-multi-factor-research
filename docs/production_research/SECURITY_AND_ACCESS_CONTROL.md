# Security and Access Control Baseline

Last updated: 2026-02-21

This baseline defines minimum controls for local + workstation development in production research workflows.

## 1) Access Principles

1. Least privilege: only required repos, hosts, and keys.
2. Separation of concerns: execution account separate from personal admin paths where possible.
3. Traceability: every official run must map to owner + decision_tag + commit.

## 2) Credential Controls

- SSH keys:
  - dedicated key pair for workstation repo sync
  - passphrase required
  - annual rotation or immediate rotation after suspected exposure
- API tokens/secrets:
  - never committed into git
  - store in env files excluded by `.gitignore`
  - access scoped to minimum required permissions

## 3) Repository and Branch Hygiene

1. Official governance changes on tracked branch with signed commit policy if enabled.
2. Do not include unrelated local artifacts in governance commits.
3. Keep append-only audit docs immutable except designated update fields.

## 4) Workstation Controls

1. Use explicit workspace path and pinned virtual environment.
2. Preflight before official run:
   - clean lineage check
   - freeze availability
   - required data path checks
3. Keep run artifacts under:
   - `audit/workstation_runs/...`
   - `gate_results/production_gates_...`

## 5) Logging and Auditability

- Required:
  - run wrapper context (`context.json`)
  - command transcript (`run.log`)
  - gate outputs (`production_gates_report.json`, `.md`)
- Recommended:
  - periodic snapshot of key artifact hashes
  - access review notes (monthly)

## 6) Breach/Exposure Response

1. Revoke compromised key/token immediately.
2. Rotate credentials and document scope.
3. Open incident record in `INCIDENT_RESPONSE.md`.
4. Validate latest trusted commit and rerun official gate if integrity uncertain.
