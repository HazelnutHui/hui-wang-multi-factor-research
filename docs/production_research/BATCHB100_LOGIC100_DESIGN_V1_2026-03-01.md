# BatchB100 Logic100 Design V1 (2026-03-01)

As-of: 2026-03-01  
Status: design-only draft (not approved, not running)

## Objective
Define the second official 100-logic batch with stricter novelty vs BatchA and stronger emphasis on:
- conditional effectiveness in recent market regimes,
- event/expectation transmission,
- crowding and capacity-aware alpha persistence,
- lag-safe, FMP-feasible implementation.

## Scope Boundary
- This file is design SSOT only.
- No runtime policy or queue is created from this draft yet.
- Run requires manual approval after review.

## Deliverables
- 100-row design table:
  - `docs/production_research/BATCHB100_LOGIC100_DESIGN_V1_2026-03-01.csv`
- Columns aligned with BatchA schema plus explicit novelty note:
  - `logic_id, logic_name, family, core_formula, primary_data, fmp_source, priority, engine_fit, dedup_vs_batchA`

## Family Distribution (100)
- Microstructure/Execution: 10
- Overnight/Calendar Micro-anomalies: 10
- Liquidity/Flow Shape: 10
- Risk Asymmetry/Tail Dependence: 10
- Value/Re-rating 2.0: 10
- Quality Dynamics: 10
- Event/Expectation Revision Chain: 10
- Ownership/Crowding Dynamics: 10
- Regime/Macro Conditioning: 10
- Orthogonalized Meta/Spread Logic: 10

## Design Principles
1. One logic = one mechanism hypothesis (not parameter sweep).
2. Prioritize conditional and interaction channels over static single-style exposures.
3. Keep capacity in view (flow, crowding, liquidity stress proxies).
4. Enforce lag-safe usage for all fundamental/event/ownership/macro inputs.
5. Keep implementation tags explicit (`requires_signal_impl` first).

## Professional Rationale (high level)
- Recent practice and literature increasingly support state-conditional and interaction effects over unconditional static factors.
- Post-event drift and revision channels are stronger when combined with disagreement/liquidity/crowding filters.
- Style premia persistence often depends on regime; explicit conditioning is part of institutional research standards.

## Governance Gate Before Any Run
1. Novelty gate: remove semantic overlap with BatchA finalists.
2. Data gate: verify each required domain path exists and coverage is non-trivial.
3. Lag gate: enforce per-domain minimum lag and timestamp semantics.
4. Engine gate: phase implementation from P0 to P1/P2.
5. Approval gate: manual review sign-off before queue generation.

## References (selection)
- NBER, 2025, *Artificial Intelligence Asset Pricing Models*.
- NBER, 2023, *Complexity in Factor Pricing Models*.
- Journal of Empirical Finance, 2024, *Expensive anomalies*.
- JFQA, 2023, *Double Machine Learning: Explaining the PEAD*.
- AQR QMJ dataset/research updates.

Inference note:
- BatchB logic set is an applied translation into FMP-observable, lag-safe proxies under current V4 process, not a direct one-to-one replication of external datasets.
