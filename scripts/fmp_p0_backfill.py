#!/usr/bin/env python3
"""Backfill missing P0 FMP datasets for batchA100 logic100.

Network required. Designed to run on workstation with outbound access.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FMP = DATA / "fmp"
BASE = "https://financialmodelingprep.com/stable"


def get_api_key() -> str:
    key = os.environ.get("FMP_API_KEY", "").strip()
    if key:
        return key
    # fallback for local legacy setup (do not print key)
    p = ROOT / "download_owner_earnings.py"
    if p.exists():
        m = re.search(r'API_KEY\s*=\s*"([^"]+)"', p.read_text(encoding="utf-8", errors="ignore"))
        if m:
            return m.group(1)
    raise SystemExit("FMP_API_KEY not set and no fallback key found")


def universe_symbols() -> list[str]:
    syms: set[str] = set()
    for d in [DATA / "prices", DATA / "prices_delisted"]:
        if not d.exists():
            continue
        syms.update(p.stem for p in d.glob("*.pkl"))
    return sorted(syms)


def fetch_json(session: requests.Session, endpoint: str, params: dict[str, Any], retries: int = 3) -> list[dict[str, Any]]:
    for attempt in range(retries):
        try:
            r = session.get(f"{BASE}/{endpoint}", params=params, timeout=30)
        except requests.RequestException:
            if attempt + 1 == retries:
                return []
            time.sleep(1.0 * (attempt + 1))
            continue
        if r.status_code == 429:
            time.sleep(2.0 * (attempt + 1))
            continue
        if r.status_code != 200:
            return []
        try:
            data = r.json()
        except Exception:
            return []
        if isinstance(data, dict):
            if "historical" in data and isinstance(data["historical"], list):
                data = data["historical"]
            else:
                data = [data]
        if not isinstance(data, list):
            return []
        return [x for x in data if isinstance(x, dict)]
    return []


def read_done_symbols(jsonl_path: Path) -> set[str]:
    done: set[str] = set()
    if not jsonl_path.exists():
        return done
    with jsonl_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            sym = obj.get("symbol")
            if isinstance(sym, str) and sym:
                done.add(sym)
    return done


def run_symbol_endpoint(symbols: list[str], endpoint: str, out_path: Path, key: str, workers: int, min_rows: int = 1, extra_params: dict[str, Any] | None = None) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = read_done_symbols(out_path)
    todo = [s for s in symbols if s not in done]
    lock = threading.Lock()

    print(f"[{endpoint}] done={len(done)} todo={len(todo)} -> {out_path}")
    if not todo:
        return

    def task(sym: str) -> tuple[str, int]:
        sess = requests.Session()
        params: dict[str, Any] = {"symbol": sym, "apikey": key}
        if extra_params:
            params.update(extra_params)
        payload = fetch_json(sess, endpoint, params)
        if len(payload) < min_rows:
            return sym, 0
        line = json.dumps({"symbol": sym, "payload": payload}, ensure_ascii=True)
        with lock:
            with out_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        return sym, len(payload)

    ok = 0
    empty = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(task, s) for s in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            _, n = fut.result()
            if n > 0:
                ok += 1
            else:
                empty += 1
            if i % 200 == 0 or i == len(todo):
                print(f"[{endpoint}] progress {i}/{len(todo)} ok={ok} empty={empty}")


def ensure_earnings_surprises(key: str, start_year: int, end_year: int) -> None:
    earnings_dir = FMP / "earnings"
    earnings_dir.mkdir(parents=True, exist_ok=True)
    sess = requests.Session()
    for y in range(start_year, end_year + 1):
        out = earnings_dir / f"earnings_surprises_{y}.csv"
        if out.exists() and out.stat().st_size > 0:
            continue
        payload = fetch_json(sess, "earnings-surprises-bulk", {"year": y, "apikey": key})
        if not payload:
            print(f"[earnings-surprises-bulk] year={y} empty")
            continue
        cols: list[str] = sorted({k for row in payload for k in row.keys()})
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for row in payload:
                w.writerow(row)
        print(f"[earnings-surprises-bulk] year={y} rows={len(payload)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--start-year", type=int, default=2010)
    parser.add_argument("--end-year", type=int, default=date.today().year)
    parser.add_argument("--skip-ratios", action="store_true")
    parser.add_argument("--skip-statements", action="store_true")
    parser.add_argument("--skip-institutional", action="store_true")
    parser.add_argument("--skip-owner-earnings", action="store_true")
    parser.add_argument("--skip-earnings-surprises", action="store_true")
    args = parser.parse_args()

    key = get_api_key()
    syms = universe_symbols()
    print(f"universe={len(syms)} workers={args.workers}")

    # ratios coverage fill (reusing existing scripts) is optional and can be long.
    if not args.skip_ratios:
        print("[ratios] running value+quality gap fill via existing scripts")
        rc1 = os.system(f"cd {ROOT} && FMP_API_KEY='{key}' python3 scripts/download_value_fundamentals.py")
        rc2 = os.system(f"cd {ROOT} && FMP_API_KEY='{key}' python3 scripts/download_quality_fundamentals.py")
        print(f"[ratios] done rc_value={rc1} rc_quality={rc2}")

    if not args.skip_earnings_surprises:
        ensure_earnings_surprises(key, args.start_year, args.end_year)

    if not args.skip_owner_earnings:
        run_symbol_endpoint(
            syms,
            endpoint="owner-earnings",
            out_path=FMP / "owner_earnings" / "owner-earnings.jsonl",
            key=key,
            workers=args.workers,
            min_rows=1,
        )

    if not args.skip_institutional:
        run_symbol_endpoint(
            syms,
            endpoint="institutional-ownership/symbol-positions-summary",
            out_path=FMP / "institutional" / "institutional-ownership__symbol-positions-summary.jsonl",
            key=key,
            workers=args.workers,
            min_rows=1,
        )

    if not args.skip_statements:
        run_symbol_endpoint(
            syms,
            endpoint="income-statement",
            out_path=FMP / "statements" / "income-statement.jsonl",
            key=key,
            workers=args.workers,
            min_rows=1,
            extra_params={"period": "quarter", "limit": 120},
        )
        run_symbol_endpoint(
            syms,
            endpoint="balance-sheet-statement",
            out_path=FMP / "statements" / "balance-sheet-statement.jsonl",
            key=key,
            workers=args.workers,
            min_rows=1,
            extra_params={"period": "quarter", "limit": 120},
        )
        run_symbol_endpoint(
            syms,
            endpoint="cash-flow-statement",
            out_path=FMP / "statements" / "cash-flow-statement.jsonl",
            key=key,
            workers=args.workers,
            min_rows=1,
            extra_params={"period": "quarter", "limit": 120},
        )
        # Optional TTM endpoint; keep best-effort.
        run_symbol_endpoint(
            syms,
            endpoint="income-statement-ttm",
            out_path=FMP / "statements" / "income-statement-ttm.jsonl",
            key=key,
            workers=args.workers,
            min_rows=1,
        )

    print("P0 backfill finished")


if __name__ == "__main__":
    main()
