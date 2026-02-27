# FMP Category Playbook (For Factor Factory)

Date: 2026-02-23

Reference data:
- `audit/fmp_probe_coverage_v1/fmp_endpoint_semantic_map_2026-02-23.csv`
- `audit/fmp_probe_coverage_v1/fmp_factor_factory_allowlist_2026-02-23.csv`
- `audit/fmp_probe_coverage_v1/fmp_high_leakage_blocklist_2026-02-23.csv`

## 1) Price/Chart (`charts`)

Use for:
- momentum/reversal/volatility/liquidity factors

Default:
- directly factor-ready (`usage_tier=factor_ready`)

Risk note:
- only use past bars; never reference current unfinished bar.

## 2) Fundamentals (`statements` + part of `company`)

Use for:
- quality/value/profitability/leverage/capital-efficiency factors

Default:
- factor-ready with lag (`usage_tier=factor_ready_with_lag`)

Risk note:
- enforce filing/acceptance-date lag (`min_lag_days` in semantic map).

## 3) Macro/Economic (`economics`)

Use for:
- market regime filters and macro-conditioned exposure control

Default:
- factor-ready with lag

Risk note:
- release lag + revisions must be handled.

## 4) Universe/Metadata (`search` + `directory`)

Use for:
- symbol universe definition, exchange/country/sector metadata

Default:
- universe metadata only (`usage_tier=universe_metadata`)

Risk note:
- not direct alpha signal by itself.

## 5) Analyst/Consensus (`analyst`, part of grades/targets)

Use for:
- research-only experiments with strict anti-leakage checks

Default:
- blocked from default factor factory (`usage_tier=research_only_high_leakage_guard`)

Risk note:
- forward-looking fields can leak future information.

## 6) News/Transcript/Event Streams (`news`, `transcript`)

Use for:
- event-monitoring or event-driven specialized pipelines

Default:
- blocked from default cross-sectional daily factor factory (`usage_tier=event_monitor_only`)

Risk note:
- timestamp alignment to market close is mandatory.

## 7) Bulk Endpoints (`bulk`)

Use for:
- offline backfill and large-scale snapshot ingestion

Default:
- ingestion source with parser constraints (`csv` mode)

Risk note:
- parser mode must be explicitly CSV; do not treat as JSON endpoints.
