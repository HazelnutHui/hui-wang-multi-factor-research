# FMP Endpoint Catalog (Probe Snapshot)

Snapshot date: 2026-02-23

Sources:
- `audit/fmp_probe/fmp_interface_probe_2026-02-23_010856.json` (stable batch1)
- `audit/fmp_probe/fmp_interface_probe_2026-02-23_011350.json` (stable batch2)
- `audit/fmp_probe_v3/fmp_interface_probe_2026-02-23_011554.json` (api/v3 comparison)
- `audit/fmp_probe_stability/*/fmp_interface_probe_latest.json` (AAPL/MSFT/NVDA stability recheck)
- `audit/fmp_probe_batch3_docs/fmp_interface_probe_2026-02-23_012205.json` (doc-aligned stable naming batch)

## 0) Failure recheck conclusion

Stability recheck on `AAPL`, `MSFT`, `NVDA` for stable batch2:
- each symbol: 12 success + 13 fail
- failed endpoint set is identical across all three symbols

Interpretation:
- failures are reproducible endpoint availability/path issues under current account mode;
- not a transient network outage and not symbol-specific missing data.

## 0.1) Doc-aligned recheck (critical correction)

Using endpoints exactly as listed in FMP stable docs (`configs/research/fmp_probe_targets_batch3_from_docs.json`):
- tested: 52
- HTTP success: 52
- HTTP fail: 0

Conclusion:
- a meaningful part of earlier 404 set came from endpoint naming mismatch (legacy/incorrect aliases), not true dataset unavailability.
- canonical source for endpoint naming should be the stable-doc-aligned target list.

## 1) High-confidence usable now (stable)

- `profile`
- `stock-list`
- `historical-price-eod/dividend-adjusted`
- `historical-market-capitalization`
- `ratios`
- `key-metrics`
- `income-statement`
- `balance-sheet-statement`
- `cash-flow-statement`
- `earnings-calendar`
- `quote`
- `quote-short`
- `historical-chart/1hour`
- `income-statement-growth`
- `balance-sheet-statement-growth`
- `cash-flow-statement-growth`
- `financial-growth`
- `enterprise-values`
- `analyst-estimates`
- `economic-calendar`
- `available-sectors`
- `available-industries`

## 2) Needs parser/semantic confirmation (stable)

These return success but need explicit contract before production ingestion:

- `earnings-surprises-bulk`: CSV text mode observed in prior probe run; parser mode must be fixed.
- `profile-bulk`: CSV text mode observed in prior probe run; parser mode must be fixed.
- `economic-calendar`: very large row count in one call; pagination/range semantics should be bounded by policy.
- `analyst-estimates`: includes forward-dated rows; ensure no look-ahead leakage in factor construction.

## 3) Currently unavailable or failing in stable probes

- `historical-price-eod` (404)
- `historical-chart/1day` (404)
- `owner_earnings` (404)
- `upgrades-downgrades-consensus` (404)
- `historical-rating` (404)
- `stock-news` (404)
- `insider-trading` (404)
- `insider-roaster-statistic` (404)
- `historical-share-float` (404)
- `institutional-holder` (404)
- `mutual-fund-holder` (404)
- `earnings-call-transcript` (404)
- `sec-filings` (404)
- `stock-screener` (404)

## 4) api/v3 comparison result (critical)

For the 25 endpoints in `configs/research/fmp_probe_targets_batch2.json`, `api/v3` returned 403 for all with message equivalent to:
- legacy endpoints are no longer supported for non-legacy subscriptions.

Interpretation:
- current research ingestion should prioritize `stable` routes;
- do not allocate pipeline time to `api/v3` legacy route recovery unless subscription/product scope changes.

## 5) Immediate ingestion boundary (recommended)

Allowed for next data expansion wave:
1. `income-statement-growth`, `balance-sheet-statement-growth`, `cash-flow-statement-growth`, `financial-growth`
2. `enterprise-values`
3. `analyst-estimates` (with strict anti-leakage checks)
4. `quote`/`quote-short`/`historical-chart/1hour` only for monitoring or intraday diagnostics, not for end-of-day factor gates unless policy updated.

Blocked pending confirmation:
1. any endpoint returning CSV-text payload without declared parser mode in pull script/doc
2. any endpoint with ambiguous date semantics
3. all `api/v3` legacy-return endpoints under current account mode
