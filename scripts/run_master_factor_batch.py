#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


VALUE_COMPONENT_FAMILIES = {
    "value_ey_cross",
    "value_fcfy_cross",
    "value_ev_ebitda_cross",
}
QUALITY_COMPONENT_FAMILIES = {
    "quality_roe_cross",
    "quality_roa_cross",
    "quality_gm_cross",
    "quality_cfoa_cross",
    "safety_de_inverse",
}
QUALITY_TREND_FAMILIES = {
    "roe_trend",
    "roa_trend",
    "margin_trend",
    "cfo_quality_trend",
    "deleveraging_trend",
}
VALUE_TREND_FAMILIES = {"value_re_rating_ey", "value_re_rating_fcfy"}
SUE_EPS_STYLE_FAMILIES = {"sue_eps_basic", "pead_short_window"}
SUE_REVENUE_STYLE_FAMILIES = {"sue_revenue_basic"}
INSTITUTIONAL_FAMILIES = {"institutional_ownership_change", "institutional_breadth_change"}


def _pybin() -> str:
    v = ROOT / ".venv" / "bin" / "python"
    if v.exists():
        return str(v)
    return "python3"


def _load_rows(csv_path: Path, batch_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("batch_id") != batch_id:
                continue
            if row.get("result_status", "").strip() not in {"", "not_run"}:
                continue
            out.append(row)
    return out


def _winsor_pair(pct: Any) -> tuple[float, float]:
    p = float(pct)
    p = max(0.0, min(p, 0.49))
    return p, 1.0 - p


def _map_params(factor_family: str, raw: dict[str, Any]) -> dict[str, Any]:
    mapped: dict[str, Any] = {}

    for k, v in raw.items():
        if str(k).isupper():
            mapped[str(k)] = v

    if "industry_neutral" in raw:
        mapped["INDUSTRY_NEUTRAL"] = bool(raw["industry_neutral"])

    if "winsor_pct" in raw:
        w_low, w_high = _winsor_pair(raw["winsor_pct"])
        mapped["SIGNAL_WINSOR_PCT_LOW"] = w_low
        mapped["SIGNAL_WINSOR_PCT_HIGH"] = w_high

    if "smooth_days" in raw:
        mapped["SIGNAL_SMOOTH_WINDOW"] = max(1, int(raw["smooth_days"]))

    lag_days = raw.get("lag_days")
    if lag_days is not None:
        lag = int(lag_days)
        if factor_family in VALUE_COMPONENT_FAMILIES:
            mapped["VALUE_COMPONENT_LAG_DAYS"] = lag
        elif factor_family in QUALITY_COMPONENT_FAMILIES:
            mapped["QUALITY_COMPONENT_LAG_DAYS"] = lag
        elif factor_family == "value_composite_v1":
            mapped["VALUE_LAG_DAYS"] = lag
        elif factor_family == "quality_composite_v1":
            mapped["QUALITY_LAG_DAYS"] = lag
        elif factor_family == "value_quality_blend":
            mapped["VALUE_QUALITY_BLEND_LAG_DAYS"] = lag
        elif factor_family == "profitability_minus_leverage":
            mapped["PML_LAG_DAYS"] = lag
        elif factor_family in QUALITY_TREND_FAMILIES:
            mapped["QUALITY_TREND_LAG_DAYS"] = lag
        elif factor_family in VALUE_TREND_FAMILIES:
            mapped["VALUE_TREND_LAG_DAYS"] = lag
        elif factor_family in SUE_EPS_STYLE_FAMILIES:
            if factor_family == "pead_short_window":
                mapped["PEAD_SHORT_WINDOW_LAG_DAYS"] = lag
            else:
                mapped["SUE_LAG_DAYS"] = lag
        elif factor_family in SUE_REVENUE_STYLE_FAMILIES:
            mapped["SUE_REVENUE_LAG_DAYS"] = lag
        elif factor_family in INSTITUTIONAL_FAMILIES:
            mapped["INSTITUTIONAL_LAG_DAYS"] = lag
        elif factor_family == "owner_earnings_yield_proxy":
            mapped["OWNER_EARNINGS_LAG_DAYS"] = lag
        else:
            mapped["FACTOR_LAG_DAYS"] = lag

    if "lookback_days" in raw:
        lb = int(raw["lookback_days"])
        if factor_family in QUALITY_TREND_FAMILIES:
            mapped["QUALITY_TREND_LOOKBACK_DAYS"] = lb
        elif factor_family in VALUE_TREND_FAMILIES:
            mapped["VALUE_TREND_LOOKBACK_DAYS"] = lb

    if "event_max_age_days" in raw:
        mapped["SUE_EVENT_MAX_AGE_DAYS"] = int(raw["event_max_age_days"])
    if "event_window_days" in raw and factor_family == "pead_short_window":
        mapped["SUE_EVENT_MAX_AGE_DAYS"] = int(raw["event_window_days"])

    if "surprise_floor" in raw:
        floor = float(raw["surprise_floor"])
        if factor_family in SUE_REVENUE_STYLE_FAMILIES:
            mapped["SUE_REVENUE_FLOOR"] = floor
        else:
            mapped["SUE_EPS_FLOOR"] = floor

    if "min_rows" in raw and factor_family in INSTITUTIONAL_FAMILIES:
        mapped["INSTITUTIONAL_MIN_ROWS"] = max(1, int(raw["min_rows"]))

    if "price_align_days" in raw and factor_family == "owner_earnings_yield_proxy":
        mapped["OWNER_EARNINGS_PRICE_ALIGN_DAYS"] = max(0, int(raw["price_align_days"]))

    return mapped


def _run_one(
    py: str,
    candidate_id: str,
    factor: str,
    years: int,
    out_dir: Path,
    log_path: Path,
    sets: list[str],
    dry_run: bool,
) -> dict[str, Any]:
    cmd = [
        py,
        str(ROOT / "scripts" / "run_segmented_factors.py"),
        "--factors",
        factor,
        "--years",
        str(years),
        "--out-dir",
        str(out_dir),
    ]
    for s in sets:
        cmd += ["--set", s]
    if dry_run:
        return {
            "candidate_id": candidate_id,
            "factor": factor,
            "return_code": 0,
            "log_path": str(log_path),
            "out_dir": str(out_dir),
            "cmd": cmd,
            "dry_run": True,
        }
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    with open(log_path, "w", encoding="utf-8") as fh:
        proc = subprocess.run(cmd, cwd=str(ROOT), env=env, stdout=fh, stderr=subprocess.STDOUT)
    return {
        "candidate_id": candidate_id,
        "factor": factor,
        "return_code": int(proc.returncode),
        "log_path": str(log_path),
        "out_dir": str(out_dir),
        "cmd": cmd,
        "dry_run": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Run master-table factor batch exactly by listed parameter rows.")
    ap.add_argument("--batch-id", required=True, help="Batch ID in FACTOR_BATCH_MASTER_TABLE.csv")
    ap.add_argument(
        "--master-csv",
        default="docs/production_research/FACTOR_BATCH_MASTER_TABLE.csv",
        help="Master table csv path",
    )
    ap.add_argument("--years", type=int, default=2)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--max-candidates", type=int, default=0)
    ap.add_argument("--skip-candidates", type=int, default=0, help="Skip first N candidates by master-table order.")
    ap.add_argument("--run-root", default="", help="Optional existing/new run root directory for outputs.")
    ap.add_argument("--audit-dir", default="", help="Optional audit directory for summary outputs.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    csv_path = (ROOT / args.master_csv).resolve()
    rows = _load_rows(csv_path, args.batch_id)
    if not rows:
        raise SystemExit(f"no rows found for batch_id={args.batch_id} in {csv_path}")

    if args.skip_candidates > 0:
        rows = rows[int(args.skip_candidates) :]
    if args.max_candidates > 0:
        rows = rows[: args.max_candidates]
    if not rows:
        raise SystemExit("no candidates left after skip/max filter")

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    if args.run_root:
        run_root = (ROOT / args.run_root).resolve()
    else:
        run_root = (ROOT / "segment_results" / "factor_factory" / f"{ts}_{args.batch_id}").resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    if args.audit_dir:
        audit_dir = (ROOT / args.audit_dir).resolve()
    else:
        audit_dir = (ROOT / "audit" / "factor_factory" / f"{ts}_{args.batch_id}").resolve()
    audit_dir.mkdir(parents=True, exist_ok=True)

    base_sets = [
        "MARKET_CAP_DIR=data/fmp/market_cap_history",
        "MARKET_CAP_STRICT=True",
        "REBALANCE_FREQ=5",
        "HOLDING_PERIOD=3",
        "REBALANCE_MODE=None",
        "EXECUTION_USE_TRADING_DAYS=True",
    ]

    py = _pybin()
    jobs = max(1, int(args.jobs))
    futures = []
    results = []

    with ThreadPoolExecutor(max_workers=jobs) as ex:
        for row in rows:
            cid = row["candidate_id"].strip()
            factor = row["factor_family"].strip()
            p = json.loads(row["params_json"]) if row.get("params_json") else {}
            mapped = _map_params(factor, p)
            sets = list(base_sets) + [f"{k}={mapped[k]}" for k in sorted(mapped.keys())]
            out_dir = run_root / cid
            out_dir.mkdir(parents=True, exist_ok=True)
            log_path = out_dir / "runner.log"
            futures.append(
                ex.submit(
                    _run_one,
                    py,
                    cid,
                    factor,
                    int(args.years),
                    out_dir,
                    log_path,
                    sets,
                    bool(args.dry_run),
                )
            )
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            print(
                f"[done] candidate={res['candidate_id']} factor={res['factor']} rc={res['return_code']} log={res['log_path']}",
                flush=True,
            )

    results = sorted(results, key=lambda x: x["candidate_id"])
    summary = {
        "generated_at": datetime.now().isoformat(),
        "batch_id": args.batch_id,
        "master_csv": str(csv_path),
        "run_root": str(run_root),
        "jobs": jobs,
        "years": int(args.years),
        "skip_candidates": int(args.skip_candidates),
        "candidate_count": len(results),
        "failed_count": sum(1 for r in results if int(r["return_code"]) != 0),
        "results": results,
    }
    jpath = audit_dir / "run_master_factor_batch_summary.json"
    mpath = audit_dir / "run_master_factor_batch_summary.md"
    jpath.write_text(json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8")

    lines = [
        "# Master Factor Batch Run Summary",
        "",
        f"- batch_id: `{summary['batch_id']}`",
        f"- run_root: `{summary['run_root']}`",
        f"- jobs: {summary['jobs']}",
        f"- years: {summary['years']}",
        f"- candidates: {summary['candidate_count']}",
        f"- failed: {summary['failed_count']}",
        "",
        "| candidate_id | factor | return_code | log_path |",
        "|---|---|---:|---|",
    ]
    for r in results:
        lines.append(f"| `{r['candidate_id']}` | `{r['factor']}` | {r['return_code']} | `{r['log_path']}` |")
    mpath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[done] run_root={run_root}")
    print(f"[done] summary_json={jpath}")
    print(f"[done] summary_md={mpath}")


if __name__ == "__main__":
    main()
