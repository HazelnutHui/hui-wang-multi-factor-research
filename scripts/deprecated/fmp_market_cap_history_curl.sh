#!/usr/bin/env bash
set -euo pipefail

API_KEY="${API_KEY:-xW9GGtIZOfJeA2r2YBvqrLLFNs0oF8ov}"
SYMS="${SYMS:-/Users/hui/quant_score/v4/data/fmp/symbols_us_basic.csv}"
OUT="${OUT:-/Users/hui/quant_score/v4/data/fmp/market_cap_history}"
PY="${PY:-/Users/hui/miniconda3/envs/qscore/bin/python}"
MAX_SYMS="${MAX_SYMS:-0}"
RESOLVE_IP="${RESOLVE_IP:-}"
mkdir -p "$OUT"

START="${START:-2010-01-01}"
END="${END:-2026-01-28}"

add_years() {
  "$PY" - "$1" "$2" <<'PY'
import sys, datetime as dt
d=dt.date.fromisoformat(sys.argv[1])
y=int(sys.argv[2])
try:
    nd=d.replace(year=d.year+y)
except ValueError:
    nd=d.replace(month=2, day=28, year=d.year+y)
print(nd.isoformat())
PY
}

# read symbols (skip header), optionally limit count
sym_stream="$(mktemp)"
if [ "$MAX_SYMS" -gt 0 ]; then
  awk -v n="$MAX_SYMS" 'NR>1 && NR<=n+1' "$SYMS" > "$sym_stream"
else
  tail -n +2 "$SYMS" > "$sym_stream"
fi

while IFS=, read -r sym; do
  sym="${sym//\"/}"
  sym="$(echo "$sym" | tr -d '\r' | xargs)"
  [ -z "$sym" ] && continue
  sym_enc="$(SYM="$sym" "$PY" - <<'PY'
import os, urllib.parse
sym=os.environ.get("SYM","")
print(urllib.parse.quote(sym, safe=""))
PY
)"
  tmp="$(mktemp)"
  cur="$START"
  while [ "$cur" \< "$END" ] || [ "$cur" == "$END" ]; do
    next="$(add_years "$cur" 2)"
    seg_end="$next"
    if [ "$seg_end" \> "$END" ]; then seg_end="$END"; fi
    url="https://financialmodelingprep.com/stable/historical-market-capitalization?symbol=${sym_enc}&from=${cur}&to=${seg_end}&limit=5000&apikey=${API_KEY}"
    if [ -n "$RESOLVE_IP" ]; then
      curl -sS --retry 5 --retry-all-errors --retry-delay 1 \
        --resolve "financialmodelingprep.com:443:${RESOLVE_IP}" \
        "$url" >> "$tmp" || true
    else
      curl -sS --retry 5 --retry-all-errors --retry-delay 1 "$url" >> "$tmp" || true
    fi
    cur=$("$PY" - <<PY
import datetime as dt
d=dt.date.fromisoformat("${seg_end}") + dt.timedelta(days=1)
print(d.isoformat())
PY
)
  done

  SYM="$sym" TMP="$tmp" OUT="$OUT" "$PY" - <<'PY'
import json, sys, os, pandas as pd
sym=os.environ.get("SYM","")
tmp=os.environ.get("TMP")
out=os.environ.get("OUT")
raw=open(tmp).read()
data=[]
for part in raw.split(']['):
    if not part.strip():
        continue
    if not part.startswith('['): part='['+part
    if not part.endswith(']'): part=part+']'
    try:
        data.extend(json.loads(part))
    except Exception:
        pass
if not data:
    print("empty", sym)
    sys.exit(0)
df=pd.DataFrame(data)
df=df[['date','marketCap']].dropna().drop_duplicates(subset=['date']).sort_values('date')
df.to_csv(f"{out}/{sym}.csv", index=False)
print("wrote", sym, len(df))
PY

  rm -f "$tmp"
  sleep 0.25
done < "$sym_stream"
rm -f "$sym_stream"
