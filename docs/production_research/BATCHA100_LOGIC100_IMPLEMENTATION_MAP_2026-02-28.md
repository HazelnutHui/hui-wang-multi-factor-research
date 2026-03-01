# BatchA100 Logic100 Implementation Map (2026-02-28)

As-of: 2026-02-28
Status: code-mapped snapshot

## Summary
- total: 100
- alias_proxy: 18
- native: 75
- proxy: 7

## Files
- csv: `docs/production_research/BATCHA100_LOGIC100_IMPLEMENTATION_MAP_2026-02-28.csv`
- source: `backtest/factor_engine.py`

## Notes
- `native`: dedicated logic path in factor engine.
- `alias_proxy`: thin wrapper to existing signal implementation.
- `proxy`: explicit fallback/proxy due to current field scope.
