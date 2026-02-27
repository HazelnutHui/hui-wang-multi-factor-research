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
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    csv_path = (ROOT / args.master_csv).resolve()
    rows = _load_rows(csv_path, args.batch_id)
    if not rows:
        raise SystemExit(f"no rows found for batch_id={args.batch_id} in {csv_path}")

    if args.max_candidates > 0:
        rows = rows[: args.max_candidates]

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_root = (ROOT / "segment_results" / "factor_factory" / f"{ts}_{args.batch_id}").resolve()
    run_root.mkdir(parents=True, exist_ok=True)
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
            sets = list(base_sets) + [f"{k}={v}" for k, v in p.items()]
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

