#!/usr/bin/env python3
"""
Download FMP earnings calendar for a date range and write a single CSV.

Designed for both:
1) incremental refresh of recent window
2) historical backfill (e.g., 2010 -> today)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import json

import pandas as pd

API_BASE = "https://financialmodelingprep.com/stable"


def _iter_windows(start: pd.Timestamp, end: pd.Timestamp, days_per_window: int) -> Iterable[tuple[pd.Timestamp, pd.Timestamp]]:
    cur = start
    step = pd.Timedelta(days=max(1, int(days_per_window)))
    while cur <= end:
        nxt = min(cur + step - pd.Timedelta(days=1), end)
        yield cur, nxt
        cur = nxt + pd.Timedelta(days=1)


def _fetch_window(api_key: str, ws: pd.Timestamp, we: pd.Timestamp, timeout: int) -> list[dict]:
    params = {
        "from": ws.strftime("%Y-%m-%d"),
        "to": we.strftime("%Y-%m-%d"),
        "apikey": api_key,
    }
    url = f"{API_BASE}/earnings-calendar?{urlencode(params)}"
    try:
        with urlopen(url, timeout=timeout) as resp:
            code = int(getattr(resp, "status", 200))
            body = resp.read().decode("utf-8", errors="ignore")
    except HTTPError:
        return []
    except URLError:
        return []
    except Exception:
        return []
    if code != 200:
        return []
    try:
        payload = json.loads(body)
    except Exception:
        return []
    if isinstance(payload, dict):
        payload = payload.get("historical", [])
    if not isinstance(payload, list):
        return []
    out: list[dict] = []
    for rec in payload:
        if isinstance(rec, dict):
            out.append(rec)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default="", help="FMP API key (fallback: env FMP_API_KEY)")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--out", required=True, help="Output CSV path")
    parser.add_argument("--window-days", type=int, default=45, help="Window size per request")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds")
    parser.add_argument("--retries", type=int, default=3, help="Retries per window")
    parser.add_argument("--append-existing", action="store_true", help="Merge with existing CSV if present")
    args = parser.parse_args()

    api_key = args.api_key.strip()
    if not api_key:
        import os
        api_key = os.environ.get("FMP_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("FMP API key is required via --api-key or FMP_API_KEY")

    start = pd.Timestamp(args.start).normalize()
    end = pd.Timestamp(args.end).normalize()
    if end < start:
        raise SystemExit("--end must be >= --start")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    windows = list(_iter_windows(start, end, args.window_days))
    for i, (ws, we) in enumerate(windows, 1):
        payload: list[dict] = []
        for attempt in range(max(1, int(args.retries))):
            payload = _fetch_window(api_key, ws, we, timeout=int(args.timeout))
            if payload:
                break
            if attempt + 1 < int(args.retries):
                import time
                time.sleep(1.0 + attempt)
        rows.extend(payload)
        print(
            f"[earnings-calendar] window {i}/{len(windows)} "
            f"{ws.date()}..{we.date()} rows={len(payload)} total={len(rows)}",
            flush=True,
        )

    df = pd.DataFrame(rows)
    if len(df) == 0:
        if args.append_existing and out_path.exists():
            print(f"[earnings-calendar] fetched 0 rows; keep existing: {out_path}", flush=True)
            return
        pd.DataFrame(columns=["symbol", "date"]).to_csv(out_path, index=False)
        print(f"[earnings-calendar] wrote empty file: {out_path}", flush=True)
        return

    if "symbol" not in df.columns or "date" not in df.columns:
        raise SystemExit("Unexpected payload: required columns 'symbol' and 'date' not found")

    if args.append_existing and out_path.exists():
        try:
            old = pd.read_csv(out_path)
            if len(old) > 0:
                df = pd.concat([old, df], ignore_index=True)
        except Exception:
            pass

    df["symbol"] = df["symbol"].astype(str)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["symbol", "date"])
    df = df.sort_values(["date", "symbol"]).drop_duplicates(subset=["symbol", "date"], keep="last")
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df.to_csv(out_path, index=False)
    print(f"[earnings-calendar] wrote rows={len(df)} -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
