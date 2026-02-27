# FMP API Callability Summary

Date: 2026-02-23

Primary source:
- `audit/fmp_probe_coverage_v1/fmp_interface_probe_latest.json`
- target set: `configs/research/fmp_probe_targets_coverage_v1.json`

## Coverage result

- tested endpoints: 156
- HTTP success: 156
- HTTP fail: 0
- base URL: `https://financialmodelingprep.com/stable`

## Category coverage

- search: 7
- directory: 11
- company: 15
- quote: 12
- statements: 25
- charts: 10
- economics: 4
- earnings_dividends: 9
- transcript: 3
- news: 8
- filings: 11
- analyst: 8
- market_perf: 11
- tech_ind: 4
- bulk: 18

## Important parser note

Bulk endpoints are mostly CSV-mode payloads and must use CSV parser mode:
- `profile-bulk`
- `rating-bulk`
- `dcf-bulk`
- `scores-bulk`
- `price-target-summary-bulk`
- `etf-holder-bulk`
- `upgrades-downgrades-consensus-bulk`
- `key-metrics-ttm-bulk`
- `ratios-ttm-bulk`
- `peers-bulk`
- `earnings-surprises-bulk`
- `income-statement-bulk`
- `income-statement-growth-bulk`
- `balance-sheet-statement-bulk`
- `balance-sheet-statement-growth-bulk`
- `cash-flow-statement-bulk`
- `cash-flow-statement-growth-bulk`
- `eod-bulk`

## Machine-readable matrix

- `audit/fmp_probe_coverage_v1/fmp_api_callable_matrix_2026-02-23.csv`

Each row contains:
- `category, endpoint, http_status, ok_http, payload_mode, payload_type, n_rows, date_min, date_max, error_message`
