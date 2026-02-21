# CODEX Session Guide

Last updated: 2026-02-21

This is the single handoff file for new Codex sessions in this repo.

## 1) Session Goal
- Primary track: production-grade research + gate workflow for `combo_v2`, in workstation-primary mode.
- Deliverables:
  - governed run manifests + freeze consistency
  - universe filter audit outputs
  - production gate reports (`cost + WF stress + risk + statistical`)
  - append-only gate registry update
  - docs sync + git push + workstation pull

## 2) Mandatory Read Order
1. `README.md`
2. `RUNBOOK.md`
3. `STATUS.md`
4. `DOCS_INDEX.md`
5. `docs/production_research/README.md`
6. `docs/production_research/GATE_SPEC.md`
7. `docs/production_research/OPS_PLAYBOOK.md`
8. `docs/production_research/WORKSTATION_PRIMARY_MODE.md`
9. `docs/production_research/SESSION_BOOTSTRAP.md`
10. `docs/production_research/AUDIT_ARTIFACTS.md`
11. `docs/production_research/TERMINOLOGY_POLICY.md`
12. `docs/production_research/RENAMING_AUDIT_2026-02-21.md`
13. `WEBSITE_HANDOFF.md`
14. `live_trading/reports/README.md`

If the task is specifically about daily validation quality, also read:
1. `live_trading/accuracy/metrics_panel.csv`
2. latest run folder: `live_trading/accuracy/<run_id>/`

## 3) Data Semantics (Must Keep Consistent)
- `signal_date = T` (score computed using data up to T close)
- `trade_date = T+1` (next trading day used for realized return)
- Run ID format:
  - `trade_YYYY-MM-DD_from_signal_YYYY-MM-DD`

## 3b) Production Run Integrity (Must Keep Consistent)
- Official heavy runs default to workstation (8C/64G).
- Official runs must use freeze and must not use skip flags:
  - do not use `--skip-guardrails`
  - do not use `--skip-risk-diagnostics`
  - do not use `--skip-statistical-gates`
- Every official run must generate:
  - run manifest(s)
  - universe audit csv
  - gate report json/md
  - gate registry row

## 4) Daily Execution Commands
- Daily eval (score + realized return):
```bash
python scripts/live_trading_eval.py \
  --signals live_trading/scores/<run_id>/scores_full_ranked.csv \
  --signal-date <T> \
  --trade-date <T+1> \
  --realized-file live_trading/accuracy/<run_id>/accuracy_check_<T+1>_symbol_returns.csv
```

- Daily bilingual report generation:
```bash
python scripts/generate_daily_live_report.py --run-id <run_id>
```

## 5) Expected Output Paths
- Scores:
  - `live_trading/scores/<run_id>/signals_T.csv`
- Accuracy:
  - `live_trading/accuracy/<run_id>/realized_Tplus1.csv`
  - `live_trading/accuracy/<run_id>/match_T_Tplus1.csv`
  - `live_trading/accuracy/<run_id>/metrics_T_Tplus1.csv`
  - `live_trading/accuracy/<run_id>/deciles_T_Tplus1.csv`
  - `live_trading/accuracy/metrics_panel.csv`
- Readable reports:
  - `live_trading/reports/daily/en/<run_id>/daily_report_en.pdf`
  - `live_trading/reports/daily/zh/<run_id>/daily_report_zh.pdf`

## 6) Scope Guardrails
- Do not change factor formulas or backtest protocol unless explicitly requested.
- Do not revert unrelated local changes.
- Keep daily reporting path and naming stable.
- Keep docs and produced artifacts aligned before push.

## 7) Git Rule For This Project
- Preferred flow:
  1. local `git commit`
  2. local `git push`
  3. workstation `git pull --ff-only`

## 7b) Workstation Rule For Heavy Runs
- Use workstation for:
  - `run_production_gates.py`
  - heavy `run_walk_forward.py`
  - large segmented stress runs
- Use local machine for:
  - code edits
  - docs updates
  - lightweight smoke checks

## 8) Minimal Prompt For New Codex
Use this prompt in a new session:

```text
Please start from docs/production_research/SESSION_BOOTSTRAP.md and continue production gate workflow in workstation-primary mode.
```

## 9) Current Run Pointers
- Latest completed validation run:
  - `trade_2026-02-19_from_signal_2026-02-18`
- Current next-day signal snapshot:
  - `trade_2026-02-20_from_signal_2026-02-19`
