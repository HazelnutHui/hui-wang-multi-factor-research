#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _load_targets(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text())
    out: dict[str, str] = {}
    for row in raw:
        ep = str(row.get("endpoint") or "").strip()
        cat = str(row.get("category") or "uncategorized").strip()
        if ep:
            out[ep] = cat
    return out


def _classify(endpoint: str, category: str, payload_mode: str) -> dict[str, str]:
    ep = endpoint.lower()
    cat = category.lower()

    usage_tier = "factor_ready"
    pit_risk = "low"
    leakage_risk = "low"
    default_role = "alpha_feature"
    notes = "general use"
    lag_days = "0"

    if payload_mode == "csv":
        notes = "csv parser required"

    if cat in {"news", "transcript"} or "news/" in ep or "earning-call-transcript" in ep:
        usage_tier = "event_monitor_only"
        pit_risk = "high"
        leakage_risk = "high"
        default_role = "event_signal_research"
        notes = "timestamp alignment required; do not mix with same-day close labels"
        lag_days = "1"
    elif "analyst" in cat or "price-target" in ep or "grades" in ep or "ratings" in ep:
        usage_tier = "research_only_high_leakage_guard"
        pit_risk = "high"
        leakage_risk = "high"
        default_role = "expectation_signal"
        notes = "forward/consensus fields may contain future information"
        lag_days = "1"
    elif cat in {"statements", "company", "filings"} or "as-reported" in ep or "sec-filings" in ep:
        usage_tier = "factor_ready_with_lag"
        pit_risk = "medium"
        leakage_risk = "medium"
        default_role = "fundamental_feature"
        notes = "use filing/accepted date for PIT-safe lagging"
        lag_days = "2"
    elif cat in {"quote"} or "aftermarket" in ep:
        usage_tier = "market_timing_monitor"
        pit_risk = "medium"
        leakage_risk = "medium"
        default_role = "execution_context"
        notes = "intraday/post-market data; not direct daily cross-sectional alpha by default"
        lag_days = "0"
    elif cat in {"charts"} or "historical-price-eod" in ep or "historical-chart" in ep:
        usage_tier = "factor_ready"
        pit_risk = "low"
        leakage_risk = "low"
        default_role = "price_volume_feature"
        notes = "safe when using past bars only"
        lag_days = "0"
    elif cat in {"economics"}:
        usage_tier = "factor_ready_with_lag"
        pit_risk = "medium"
        leakage_risk = "medium"
        default_role = "macro_regime_feature"
        notes = "release lag and revision handling required"
        lag_days = "2"
    elif cat in {"earnings_dividends"}:
        usage_tier = "factor_ready_with_lag"
        pit_risk = "medium"
        leakage_risk = "medium"
        default_role = "event_calendar_feature"
        notes = "event-date semantics must be aligned with trade date"
        lag_days = "1"
    elif cat in {"bulk"}:
        usage_tier = "ingestion_source"
        pit_risk = "medium"
        leakage_risk = "medium"
        default_role = "batch_data_source"
        notes = "best for offline snapshots/backfills"
        lag_days = "1"
    elif cat in {"directory", "search"}:
        usage_tier = "universe_metadata"
        pit_risk = "low"
        leakage_risk = "low"
        default_role = "universe_filter"
        notes = "use for symbol universe and metadata only"
        lag_days = "0"

    if ep in {"analyst-estimates", "price-target-summary", "price-target-consensus"}:
        notes = "contains forward estimates; strict anti-leakage checks required"
        usage_tier = "research_only_high_leakage_guard"
        pit_risk = "high"
        leakage_risk = "high"
        lag_days = "1"

    return {
        "usage_tier": usage_tier,
        "pit_risk": pit_risk,
        "leakage_risk": leakage_risk,
        "default_role": default_role,
        "notes": notes,
        "min_lag_days": lag_days,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Build endpoint semantic/PIT label map for factor factory constraints.")
    ap.add_argument("--targets-json", default="configs/research/fmp_probe_targets_coverage_v1.json")
    ap.add_argument("--probe-json", default="audit/fmp_probe_coverage_v1/fmp_interface_probe_latest.json")
    ap.add_argument("--out-csv", default="audit/fmp_probe_coverage_v1/fmp_endpoint_semantic_map_2026-02-23.csv")
    ap.add_argument("--out-md", default="audit/fmp_probe_coverage_v1/fmp_endpoint_semantic_map_2026-02-23.md")
    ap.add_argument(
        "--out-allowlist-csv",
        default="audit/fmp_probe_coverage_v1/fmp_factor_factory_allowlist_2026-02-23.csv",
    )
    ap.add_argument(
        "--out-blocklist-csv",
        default="audit/fmp_probe_coverage_v1/fmp_high_leakage_blocklist_2026-02-23.csv",
    )
    args = ap.parse_args()

    targets = _load_targets((ROOT / args.targets_json).resolve())
    probe = json.loads((ROOT / args.probe_json).resolve().read_text())
    results = probe.get("results", [])

    out_rows: list[dict[str, Any]] = []
    for r in results:
        ep = str(r.get("endpoint") or "")
        cat = targets.get(ep, "uncategorized")
        payload_mode = str(r.get("payload_mode") or "")
        labels = _classify(ep, cat, payload_mode)
        out_rows.append(
            {
                "category": cat,
                "endpoint": ep,
                "http_status": r.get("http_status"),
                "ok_http": r.get("ok_http"),
                "payload_mode": payload_mode,
                "payload_type": r.get("payload_type"),
                "n_rows": r.get("n_rows"),
                "date_min": r.get("date_min"),
                "date_max": r.get("date_max"),
                **labels,
            }
        )

    out_csv = (ROOT / args.out_csv).resolve()
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "category",
        "endpoint",
        "http_status",
        "ok_http",
        "payload_mode",
        "payload_type",
        "n_rows",
        "date_min",
        "date_max",
        "usage_tier",
        "pit_risk",
        "leakage_risk",
        "default_role",
        "min_lag_days",
        "notes",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in out_rows:
            w.writerow(row)

    allowlist_rows = [
        r
        for r in out_rows
        if r["usage_tier"] in {"factor_ready", "factor_ready_with_lag"}
        and str(r["ok_http"]).lower() == "true"
    ]
    out_allow = (ROOT / args.out_allowlist_csv).resolve()
    with out_allow.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in allowlist_rows:
            w.writerow(row)

    block_rows = [
        r
        for r in out_rows
        if r["usage_tier"] in {"research_only_high_leakage_guard", "event_monitor_only"}
    ]
    out_block = (ROOT / args.out_blocklist_csv).resolve()
    with out_block.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in block_rows:
            w.writerow(row)

    tier_counts: dict[str, int] = {}
    for row in out_rows:
        t = str(row["usage_tier"])
        tier_counts[t] = tier_counts.get(t, 0) + 1

    out_md = (ROOT / args.out_md).resolve()
    lines = [
        "# FMP Endpoint Semantic Map",
        "",
        f"- generated_from: `{args.probe_json}`",
        f"- total_endpoints: {len(out_rows)}",
        "",
        "## Usage Tier Counts",
    ]
    for k in sorted(tier_counts.keys()):
        lines.append(f"- {k}: {tier_counts[k]}")
    lines += [
        "",
        "## Notes",
        "- `research_only_high_leakage_guard`: requires explicit anti-leakage checks before feature usage.",
        "- `factor_ready_with_lag`: enforce PIT lag using filing/release timestamps.",
        "- `event_monitor_only`: not default cross-sectional alpha input for daily close execution.",
        "",
        f"CSV source: `{args.out_csv}`",
        f"Allowlist source: `{args.out_allowlist_csv}`",
        f"Blocklist source: `{args.out_blocklist_csv}`",
    ]
    out_md.write_text("\n".join(lines) + "\n")

    print(f"[done] out_csv={out_csv}")
    print(f"[done] out_md={out_md}")
    print(f"[done] out_allowlist_csv={out_allow}")
    print(f"[done] out_blocklist_csv={out_block}")


if __name__ == "__main__":
    main()
