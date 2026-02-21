# Documentation Index

Last updated: 2026-02-21

## Core Documents
- `README.md`: project overview and public-facing summary
- `RUNBOOK.md`: practical command guide
- `STATUS.md`: current progress and roadmap snapshot
- `WEBSITE_HANDOFF.md`: website migration handoff (current state, fixes, next tasks, run/deploy notes)
- `COMBO_WEIGHT_EXPERIMENTS.md`: combo weight research log and selection record
- `POST_WF_PRODUCTION_CHECKLIST.md`: post walk-forward production validation gates (stress + risk + pass/fail)
- `SINGLE_FACTOR_BASELINE.md`: single-factor validation checklist
- `FACTOR_NOTES.md`: factor implementation notes
- `FACTOR_EVAL_TEMPLATE.md`: standardized factor evaluation template

## Additional References
- `CODEX_SESSION_GUIDE.md`: single-file Codex handoff guide (recommended first read)
- `docs/production_research/README.md`: production governance docs index
- `docs/production_research/GATE_SPEC.md`: formal hard-gate specification
- `docs/production_research/OPS_PLAYBOOK.md`: production run operations playbook
- `docs/production_research/WORKSTATION_PRIMARY_MODE.md`: workstation-primary execution policy
- `docs/production_research/SESSION_BOOTSTRAP.md`: strict read order for new Codex sessions
- `docs/production_research/AUDIT_ARTIFACTS.md`: mandatory audit artifact definitions
- `docs/production_research/CURRENT_GATE_STATUS_2026-02-20.md`: current production gate state snapshot and rerun checklist
- `docs/production_research/AUDIT_SNAPSHOT_2026-02-20.md`: current path-level audit snapshot
- `docs/production_research/TERMINOLOGY_POLICY.md`: canonical production naming policy
- `docs/production_research/RENAMING_AUDIT_2026-02-21.md`: full renaming audit trail
- `docs/public_factor_references/FACTOR_PUBLIC_FORMULAS_AND_EXECUTION_CONSTRAINTS_EN.md`: public factor formulas + execution constraints + V4 gap audit (English)
- `docs/public_factor_references/FACTOR_PUBLIC_FORMULAS_AND_EXECUTION_CONSTRAINTS_CN.md`: 公开因子公式 + 执行约束 + V4 缺陷审查（中文）
- `iterm_commands.txt`: convenience command snippets
- `scripts/daily_pull_incremental.sh`: incremental pull entry (daily)
- `scripts/daily_run_combo_current.sh`: daily combo run entry (live snapshot by default)
- `scripts/daily_sync_web.sh`: daily minimal web sync entry
- `scripts/daily_update_pipeline.sh`: orchestrator (`pull -> run -> sync`)
- `scripts/compare_v1_v2.py`: three-layer comparison helper (`v1` vs overwritten `v2.1`)
- `scripts/derive_combo_weights.py`: derives robust combo weights from segmented outputs
- `scripts/run_stage2_strict_top3_parallel.sh`: strict Stage2 segmented runner with cache support
- `scripts/live_trading_eval.py`: daily live-trading score vs realized-return evaluation (IC/Top-Bottom/win-rate/coverage/deciles)
- `scripts/generate_daily_live_report.py`: generate bilingual (EN/ZH) daily readable PDF report for a run_id
- `live_trading/reports/README.md`: report path convention and generation command
- `strategies/`: strategy-level docs and configs
- `configs/`: protocol and strategy configuration files
