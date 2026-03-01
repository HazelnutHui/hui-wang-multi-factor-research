#!/usr/bin/env python3
from pathlib import Path
import csv
root = Path(__file__).resolve().parents[1]
univ = {p.stem for p in (root/'data/prices').glob('*.pkl')} | {p.stem for p in (root/'data/prices_delisted').glob('*.pkl')}
mcap = {p.stem for p in (root/'data/fmp/market_cap_history').glob('*.csv')}
miss = sorted(univ - mcap)
out = root/'data/fmp/market_cap_missing_symbols.csv'
out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['symbol'])
    w.writeheader()
    for s in miss:
        w.writerow({'symbol': s})
print('wrote', out, 'rows', len(miss))
