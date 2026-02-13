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
OUT_DIR = ROOT / "data" / "fmp" / "ratios" / "quality"
LOG_PATH = ROOT / "logs" / f"quality_fund_download_{time.strftime('%Y-%m-%d_%H%M%S')}.log"

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


def build_quality_frame(symbol: str):
    status, ratios = fetch_json("ratios", symbol)
    if status != "ok":
        return status, None

    status, bs = fetch_json("balance-sheet-statement", symbol)
    if status != "ok":
        return status, None

    status, cf = fetch_json("cash-flow-statement", symbol)
    if status != "ok":
        return status, None

    ratios_df = pd.DataFrame(ratios)
    bs_df = pd.DataFrame(bs)
    cf_df = pd.DataFrame(cf)

    def prep(df: pd.DataFrame) -> pd.DataFrame:
        if 'date' not in df.columns:
            return None
        out = df.copy()
        out['date'] = pd.to_datetime(out['date'])
        # availability date for PIT (acceptedDate > fillingDate > date)
        avail = None
        if 'acceptedDate' in out.columns:
            avail = pd.to_datetime(out['acceptedDate'], errors='coerce')
        if avail is None or avail.isna().all():
            if 'fillingDate' in out.columns:
                avail = pd.to_datetime(out['fillingDate'], errors='coerce')
        if avail is None:
            avail = out['date']
        out['available_date'] = avail
        return out

    ratios_df = prep(ratios_df)
    bs_df = prep(bs_df)
    cf_df = prep(cf_df)
    if ratios_df is None or bs_df is None or cf_df is None:
        return "no_date", None

    # Merge on period end date
    df = ratios_df.merge(bs_df, on='date', suffixes=('', '_bs'))
    df = df.merge(cf_df, on='date', suffixes=('', '_cf'))
    if len(df) == 0:
        return "empty_merge", None

    # Compute quality metrics
    df = df.sort_values('date').reset_index(drop=True)
    df = df[(df['date'] >= START_DATE) & (df['date'] <= END_DATE)]
    if len(df) == 0:
        return "empty_date_range", None
    df['roe'] = df.get('returnOnEquity')
    df['roa'] = df.get('returnOnAssets')
    df['gross_margin'] = df.get('grossProfitMargin')
    df['debt_to_equity'] = df.get('debtToEquityRatio')

    # CFO/Assets
    if 'operatingCashFlow' in df.columns and 'totalAssets' in df.columns:
        df['cfo_to_assets'] = df['operatingCashFlow'] / df['totalAssets']
    else:
        df['cfo_to_assets'] = None

    # PIT availability: latest date among components
    avail_cols = [c for c in df.columns if c.startswith('available_date')]
    if avail_cols:
        df['available_date'] = df[avail_cols].max(axis=1)
    else:
        df['available_date'] = df['date']

    # Keep minimal columns
    keep = [
        'date',
        'available_date',
        'roe',
        'roa',
        'gross_margin',
        'cfo_to_assets',
        'debt_to_equity',
    ]
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

        status, df = build_quality_frame(sym)
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
