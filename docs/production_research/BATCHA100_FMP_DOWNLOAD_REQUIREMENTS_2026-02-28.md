# BatchA100 FMP Download Requirements (2026-02-28)

As-of: 2026-02-28

Primary callable reference (single-file):
- `docs/production_research/FMP_CALLABLE_DATA_REFERENCE_2026-03-07.md`
Status: required before full run of logic100 blueprint

Purpose:
- define what must be downloaded for BatchA100 logic100 coverage,
- separate mandatory core vs optional enhancement datasets,
- keep storage layout aligned to `data/fmp` and `data/fmp/research_only`.

## Storage Standard

- core/default lane: `data/fmp/<domain>/...`
- high-leakage or unstable lane: `data/fmp/research_only/<domain>/...`

## P0 Must-Have (download first)

1. Price + volume history (adjusted + survivorship-handled)
- use existing v4 price pipeline roots; ensure full coverage of universe and dates.
- supports logic: 1-50, 93-95.

2. Market cap history
- path: `data/fmp/market_cap_history/`
- supports logic: 31, 51-65, 98.

3. Ratios value package
- path: `data/fmp/ratios/value/`
- supports logic: 51-65.

4. Ratios quality package
- path: `data/fmp/ratios/quality/`
- supports logic: 66-80.

5. Financial statements (income/balance/cashflow, annual+quarter)
- suggested domain path: `data/fmp/statements/`
- supports logic: 53-57, 66-90.

6. Earnings calendar + earnings surprises
- paths:
  - `data/fmp/earnings/earnings_calendar.csv`
  - `data/fmp/earnings/earnings_surprises_*.csv`
- supports logic: 91-95.

7. Institutional ownership core
- path: `data/fmp/institutional/`
- endpoints already validated in prior docs:
  - `institutional-ownership/latest`
  - `institutional-ownership/symbol-positions-summary`
- supports logic: 34, 96, 97, 99.

8. Owner earnings
- path: `data/fmp/owner_earnings/`
- supports logic: 98.

## P1 Strongly Recommended (download after P0)

1. Analyst estimates and target summary
- path: `data/fmp/research_only/analyst/`
- supports future upgrade of event/expectation logic.

2. Insider trading datasets
- path: `data/fmp/research_only/insider/`
- supports extension of ownership/event reactions.

3. Funds holdings / disclosure holders (after schema map)
- path: `data/fmp/research_only/funds/`
- supports crowding/capacity extensions.

## P2 Optional / Experimental

1. Transcript and textual endpoints
- path: `data/fmp/research_only/transcript/`
- for NLP/event sentiment experiments only.

2. Macro/economic series
- path: `data/fmp/research_only/macro/`
- for regime conditioning, not mandatory for first 100 logic run.

## Endpoint-to-Logic Coverage Summary

- Fully covered by P0: logic 1-100 baseline implementation.
- Enhanced by P1/P2: robustness and second-round variants, not required for first canonical run.

## Execution Checklist

1. verify P0 paths exist and contain non-trivial rows.
2. run endpoint-level schema sanity check (field names + date ranges).
3. enforce lag policy by domain:
- price/volume: T+1 bar alignment,
- fundamentals/statements: filing/publication lag,
- earnings/events: event timestamp lag,
- ownership: report-date lag.
4. generate run manifest with immutable data snapshot hashes.

## Source References (for factor priority rationale)

- Fama-French data library and multi-factor literature.
- AQR quality-minus-junk framework.
- Amihud illiquidity and liquidity risk literature.
- PEAD and momentum/reversal canonical studies.
- FMP stable API endpoint documentation.

Direct links:
- FMP stable API index: https://site.financialmodelingprep.com/developer/docs/stable
- FMP Company Financial Statements API: https://site.financialmodelingprep.com/developer/docs/stable/company-financial-statements
- FMP Earnings API: https://site.financialmodelingprep.com/developer/docs/stable/earnings
- FMP Institutional Holder APIs: https://site.financialmodelingprep.com/developer/docs/stable/institutional-holder
