# Data Quality Policy

Last updated: 2026-02-21

This policy defines minimum data quality checks before running official production gates.

## 1) Objective

Prevent invalid promotion decisions caused by stale, broken, or schema-shifted inputs.

## 2) Mandatory Pre-Gate Checks

Run `scripts/data_quality_gate.py` against each official input table (or merged research dataset) and enforce:

1. required columns present
2. row count above minimum
3. duplicate ratio below threshold (by key columns if provided)
4. per-column missing ratio below threshold
5. no NaN/inf in declared numeric columns
6. freshness within allowed staleness window (when date column provided)

## 3) Default Threshold Baseline

- `min_rows = 1000`
- `max_missing_ratio = 0.05`
- `max_duplicate_ratio = 0.01`
- `max_staleness_days = 7`

Thresholds may be tightened by strategy-specific policy, not loosened for official runs without recorded approval.

## 4) Official Run Integration

Recommended command pattern:

```bash
python scripts/data_quality_gate.py \
  --input-csv data/your_input.csv \
  --required-columns date,ticker,score \
  --numeric-columns score \
  --key-columns date,ticker \
  --date-column date \
  --max-staleness-days 7 \
  --out-dir gate_results/data_quality
```

If `overall_pass=false`, official gate run must not proceed until data issue is resolved and rechecked.

## 5) Audit Artifacts

Each check produces:

- `data_quality_report.json`
- `data_quality_report.md`

These artifacts should be referenced in run notes and retained with gate artifacts for decision traceability.

## 6) Ownership and Review

- owner: strategy owner (`hui` by default)
- review cadence: weekly during active development; mandatory before promotion decision
- linked docs:
  - `RISK_REGISTER.md`
  - `INCIDENT_RESPONSE.md`
  - `GATE_SPEC.md`
