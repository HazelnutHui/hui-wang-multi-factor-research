#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from io import StringIO
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "https://financialmodelingprep.com/stable"


def _safe_json(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return {"_non_json_preview": resp.text[:400]}


def _parse_csv_payload(resp: requests.Response) -> tuple[Any, str]:
    text = resp.text or ""
    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "csv" not in content_type and "," not in text[:2000]:
        return None, "non_csv"
    try:
        df = pd.read_csv(StringIO(text))
        return df.to_dict(orient="records"), "csv"
    except Exception:
        return None, "non_csv"


def _shape(payload: Any) -> tuple[int, list[str], str]:
    if isinstance(payload, list):
        if len(payload) == 0:
            return 0, [], "list"
        first = payload[0]
        if isinstance(first, dict):
            cols = sorted({k for row in payload[:50] if isinstance(row, dict) for k in row.keys()})
            return len(payload), cols, "list[dict]"
        return len(payload), [], "list"
    if isinstance(payload, dict):
        keys = list(payload.keys())
        return 1, keys[:80], "dict"
    return 0, [], type(payload).__name__


def _date_span(payload: Any) -> tuple[str | None, str | None]:
    if not isinstance(payload, list) or not payload:
        return None, None
    dates: list[str] = []
    for row in payload[:5000]:
        if not isinstance(row, dict):
            continue
        for k in ("date", "fillingDate", "acceptedDate", "publishedDate"):
            v = row.get(k)
            if isinstance(v, str) and len(v) >= 10:
                dates.append(v[:10])
                break
    if not dates:
        return None, None
    try:
        ds = sorted(pd.to_datetime(pd.Series(dates), errors="coerce").dropna().dt.strftime("%Y-%m-%d").tolist())
        if not ds:
            return None, None
        return ds[0], ds[-1]
    except Exception:
        return None, None


def _probe(
    session: requests.Session,
    api_key: str,
    base_url: str,
    endpoint: str,
    params: dict[str, Any],
    timeout: int = 30,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    q = dict(params)
    q["apikey"] = api_key
    started = datetime.now(timezone.utc).isoformat()
    try:
        r = session.get(url, params=q, timeout=timeout)
        payload = _safe_json(r)
        csv_payload, csv_mode = _parse_csv_payload(r)
        if isinstance(payload, dict) and "_non_json_preview" in payload and csv_mode == "csv" and csv_payload is not None:
            payload = csv_payload
        n_rows, cols, payload_type = _shape(payload)
        d0, d1 = _date_span(payload)
        err = None
        if isinstance(payload, dict):
            if "Error Message" in payload:
                err = payload.get("Error Message")
            elif "error" in payload:
                err = payload.get("error")
        return {
            "endpoint": endpoint,
            "url": url,
            "params": params,
            "http_status": int(r.status_code),
            "ok_http": bool(r.ok),
            "payload_type": payload_type,
            "payload_mode": csv_mode if csv_mode == "csv" else "json_or_other",
            "n_rows": int(n_rows),
            "columns_sample": cols[:120],
            "date_min": d0,
            "date_max": d1,
            "error_message": err,
            "response_preview": payload[:2] if isinstance(payload, list) else payload,
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "url": url,
            "params": params,
            "http_status": None,
            "ok_http": False,
            "payload_type": "exception",
            "n_rows": 0,
            "columns_sample": [],
            "date_min": None,
            "date_max": None,
            "error_message": str(e),
            "response_preview": {},
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }


def _default_targets(symbol: str) -> list[tuple[str, dict[str, Any]]]:
    return [
        ("stock-list", {"limit": 50}),
        ("profile", {"symbol": symbol}),
        ("historical-price-eod", {"symbol": symbol, "from": "2025-01-01", "to": "2025-12-31"}),
        ("historical-price-eod/dividend-adjusted", {"symbol": symbol, "from": "2025-01-01", "to": "2025-12-31"}),
        ("historical-market-capitalization", {"symbol": symbol, "from": "2024-01-01", "to": "2025-12-31", "limit": 1000}),
        ("ratios", {"symbol": symbol, "period": "quarter"}),
        ("key-metrics", {"symbol": symbol, "period": "quarter"}),
        ("income-statement", {"symbol": symbol, "period": "quarter", "limit": 20}),
        ("balance-sheet-statement", {"symbol": symbol, "period": "quarter", "limit": 20}),
        ("cash-flow-statement", {"symbol": symbol, "period": "quarter", "limit": 20}),
        ("earnings-surprises-bulk", {"year": 2025}),
        ("earnings-calendar", {"from": "2025-01-01", "to": "2025-03-31"}),
        ("profile-bulk", {"part": 0}),
        ("delisted-companies", {"from": "2025-01-01", "to": "2025-12-31"}),
    ]


def _load_targets(path: Path, symbol: str) -> list[tuple[str, dict[str, Any]]]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError("targets json must be a list")
    out: list[tuple[str, dict[str, Any]]] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"targets[{i}] must be an object")
        ep = str(item.get("endpoint") or "").strip()
        params = item.get("params") or {}
        if not ep:
            raise ValueError(f"targets[{i}].endpoint is required")
        if not isinstance(params, dict):
            raise ValueError(f"targets[{i}].params must be an object")
        norm_params: dict[str, Any] = {}
        for k, v in params.items():
            if isinstance(v, str):
                norm_params[str(k)] = v.replace("{symbol}", symbol)
            else:
                norm_params[str(k)] = v
        out.append((ep, norm_params))
    return out


def _write_md(path: Path, report: dict[str, Any]) -> None:
    rows = report.get("results", [])
    lines = [
        "# FMP Interface Probe Report",
        "",
        f"- generated_at: {report.get('generated_at')}",
        f"- symbol: {report.get('symbol')}",
        f"- endpoints_tested: {len(rows)}",
        f"- success_count: {sum(1 for r in rows if r.get('ok_http'))}",
        "",
        "| endpoint | status | ok | rows | date_min | date_max | columns_sample | note |",
        "|---|---:|---|---:|---|---|---|---|",
    ]
    for r in rows:
        cols = ",".join((r.get("columns_sample") or [])[:8])
        note = r.get("error_message") or ""
        lines.append(
            f"| {r.get('endpoint')} | {r.get('http_status')} | {r.get('ok_http')} | {r.get('n_rows')} | "
            f"{r.get('date_min')} | {r.get('date_max')} | {cols} | {note} |"
        )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Probe FMP endpoints with small samples and record schema/date coverage.")
    ap.add_argument("--symbol", default="AAPL")
    ap.add_argument("--out-dir", default="audit/fmp_probe")
    ap.add_argument("--targets-json", default="", help="Optional json file of probe targets.")
    ap.add_argument("--base-url", default=DEFAULT_BASE, help="FMP base url, e.g. stable or api/v3.")
    args = ap.parse_args()

    api_key = os.environ.get("FMP_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("FMP_API_KEY not found in environment.")

    out_dir = (ROOT / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    symbol = args.symbol.strip().upper()
    if args.targets_json:
        targets = _load_targets((ROOT / args.targets_json).resolve(), symbol)
    else:
        targets = _default_targets(symbol)
    results = []
    for ep, p in targets:
        print(f"[probe] {ep}", flush=True)
        results.append(_probe(session, api_key, args.base_url, ep, p))

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "base_url": args.base_url,
        "targets_source": args.targets_json or "default_targets",
        "results": results,
    }
    out_json = out_dir / f"fmp_interface_probe_{ts}.json"
    out_md = out_dir / f"fmp_interface_probe_{ts}.md"
    latest_json = out_dir / "fmp_interface_probe_latest.json"
    latest_md = out_dir / "fmp_interface_probe_latest.md"

    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    _write_md(out_md, report)
    latest_json.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    latest_md.write_text(out_md.read_text())

    print(f"[done] report_json={out_json}")
    print(f"[done] report_md={out_md}")
    print(f"[done] latest_json={latest_json}")
    print(f"[done] latest_md={latest_md}")


if __name__ == "__main__":
    main()
