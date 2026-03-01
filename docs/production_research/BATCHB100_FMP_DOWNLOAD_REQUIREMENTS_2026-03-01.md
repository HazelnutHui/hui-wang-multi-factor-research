# BatchB100 FMP Download Requirements (2026-03-01)

As-of: 2026-03-01  
Status: planning draft for BatchB100 design (not running)

Purpose:
- map BatchB100 logic requirements to FMP domains,
- separate must-have vs enhancement paths,
- keep storage aligned to `data/fmp/` and `data/fmp/research_only/`.

## Storage Standard
- default lane: `data/fmp/<domain>/...`
- research lane: `data/fmp/research_only/<domain>/...`

## P0 Must-Have
1. Price/volume history (full universe and long history)
- supports B001-B040, B086-B090, B091-B100.

2. Market cap history
- path: `data/fmp/market_cap_history/`
- supports value/ownership interaction and sizing controls.

3. Financial statements (income/balance/cashflow, annual+quarter+ttm)
- suggested path: `data/fmp/statements/`
- supports B041-B060.

4. Ratios packages (value/quality)
- paths:
  - `data/fmp/ratios/value/`
  - `data/fmp/ratios/quality/`
- supports B049-B060 and style spreads.

5. Earnings calendar + surprises
- paths:
  - `data/fmp/earnings/earnings_calendar.csv`
  - `data/fmp/earnings/earnings_surprises_*.csv`
- supports event revision chain interactions.

6. Institutional ownership core
- path: `data/fmp/institutional/`
- supports B071-B080 and crowding logic.

7. Owner earnings core
- path: `data/fmp/owner_earnings/`
- supports B077 and ownership-value links.

## P1 Strongly Recommended
1. Analyst estimates + target summary
- path: `data/fmp/research_only/analyst/`
- supports B061-B070 (revision chain; high expected value block).

2. Insider datasets
- path: `data/fmp/research_only/insider/`
- supports B078-B079 and ownership-event extensions.

3. Macro/economic series
- path: `data/fmp/research_only/macro/`
- supports B081-B090 regime conditioning.

## Pre-Run Validation Checklist
1. Coverage check: each required domain has non-trivial rows and date span.
2. Schema check: endpoint fields and date semantics validated.
3. Lag check: enforce `factor_ready_with_lag` minimum lag rules.
4. Repro check: write data snapshot manifest before any run.

## Note
- BatchB design intentionally uses more event/expectation and regime-conditioning signals.
- Therefore analyst/macro research-only domains are near-core for BatchB quality, even if not all were mandatory in BatchA.
