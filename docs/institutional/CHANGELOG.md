# Institutional Layer Changelog

## 2026-02-20

### Added
- governed manifest/freeze utilities:
  - `scripts/research_governance.py`
- unified governed dispatcher:
  - `scripts/run_research_workflow.py`
- freeze + manifest support for:
  - `scripts/run_with_config.py`
  - `scripts/run_segmented_factors.py`
  - `scripts/run_walk_forward.py`
- universe filter audit plumbing:
  - `backtest/universe_builder.py`
  - `backtest/backtest_engine.py`
  - runner-level audit csv outputs
- PIT/lag guardrails in all core runners (default enabled)
- institutional hard-gate runner:
  - `scripts/run_institutional_gates.py`
- risk diagnostics integrated into hard-gate pass/fail
- institutional docs folder:
  - `docs/institutional/README.md`
  - `docs/institutional/GATE_SPEC.md`
  - `docs/institutional/OPS_PLAYBOOK.md`

### Policy impact
- Core research now supports formal promotion gates and decision audit trail.
- Official runs should not use skip flags (`--skip-guardrails`, `--skip-risk-diagnostics`).
