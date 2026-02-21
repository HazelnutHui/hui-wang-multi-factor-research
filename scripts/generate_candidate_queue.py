#!/usr/bin/env python3
"""Generate next-run candidate queue from factor experiment registry."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
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


def _load_failure_db(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _load_policy(path: Path | None) -> dict[str, Any]:
    policy = {
        "mode": "mixed",
        "top_n": 4,
        "min_score": 45.0,
        "mixed": {
            "robust_slots": 3,
            "exploration_slots": 1,
        },
        "failure_feedback": {
            "enabled": True,
            "failure_db_csv": "audit/failure_patterns/failure_patterns.csv",
            "high_penalty_per_item": 6.0,
            "domain_penalties": {
                "Consistency": 4.0,
                "DataQuality": 4.0,
                "Runtime": 3.0,
                "Artifacts": 3.0,
                "Ledger": 2.0,
            },
        },
    }
    if path is None or not path.exists():
        return policy
    try:
        loaded = json.loads(path.read_text())
        if isinstance(loaded, dict):
            policy.update({k: v for k, v in loaded.items() if k in policy})
            if isinstance(loaded.get("mixed"), dict):
                policy["mixed"].update(
                    {
                        k: loaded["mixed"][k]
                        for k in ["robust_slots", "exploration_slots"]
                        if k in loaded["mixed"]
                    }
                )
            if isinstance(loaded.get("failure_feedback"), dict):
                policy["failure_feedback"].update(
                    {
                        k: loaded["failure_feedback"][k]
                        for k in ["enabled", "failure_db_csv", "high_penalty_per_item"]
                        if k in loaded["failure_feedback"]
                    }
                )
                if isinstance(loaded["failure_feedback"].get("domain_penalties"), dict):
                    policy["failure_feedback"]["domain_penalties"].update(
                        loaded["failure_feedback"]["domain_penalties"]
                    )
    except Exception:
        pass
    return policy


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


def _failure_penalty(
    *,
    decision_tag: str,
    failure_rows: list[dict[str, Any]],
    high_penalty_per_item: float,
    domain_penalties: dict[str, float],
) -> tuple[float, int, list[str]]:
    if not decision_tag:
        return 0.0, 0, []
    matched = [r for r in failure_rows if str(r.get("decision_tag", "")) == decision_tag]
    if not matched:
        return 0.0, 0, []
    penalty = 0.0
    domains: list[str] = []
    for r in matched:
        sev = str(r.get("severity", ""))
        dom = str(r.get("domain", ""))
        if sev == "High":
            penalty += float(high_penalty_per_item)
        penalty += float(domain_penalties.get(dom, 0.0))
        if dom and dom not in domains:
            domains.append(dom)
    return round(penalty, 4), len(matched), domains


def _build_queue(
    rows: list[dict[str, Any]],
    mode: str,
    top_n: int,
    min_score: float,
    robust_slots: int,
    exploration_slots: int,
    failure_rows: list[dict[str, Any]],
    failure_feedback_enabled: bool,
    high_penalty_per_item: float,
    domain_penalties: dict[str, float],
) -> list[dict[str, Any]]:
    latest_by_factor: dict[str, dict[str, Any]] = {}
    for r in rows:
        fac = str(r.get("factor") or "unknown")
        cur_ts = str(r.get("generated_at") or "")
        old = latest_by_factor.get(fac)
        if old is None or str(old.get("generated_at") or "") <= cur_ts:
            latest_by_factor[fac] = r

    robust: list[dict[str, Any]] = []
    exploration: list[dict[str, Any]] = []
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
        source_tag = str(r.get("decision_tag") or "")
        fail_penalty = 0.0
        fail_count = 0
        fail_domains: list[str] = []
        if failure_feedback_enabled:
            fail_penalty, fail_count, fail_domains = _failure_penalty(
                decision_tag=source_tag,
                failure_rows=failure_rows,
                high_penalty_per_item=high_penalty_per_item,
                domain_penalties=domain_penalties,
            )
            pr = round(pr - fail_penalty, 4)
        next_tag = _next_tag(r)
        cmd = (
            "bash scripts/workstation_official_run.sh "
            f"--workflow production_gates --tag {next_tag} --owner hui "
            '--notes "candidate queue run" --threads 8 --dq-input-csv data/your_input.csv -- '
            f"--strategy {strategy} --factor {factor} --cost-multipliers 1.5,2.0 --wf-shards 4 "
            f"--freeze-file {freeze_file} --out-dir gate_results"
        )
        item = (
            {
                "queue_generated_at": dt.datetime.now().isoformat(),
                "factor": factor,
                "strategy": strategy,
                "source_decision_tag": source_tag,
                "source_report_json": str(r.get("report_json") or ""),
                "source_score_total": score,
                "source_recommendation": rec,
                "priority_score": pr,
                "failure_penalty": fail_penalty,
                "failure_match_count": fail_count,
                "failure_domains": "|".join(fail_domains),
                "suggested_action": action,
                "proposed_decision_tag": next_tag,
                "proposed_command": cmd,
            }
        )
        if rec in {"promote_candidate", "watchlist_rerun"}:
            robust.append(item)
        else:
            exploration.append(item)

    robust = sorted(robust, key=lambda x: float(x["priority_score"]), reverse=True)
    exploration = sorted(exploration, key=lambda x: float(x["priority_score"]), reverse=True)

    if mode == "robust_only":
        selected = robust[:top_n]
    elif mode == "exploration_only":
        selected = exploration[:top_n]
    elif mode == "mixed":
        r_slots = max(0, int(robust_slots))
        e_slots = max(0, int(exploration_slots))
        if r_slots + e_slots <= 0:
            r_slots = top_n
        selected = robust[:r_slots] + exploration[:e_slots]
        if len(selected) < top_n:
            remainder = robust[r_slots:] + exploration[e_slots:]
            remainder = sorted(remainder, key=lambda x: float(x["priority_score"]), reverse=True)
            selected += remainder[: max(0, top_n - len(selected))]
        selected = selected[:top_n]
    else:
        selected = (robust + exploration)[:top_n]
    if selected:
        return selected

    # Fallback exploration mode: keep pipeline moving when no row passes strict thresholds.
    fallback: list[dict[str, Any]] = []
    for r in latest_by_factor.values():
        score = _to_float(r.get("score_total"))
        if score <= 0:
            continue
        factor = str(r.get("factor") or "")
        strategy = str(r.get("strategy") or "")
        freeze_file = str(r.get("freeze_file") or "")
        source_tag = str(r.get("decision_tag") or "")
        fail_penalty = 0.0
        fail_count = 0
        fail_domains: list[str] = []
        if failure_feedback_enabled:
            fail_penalty, fail_count, fail_domains = _failure_penalty(
                decision_tag=source_tag,
                failure_rows=failure_rows,
                high_penalty_per_item=high_penalty_per_item,
                domain_penalties=domain_penalties,
            )
        next_tag = _next_tag(r)
        fallback.append(
            {
                "queue_generated_at": dt.datetime.now().isoformat(),
                "factor": factor,
                "strategy": strategy,
                "source_decision_tag": source_tag,
                "source_report_json": str(r.get("report_json") or ""),
                "source_score_total": score,
                "source_recommendation": str(r.get("recommendation") or ""),
                "priority_score": round(score - fail_penalty, 4),
                "failure_penalty": fail_penalty,
                "failure_match_count": fail_count,
                "failure_domains": "|".join(fail_domains),
                "suggested_action": "research_iteration_with_new_hypothesis",
                "proposed_decision_tag": next_tag,
                "proposed_command": (
                    "bash scripts/workstation_official_run.sh "
                    f"--workflow production_gates --tag {next_tag} --owner hui "
                    '--notes "candidate queue fallback run" --threads 8 --dq-input-csv data/your_input.csv -- '
                    f"--strategy {strategy} --factor {factor} --cost-multipliers 1.5,2.0 --wf-shards 4 "
                    f"--freeze-file {freeze_file} --out-dir gate_results"
                ),
            }
        )
    fallback = sorted(fallback, key=lambda x: float(x["priority_score"]), reverse=True)
    return fallback[:top_n]


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
        "| rank | factor | source_decision_tag | source_score_total | source_recommendation | priority_score | failure_penalty | failure_domains | suggested_action | proposed_decision_tag |",
        "|---|---|---|---:|---|---:|---:|---|---|---|",
    ]
    for i, r in enumerate(rows, start=1):
        lines.append(
            f"| {i} | {r['factor']} | {r['source_decision_tag']} | {r['source_score_total']} | {r['source_recommendation']} | {r['priority_score']} | {r.get('failure_penalty',0)} | {r.get('failure_domains','')} | {r['suggested_action']} | {r['proposed_decision_tag']} |"
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
    p.add_argument("--policy-json", default="configs/research/candidate_queue_policy.json")
    p.add_argument("--mode", default="", choices=["", "mixed", "robust_only", "exploration_only"])
    p.add_argument("--registry-csv", default="audit/factor_registry/factor_experiment_registry.csv")
    p.add_argument("--out-csv", default="audit/factor_registry/factor_candidate_queue.csv")
    p.add_argument("--out-md", default="audit/factor_registry/factor_candidate_queue.md")
    p.add_argument("--top-n", type=int, default=0)
    p.add_argument("--min-score", type=float, default=-1.0)
    p.add_argument("--robust-slots", type=int, default=-1)
    p.add_argument("--exploration-slots", type=int, default=-1)
    args = p.parse_args()

    policy = _load_policy(Path(args.policy_json).resolve() if args.policy_json else None)
    mode = args.mode if args.mode else str(policy.get("mode", "mixed"))
    top_n = int(args.top_n) if int(args.top_n) > 0 else int(policy.get("top_n", 4))
    min_score = float(args.min_score) if float(args.min_score) >= 0 else float(policy.get("min_score", 45.0))
    mixed = policy.get("mixed") or {}
    robust_slots = int(args.robust_slots) if int(args.robust_slots) >= 0 else int(mixed.get("robust_slots", 3))
    exploration_slots = int(args.exploration_slots) if int(args.exploration_slots) >= 0 else int(mixed.get("exploration_slots", 1))
    failure_feedback = policy.get("failure_feedback") or {}
    failure_feedback_enabled = bool(failure_feedback.get("enabled", True))
    failure_db_csv = Path(str(failure_feedback.get("failure_db_csv", "audit/failure_patterns/failure_patterns.csv"))).resolve()
    high_penalty_per_item = float(failure_feedback.get("high_penalty_per_item", 6.0))
    domain_penalties = {
        str(k): float(v)
        for k, v in dict(failure_feedback.get("domain_penalties") or {}).items()
    }

    registry_csv = Path(args.registry_csv).resolve()
    rows = _load_registry(registry_csv)
    failure_rows = _load_failure_db(failure_db_csv if failure_feedback_enabled else None)
    queue = _build_queue(
        rows,
        mode=mode,
        top_n=max(1, top_n),
        min_score=min_score,
        robust_slots=robust_slots,
        exploration_slots=exploration_slots,
        failure_rows=failure_rows,
        failure_feedback_enabled=failure_feedback_enabled,
        high_penalty_per_item=high_penalty_per_item,
        domain_penalties=domain_penalties,
    )

    out_csv = Path(args.out_csv).resolve()
    out_md = Path(args.out_md).resolve()
    _write_csv(out_csv, queue)
    _write_md(out_md, queue, registry_csv)
    print(f"[done] candidate_queue_csv={out_csv}")
    print(f"[done] candidate_queue_md={out_md}")
    print(f"[done] queue_size={len(queue)}")


if __name__ == "__main__":
    main()
