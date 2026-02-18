# Live Trading Reports

Daily readable reports are stored under:

- `daily/en/<run_id>/daily_report_en.pdf`
- `daily/zh/<run_id>/daily_report_zh.pdf`

`run_id` follows: `trade_YYYY-MM-DD_from_signal_YYYY-MM-DD`.

Generation command:

```bash
python scripts/generate_daily_live_report.py --run-id trade_2026-02-18_from_signal_2026-02-17
```
