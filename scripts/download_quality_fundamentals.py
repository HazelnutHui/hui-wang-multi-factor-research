#!/usr/bin/env python3
import argparse
import os
import time
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import pandas as pd

API_BASE = "https://financialmodelingprep.com/stable"
START_DATE = "2010-01-01"
END_DATE = date.today().isoformat()
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

write_lock = threading.Lock()


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
    url = f"{API_BASE}/{endpoint}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=30) as resp:
            code = int(getattr(resp, "status", 200))
            body = resp.read().decode("utf-8", errors="ignore")
    except HTTPError as e:
        if int(e.code) == 429:
            return "rate_limit", None
        return f"http_{int(e.code)}", None
    except URLError:
        return "network_error", None
    except Exception:
        return "network_error", None
    if code == 429:
        return "rate_limit", None
    if code != 200:
        return f"http_{code}", None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return "bad_json", None
    if isinstance(data, dict):
        data = data.get("historical", [])
    if not isinstance(data, list) or len(data) == 0:
        return "empty", None
    return "ok", data


def _pick_first_series(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    for col in candidates:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            if s.notna().any():
                return s
    return pd.Series([None] * len(df), index=df.index)


def build_quality_frame(symbol: str, start_date: str, end_date: str):
    status, ratios = fetch_json("ratios", symbol)
    if status != "ok":
        return status, None

    status, inc = fetch_json("income-statement", symbol)
    if status != "ok":
        return status, None

    status, bs = fetch_json("balance-sheet-statement", symbol)
    if status != "ok":
        return status, None

    status, cf = fetch_json("cash-flow-statement", symbol)
    if status != "ok":
        return status, None

    ratios_df = pd.DataFrame(ratios)
    inc_df = pd.DataFrame(inc)
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
    inc_df = prep(inc_df)
    bs_df = prep(bs_df)
    cf_df = prep(cf_df)
    if ratios_df is None or inc_df is None or bs_df is None or cf_df is None:
        return "no_date", None

    # Merge on period end date
    df = ratios_df.merge(inc_df, on='date', suffixes=('', '_inc'))
    df = df.merge(bs_df, on='date', suffixes=('', '_bs'))
    df = df.merge(cf_df, on='date', suffixes=('', '_cf'))
    if len(df) == 0:
        return "empty_merge", None

    # Compute quality metrics
    df = df.sort_values('date').reset_index(drop=True)
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    if len(df) == 0:
        return "empty_date_range", None
    # FMP field names can vary by endpoint/version; use first non-empty alias.
    df['roe'] = _pick_first_series(df, [
        'returnOnEquity',
        'returnOnEquityTTM',
        'roe',
    ])
    df['roa'] = _pick_first_series(df, [
        'returnOnAssets',
        'returnOnAssetsTTM',
        'roa',
    ])
    df['gross_margin'] = _pick_first_series(df, [
        'grossProfitMargin',
        'grossMargin',
        'gross_margin',
    ])
    df['debt_to_equity'] = _pick_first_series(df, [
        'debtToEquityRatio',
        'debtToEquity',
        'debt_to_equity',
    ])

    # Fallback derivation when ratio endpoint does not expose ROE/ROA.
    ni = _pick_first_series(df, ['netIncome', 'netIncome_inc'])
    equity = _pick_first_series(df, ['totalStockholdersEquity', 'totalEquity', 'totalStockholdersEquity_bs', 'totalEquity_bs'])
    assets = _pick_first_series(df, ['totalAssets', 'totalAssets_bs'])
    if 'roe' in df.columns:
        miss_roe = pd.to_numeric(df['roe'], errors='coerce').isna()
        if miss_roe.any():
            alt_roe = (ni / equity.replace(0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
            df.loc[miss_roe, 'roe'] = alt_roe.loc[miss_roe]
    if 'roa' in df.columns:
        miss_roa = pd.to_numeric(df['roa'], errors='coerce').isna()
        if miss_roa.any():
            alt_roa = (ni / assets.replace(0, pd.NA)).replace([float("inf"), float("-inf")], pd.NA)
            df.loc[miss_roa, 'roa'] = alt_roa.loc[miss_roa]

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
    parser.add_argument("--start-date", default=START_DATE, help="YYYY-MM-DD")
    parser.add_argument("--end-date", default=END_DATE, help="YYYY-MM-DD")
    parser.add_argument("--sleep", type=float, default=0.25, help="Sleep between symbols")
    parser.add_argument("--workers", type=int, default=8, help="Parallel workers")
    args = parser.parse_args()

    active_syms = load_symbols(ACTIVE_SRC)
    delisted_syms = load_symbols(DELISTED_SRC)
    symbols = active_syms + delisted_syms

    log(f"Active symbols: {len(active_syms)}")
    log(f"Delisted symbols: {len(delisted_syms)}")
    log(
        f"Date range: {args.start_date} -> {args.end_date} | overwrite={int(args.overwrite)}"
    )

    random.shuffle(symbols)

    total = len(symbols)
    ok = 0
    skipped = 0
    errors = 0

    def task(sym: str):
        out_path = OUT_DIR / f"{sym}.pkl"
        if out_path.exists() and not args.overwrite:
            return ("skipped", sym, None)

        status, df = build_quality_frame(sym, args.start_date, args.end_date)
        if status == "ok":
            with write_lock:
                df.to_pickle(out_path)
            if args.sleep > 0:
                time.sleep(args.sleep)
            return ("ok", sym, None)
        return ("error", sym, status)

    workers = max(1, int(args.workers))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(task, sym) for sym in symbols]
        for i, fut in enumerate(as_completed(futs), 1):
            state, sym, detail = fut.result()
            if state == "ok":
                ok += 1
            elif state == "skipped":
                skipped += 1
            else:
                errors += 1
                log(f"Error {detail} for {sym}")
                if detail == "rate_limit":
                    log("Rate limit observed; consider lowering --workers or increasing --sleep.")

            if i % 200 == 0 or i == total:
                log(f"Progress {i}/{total} ok={ok} skipped={skipped} errors={errors}")

    log(f"Done. ok={ok} skipped={skipped} errors={errors}")

if __name__ == "__main__":
    main()
