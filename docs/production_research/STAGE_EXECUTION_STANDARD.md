# Stage Execution Standard (Production Research)

Last updated: 2026-02-21

## Objective

Define a strict, repeatable stage system so every research phase has:
- clear goal and entry criteria;
- explicit must-produce artifacts;
- pass/fail gate and rollback rules;
- audit-ready explanation for next Codex session handoff.

## Stage Model

1. `S0` Scope Freeze
- Input: research question, universe constraints, protocol version.
- Required artifacts:
  - decision note (`decision_tag`, owner, date)
  - freeze file (`runs/freeze/*.freeze.json`)
  - data contract declaration (required columns/key/date fields)
- Gate:
  - no run without freeze artifact for official path.

2. `S1` Baseline Validation
- Input: frozen config, baseline backtest/walk-forward spec.
- Required artifacts:
  - data quality report (`data_quality_report.json/.md`)
  - run manifest(s)
  - baseline summary metrics (IC/coverage/cost assumptions)
- Gate:
  - data quality pass + baseline metrics not violating hard rejection criteria.

3. `S2` Stress and Robustness
- Input: S1 candidate.
- Required artifacts:
  - segmented/walk-forward stress outputs
  - risk diagnostics outputs
- Gate:
  - stress pass + risk pass + no skip flags.

4. `S3` Production Gates (Promotion Candidate)
- Input: S2 survivor.
- Required artifacts:
  - `gate_results/production_gates_<ts>/production_gates_report.json`
  - `gate_results/production_gates_<ts>/production_gates_report.md`
  - `gate_results/gate_registry.csv` appended
- Gate:
  - `overall_pass == true` and registry row present.

5. `S4` Deployment Readiness
- Input: S3 pass.
- Required artifacts:
  - deployment notes and monitoring checkpoints
  - post-promotion watchlist and rollback trigger definitions
- Gate:
  - committee sign-off documented.

## Execution Environment Rule

- Heavy official runs (`S2`/`S3`) must run on workstation.
- Use:
  - `scripts/workstation_preflight.sh`
  - `scripts/workstation_official_run.sh`
- Performance profile for heavy gates:
  - `--threads 8`
  - `--cost-multipliers 1.5,2.0` (baseline 1.0 can be omitted for speed in rerun mode)
  - `--wf-shards 4` (walk-forward shard parallelism)
- Local machine is for code/docs edits and lightweight checks.

## Mandatory Explainability Pack per Stage

Each stage must include a short markdown packet in `docs/production_research/` or strategy folder with:
- what changed;
- why this change is necessary;
- expected impact and risk;
- concrete evidence files and paths;
- decision outcome and next action.

## Minimum Audit Pack per Stage

1. command record (`command.sh` or exact command line)
2. environment snapshot (host, commit, preflight)
3. raw run log
4. machine-readable result (`*.json`)
5. human summary (`*.md`)
6. registry/ledger update

## Failure Policy

- Failures are not deleted or overwritten.
- Rerun must use new `decision_tag` with root-cause note.
- Keep both failed and succeeding records for traceability.
