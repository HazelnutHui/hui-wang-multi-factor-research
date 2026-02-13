#!/usr/bin/env python3
"""
Fetch FMP profile-bulk parts and write a compact company profile CSV.
Output columns: symbol, sector, industry
"""

import argparse
import csv
import sys
import time
from typing import List

import requests
try:
    from tqdm import tqdm
except Exception:  # pragma: no cover - optional dependency
    tqdm = None


def fetch_part(api_key: str, part: int, base_url: str) -> List[dict]:
    url = f"{base_url}?part={part}&apikey={api_key}"
    resp = requests.get(url, timeout=60)
    if resp.status_code in (400, 404):
        return []
    resp.raise_for_status()
    text = resp.text.strip()
    if not text:
        return []
    # CSV response with header
    rows = list(csv.DictReader(text.splitlines()))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--base-url", default="https://financialmodelingprep.com/stable/profile-bulk")
    parser.add_argument("--out", required=True)
    parser.add_argument("--start-part", type=int, default=0)
    parser.add_argument("--max-parts", type=int, default=200)
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    out_rows = []
    parts = range(args.start_part, args.start_part + args.max_parts)
    iterator = tqdm(parts, desc="FMP profile-bulk parts", unit="part") if tqdm else parts
    for part in iterator:
        rows = fetch_part(args.api_key, part, args.base_url)
        if not rows:
            break
        for r in rows:
            sym = (r.get("symbol") or "").strip()
            if not sym:
                continue
            out_rows.append(
                {
                    "symbol": sym,
                    "sector": (r.get("sector") or "").strip(),
                    "industry": (r.get("industry") or "").strip(),
                }
            )
        time.sleep(args.sleep)

    if not out_rows:
        print("No rows fetched; check API key or part range.", file=sys.stderr)
        return 1

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol", "sector", "industry"])
        w.writeheader()
        w.writerows(out_rows)

    print(f"Wrote {len(out_rows)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
