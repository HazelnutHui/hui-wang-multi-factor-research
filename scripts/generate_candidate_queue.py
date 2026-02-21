#!/usr/bin/env python3
"""Generate next-run candidate queue from factor experiment registry."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path
from typing import Any


def _to_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _to_bool(v: Any) -> bool:
    return str(v).strip().lower() == "true"


def _load_registry(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"registry not found: {path}")
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _priority(row: dict[str, Any]) -> float:
    score = _to_float(row.get("score_total"))
    overall = _to_bool(row.get("overall_pass"))
    gov = _to_bool(row.get("governance_audit_pass"))
    dq = _to_bool(row.get("data_quality_pass"))
    high_rem = int(_to_float(row.get("remediation_high_count")))
    rec = str(row.get("recommendation", ""))
    p = score
    if overall:
        p += 15.0
    if gov:
        p += 5.0
    if dq:
        p += 5.0
    p -= high_rem * 8.0
    if rec == "watchlist_rerun":
        p += 3.0
    return round(p, 4)


def _suggested_action(row: dict[str, Any]) -> str:
    rec = str(row.get("recommendation", ""))
    overall = _to_bool(row.get("overall_pass"))
    if rec == "promote_candidate" and overall:
        return "paper_candidate_validation"
    if rec == "watchlist_rerun":
        return "official_rerun_with_targeted_adjustments"
    return "research_iteration_with_new_hypothesis"


def _next_tag(row: dict[str, Any]) -> str:
    base = str(row.get("decision_tag") or "candidate")
    return f"{base}_next"


def _build_queue(rows: list[dict[str, Any]], top_n: int, min_score: float) -> list[dict[str, Any]]:
    latest_by_factor: dict[str, dict[str, Any]] = {}
    for r in rows:
        fac = str(r.get("factor") or "unknown")
        cur_ts = str(r.get("generated_at") or "")
        old = latest_by_factor.get(fac)
        if old is None or str(old.get("generated_at") or "") <= cur_ts:
            latest_by_factor[fac] = r

    candidates: list[dict[str, Any]] = []
    for r in latest_by_factor.values():
        score = _to_float(r.get("score_total"))
        rec = str(r.get("recommendation") or "")
        if score < min_score:
            continue
        if rec not in {"promote_candidate", "watchlist_rerun", "reject_or_research"}:
            continue
        action = _suggested_action(r)
        if rec == "reject_or_research" and score < 55.0:
            continue
        pr = _priority(r)
        factor = str(r.get("factor") or "")
        strategy = str(r.get("strategy") or "")
        freeze_file = str(r.get("freeze_file") or "")
        next_tag = _next_tag(r)
        cmd = (
            "bash scripts/workstation_official_run.sh "
            f"--workflow production_gates --tag {next_tag} --owner hui "
            '--notes "candidate queue run" --threads 8 --dq-input-csv data/your_input.csv -- '
            f"--strategy {strategy} --factor {factor} --cost-multipliers 1.5,2.0 --wf-shards 4 "
            f"--freeze-file {freeze_file} --out-dir gate_results"
        )
        candidates.append(
            {
                "queue_generated_at": dt.datetime.now().isoformat(),
                "factor": factor,
                "strategy": strategy,
                "source_decision_tag": str(r.get("decision_tag") or ""),
                "source_report_json": str(r.get("report_json") or ""),
                "source_score_total": score,
                "source_recommendation": rec,
                "priority_score": pr,
                "suggested_action": action,
                "proposed_decision_tag": next_tag,
                "proposed_command": cmd,
            }
        )

    candidates = sorted(candidates, key=lambda x: float(x["priority_score"]), reverse=True)
    return candidates[:top_n]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        with open(path, "w", newline="") as f:
            f.write("")
        return
    fields = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _write_md(path: Path, rows: list[dict[str, Any]], registry_csv: Path) -> None:
    lines = [
        "# Factor Candidate Queue",
        "",
        f"- generated_at: {dt.datetime.now().isoformat()}",
        f"- source_registry: `{registry_csv}`",
        f"- queue_size: {len(rows)}",
        "",
        "| rank | factor | source_decision_tag | source_score_total | source_recommendation | priority_score | suggested_action | proposed_decision_tag |",
        "|---|---|---|---:|---|---:|---|---|",
    ]
    for i, r in enumerate(rows, start=1):
        lines.append(
            f"| {i} | {r['factor']} | {r['source_decision_tag']} | {r['source_score_total']} | {r['source_recommendation']} | {r['priority_score']} | {r['suggested_action']} | {r['proposed_decision_tag']} |"
        )
    lines += ["", "## Proposed Commands", ""]
    if rows:
        for r in rows:
            lines.append(f"- `{r['factor']}`: `{r['proposed_command']}`")
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description="Generate factor candidate queue from registry.")
    p.add_argument("--registry-csv", default="audit/factor_registry/factor_experiment_registry.csv")
    p.add_argument("--out-csv", default="audit/factor_registry/factor_candidate_queue.csv")
    p.add_argument("--out-md", default="audit/factor_registry/factor_candidate_queue.md")
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--min-score", type=float, default=45.0)
    args = p.parse_args()

    registry_csv = Path(args.registry_csv).resolve()
    rows = _load_registry(registry_csv)
    queue = _build_queue(rows, top_n=max(1, int(args.top_n)), min_score=float(args.min_score))

    out_csv = Path(args.out_csv).resolve()
    out_md = Path(args.out_md).resolve()
    _write_csv(out_csv, queue)
    _write_md(out_md, queue, registry_csv)
    print(f"[done] candidate_queue_csv={out_csv}")
    print(f"[done] candidate_queue_md={out_md}")
    print(f"[done] queue_size={len(queue)}")


if __name__ == "__main__":
    main()
