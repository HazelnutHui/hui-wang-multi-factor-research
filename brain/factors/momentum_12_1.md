# Factor: Momentum 12-1 (Draft)

Goal: classic 12-1 momentum (skip most recent month).

Candidate formulas (validate in BRAIN):
1) Simple price ratio with skip:
   - `ts_delay(close, 21) / ts_delay(close, 252)`
   - Use `rank(...)` for cross-sectional signal.

2) Log return version:
   - `log(ts_delay(close, 21) / ts_delay(close, 252))`
   - Use `rank(...)` or z-score if supported.

Recommended starting point:
- `rank(log(ts_delay(close, 21) / ts_delay(close, 252)))`

Notes
- Assumes ~21 trading days/month, ~252 trading days/year.
- If BRAIN has built-in `returns` or `ts_delta`, adjust accordingly.

Record results in:
- `brain/logs/brain_factor_log.md`
