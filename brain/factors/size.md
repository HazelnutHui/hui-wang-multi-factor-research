# Factor: Size (Market Cap)

Field
- `cap` = Daily market capitalization (in millions)

Candidate formulas (pick one):
1. Small-cap tilt (preferred for size effect):
   - `-rank(cap)`
2. Log size (stabilized scale):
   - `-log(cap)`
3. Inverse size (aggressive small-cap):
   - `1 / cap`

Notes
- `cap` is in millions, so `log(cap)` is stable.
- If you want pure size (large-cap bias), drop the negative sign.

Recommended starting point:
- `-rank(cap)`

Record results in:
- `brain/logs/brain_factor_log.md`
