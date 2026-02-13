# Strategy Comparison (English)

> Scope: PEAD v1 / Short-Term Reversal v1 / Medium-Term Momentum v1

---

## 1. Core Logic Comparison

| Strategy | Core Logic | Data Required | Timing Sensitivity | Signal Update Speed | Best Use Case |
|---|---|---|---|---|---|
| PEAD v1 | SUE-driven earnings drift | Earnings + Prices | High | Low (event-driven) | Event strategies, drift validation |
| Reversal v1 | Intraday reversal (-Close/Open) | Daily OHLCV | Medium | High (daily) | Short-term mean reversion |
| Momentum v1 | 12-1 momentum | Adjusted prices | Low | Low (monthly) | Medium-term trend capture |

---

## 2. Timing and Execution

| Strategy | Signal Time | Execution | Holding Period | Rebalance |
|---|---|---|---|---|
| PEAD v1 | earnings_date close | Next open | 1 day (current) | 5 days |
| Reversal v1 | Day close | Next open | 1 day | Daily |
| Momentum v1 | Day close | Next open | 20 days | Monthly (21 days) |

---

## 3. Parameter Summary

| Strategy | Key Parameters |
|---|---|
| PEAD v1 | `SUE_THRESHOLD=0.5`, `LOOKBACK_QUARTERS=8`, `DATE_SHIFT_DAYS=0`, `HOLDING=1` |
| Reversal v1 | `REVERSAL_MODE=intraday`, `REVERSAL_VOL_LOOKBACK=20`, `EARNINGS_FILTER=1` |
| Momentum v1 | `MOMENTUM_LOOKBACK=252`, `MOMENTUM_SKIP=21`, `MOMENTUM_VOL_LOOKBACK=60` |

---

## 4. Strengths and Risks

**PEAD v1**
- Strength: clear economic intuition; event-driven
- Risk: missing announcement timing → alignment/forward-looking risk; sparse signals

**Reversal v1**
- Strength: fast response; low data requirements
- Risk: cost sensitive; can break on event days

**Momentum v1**
- Strength: robust across markets; stable
- Risk: momentum crash regimes; turnover must be controlled

---

## 5. Recommended Priority

1. Momentum v1 as a stable baseline
2. Reversal v1 as short-horizon complement
3. PEAD v1 as observational unless timing data improves

---

## 6. Output Locations

- PEAD: `strategies/pead_v1/`
- Reversal: `strategies/reversal_v1/`
- Momentum: `strategies/momentum_v1/`

