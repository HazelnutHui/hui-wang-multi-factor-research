# FMP API Reference Note (Public English Edition)

Last updated: 2026-02-13

This repository uses Financial Modeling Prep (FMP) endpoints for:
- Price history and delisted coverage workflows
- Fundamentals (quality/value-related ratios and statements)
- Earnings/event datasets used by event-driven factors
- Company profile/industry metadata
- Market-cap history for PIT size filtering

## Important Usage Notes
- API access level depends on your FMP plan.
- Some endpoints may return empty rows for specific symbols.
- Use environment variables for credentials (for example `FMP_API_KEY`).
- Never commit API keys or raw secret-bearing logs.

## Related Scripts in This Repo
- `scripts/download_dividend_adjusted_prices.py`
- `scripts/download_quality_fundamentals.py`
- `scripts/download_value_fundamentals.py`
- `scripts/fmp_profile_bulk_to_csv.py`
- `scripts/fmp_market_cap_history.py`
- `scripts/fmp_delisted_companies.py`
