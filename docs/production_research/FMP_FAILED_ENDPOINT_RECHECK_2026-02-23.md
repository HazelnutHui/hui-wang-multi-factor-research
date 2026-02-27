# FMP Failed Endpoint Recheck (Batch1/Batch2)

Date: 2026-02-23

Scope:
- recheck all failed endpoints from:
  - `audit/fmp_probe/fmp_interface_probe_2026-02-23_010856.json` (batch1)
  - `audit/fmp_probe/fmp_interface_probe_2026-02-23_011350.json` (batch2)
- use doc-aligned stable endpoint names as replacement candidates.

## Result summary

- replacement targets tested: 23
- HTTP success: 23
- HTTP fail: 0
- report: `audit/fmp_probe_failed_recheck/fmp_interface_probe_2026-02-23_012441.json`

## Main conclusion

Most earlier failures were naming/path mismatches against current stable docs, not true data-source unavailability.

## Mapping artifacts

- old-to-new mapping:
  - `audit/fmp_probe_failed_recheck/failed_endpoint_replacement_map_2026-02-23.csv`
- replacement probe results:
  - `audit/fmp_probe_failed_recheck/failed_recheck_probe_results_2026-02-23.csv`

## Exceptions / nuance

1. `institutional-holder` and `mutual-fund-holder`:
- no exact one-to-one endpoint name in current stable docs;
- replaced by related datasets:
  - `institutional-ownership/latest`
  - `institutional-ownership/symbol-positions-summary`
  - `funds/disclosure-holders-latest`

2. `historical-chart/1day`:
- current stable docs emphasize `historical-price-eod/*` for EOD daily;
- practical replacement is `historical-price-eod/full|light|non-split-adjusted`.

3. `api/v3` legacy route:
- remains blocked by account mode (403 legacy notice), unchanged.
