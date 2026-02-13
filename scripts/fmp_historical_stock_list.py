#!/usr/bin/env python3
"""
Download FMP historical stock list and save as CSV.
"""

import argparse
from pathlib import Path
import sys
import time

import requests


def fetch(api_key: str, base_url: str, timeout: int):
    url = f"{base_url}?apikey={api_key}"
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
        default="/Users/hui/quant_score/v4/data/fmp/historical_stock_list.csv",
    )
    parser.add_argument(
        "--base-url",
        default="https://financialmodelingprep.com/stable/stock-list",
    )
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    rows = fetch(args.api_key, args.base_url, args.timeout)
    if not rows:
        print("No rows fetched; check API key or endpoint.", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

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

    time.sleep(args.sleep)
    print(f"Wrote {len(rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
