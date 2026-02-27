#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _family(field: str) -> str:
    f = field.lower()
    if any(k in f for k in ["open", "high", "low", "close", "adjclose", "volume", "vwap", "change", "price", "return"]):
        return "market_price_volume"
    if any(k in f for k in ["revenue", "income", "ebit", "ebitda", "eps", "margin", "profit", "cashflow", "freecashflow"]):
        return "fundamental_profitability"
    if any(k in f for k in ["asset", "liabilit", "equity", "debt", "payable", "receivable", "inventory", "capital"]):
        return "fundamental_balance_sheet"
    if any(k in f for k in ["ratio", "yield", "multiple", "priceto", "evto", "bookvalue", "valuation", "dcf"]):
        return "valuation_ratio"
    if "growth" in f:
        return "growth"
    if any(k in f for k in ["sector", "industry", "exchange", "country", "cik", "cusip", "isin", "symbol"]):
        return "metadata_universe"
    if any(k in f for k in ["filing", "accepted", "period", "fiscal", "date", "updated"]):
        return "time_reference"
    if any(k in f for k in ["news", "transcript", "headline", "article", "publisher", "consensus", "target", "rating", "grade"]):
        return "event_sentiment"
    return "other"


def _unit_hint(field: str) -> str:
    f = field.lower()
    if "percentage" in f or "ratio" in f or "margin" in f or "yield" in f:
        return "ratio_or_pct"
    if "price" in f or "open" in f or "high" in f or "low" in f or "close" in f or "eps" in f or "dcf" in f:
        return "currency_per_share_or_price"
    if "volume" in f or "shares" in f or "employees" in f or "count" in f:
        return "count"
    if "marketcap" in f or "revenue" in f or "income" in f or "asset" in f or "liabilit" in f or "cash" in f:
        return "currency_amount"
    if "date" in f or "filing" in f or "accepted" in f:
        return "date_or_timestamp"
    return "unknown"


def _time_semantics(field: str) -> str:
    f = field.lower()
    if f in {"date", "filingdate", "accepteddate", "lastupdated", "periodofreport"} or "date" in f or "filing" in f or "accepted" in f:
        return "explicit_date"
    if any(k in f for k in ["fiscalyear", "period"]):
        return "reporting_period"
    return "implicit_or_cross_sectional"


def main() -> None:
    ap = argparse.ArgumentParser(description="Build field-level semantic catalog from endpoint dictionary + semantic map.")
    ap.add_argument("--field-dict-csv", default="audit/fmp_probe_coverage_v1/fmp_endpoint_field_dictionary_2026-02-23.csv")
    ap.add_argument("--endpoint-semantic-csv", default="audit/fmp_probe_coverage_v1/fmp_endpoint_semantic_map_2026-02-23.csv")
    ap.add_argument("--out-csv", default="audit/fmp_probe_coverage_v1/fmp_field_semantic_catalog_2026-02-23.csv")
    ap.add_argument("--out-md", default="audit/fmp_probe_coverage_v1/fmp_field_semantic_catalog_2026-02-23.md")
    args = ap.parse_args()

    sem_by_ep: dict[str, dict[str, str]] = {}
    with (ROOT / args.endpoint_semantic_csv).open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            sem_by_ep[r["endpoint"]] = r

    field_acc: dict[str, dict[str, Any]] = {}
    with (ROOT / args.field_dict_csv).open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ep = r["endpoint"]
            cat = r["category"]
            ep_sem = sem_by_ep.get(ep, {})
            tier = ep_sem.get("usage_tier", "unknown")
            try:
                lag = int(ep_sem.get("min_lag_days", "0"))
            except Exception:
                lag = 0
            cols = [c for c in (r.get("columns_sample") or "").split("|") if c]
            for c in cols:
                cur = field_acc.setdefault(
                    c,
                    {
                        "field": c,
                        "categories": set(),
                        "endpoints": set(),
                        "usage_tiers": set(),
                        "max_min_lag_days": 0,
                    },
                )
                cur["categories"].add(cat)
                cur["endpoints"].add(ep)
                cur["usage_tiers"].add(tier)
                if lag > cur["max_min_lag_days"]:
                    cur["max_min_lag_days"] = lag

    rows: list[dict[str, Any]] = []
    for f_name, cur in field_acc.items():
        tiers = cur["usage_tiers"]
        allow_default = "true"
        caution = "none"
        if "research_only_high_leakage_guard" in tiers or "event_monitor_only" in tiers:
            allow_default = "false"
            caution = "high_leakage_or_event"
        elif "factor_ready_with_lag" in tiers:
            caution = "needs_lag"
        rows.append(
            {
                "field": f_name,
                "feature_family": _family(f_name),
                "unit_hint": _unit_hint(f_name),
                "time_semantics": _time_semantics(f_name),
                "allow_default_factor_factory": allow_default,
                "caution_level": caution,
                "max_min_lag_days": cur["max_min_lag_days"],
                "endpoint_count": len(cur["endpoints"]),
                "categories": "|".join(sorted(cur["categories"])),
                "usage_tiers": "|".join(sorted(tiers)),
                "example_endpoints": "|".join(sorted(cur["endpoints"])[:6]),
            }
        )

    rows.sort(key=lambda x: (-int(x["endpoint_count"]), x["field"]))

    out_csv = (ROOT / args.out_csv).resolve()
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "field",
        "feature_family",
        "unit_hint",
        "time_semantics",
        "allow_default_factor_factory",
        "caution_level",
        "max_min_lag_days",
        "endpoint_count",
        "categories",
        "usage_tiers",
        "example_endpoints",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    total = len(rows)
    allow = sum(1 for r in rows if r["allow_default_factor_factory"] == "true")
    block = total - allow
    out_md = (ROOT / args.out_md).resolve()
    out_md.write_text(
        "\n".join(
            [
                "# FMP Field Semantic Catalog",
                "",
                f"- total_fields: {total}",
                f"- allow_default_factor_factory: {allow}",
                f"- blocked_or_caution: {block}",
                f"- csv: `{args.out_csv}`",
            ]
        )
        + "\n"
    )

    print(f"[done] out_csv={out_csv}")
    print(f"[done] out_md={out_md}")


if __name__ == "__main__":
    main()
