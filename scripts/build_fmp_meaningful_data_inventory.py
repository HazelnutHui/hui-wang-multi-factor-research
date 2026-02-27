#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


THEME_KEYWORDS: dict[str, list[str]] = {
    "quality_profitability": [
        "roe",
        "roa",
        "margin",
        "ebit",
        "ebitda",
        "netincome",
        "grossprofit",
        "operatingincome",
        "assetturnover",
    ],
    "value_valuation": [
        "priceto",
        "priceTo".lower(),
        "bookvalue",
        "earningsyield",
        "evto",
        "enterprisevalue",
        "dcf",
        "graham",
    ],
    "growth_trend": [
        "growth",
        "revenuegrowth",
        "epsgrowth",
        "assetgrowth",
        "debtgrowth",
    ],
    "liquidity_cashflow": [
        "currentratio",
        "quickratio",
        "cashratio",
        "freecashflow",
        "operatingcashflow",
        "cashconversioncycle",
        "workingcapital",
    ],
    "leverage_solvency": [
        "debt",
        "liabilities",
        "interestcoverage",
        "solvency",
        "netdebt",
        "debtto",
    ],
    "price_volume_microstructure": [
        "open",
        "high",
        "low",
        "close",
        "adjclose",
        "volume",
        "vwap",
        "change",
        "volatility",
    ],
}


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _match_theme(field: str, keywords: list[str]) -> bool:
    f = field.lower()
    return any(k in f for k in keywords)


def main() -> None:
    ap = argparse.ArgumentParser(description="Build meaningful data inventory and field theme seeds from semantic catalog.")
    ap.add_argument(
        "--semantic-csv",
        default="audit/fmp_probe_coverage_v1/fmp_field_semantic_catalog_2026-02-23.csv",
    )
    ap.add_argument(
        "--out-json",
        default="audit/fmp_probe_coverage_v1/fmp_meaningful_data_inventory_2026-02-23.json",
    )
    ap.add_argument(
        "--out-md",
        default="audit/fmp_probe_coverage_v1/fmp_meaningful_data_inventory_2026-02-23.md",
    )
    ap.add_argument(
        "--out-theme-json",
        default="configs/research/fmp_field_theme_seeds_2026-02-23.json",
    )
    args = ap.parse_args()

    rows = _load_csv((ROOT / args.semantic_csv).resolve())
    allow = [r for r in rows if (r.get("allow_default_factor_factory") or "").lower() == "true"]
    block = [r for r in rows if (r.get("allow_default_factor_factory") or "").lower() != "true"]

    fam_count = Counter(r.get("feature_family", "other") for r in rows)
    fam_allow = Counter(r.get("feature_family", "other") for r in allow)
    caution_count = Counter(r.get("caution_level", "unknown") for r in rows)

    themes: dict[str, list[str]] = {}
    for theme, keys in THEME_KEYWORDS.items():
        candidates = sorted(
            {
                r["field"]
                for r in allow
                if _match_theme(r.get("field", ""), keys)
                and (r.get("feature_family") not in {"metadata_universe", "time_reference"})
            }
        )
        themes[theme] = candidates

    payload: dict[str, Any] = {
        "total_fields": len(rows),
        "allow_default_fields": len(allow),
        "blocked_fields": len(block),
        "feature_family_counts": dict(fam_count),
        "allow_feature_family_counts": dict(fam_allow),
        "caution_level_counts": dict(caution_count),
        "themes": themes,
    }

    out_json = (ROOT / args.out_json).resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=True))

    out_theme = (ROOT / args.out_theme_json).resolve()
    out_theme.parent.mkdir(parents=True, exist_ok=True)
    out_theme.write_text(json.dumps({"generated_from": args.semantic_csv, "themes": themes}, indent=2, ensure_ascii=True))

    lines = [
        "# FMP Meaningful Data Inventory",
        "",
        f"- total_fields: {len(rows)}",
        f"- allow_default_fields: {len(allow)}",
        f"- blocked_fields: {len(block)}",
        "",
        "## Allow Fields By Family",
    ]
    for k, v in sorted(fam_allow.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- {k}: {v}")
    lines += ["", "## Theme Seed Sizes"]
    for t, fs in themes.items():
        lines.append(f"- {t}: {len(fs)} fields")
    lines += [
        "",
        f"Inventory JSON: `{args.out_json}`",
        f"Theme Seeds JSON: `{args.out_theme_json}`",
    ]
    out_md = (ROOT / args.out_md).resolve()
    out_md.write_text("\n".join(lines) + "\n")

    print(f"[done] out_json={out_json}")
    print(f"[done] out_md={out_md}")
    print(f"[done] out_theme_json={out_theme}")


if __name__ == "__main__":
    main()
