#!/usr/bin/env python3
"""
Download A-share stock list via AKShare and save as CSV.
"""

import argparse
from pathlib import Path
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="/Users/hui/quant_score/v4/data/cn/stock_list.csv",
    )
    args = parser.parse_args()

    try:
        import akshare as ak
    except Exception as exc:
        print("Missing dependency: akshare. Install with `pip install akshare`.", file=sys.stderr)
        return 1

    df = None
    last_err = None
    for attempt in range(5):
        try:
            df = ak.stock_zh_a_spot_em()
            break
        except Exception as exc:
            last_err = exc
            time.sleep(1.5 * (attempt + 1))

    if df is None or len(df) == 0:
        # Fallback to legacy interface
        try:
            df = ak.stock_zh_a_spot()
        except Exception as exc:
            last_err = exc

    if df is None or len(df) == 0:
        print(f"Empty stock list returned by AKShare. last_err={last_err}", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
