#!/usr/bin/env python3
"""
Download FMP earnings-surprises-bulk (CSV) for one or more years.
Saves raw CSV per year under data/fmp/earnings/.
"""

import argparse
from pathlib import Path
import sys
import time

import requests


def fetch_year(api_key: str, year: int, base_url: str, timeout: int) -> str:
    url = f"{base_url}?year={year}&apikey={api_key}"
    resp = requests.get(url, timeout=timeout)
    if resp.status_code in (400, 404):
        return ""
    resp.raise_for_status()
    return resp.text.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument(
        "--out-dir",
        default="/Users/hui/quant_score/v4/data/fmp/earnings",
    )
    parser.add_argument(
        "--base-url",
        default="https://financialmodelingprep.com/stable/earnings-surprises-bulk",
    )
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--max-retries", type=int, default=6)
    parser.add_argument("--backoff", type=float, default=2.0)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for year in range(args.start_year, args.end_year + 1):
        out_path = out_dir / f"earnings_surprises_{year}.csv"
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"Skip existing {out_path}")
            continue

        attempt = 0
        while True:
            try:
                csv_text = fetch_year(args.api_key, year, args.base_url, args.timeout)
                break
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status == 429 and attempt < args.max_retries:
                    wait = args.sleep * (args.backoff ** attempt)
                    print(f"429 for {year}, retry in {wait:.1f}s...", file=sys.stderr)
                    time.sleep(wait)
                    attempt += 1
                    continue
                raise

        if not csv_text:
            print(f"No data for year {year}.", file=sys.stderr)
            time.sleep(args.sleep)
            continue

        out_path.write_text(csv_text, encoding="utf-8")
        print(f"Wrote {out_path}")
        time.sleep(args.sleep)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
