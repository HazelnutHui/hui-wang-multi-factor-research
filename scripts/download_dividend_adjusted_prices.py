#!/usr/bin/env python3
import os
import time
import json
import random
from pathlib import Path
import pandas as pd
import requests

API_BASE = "https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted"
START_DATE = "2010-01-01"
END_DATE = "2026-01-28"

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_SRC = ROOT / "data" / "prices"
DELISTED_SRC = ROOT / "data" / "prices_delisted"
ACTIVE_OUT = ROOT / "data" / "prices_divadj"
DELISTED_OUT = ROOT / "data" / "prices_delisted_divadj"
LOG_PATH = ROOT / "logs" / f"divadj_download_{time.strftime('%Y-%m-%d_%H%M%S')}.log"

API_KEY = os.getenv("FMP_API_KEY")
if not API_KEY:
    raise SystemExit("FMP_API_KEY not set")

ACTIVE_OUT.mkdir(parents=True, exist_ok=True)
DELISTED_OUT.mkdir(parents=True, exist_ok=True)
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


def fetch_symbol(symbol: str):
    params = {
        "symbol": symbol,
        "from": START_DATE,
        "to": END_DATE,
        "apikey": API_KEY,
    }
    r = session.get(API_BASE, params=params, timeout=30)
    if r.status_code == 429:
        return "rate_limit", None
    if r.status_code != 200:
        return f"http_{r.status_code}", None
    try:
        data = r.json()
    except json.JSONDecodeError:
        return "bad_json", None

    # API may return list or dict with historical
    if isinstance(data, dict):
        data = data.get("historical", [])
    if not isinstance(data, list) or len(data) == 0:
        return "empty", None

    df = pd.DataFrame(data)
    if "date" not in df.columns:
        return "no_date", None

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return "ok", df


def save_df(df: pd.DataFrame, out_path: Path):
    df.to_pickle(out_path)


def main():
    active_syms = load_symbols(ACTIVE_SRC)
    delisted_syms = load_symbols(DELISTED_SRC)

    log(f"Active symbols: {len(active_syms)}")
    log(f"Delisted symbols: {len(delisted_syms)}")

    jobs = [(s, ACTIVE_OUT / f"{s}.pkl") for s in active_syms] + \
           [(s, DELISTED_OUT / f"{s}.pkl") for s in delisted_syms]

    random.shuffle(jobs)

    total = len(jobs)
    ok = 0
    skipped = 0
    errors = 0

    for i, (sym, out_path) in enumerate(jobs, 1):
        if out_path.exists():
            skipped += 1
            if i % 200 == 0:
                log(f"Progress {i}/{total} ok={ok} skipped={skipped} errors={errors}")
            continue

        status, df = fetch_symbol(sym)
        if status == "ok":
            save_df(df, out_path)
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
