#!/usr/bin/env python3
"""
Download FMP delisted companies list and save as CSV.
"""

import argparse
from pathlib import Path
import sys
import time

import requests


def fetch_page(api_key: str, base_url: str, page: int, limit: int, timeout: int):
    url = f"{base_url}?page={page}&limit={limit}&apikey={api_key}"
    resp = requests.get(url, timeout=timeout)
    if resp.status_code in (400, 404):
        return []
    resp.raise_for_status()
    return resp.json() if resp.text.strip() else []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument(
        "--out",
        default="/Users/hui/quant_score/v4/data/fmp/delisted_companies.csv",
    )
    parser.add_argument(
        "--base-url",
        default="https://financialmodelingprep.com/stable/delisted-companies",
    )
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=1000)
    args = parser.parse_args()

    rows = []
    page = 0
    while page < args.max_pages:
        page_rows = fetch_page(args.api_key, args.base_url, page, args.limit, args.timeout)
        if not page_rows:
            break
        rows.extend(page_rows)
        page += 1
        time.sleep(args.sleep)
    if not rows:
        print("No rows fetched; check API key or endpoint/pagination.", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Union of keys for stable CSV header
    keys = set()
    for r in rows:
        if isinstance(r, dict):
            keys.update(r.keys())
    if not keys:
        print("No dict rows returned.", file=sys.stderr)
        return 1

    import csv

    fieldnames = sorted(keys)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            if isinstance(r, dict):
                w.writerow({k: r.get(k, "") for k in fieldnames})

    print(f"Wrote {len(rows)} rows to {out_path} (pages={page}, limit={args.limit})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
