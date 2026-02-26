# FMP Next100 Data Plan (2026-02-26)

As-of: 2026-02-26

Purpose:
- define which FMP datasets are required for next100 candidate generation,
- enforce usage-tier boundaries to prevent leakage,
- keep data actions centralized in one place (no distributed run-notes).

## 1) Current Data State (Relevant to Next100)

Already present:
- `data/fmp/earnings/earnings_calendar.csv`
- `data/fmp/earnings/earnings_surprises_YYYY.csv` for 2010-2026 (completed backfill)
- existing baseline datasets used by current factors:
  - `data/fmp/market_cap_history/*`
  - `data/fmp/ratios/value/*`
  - `data/fmp/ratios/quality/*`

Unified directories (workstation):
- default/core data remains under `data/fmp/` domain folders.
- high-leakage isolated lane:
  - `data/fmp/research_only/`
- next100 endpoint outputs now stored in:
  - `data/fmp/institutional/`
  - `data/fmp/owner_earnings/`
  - `data/fmp/research_only/`

Current execution status:
- symbol-level next100 endpoint download finished (`all_done`).
- 429 backfill retry finished (`all_retry_done`).
- staging path `data/fmp/next100_inputs/` was migrated, and temporary backup was removed after verification.

## 2) Usage-Tier Rule (Must Keep)

1. `factor_ready_with_lag`:
- allowed for default next100 generation.
- enforce endpoint-level `min_lag_days`.

2. `research_only_high_leakage_guard`:
- not allowed in default next100 ranking.
- only usable in isolated research lane with explicit PIT checks and anti-leakage note.

3. `blocked_until_stable`:
- hold download/use until endpoint stability and schema reliability are confirmed.

## 3) Endpoint Classification For Next100

Core (download + default-use allowed with lag):
- `owner-earnings`
- `institutional-ownership/latest`
- `institutional-ownership/symbol-positions-summary`
- `earnings-calendar`
- `earnings-surprises-bulk` (as ingestion/backfill source)

Research-only (download to isolated lane, do not mix into default ranking):
- `analyst-estimates`
- `price-target-summary`
- `price-target-consensus`
- `grades-consensus`
- `insider-trading/latest`
- `insider-trading/search`
- `insider-trading/statistics`

Hold:
- `upgrades-downgrades-consensus-bulk` (empty/unstable in current validation run)

Conditional (mapping first):
- `funds/disclosure-holders-latest`
  - requires semantic-map row + lag policy before default use.

## 4) Download Execution Policy

1. parallelism:
- use `8` workers for symbol-level pulls (workstation).

2. output separation:
- core endpoints -> `data/fmp/institutional/` and `data/fmp/owner_earnings/`
- high-leakage endpoints -> `data/fmp/research_only/`

3. idempotency:
- resume by symbol; do not redownload already-complete symbol rows.

4. traceability:
- keep endpoint probe/validation artifacts under:
  - `audit/fmp_probe_validation_2026-02-26/`
  - `audit/fmp_probe_validation_2026-02-26_next100/`

## 5) Next100 Data Gate Before Factor Run

Required checks:
1. core endpoints have non-trivial coverage and pass lag policy.
2. research-only endpoints are not imported into default candidate queue.
3. dataset lineage and output path are fixed in run manifest.
4. factor queue run starts from new lineage (no reuse of removed restarted p1 outputs).
