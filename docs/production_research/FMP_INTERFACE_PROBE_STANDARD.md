# FMP Interface Probe Standard

Last updated: 2026-02-23

Purpose:
- probe FMP endpoints with small samples before large-scale ingestion;
- identify payload format, core fields, and detectable date coverage;
- record ambiguity for later human validation.

## 1) Command (workstation preferred)

```bash
cd ~/projects/hui-wang-multi-factor-research
set -a && source .env.daily && set +a
.venv/bin/python scripts/fmp_interface_probe.py --symbol AAPL --out-dir audit/fmp_probe
```

Generated artifacts:
- `audit/fmp_probe/fmp_interface_probe_latest.json`
- `audit/fmp_probe/fmp_interface_probe_latest.md`
- timestamped copies in the same folder.

## 2) Probe scope (current)

Current default endpoints:
- `stock-list`
- `profile`
- `historical-price-eod`
- `historical-price-eod/dividend-adjusted`
- `historical-market-capitalization`
- `ratios`
- `key-metrics`
- `income-statement`
- `balance-sheet-statement`
- `cash-flow-statement`
- `earnings-surprises-bulk`
- `earnings-calendar`
- `profile-bulk`
- `delisted-companies`

## 3) Latest snapshot summary (2026-02-23)

Source:
- `audit/fmp_probe/fmp_interface_probe_latest.json`
- `audit/fmp_probe/fmp_interface_probe_latest.md`

Status summary:
- endpoints tested: 14
- HTTP success: 13/14
- failed endpoint: `historical-price-eod` (HTTP 404)

Confirmed format findings:
- `historical-price-eod/dividend-adjusted` returns JSON list with fields like `date, symbol, adjOpen, adjHigh, adjLow, adjClose, volume`.
- `historical-market-capitalization` returns JSON list with `date, symbol, marketCap`.
- `earnings-surprises-bulk` and `profile-bulk` currently return CSV text payload (not JSON) in this access path.
- `api/v3` comparison test (2026-02-23) returned 403 legacy-endpoint errors for all tested batch2 endpoints; treat `stable` as primary route under current account mode.

## 4) Ambiguity log (requires human verification)

The following items must be explicitly confirmed against intended production semantics:

1. `historical-price-eod` route behavior:
- probe got 404 while dividend-adjusted route works;
- verify whether route is deprecated, renamed, or plan-gated.

2. Bulk endpoints payload mode:
- `earnings-surprises-bulk`, `profile-bulk` returned CSV text;
- confirm whether JSON mode exists (parameter/header/path variant) and lock one canonical parser.
3. Legacy route boundary:
- `api/v3` in current account mode appears blocked for many historical endpoints (legacy-only notice);
- verify subscription scope before planning any `api/v3`-dependent ingestion.

4. Date-span meaning:
- probe date range is based on sampled rows only;
- for each endpoint, confirm whether dates represent trading date, filing date, publish date, or update date.

5. Limit/window behavior:
- some endpoints can return very large rows (`stock-list`, `earnings-calendar`);
- verify stable pagination/limit semantics before full pull.

## 5) Execution policy

1. Do not full-ingest a new endpoint before one probe pass is archived.
2. If any endpoint returns non-JSON payload, parser type must be declared in pull script/doc.
3. If endpoint date semantics are unclear, keep it out of gate-critical data path until validated.
4. Keep latest probe artifacts synced between local and workstation repos.
