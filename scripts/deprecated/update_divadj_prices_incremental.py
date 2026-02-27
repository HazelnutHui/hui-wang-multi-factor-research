#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import requests


API_BASE = "https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted"
ROOT = Path(__file__).resolve().parents[1]
ACTIVE_SRC = ROOT / "data" / "prices"
DELISTED_SRC = ROOT / "data" / "prices_delisted"
ACTIVE_OUT = ROOT / "data" / "prices_divadj"
DELISTED_OUT = ROOT / "data" / "prices_delisted_divadj"


def load_symbols(dir_path: Path) -> list[str]:
    if not dir_path.exists():
        return []
    return sorted([p.stem for p in dir_path.glob("*.pkl")])


def fetch_symbol(session: requests.Session, api_key: str, symbol: str, start_date: str, end_date: str):
    params = {
        "symbol": symbol,
        "from": start_date,
        "to": end_date,
        "apikey": api_key,
    }
    try:
        r = session.get(API_BASE, params=params, timeout=30)
    except requests.RequestException:
        return "request_error", None
    if r.status_code == 429:
        return "rate_limit", None
    if r.status_code != 200:
        return f"http_{r.status_code}", None
    try:
        payload = r.json()
    except json.JSONDecodeError:
        return "bad_json", None
    if isinstance(payload, dict):
        payload = payload.get("historical", [])
    if not isinstance(payload, list) or len(payload) == 0:
        return "empty", None
    df = pd.DataFrame(payload)
    if "date" not in df.columns:
        return "no_date", None
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return "ok", df


def fetch_symbol_with_resolve(api_key: str, symbol: str, start_date: str, end_date: str, resolve_ip: str):
    params = {
        "symbol": symbol,
        "from": start_date,
        "to": end_date,
        "apikey": api_key,
    }
    url = f"{API_BASE}?{urlencode(params)}"
    cmd = [
        "curl",
        "-sS",
        "--max-time",
        "25",
        "--retry",
        "2",
        "--retry-all-errors",
        "--resolve",
        f"financialmodelingprep.com:443:{resolve_ip}",
        url,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return "curl_error", None
    raw = p.stdout.strip()
    if not raw:
        return "empty", None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return "bad_json", None
    if isinstance(payload, dict):
        payload = payload.get("historical", [])
    if not isinstance(payload, list) or len(payload) == 0:
        return "empty", None
    df = pd.DataFrame(payload)
    if "date" not in df.columns:
        return "no_date", None
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return "ok", df


def incremental_update(
    session: requests.Session,
    api_key: str,
    symbol: str,
    out_path: Path,
    end_date: str,
    resolve_ips: list[str],
):
    if out_path.exists():
        try:
            old = pd.read_pickle(out_path)
        except Exception:
            old = pd.DataFrame()
    else:
        old = pd.DataFrame()
    if "date" in old.columns and len(old) > 0:
        d = pd.to_datetime(old["date"], errors="coerce").max()
        if pd.notna(d):
            start = (d.date() + timedelta(days=1)).isoformat()
        else:
            start = "2010-01-01"
    else:
        start = "2010-01-01"
    if start > end_date:
        return "up_to_date"

    if resolve_ips:
        status, new = "resolve_failed", None
        for ip in resolve_ips:
            s2, n2 = fetch_symbol_with_resolve(api_key, symbol, start, end_date, ip)
            if s2 == "ok":
                status, new = s2, n2
                break
    else:
        status, new = fetch_symbol(session, api_key, symbol, start, end_date)
    if status != "ok":
        return status

    merged = pd.concat([old, new], ignore_index=True)
    merged = merged.dropna(subset=["date"]).drop_duplicates(subset=["date"], keep="last")
    merged = merged.sort_values("date").reset_index(drop=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_pickle(out_path)
    return "updated"


def main() -> int:
    parser = argparse.ArgumentParser(description="Incremental update for dividend-adjusted prices.")
    parser.add_argument("--scope", choices=["active", "delisted", "both"], default="active")
    parser.add_argument("--sleep", type=float, default=0.15)
    parser.add_argument("--max-symbols", type=int, default=0, help="0 means no limit")
    parser.add_argument(
        "--resolve-ip",
        default="",
        help="Comma-separated IPs for curl --resolve fallback, e.g. 34.194.189.88,52.202.201.64",
    )
    args = parser.parse_args()

    api_key = os.getenv("FMP_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("FMP_API_KEY not set")

    end_date = date.today().isoformat()
    jobs: list[tuple[str, Path]] = []
    if args.scope in ("active", "both"):
        jobs.extend([(s, ACTIVE_OUT / f"{s}.pkl") for s in load_symbols(ACTIVE_SRC)])
    if args.scope in ("delisted", "both"):
        jobs.extend([(s, DELISTED_OUT / f"{s}.pkl") for s in load_symbols(DELISTED_SRC)])
    if args.max_symbols and args.max_symbols > 0:
        jobs = jobs[: args.max_symbols]

    session = requests.Session()
    resolve_ips = [x.strip() for x in str(args.resolve_ip).split(",") if x.strip()]
    updated = 0
    up_to_date = 0
    errors = 0

    for i, (sym, out_path) in enumerate(jobs, 1):
        status = incremental_update(session, api_key, sym, out_path, end_date, resolve_ips)
        if status == "updated":
            updated += 1
        elif status == "up_to_date":
            up_to_date += 1
        elif status == "rate_limit":
            errors += 1
            time.sleep(20)
            continue
        else:
            errors += 1
        if i % 200 == 0:
            print(f"progress {i}/{len(jobs)} updated={updated} up_to_date={up_to_date} errors={errors}", flush=True)
        time.sleep(args.sleep)

    print(f"done updated={updated} up_to_date={up_to_date} errors={errors}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
