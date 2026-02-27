# WorldQuant BRAIN Operators Quick Ref

Source:
- `/Users/hui/Downloads/operators.pdf`
- Extracted raw text saved to:
  - `brain/results/operators_worldquant_2026-02-19.txt`

Capture note:
- Snapshot appears to be from `https://platform.worldquantbrain.com/learn/operators`.
- This file is a concise working summary for formula drafting.

## 1) Arithmetic Operators (seen in snapshot)
- `abs(x)`: absolute value.
- `add(x, y, filter=false)`: element-wise addition; with `filter=true`, NaN treated as 0.
- `densify(x)`: remap sparse group bucket IDs to compact bucket IDs.
- `divide(x, y)`: division.
- `inverse(x)`: reciprocal.
- `log(x)`: natural log (expects positive input).
- `max(x, y, ...)`: max of inputs.
- `min(x, y, ...)`: min of inputs.
- `multiply(x, y, ..., filter=false)`: element-wise product; with `filter=true`, NaN treated as 1.
- `power(x, y)`: exponentiation.
- `reverse(x)`: negation (`-x`).
- `sign(x)`: sign function (`+1/-1/0/NaN`).
- `signed_power(x, y)`: `sign(x) * (abs(x)^y)`.
- `sqrt(x)`: non-negative square root.
- `subtract(x, y, ..., filter=false)`: left-to-right subtraction; with `filter=true`, NaN treated as 0.

## 2) Logical Operators (seen in snapshot)
- `if_else(cond, a, b)`: conditional selection.
- Comparisons:
  - `input1 < input2`
  - `input1 <= input2`
  - `input1 == input2`
  - `input1 > input2`
  - `input1 >= input2`
  - `input1 != input2`
- `is_nan(x)`: NaN indicator.
- `not(x)`: logical negation.
- `or(input1, input2)`: logical OR.
- Logical AND operator is listed in page text (returns true only when both operands are true).

## 3) Time-Series Operators (visible in extracted pages)
- `days_from_last_change(x)`: days since last value change.
- `hump(x, hump=0.01)`: limit magnitude/frequency of changes (turnover control).
- `kth_element(x, d, k)`: kth valid value in lookback (can be used for backfill).
- `last_diff_value(x, d)`: last value not equal to current value in lookback.
- `ts_arg_max(x, d)`: relative index of max in lookback window.
- `ts_arg_min(x, d)`: relative index of min in lookback window.
- `ts_av_diff(x, d)`: `x - ts_mean(x, d)` with NaN-aware mean.
- `ts_backfill(x, d)`: backfill from recent valid values.
- `ts_corr(x, y, d)`: rolling correlation.

## 4) Practical Notes For This Repo
- Prefer plain decimal constants over scientific notation in expressions (e.g., `0.000000001` not `1e-9`) to avoid parser issues.
- Validate field names from Data Search first; do not assume aliases like `pe`, `pfcf`, or `ev_ebitda`.
- For missing-heavy fundamentals fields, combine `is_nan`, `if_else`, and backfill-style operators where needed.

