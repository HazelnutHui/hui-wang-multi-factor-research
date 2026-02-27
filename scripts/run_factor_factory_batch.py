#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
import os
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def _pybin() -> str:
    v = ROOT / ".venv" / "bin" / "python"
    if v.exists():
        return str(v)
    return "python3"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))


def _cartesian(space: dict[str, list[Any]]) -> list[dict[str, Any]]:
    keys = list(space.keys())
    values = [space[k] if isinstance(space[k], list) else [space[k]] for k in keys]
    out: list[dict[str, Any]] = []
    for combo in itertools.product(*values):
        out.append({k: v for k, v in zip(keys, combo)})
    return out


def _candidate_id(family: str, idx: int) -> str:
    return f"{family}_{idx:03d}"


@dataclass
class Candidate:
    candidate_id: str
    family: str
    factor: str
    years: int
    sets: list[str]
    out_dir: Path
    log_path: Path
    cmd: list[str]


def _make_candidates(policy: dict[str, Any], run_dir: Path, max_candidates: int, seed: int) -> list[Candidate]:
    families = policy.get("families") if isinstance(policy.get("families"), list) else []
    years = int(policy.get("years", 2))
    default_sets = [str(x) for x in (policy.get("default_set") or [])]
    mode = str(policy.get("mode", "grid")).lower()
    rng = random.Random(seed)

    cands: list[Candidate] = []
    py = _pybin()
    for fam in families:
        if not isinstance(fam, dict):
            continue
        family = str(fam.get("name", "")).strip()
        factor = str(fam.get("factor", "")).strip()
        if not family or not factor:
            continue
        grid = fam.get("grid") if isinstance(fam.get("grid"), dict) else {}
        combos = _cartesian(grid) if grid else [{}]
        fam_cap = int(fam.get("max_candidates", len(combos)))
        fam_cap = max(1, min(fam_cap, len(combos)))
        if mode == "random":
            rng.shuffle(combos)
        combos = combos[:fam_cap]

        for i, combo in enumerate(combos, start=1):
            cid = _candidate_id(family, i)
            out_dir = (ROOT / "segment_results" / "factor_factory" / run_dir.name / cid).resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            log_path = (out_dir / "runner.log").resolve()

            sets = list(default_sets)
            for k, v in combo.items():
                sets.append(f"{k}={v}")

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

            cands.append(
                Candidate(
                    candidate_id=cid,
                    family=family,
                    factor=factor,
                    years=years,
                    sets=sets,
                    out_dir=out_dir,
                    log_path=log_path,
                    cmd=cmd,
                )
            )

    if max_candidates > 0:
        cands = cands[:max_candidates]
    return cands


def _run_one(c: Candidate, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {
            "candidate_id": c.candidate_id,
            "factor": c.factor,
            "family": c.family,
            "return_code": 0,
            "dry_run": True,
            "out_dir": str(c.out_dir),
            "log_path": str(c.log_path),
            "cmd": c.cmd,
        }

    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    with open(c.log_path, "w") as f:
        p = subprocess.run(c.cmd, cwd=str(ROOT), env=env, stdout=f, stderr=subprocess.STDOUT)
    return {
        "candidate_id": c.candidate_id,
        "factor": c.factor,
        "family": c.family,
        "return_code": int(p.returncode),
        "dry_run": False,
        "out_dir": str(c.out_dir),
        "log_path": str(c.log_path),
        "cmd": c.cmd,
    }


def _summarize_candidate(c: Candidate) -> dict[str, Any]:
    summary_csv = c.out_dir / c.factor / "segment_summary.csv"
    if not summary_csv.exists():
        return {
            "candidate_id": c.candidate_id,
            "factor": c.factor,
            "family": c.family,
            "summary_csv": str(summary_csv),
            "n_segments": 0,
            "n_valid": 0,
            "ic_overall_mean": None,
            "ic_overall_std": None,
            "ic_pos_ratio": None,
            "sharpe_mean": None,
            "score": -1e9,
        }

    df = pd.read_csv(summary_csv)
    df = df[pd.to_numeric(df.get("n_dates"), errors="coerce").fillna(0) > 0].copy()
    ic = pd.to_numeric(df.get("ic_overall"), errors="coerce").dropna()
    shp = pd.to_numeric(df.get("sharpe"), errors="coerce").dropna()
    if len(ic) == 0:
        return {
            "candidate_id": c.candidate_id,
            "factor": c.factor,
            "family": c.family,
            "summary_csv": str(summary_csv),
            "n_segments": int(len(df)),
            "n_valid": 0,
            "ic_overall_mean": None,
            "ic_overall_std": None,
            "ic_pos_ratio": None,
            "sharpe_mean": float(shp.mean()) if len(shp) else None,
            "score": -1e9,
        }

    mean_ic = float(ic.mean())
    std_ic = float(ic.std(ddof=1)) if len(ic) > 1 else 0.0
    pos_ratio = float((ic > 0).mean())
    sharpe_mean = float(shp.mean()) if len(shp) else None
    score = mean_ic - 0.5 * std_ic + 0.01 * pos_ratio
    return {
        "candidate_id": c.candidate_id,
        "factor": c.factor,
        "family": c.family,
        "summary_csv": str(summary_csv),
        "n_segments": int(len(df)),
        "n_valid": int(len(ic)),
        "ic_overall_mean": mean_ic,
        "ic_overall_std": std_ic,
        "ic_pos_ratio": pos_ratio,
        "sharpe_mean": sharpe_mean,
        "score": score,
    }


def _write_md(path: Path, payload: dict[str, Any], ranked: pd.DataFrame) -> None:
    lines = [
        "# Factor Factory Batch",
        "",
        f"- generated_at: {payload.get('generated_at')}",
        f"- policy_json: `{payload.get('policy_json')}`",
        f"- run_dir: `{payload.get('run_dir')}`",
        f"- dry_run: {payload.get('dry_run')}",
        f"- jobs: {payload.get('jobs')}",
        f"- candidates: {payload.get('candidate_count')}",
        "",
        "## Top Candidates",
        "",
        "| rank | candidate_id | factor | family | ic_mean | ic_std | pos_ratio | sharpe_mean | score |",
        "|---|---|---|---|---:|---:|---:|---:|---:|",
    ]
    if len(ranked) == 0:
        lines.append("| - | - | - | - | - | - | - | - | - |")
    else:
        for i, (_, r) in enumerate(ranked.head(20).iterrows(), start=1):
            lines.append(
                f"| {i} | {r.get('candidate_id')} | {r.get('factor')} | {r.get('family')} | "
                f"{r.get('ic_overall_mean')} | {r.get('ic_overall_std')} | {r.get('ic_pos_ratio')} | "
                f"{r.get('sharpe_mean')} | {r.get('score')} |"
            )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Run factor-factory batch candidates and rank outputs.")
    ap.add_argument("--policy-json", default="configs/research/factor_factory_policy.json")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--max-candidates", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    policy_path = (ROOT / args.policy_json).resolve()
    if not policy_path.exists():
        raise SystemExit(f"policy not found: {policy_path}")
    policy = _read_json(policy_path)

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    batch_name = str(policy.get("batch_name", "batch")).strip() or "batch"
    run_dir = (ROOT / "audit" / "factor_factory" / f"{ts}_{batch_name}").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    cands = _make_candidates(policy, run_dir, max_candidates=int(args.max_candidates), seed=int(args.seed))
    if not cands:
        raise SystemExit("no candidates generated from policy")

    plan_rows = []
    for c in cands:
        plan_rows.append(
            {
                "candidate_id": c.candidate_id,
                "factor": c.factor,
                "family": c.family,
                "years": c.years,
                "sets": ";".join(c.sets),
                "out_dir": str(c.out_dir),
                "log_path": str(c.log_path),
                "cmd": " ".join(c.cmd),
            }
        )
    plan_df = pd.DataFrame(plan_rows)
    plan_csv = run_dir / "candidate_plan.csv"
    plan_df.to_csv(plan_csv, index=False)

    results = []
    jobs = max(1, int(args.jobs))
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        futs = [ex.submit(_run_one, c, bool(args.dry_run)) for c in cands]
        for fut in as_completed(futs):
            results.append(fut.result())
    res_df = pd.DataFrame(results).sort_values(["return_code", "candidate_id"])
    res_csv = run_dir / "execution_results.csv"
    res_df.to_csv(res_csv, index=False)

    ranked_rows = []
    if not args.dry_run:
        by_id = {c.candidate_id: c for c in cands}
        for _, r in res_df.iterrows():
            cid = str(r.get("candidate_id"))
            c = by_id[cid]
            s = _summarize_candidate(c)
            s["return_code"] = int(r.get("return_code", 1))
            ranked_rows.append(s)
    ranked_df = pd.DataFrame(ranked_rows)
    if len(ranked_df) > 0:
        ranked_df = ranked_df.sort_values("score", ascending=False)
    ranked_csv = run_dir / "leaderboard.csv"
    ranked_df.to_csv(ranked_csv, index=False)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "policy_json": str(policy_path),
        "run_dir": str(run_dir),
        "dry_run": bool(args.dry_run),
        "jobs": jobs,
        "candidate_count": int(len(cands)),
        "plan_csv": str(plan_csv),
        "execution_csv": str(res_csv),
        "leaderboard_csv": str(ranked_csv),
        "all_success": bool((res_df["return_code"] == 0).all()) if len(res_df) else False,
    }
    out_json = run_dir / "factor_factory_batch_report.json"
    _write_json(out_json, payload)
    out_md = run_dir / "factor_factory_batch_report.md"
    _write_md(out_md, payload, ranked_df)

    print(f"[done] run_dir={run_dir}")
    print(f"[done] plan_csv={plan_csv}")
    print(f"[done] execution_csv={res_csv}")
    print(f"[done] leaderboard_csv={ranked_csv}")
    print(f"[done] report_json={out_json}")
    print(f"[done] report_md={out_md}")


if __name__ == "__main__":
    main()
