# BatchA100 Logic100 Formal V1 (2026-02-28)

As-of: 2026-02-28  
Status: draft for manual approval (not running)

## Objective
Define `100` high-value, mechanism-distinct single-factor logics for your official first batch, with focus on:
- current-market relevance,
- professional literature consistency,
- data realism under FMP + v4 process,
- no mechanical pair/tri stacking as "new logic".

## Hard Constraints Applied
- One logic = one clear mechanism hypothesis.
- No simple parameter sweep counted as new logic.
- Every logic has explicit formula expression and data dependency.
- Every event/fundamental logic assumes lag-safe execution (T+1 and filing/announcement lag guard).

## Deliverable SSOT
- Full table (100 rows):
  - `docs/production_research/BATCHA100_LOGIC100_FORMAL_V1_2026-02-28.csv`
- Key columns:
  - `logic_id`, `logic_name`, `family`, `core_formula`
  - `primary_data`, `fmp_source`
  - `priority` (`P0/P1/P2`)
  - `engine_fit` (`runnable_now` / `requires_signal_impl`)

## Distribution (100)
- Price Trend/Behavior: 20
- Liquidity/Flow/Crowding: 10
- Risk/Tail/Beta: 10
- Value/Re-rating: 10
- Quality/Profitability: 10
- Growth/Investment: 10
- Event/Expectation: 10
- Ownership/Sentiment Proxy: 10
- Regime/State-aware: 10

## Why This Version Is Stronger
- Removes prior overuse of pair/tri linear blending.
- Emphasizes interpretable economic mechanisms (underreaction, crowding, balance-sheet quality, tail-risk pricing).
- Couples return predictors with capacity/tradability checks (liquidity filters, crowding-aware variants).
- Keeps high-signal event block (SUE/PEAD) while controlling leakage risk.

## External Research Backbone (used for this design refresh)
- Fama/French factor framework: size, value, profitability, investment (Ken French data library + five-factor definition).
- Novy-Marx gross profitability premium (NBER w15940): supports quality/profitability block.
- Daniel & Moskowitz momentum crashes (NBER w20439): supports crash-aware momentum and regime gates.
- QMJ (AQR working paper + 2025 updated QMJ factor datasets): supports quality decomposition and quality-price timing view.
- Hirshleifer et al. macro/micro news and diffusion work (NBER w28931, w30860): supports event attention and PEAD state-conditioning.
- Luo et al. retail contrarian behavior around earnings/news (NBER w34086, 2025): supports underreaction/event-drift + ownership interaction ideas.
  - Ken French data library: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
  - Fama/French 5-factor description: https://mba.tuck.dartmouth.edu/pages/faculty/Ken.french/Data_Library/f-f_5_factors_2x3.html
  - NBER w15940: https://www.nber.org/papers/w15940
  - NBER w20439: https://www.nber.org/papers/w20439
  - AQR QMJ paper page: https://www.aqr.com/Insights/Research/Working-Paper/Quality-Minus-Junk
  - AQR 2025 QMJ datasets: https://www.aqr.com/Insights/Datasets/Quality-Minus-Junk-Factors-Daily
  - NBER w28931: https://www.nber.org/papers/w28931
  - NBER w30860: https://www.nber.org/papers/w30860
  - NBER w34086: https://www.nber.org/papers/w34086

## Gate Before Formal Generation To Runtime Catalog
1. Logic uniqueness gate: verify no semantic duplicates across 100 rows.
2. Data gate: confirm each `fmp_source` path exists or is backfillable.
3. Engine gate: convert `requires_signal_impl` items to concrete factor-engine methods in phased order (`P0` first).
4. Governance gate: freeze policy hash before first run.

## Notes
- This file supersedes mechanism design intent from earlier pair/tri-heavy draft files.
- Earlier files can be kept as historical planning references, but must not be used as runtime SSOT for this batch.
- Inference note: event/ownership interaction logics are inferred from the research direction above and adapted to FMP-observable proxies (not direct replication of paper datasets).
