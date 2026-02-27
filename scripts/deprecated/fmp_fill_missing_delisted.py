#!/usr/bin/env python3
import os
import time
import json
import random
from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DELISTED_CSV = ROOT / "data" / "delisted_companies_2010_2026.csv"
RAW_DIR = ROOT / "data" / "prices_delisted"
ADJ_DIR = ROOT / "data" / "prices_delisted_divadj"
LOG_PATH = ROOT / "logs" / f"fmp_fill_delisted_{time.strftime('%Y-%m-%d_%H%M%S')}.log"

RAW_API = "https://financialmodelingprep.com/stable/historical-price-eod"
ADJ_API = "https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted"
START_DATE = "2010-01-01"
END_DATE = "2026-01-28"


def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")


def load_missing_symbols(only_us: bool, only_adj: bool):
    if not DELISTED_CSV.exists():
        return []
    df = pd.read_csv(DELISTED_CSV)
    df = df.dropna(subset=["symbol"])
    if only_us and "exchange" in df.columns:
        df = df[df["exchange"].isin(["NASDAQ", "NYSE", "AMEX", "OTC"])]
    csv_syms = set(df["symbol"].astype(str))
    if only_adj:
        existing = set([p.stem for p in ADJ_DIR.glob("*.pkl")])
    else:
        existing = set([p.stem for p in RAW_DIR.glob("*.pkl")])
    missing = sorted(list(csv_syms - existing))
    return missing


def fetch(session, api_base, symbol, api_key):
    params = {"symbol": symbol, "from": START_DATE, "to": END_DATE, "apikey": api_key}
    r = session.get(api_base, params=params, timeout=30)
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
    df = pd.DataFrame(data)
    if "date" not in df.columns:
        return "no_date", None
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return "ok", df


def save_df(df, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(path)


def main():
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        raise SystemExit("FMP_API_KEY not set")

    only_us = True
    only_adj = True
    missing = load_missing_symbols(only_us=only_us, only_adj=only_adj)

    # If we already have a curated missing list, prefer it
    if only_us and only_adj:
        curated = ROOT / "data" / "fmp" / "missing_delisted_adj_us.txt"
        if curated.exists():
            curated_syms = [s.strip() for s in curated.read_text().splitlines() if s.strip()]
            if curated_syms:
                missing = curated_syms
    scope = "US-only" if only_us else "all"
    mode = "adj-only" if only_adj else "raw+adj"
    log(f"Missing delisted symbols ({scope}, {mode}): {len(missing)}")
    if not missing:
        log("Nothing to do")
        return

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ADJ_DIR.mkdir(parents=True, exist_ok=True)

    random.shuffle(missing)
    session = requests.Session()

    ok_raw = ok_adj = 0
    err_raw = err_adj = 0
    skipped = 0

    for i, sym in enumerate(missing, 1):
        raw_path = RAW_DIR / f"{sym}.pkl"
        adj_path = ADJ_DIR / f"{sym}.pkl"

        if not only_adj:
            if raw_path.exists() and adj_path.exists():
                skipped += 1
                continue

            if not raw_path.exists():
                status, df = fetch(session, RAW_API, sym, api_key)
                if status == "ok":
                    save_df(df, raw_path)
                    ok_raw += 1
                elif status == "rate_limit":
                    err_raw += 1
                    log(f"Rate limit raw {sym} -> sleep 60s")
                    time.sleep(60)
                    continue
                else:
                    err_raw += 1
                    log(f"Raw error {status} for {sym}")

        if not adj_path.exists():
            status, df = fetch(session, ADJ_API, sym, api_key)
            if status == "ok":
                save_df(df, adj_path)
                ok_adj += 1
            elif status == "rate_limit":
                err_adj += 1
                log(f"Rate limit adj {sym} -> sleep 60s")
                time.sleep(60)
                continue
            else:
                err_adj += 1
                log(f"Adj error {status} for {sym}")

        time.sleep(0.25)

        if i % 50 == 0:
            log(f"Progress {i}/{len(missing)} ok_raw={ok_raw} ok_adj={ok_adj} skipped={skipped} err_raw={err_raw} err_adj={err_adj}")

    log(f"Done. ok_raw={ok_raw} ok_adj={ok_adj} skipped={skipped} err_raw={err_raw} err_adj={err_adj}")


if __name__ == "__main__":
    main()
