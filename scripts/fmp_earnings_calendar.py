#!/usr/bin/env python3
"""
Download FMP earnings calendar (JSON) for a date range and save as CSV.
FMP calendar requires a max 90-day window; this script slices ranges.
"""

import argparse
from datetime import date, timedelta, datetime
from pathlib import Path
import sys
import time

import requests


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def fetch_range(api_key: str, start: date, end: date, base_url: str):
    url = f"{base_url}?from={start.isoformat()}&to={end.isoformat()}&apikey={api_key}"
    resp = requests.get(url, timeout=60)
    if resp.status_code in (400, 404):
        return []
    resp.raise_for_status()
    return resp.json() if resp.text.strip() else []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument(
        "--out",
        default="/Users/hui/quant_score/v4/data/fmp/earnings/earnings_calendar.csv",
    )
    parser.add_argument(
        "--base-url",
        default="https://financialmodelingprep.com/stable/earnings-calendar",
    )
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--max-window-days", type=int, default=90)
    args = parser.parse_args()

    start = parse_date(args.start)
    end = parse_date(args.end)
    if end < start:
        print("end must be >= start", file=sys.stderr)
        return 1

    rows = []
    cursor = start
    while cursor <= end:
        window_end = min(end, cursor + timedelta(days=args.max_window_days - 1))
        rows.extend(fetch_range(args.api_key, cursor, window_end, args.base_url))
        cursor = window_end + timedelta(days=1)
        time.sleep(args.sleep)

    if not rows:
        print("No rows fetched; check API key or date range.", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV with stable columns
    import csv

    fieldnames = [
        "symbol",
        "date",
        "epsActual",
        "epsEstimated",
        "revenueActual",
        "revenueEstimated",
        "lastUpdated",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    print(f"Wrote {len(rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
