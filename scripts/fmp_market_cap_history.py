#!/usr/bin/env python3
"""
Download FMP market cap history per symbol.
Output: one CSV per symbol with columns: date, marketCap
"""

import argparse
import csv
import os
import sys
import time
from typing import Iterable, List

import requests
import subprocess
import json
from datetime import datetime, date, timedelta


def iter_symbols(path: str) -> Iterable[str]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "symbol" not in reader.fieldnames:
            raise ValueError("symbols csv must include 'symbol' column")
        for row in reader:
            sym = (row.get("symbol") or "").strip()
            if sym:
                yield sym


def _build_url(base_url: str, symbol: str) -> str:
    if "{symbol}" in base_url:
        return base_url.format(symbol=symbol)
    return base_url


def _extract_rows(data):
    # FMP may return list or dict with "historical"
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        hist = data.get("historical")
        if isinstance(hist, list):
            return hist
    return []

def _fetch_with_curl(url: str, resolve_ip: str, timeout: int,
                     retries: int, retry_sleep: float) -> List[dict]:
    # Use curl with --resolve to bypass local DNS issues.
    # url must use financialmodelingprep.com as host for SNI/cert validation.
    cmd = [
        "curl",
        "-sS",
        "--max-time", str(int(timeout)),
        "--retry", str(max(0, int(retries))),
        "--retry-connrefused",
        "--retry-all-errors",
        "--retry-delay", str(int(retry_sleep)),
        "--resolve", f"financialmodelingprep.com:443:{resolve_ip}",
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"curl failed (code {proc.returncode})")
    raw = proc.stdout.strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return _extract_rows(data)


def fetch_market_cap(api_key: str, symbol: str, base_url: str,
                     date_from: str | None, date_to: str | None,
                     limit: int | None, timeout: int,
                     host_header: str | None, verify: bool,
                     resolve_ip: str | None,
                     retries: int, retry_sleep: float) -> List[dict]:
    url = _build_url(base_url, symbol)
    params = {"apikey": api_key}
    if "{symbol}" not in base_url:
        params["symbol"] = symbol
    if date_from:
        params["from"] = date_from
    if date_to:
        params["to"] = date_to
    if limit:
        # API docs: max 5000 records per request
        params["limit"] = int(min(int(limit), 5000))
    last_err = None
    for i in range(max(1, int(retries))):
        try:
            if resolve_ip:
                # Build final URL with query params (curl won't add them)
                from urllib.parse import urlencode
                q = urlencode(params)
                full_url = f"{url}?{q}"
                # Support multiple IPs separated by comma
                ips = [x.strip() for x in str(resolve_ip).split(",") if x.strip()]
                last_err = None
                for ip in ips or []:
                    try:
                        return _fetch_with_curl(full_url, ip, timeout, retries, retry_sleep)
                    except Exception as exc:
                        last_err = exc
                        continue
                if last_err:
                    raise last_err
                return []
            else:
                headers = {"Host": host_header} if host_header else None
                resp = requests.get(url, params=params, headers=headers, timeout=timeout, verify=verify)
                if resp.status_code in (400, 404):
                    return []
                resp.raise_for_status()
                data = resp.json()
                return _extract_rows(data)
        except Exception as exc:
            last_err = exc
            if i < int(retries) - 1:
                time.sleep(float(retry_sleep))
                continue
            raise
    if last_err:
        raise last_err
    return []

def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def _format_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def _add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        # handle Feb 29
        return d.replace(month=2, day=28, year=d.year + years)

def fetch_market_cap_chunked(api_key: str, symbol: str, base_url: str,
                             date_from: str | None, date_to: str | None,
                             limit: int | None, timeout: int,
                             host_header: str | None, verify: bool,
                             resolve_ip: str | None,
                             retries: int, retry_sleep: float,
                             chunk_years: int) -> List[dict]:
    if not date_from:
        raise ValueError("chunked fetch requires --from-date")
    if date_to:
        end_date = _parse_date(date_to)
    else:
        end_date = datetime.utcnow().date()

    cur = _parse_date(date_from)
    all_rows: List[dict] = []
    while cur <= end_date:
        seg_end = _add_years(cur, int(chunk_years))
        # inclusive end, keep within overall end_date
        if seg_end > end_date:
            seg_end = end_date
        rows = fetch_market_cap(
            api_key=api_key,
            symbol=symbol,
            base_url=base_url,
            date_from=_format_date(cur),
            date_to=_format_date(seg_end),
            limit=limit,
            timeout=timeout,
            host_header=host_header,
            verify=verify,
            resolve_ip=resolve_ip,
            retries=retries,
            retry_sleep=retry_sleep,
        )
        if rows:
            all_rows.extend(rows)
        # advance to next day after seg_end
        cur = seg_end + timedelta(days=1)

    # de-dup by date, keep last
    if not all_rows:
        return []
    dedup = {}
    for r in all_rows:
        d = r.get("date")
        if d is None:
            continue
        dedup[d] = r
    return [dedup[k] for k in sorted(dedup.keys())]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--symbols-csv", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument(
        "--base-url",
        default="https://financialmodelingprep.com/stable/historical-market-capitalization",
    )
    parser.add_argument("--from-date", dest="from_date")
    parser.add_argument("--to-date", dest="to_date")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--sleep", type=float, default=0.25)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--retry-sleep", type=float, default=1.0)
    parser.add_argument("--chunk-years", type=int, default=0,
                        help="Split requests into N-year chunks to respect max 5000 rows")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--host-header", dest="host_header")
    parser.add_argument("--insecure", action="store_true",
                        help="Disable TLS verification (use with --host-header + IP base-url)")
    parser.add_argument("--resolve-ip",
                        help="Use curl --resolve to bypass DNS (host must be financialmodelingprep.com)")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    total = 0
    written = 0
    for sym in iter_symbols(args.symbols_csv):
        total += 1
        out_path = os.path.join(args.out_dir, f"{sym}.csv")
        if os.path.exists(out_path) and not args.overwrite:
            continue

        try:
            if args.chunk_years and int(args.chunk_years) > 0:
                rows = fetch_market_cap_chunked(
                    api_key=args.api_key,
                    symbol=sym,
                    base_url=args.base_url,
                    date_from=args.from_date,
                    date_to=args.to_date,
                    limit=args.limit,
                    timeout=args.timeout,
                    host_header=args.host_header,
                    verify=not args.insecure,
                    resolve_ip=args.resolve_ip,
                    retries=args.retries,
                    retry_sleep=args.retry_sleep,
                    chunk_years=int(args.chunk_years),
                )
            else:
                rows = fetch_market_cap(
                    args.api_key,
                    sym,
                    args.base_url,
                    args.from_date,
                    args.to_date,
                    args.limit,
                    args.timeout,
                    args.host_header,
                    verify=not args.insecure,
                    resolve_ip=args.resolve_ip,
                    retries=args.retries,
                    retry_sleep=args.retry_sleep,
                )
        except Exception as exc:
            print(f"Error {sym}: {exc}", file=sys.stderr)
            time.sleep(args.sleep)
            continue

        if not rows:
            time.sleep(args.sleep)
            continue

        # Keep only symbol/date/marketCap
        cleaned = []
        for r in rows:
            date = r.get("date")
            mc = r.get("marketCap")
            if date is None or mc is None:
                continue
            cleaned.append({"date": date, "marketCap": mc})

        if not cleaned:
            time.sleep(args.sleep)
            continue

        cleaned.sort(key=lambda x: x["date"])
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["date", "marketCap"])
            w.writeheader()
            w.writerows(cleaned)
        written += 1
        time.sleep(args.sleep)

    print(f"Done. total symbols={total} written={written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
