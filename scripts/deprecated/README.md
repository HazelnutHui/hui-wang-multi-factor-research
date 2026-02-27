# Deprecated Scripts

Last updated: 2026-02-22

These scripts were moved from `scripts/` to `scripts/deprecated/` after script-surface review.

Reason:
- no in-repo references found outside `scripts/`;
- not part of the current primary operator surface (`ops_entry.sh`).

Moved list:
- `akshare_download_daily.py`
- `akshare_stock_list.py`
- `committee_checklist.py`
- `fmp_earnings_calendar.py`
- `fmp_earnings_surprises_bulk.py`
- `fmp_fill_missing_delisted.py`
- `fmp_historical_stock_list.py`
- `fmp_market_cap_history_curl.sh`
- `run_live_signal_snapshot.py`
- `run_market_cap_batches.py`
- `update_divadj_prices_incremental.py`

If one script is needed again, move it back to `scripts/` and add doc references.
