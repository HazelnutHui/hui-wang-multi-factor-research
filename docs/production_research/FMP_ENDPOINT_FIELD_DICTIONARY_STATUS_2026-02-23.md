# FMP Endpoint Field Dictionary Status

Date: 2026-02-23

## What is now fully mapped

For stable coverage set (`156` endpoints), we now have a machine-readable endpoint dictionary including:
- category
- endpoint
- http status
- payload mode (`json_or_other` vs `csv`)
- payload type
- sample row count
- detected date span
- sampled column list

Primary file:
- `audit/fmp_probe_coverage_v1/fmp_endpoint_field_dictionary_2026-02-23.csv`

## CSV-mode endpoints (special parser required)

File:
- `audit/fmp_probe_coverage_v1/fmp_csv_endpoints_2026-02-23.txt`

Count:
- 18 endpoints

## What is not yet 100% complete

The remaining non-fully-closed part is semantic interpretation at field level:
- exact business meaning/units for all fields,
- PIT safety and revision behavior per field,
- hard whitelist for factor usage by stage.

This is now a documentation/labeling task on top of the completed callability + schema map.
