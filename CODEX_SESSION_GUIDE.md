# CODEX Session Guide

Last updated: 2026-02-18

This is the single handoff file for new Codex sessions in this repo.

## 1) Session Goal
- Primary track: daily live-trading validation for `combo_v2` using T->T+1 protocol.
- Deliverables each day:
  - score archive
  - accuracy archive
  - bilingual readable PDF reports
  - docs sync + git push

## 2) Mandatory Read Order
1. `README.md`
2. `RUNBOOK.md`
3. `STATUS.md`
4. `DOCS_INDEX.md`
5. `WEBSITE_HANDOFF.md`
6. `live_trading/reports/README.md`

If the task is specifically about daily validation quality, also read:
1. `live_trading/accuracy/metrics_panel.csv`
2. latest run folder: `live_trading/accuracy/<run_id>/`

## 3) Data Semantics (Must Keep Consistent)
- `signal_date = T` (score computed using data up to T close)
- `trade_date = T+1` (next trading day used for realized return)
- Run ID format:
  - `trade_YYYY-MM-DD_from_signal_YYYY-MM-DD`

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

## 8) Minimal Prompt For New Codex
Use this prompt in a new session:

```text
Please start from CODEX_SESSION_GUIDE.md and continue today’s live_trading workflow only.
```
