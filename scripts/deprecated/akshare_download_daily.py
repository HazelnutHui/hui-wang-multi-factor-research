#!/usr/bin/env python3
"""
Download A-share daily price data via AKShare and save as pickle per symbol.
"""

import argparse
import time
from pathlib import Path
import sys
import pandas as pd


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols-csv", required=True, help="CSV from akshare_stock_list.py")
    parser.add_argument("--out-dir", default="/Users/hui/quant_score/v4/data/cn/prices")
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    try:
        import akshare as ak
    except Exception as exc:
        print("Missing dependency: akshare. Install with `pip install akshare`.", file=sys.stderr)
        return 1

    symbols_df = pd.read_csv(args.symbols_csv)
    if "代码" in symbols_df.columns:
        symbols = symbols_df["代码"].astype(str).tolist()
    elif "symbol" in symbols_df.columns:
        symbols = symbols_df["symbol"].astype(str).tolist()
    else:
        print("Symbols CSV must include column `代码` or `symbol`.", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    total = len(symbols)
    ok = 0
    skipped = 0
    errors = 0

    for i, sym in enumerate(symbols, 1):
        out_path = out_dir / f"{sym}.pkl"
        if out_path.exists() and not args.overwrite:
            skipped += 1
            continue

        try:
            df = ak.stock_zh_a_hist(symbol=sym, start_date=args.start, end_date=args.end, adjust="qfq")
        except Exception:
            errors += 1
            continue

        if df is None or len(df) == 0:
            errors += 1
            continue

        # Normalize columns
        rename_map = {
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
        }
        df = df.rename(columns=rename_map)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        df["symbol"] = sym

        df = df[["symbol", "date", "open", "high", "low", "close", "volume"]]
        df.to_pickle(out_path)
        ok += 1

        if i % 200 == 0:
            print(f"Progress {i}/{total} ok={ok} skipped={skipped} errors={errors}")
        time.sleep(args.sleep)

    print(f"Done. ok={ok} skipped={skipped} errors={errors}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
