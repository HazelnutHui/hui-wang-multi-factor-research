#!/usr/bin/env python3
import argparse
import os
import time
import json
import random
from pathlib import Path
import pandas as pd
import requests

API_BASE = "https://financialmodelingprep.com/stable"
START_DATE = "2010-01-01"
END_DATE = "2026-01-28"
PERIOD = "quarter"
LIMIT = 400

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_SRC = ROOT / "data" / "prices"
DELISTED_SRC = ROOT / "data" / "prices_delisted"
OUT_DIR = ROOT / "data" / "fmp" / "ratios" / "value"
LOG_PATH = ROOT / "logs" / f"value_fund_download_{time.strftime('%Y-%m-%d_%H%M%S')}.log"

API_KEY = os.getenv("FMP_API_KEY")
if not API_KEY:
    raise SystemExit("FMP_API_KEY not set")

OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

session = requests.Session()


def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")


def load_symbols(dir_path: Path):
    if not dir_path.exists():
        return []
    return sorted([p.stem for p in dir_path.glob("*.pkl")])


def fetch_json(endpoint: str, symbol: str):
    params = {
        "symbol": symbol,
        "apikey": API_KEY,
        "period": PERIOD,
        "limit": LIMIT,
    }
    r = session.get(f"{API_BASE}/{endpoint}", params=params, timeout=30)
    if r.status_code == 429:
        return "rate_limit", None
    if r.status_code != 200:
        return f"http_{r.status_code}", None
    try:
        data = r.json()
    except json.JSONDecodeError:
        return "bad_json", None
    if isinstance(data, dict):
        data = data.get("historical", [])
    if not isinstance(data, list) or len(data) == 0:
        return "empty", None
    return "ok", data


def build_value_frame(symbol: str):
    status, ratios = fetch_json("ratios", symbol)
    if status != "ok":
        return status, None

    df = pd.DataFrame(ratios)
    if 'date' not in df.columns:
        return "no_date", None
    df['date'] = pd.to_datetime(df['date'])
    # availability date for PIT (acceptedDate > fillingDate > date)
    avail = None
    if 'acceptedDate' in df.columns:
        avail = pd.to_datetime(df['acceptedDate'], errors='coerce')
    if avail is None or avail.isna().all():
        if 'fillingDate' in df.columns:
            avail = pd.to_datetime(df['fillingDate'], errors='coerce')
    if avail is None:
        avail = df['date']
    df['available_date'] = avail
    df = df.sort_values('date').reset_index(drop=True)
    df = df[(df['date'] >= START_DATE) & (df['date'] <= END_DATE)]
    if len(df) == 0:
        return "empty_date_range", None

    # Build yields (support both TTM and non-TTM column names)
    def _pick_series(cols):
        for c in cols:
            if c in df.columns and df[c].notna().any():
                return df[c]
        return None

    def safe_inv(x):
        try:
            x = float(x)
        except Exception:
            return None
        if x is None or x == 0:
            return None
        return 1.0 / x

    pe_series = _pick_series([
        'priceToEarningsRatioTTM',
        'priceEarningsRatioTTM',
        'priceEarningsRatio',
        'priceToEarningsRatio',
    ])
    fcf_series = _pick_series([
        'priceToFreeCashFlowRatioTTM',
        'priceToFreeCashFlowRatio',
    ])
    ev_series = _pick_series([
        'enterpriseValueMultipleTTM',
        'enterpriseValueMultiple',
    ])

    df['earnings_yield'] = pe_series.apply(safe_inv) if pe_series is not None else None
    df['fcf_yield'] = fcf_series.apply(safe_inv) if fcf_series is not None else None
    df['ev_ebitda_yield'] = ev_series.apply(safe_inv) if ev_series is not None else None

    keep = ['date', 'available_date', 'earnings_yield', 'fcf_yield', 'ev_ebitda_yield']
    df = df[keep]
    return "ok", df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    active_syms = load_symbols(ACTIVE_SRC)
    delisted_syms = load_symbols(DELISTED_SRC)
    symbols = active_syms + delisted_syms

    log(f"Active symbols: {len(active_syms)}")
    log(f"Delisted symbols: {len(delisted_syms)}")

    random.shuffle(symbols)

    total = len(symbols)
    ok = 0
    skipped = 0
    errors = 0

    for i, sym in enumerate(symbols, 1):
        out_path = OUT_DIR / f"{sym}.pkl"
        if out_path.exists() and not args.overwrite:
            skipped += 1
            if i % 200 == 0:
                log(f"Progress {i}/{total} ok={ok} skipped={skipped} errors={errors}")
            continue

        status, df = build_value_frame(sym)
        if status == "ok":
            df.to_pickle(out_path)
            ok += 1
        elif status == "rate_limit":
            errors += 1
            log(f"Rate limit hit at {sym}. Sleeping 60s...")
            time.sleep(60)
            continue
        else:
            errors += 1
            log(f"Error {status} for {sym}")

        time.sleep(0.25)

        if i % 200 == 0:
            log(f"Progress {i}/{total} ok={ok} skipped={skipped} errors={errors}")

    log(f"Done. ok={ok} skipped={skipped} errors={errors}")

if __name__ == "__main__":
    main()
