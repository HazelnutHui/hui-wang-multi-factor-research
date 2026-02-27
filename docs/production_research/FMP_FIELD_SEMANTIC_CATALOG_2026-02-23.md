# FMP Field Semantic Catalog

Date: 2026-02-23

## Current scope

- based on stable-callable coverage set (`156` endpoints)
- field-level catalog built from sampled columns

## Field-level counts

- total sampled unique fields: `824`
- default-allow fields for factor factory: `751`
- blocked/caution fields (event or high-leakage linked): `73`

## Main artifact

- `audit/fmp_probe_coverage_v1/fmp_field_semantic_catalog_2026-02-23.csv`

Key columns in catalog:
- `field`
- `feature_family`
- `unit_hint`
- `time_semantics`
- `allow_default_factor_factory`
- `caution_level`
- `max_min_lag_days`
- `endpoint_count`
- `categories`
- `usage_tiers`
- `example_endpoints`

## Important interpretation

1. `824` is a sampled unique-field surface from active probes, not a guaranteed complete vendor dictionary.
2. `751` default-allow fields are suitable for controlled factor generation under current lag constraints.
3. `73` blocked/caution fields are mainly from event/news/transcript or high-leakage categories.
