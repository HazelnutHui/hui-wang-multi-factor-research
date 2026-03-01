#!/usr/bin/env python3
"""Audit P0 FMP readiness for batchA100 logic100."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FMP = DATA / "fmp"


@dataclass
class Item:
    name: str
    required: bool
    status: str
    detail: str


def _count(path: Path, pattern: str) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.glob(pattern))


def _universe_symbols() -> set[str]:
    syms: set[str] = set()
    for d in [DATA / "prices", DATA / "prices_delisted"]:
        if not d.exists():
            continue
        syms.update(p.stem for p in d.glob("*.pkl"))
    return syms


def _jsonl_symbols(path: Path) -> set[str]:
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


def main() -> None:
    univ = _universe_symbols()
    univ_n = len(univ)

    items: list[Item] = []

    mcap = FMP / "market_cap_history"
    mcap_files = {p.stem for p in mcap.glob("*.csv")} if mcap.exists() else set()
    items.append(Item("market_cap_history", True, "ok" if len(mcap_files) > 0 else "missing", f"files={len(mcap_files)}, coverage={len(mcap_files & univ)}/{univ_n}"))

    val = FMP / "ratios" / "value"
    val_files = {p.stem for p in val.glob("*.pkl")} if val.exists() else set()
    items.append(Item("ratios/value", True, "ok" if len(val_files) > 0 else "missing", f"files={len(val_files)}, coverage={len(val_files & univ)}/{univ_n}"))

    qual = FMP / "ratios" / "quality"
    qual_files = {p.stem for p in qual.glob("*.pkl")} if qual.exists() else set()
    items.append(Item("ratios/quality", True, "ok" if len(qual_files) > 0 else "missing", f"files={len(qual_files)}, coverage={len(qual_files & univ)}/{univ_n}"))

    earnings = FMP / "earnings"
    cal = earnings / "earnings_calendar.csv"
    years = []
    if earnings.exists():
        for p in earnings.glob("earnings_surprises_*.csv"):
            m = re.search(r"(\d{4})", p.name)
            if m:
                years.append(int(m.group(1)))
    years = sorted(years)
    full_years = list(range(2010, 2027))
    missing_years = [y for y in full_years if y not in years]
    items.append(Item("earnings/calendar", True, "ok" if cal.exists() else "missing", f"path={cal}"))
    items.append(Item("earnings/surprises", True, "ok" if not missing_years else "partial", f"years_present={years}, missing={missing_years}"))

    inst_path = FMP / "institutional" / "institutional-ownership__symbol-positions-summary.jsonl"
    inst_syms = _jsonl_symbols(inst_path)
    items.append(Item("institutional/summary", True, "ok" if inst_syms else "missing", f"symbols={len(inst_syms)}"))

    owner_path = FMP / "owner_earnings" / "owner-earnings.jsonl"
    owner_syms = _jsonl_symbols(owner_path)
    items.append(Item("owner_earnings", True, "ok" if owner_syms else "missing", f"symbols={len(owner_syms)}"))

    statements_dir = FMP / "statements"
    st_income = statements_dir / "income-statement.jsonl"
    st_balance = statements_dir / "balance-sheet-statement.jsonl"
    st_cash = statements_dir / "cash-flow-statement.jsonl"
    st_ttm = statements_dir / "income-statement-ttm.jsonl"
    st_ok = all(p.exists() for p in [st_income, st_balance, st_cash])
    ttm_ok = st_ttm.exists()
    items.append(Item("statements/core", True, "ok" if st_ok else "missing", f"income={st_income.exists()}, balance={st_balance.exists()}, cash={st_cash.exists()}"))
    items.append(Item("statements/ttm", False, "ok" if ttm_ok else "missing", f"income_ttm={ttm_ok}"))

    report = {
        "as_of": "2026-02-28",
        "universe_symbols": univ_n,
        "items": [asdict(i) for i in items],
    }

    out = ROOT / "audit" / "p0_readiness_2026-02-28.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(f"universe_symbols={univ_n}")
    for i in items:
        print(f"{i.name:24s} {i.status:8s} {i.detail}")
    print(f"report={out}")


if __name__ == "__main__":
    main()
