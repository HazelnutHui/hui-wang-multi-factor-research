#!/usr/bin/env python3
"""Backfill only FMP cash-flow-statement JSONL for all universe symbols."""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "fmp" / "statements" / "cash-flow-statement.jsonl"
BASE = "https://financialmodelingprep.com/stable/cash-flow-statement"


def universe_symbols() -> list[str]:
    syms: set[str] = set()
    for d in [ROOT / "data" / "prices", ROOT / "data" / "prices_delisted"]:
        if d.exists():
            syms.update(p.stem for p in d.glob("*.pkl"))
    return sorted(syms)


def read_done(path: Path) -> set[str]:
    out: set[str] = set()
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8") as fh:
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
                out.add(sym)
    return out


def fetch_one(sym: str, key: str) -> tuple[str, int]:
    sess = requests.Session()
    params: dict[str, Any] = {
        "symbol": sym,
        "period": "quarter",
        "limit": 120,
        "apikey": key,
    }
    for attempt in range(3):
        try:
            r = sess.get(BASE, params=params, timeout=30)
        except requests.RequestException:
            time.sleep(0.8 * (attempt + 1))
            continue
        if r.status_code == 429:
            time.sleep(1.5 * (attempt + 1))
            continue
        if r.status_code != 200:
            return sym, 0
        try:
            data = r.json()
        except Exception:
            return sym, 0
        if isinstance(data, dict):
            data = data.get("historical", [])
        if not isinstance(data, list) or not data:
            return sym, 0
        payload = [x for x in data if isinstance(x, dict)]
        line = json.dumps({"symbol": sym, "payload": payload}, ensure_ascii=True)
        return line, len(payload)
    return sym, 0


def main() -> None:
    key = os.environ.get("FMP_API_KEY", "").strip()
    if not key:
        raise SystemExit("FMP_API_KEY not set")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    syms = universe_symbols()
    done = read_done(OUT)
    todo = [s for s in syms if s not in done]

    print(f"universe={len(syms)} done={len(done)} todo={len(todo)}")
    if not todo:
        print("cash-flow already complete")
        return

    ok = 0
    empty = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(fetch_one, s, key) for s in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            result, n = fut.result()
            if n > 0 and isinstance(result, str) and result.startswith("{"):
                with OUT.open("a", encoding="utf-8") as fh:
                    fh.write(result + "\n")
                ok += 1
            else:
                empty += 1
            if i % 200 == 0 or i == len(todo):
                print(f"progress {i}/{len(todo)} ok={ok} empty={empty}", flush=True)

    print(f"done ok={ok} empty={empty}")


if __name__ == "__main__":
    main()
