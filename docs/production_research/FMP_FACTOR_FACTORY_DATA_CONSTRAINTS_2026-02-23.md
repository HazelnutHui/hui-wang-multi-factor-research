# FMP Factor Factory Data Constraints

Date: 2026-02-23

Purpose:
- convert FMP endpoint research into enforceable constraints for batch factor generation.

## Inputs

- endpoint semantic map:
  - `audit/fmp_probe_coverage_v1/fmp_endpoint_semantic_map_2026-02-23.csv`
- endpoint dictionary:
  - `audit/fmp_probe_coverage_v1/fmp_endpoint_field_dictionary_2026-02-23.csv`

## Hard constraints

1. Allowed for default factor factory:
- `usage_tier in {factor_ready, factor_ready_with_lag}`
- source file:
  - `audit/fmp_probe_coverage_v1/fmp_factor_factory_allowlist_2026-02-23.csv`

2. Blocked by default:
- `usage_tier in {research_only_high_leakage_guard, event_monitor_only}`
- source file:
  - `audit/fmp_probe_coverage_v1/fmp_high_leakage_blocklist_2026-02-23.csv`

3. CSV payload endpoints:
- must declare CSV parser mode before ingestion.
- source file:
  - `audit/fmp_probe_coverage_v1/fmp_csv_endpoints_2026-02-23.txt`

## Operational rule for factor generation

1. New factor recipes can only reference endpoints in allowlist.
2. If endpoint is `factor_ready_with_lag`, enforce `min_lag_days >= endpoint.min_lag_days`.
3. Any endpoint in blocklist requires explicit manual approval and anti-leakage note in run audit.
