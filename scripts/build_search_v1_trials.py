#!/usr/bin/env python3
"""Build (and optionally execute) search_v1 trial plans with audit artifacts."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import itertools
import json
import random
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))


def _as_float(x: Any, *, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _as_int(x: Any, *, default: int = 0) -> int:
    try:
        return int(float(x))
    except Exception:
        return int(default)


def _cartesian(space: dict[str, list[Any]]) -> list[dict[str, Any]]:
    keys = list(space.keys())
    values = [space[k] if isinstance(space[k], list) else [space[k]] for k in keys]
    out: list[dict[str, Any]] = []
    for combo in itertools.product(*values):
        out.append({k: v for k, v in zip(keys, combo)})
    return out


def _pick_trials(
    all_trials: list[dict[str, Any]],
    *,
    mode: str,
    max_trials: int,
    seed: int,
) -> list[dict[str, Any]]:
    if not all_trials:
        return []
    cap = max(1, min(int(max_trials), len(all_trials)))
    if mode == "random":
        rng = random.Random(int(seed))
        idxs = list(range(len(all_trials)))
        rng.shuffle(idxs)
        return [all_trials[i] for i in idxs[:cap]]
    return all_trials[:cap]


def _rewrite_base_strategy_text(base_text: str, trial: dict[str, Any]) -> str:
    value_w = _as_float(trial.get("value_weight"), default=0.7)
    value_w = min(max(value_w, 0.0), 1.0)
    momentum_w = round(1.0 - value_w, 6)
    lookback = _as_int(trial.get("momentum_lookback"), default=126)
    rebalance_freq = _as_int(trial.get("rebalance_freq"), default=21)
    min_dollar_volume = _as_float(trial.get("min_dollar_volume"), default=2_000_000.0)

    out = str(base_text)
    patterns = [
        (r"(?m)^(\s*value:\s*)([-+0-9.eE]+)\s*$", r"\g<1>" + f"{value_w:.6f}"),
        (r"(?m)^(\s*momentum:\s*)([-+0-9.eE]+)\s*$", r"\g<1>" + f"{momentum_w:.6f}"),
        (r"(?m)^(\s*lookback:\s*)([-+0-9.eE]+)\s*$", r"\g<1>" + f"{lookback}"),
        (r"(?m)^(\s*rebalance_freq:\s*)([-+0-9.eE]+)\s*$", r"\g<1>" + f"{rebalance_freq}"),
        (r"(?m)^(\s*min_dollar_volume:\s*)([-+0-9.eE]+)\s*$", r"\g<1>" + f"{min_dollar_volume:.1f}"),
    ]
    for pat, repl in patterns:
        next_out, n = re.subn(pat, repl, out, count=1)
        if n != 1:
            raise SystemExit(f"base strategy rewrite failed for pattern: {pat}")
        out = next_out
    return out


def _write_trials_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fields = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def _write_md(path: Path, payload: dict[str, Any]) -> None:
    trials = payload.get("trials") or []
    lines = [
        "# Search V1 Trial Plan",
        "",
        f"- generated_at: {payload.get('generated_at','')}",
        f"- mode: {payload.get('mode','')}",
        f"- max_trials: {payload.get('max_trials','')}",
        f"- selected_trials: {len(trials)}",
        f"- execute: {payload.get('execute', False)}",
        f"- dry_run: {payload.get('dry_run', True)}",
        f"- base_strategy: `{payload.get('base_strategy','')}`",
        "",
        "## Trials",
        "",
        "| trial_id | value_weight | momentum_lookback | rebalance_freq | min_dollar_volume | strategy_yaml | command |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for t in trials:
        lines.append(
            f"| {t.get('trial_id','')} | {t.get('value_weight','')} | {t.get('momentum_lookback','')} | "
            f"{t.get('rebalance_freq','')} | {t.get('min_dollar_volume','')} | `{t.get('strategy_yaml','')}` | `{t.get('command','')}` |"
        )
    lines += ["", f"- output_json: `{payload.get('output_json','')}`"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def _run_cmd(cmd: str, root: Path) -> int:
    return int(subprocess.call(cmd, shell=True, cwd=str(root)))


def main() -> None:
    p = argparse.ArgumentParser(description="Build search_v1 trial plans and optional execution log.")
    p.add_argument("--policy-json", default="configs/research/auto_research_search_v1_policy.json")
    p.add_argument("--mode", choices=["grid", "random"], default="")
    p.add_argument("--max-trials", type=int, default=0)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    policy_path = (ROOT / args.policy_json).resolve()
    if not policy_path.exists():
        raise SystemExit(f"policy json not found: {policy_path}")

    policy = _read_json(policy_path)
    mode = str(args.mode or policy.get("mode", "grid")).strip().lower() or "grid"
    max_trials = int(args.max_trials) if int(args.max_trials) > 0 else int(policy.get("max_trials", 12))
    seed = int(policy.get("seed", 42))
    execute = bool(args.execute) or bool(policy.get("execute", False))
    dry_run = bool(args.dry_run) or bool(policy.get("dry_run", True))

    base_strategy_rel = str(policy.get("base_strategy", "configs/strategies/combo_v2_prod.yaml"))
    base_strategy_path = (ROOT / base_strategy_rel).resolve()
    if not base_strategy_path.exists():
        raise SystemExit(f"base strategy not found: {base_strategy_path}")

    workflow = policy.get("workflow") if isinstance(policy.get("workflow"), dict) else {}
    factor = str(workflow.get("factor", "combo_v2"))
    cost_multipliers = str(workflow.get("cost_multipliers", "1.5,2.0"))
    wf_shards = max(1, _as_int(workflow.get("wf_shards", 4), default=4))
    wf_out_root = str(workflow.get("out_dir", "gate_results/search_v1"))

    space = policy.get("space") if isinstance(policy.get("space"), dict) else {}
    required_keys = ["value_weight", "momentum_lookback", "rebalance_freq", "min_dollar_volume"]
    missing = [k for k in required_keys if k not in space]
    if missing:
        raise SystemExit(f"policy space missing required keys: {missing}")

    base_strategy_text = base_strategy_path.read_text()

    all_trials = _cartesian({k: space[k] for k in required_keys})
    selected = _pick_trials(all_trials, mode=mode, max_trials=max_trials, seed=seed)

    ts = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir = (ROOT / "audit" / "search_v1" / f"{ts}_search_v1").resolve()
    strat_dir = run_dir / "strategies"
    strat_dir.mkdir(parents=True, exist_ok=True)

    trial_rows: list[dict[str, Any]] = []
    exec_rows: list[dict[str, Any]] = []

    for i, trial in enumerate(selected, start=1):
        trial_id = f"trial_{i:03d}"
        trial_strategy_text = _rewrite_base_strategy_text(base_strategy_text, trial)
        trial_strategy_path = strat_dir / f"{trial_id}.yaml"
        trial_strategy_path.write_text(trial_strategy_text)

        out_dir = f"{wf_out_root}/{trial_id}"
        cmd_tokens = [
            "python",
            "scripts/run_research_workflow.py",
            "--workflow",
            "production_gates",
            "--",
            "--strategy",
            str(trial_strategy_path),
            "--factor",
            factor,
            "--cost-multipliers",
            cost_multipliers,
            "--wf-shards",
            str(wf_shards),
            "--out-dir",
            out_dir,
        ]
        if dry_run:
            cmd_tokens.append("--dry-run")
        cmd = " ".join(shlex.quote(x) for x in cmd_tokens)

        rec = {
            "trial_id": trial_id,
            "value_weight": trial.get("value_weight"),
            "momentum_lookback": trial.get("momentum_lookback"),
            "rebalance_freq": trial.get("rebalance_freq"),
            "min_dollar_volume": trial.get("min_dollar_volume"),
            "strategy_yaml": str(trial_strategy_path),
            "out_dir": out_dir,
            "command": cmd,
        }
        trial_rows.append(rec)

        rc = -1
        if execute:
            rc = _run_cmd(cmd, ROOT)
        exec_rows.append({"trial_id": trial_id, "executed": execute, "dry_run": dry_run, "rc": rc})

    out_json = run_dir / "search_v1_trial_plan.json"
    out_md = run_dir / "search_v1_trial_plan.md"
    out_csv = run_dir / "search_v1_trial_plan.csv"
    exec_json = run_dir / "search_v1_execution_report.json"

    payload = {
        "generated_at": dt.datetime.now().isoformat(),
        "root_dir": str(ROOT),
        "policy_json": str(policy_path),
        "base_strategy": str(base_strategy_path),
        "mode": mode,
        "max_trials": max_trials,
        "seed": seed,
        "execute": execute,
        "dry_run": dry_run,
        "total_space": len(all_trials),
        "selected_trials": len(trial_rows),
        "trials": trial_rows,
        "output_json": str(out_json),
    }
    _write_json(out_json, payload)
    _write_md(out_md, payload)
    _write_trials_csv(out_csv, trial_rows)

    exec_payload = {
        "generated_at": dt.datetime.now().isoformat(),
        "run_dir": str(run_dir),
        "execute": execute,
        "dry_run": dry_run,
        "rows": exec_rows,
        "all_rc_zero": all(int(r.get("rc", -1)) == 0 for r in exec_rows if bool(r.get("executed", False))),
    }
    _write_json(exec_json, exec_payload)

    print(f"[done] search_v1_run_dir={run_dir}")
    print(f"[done] search_v1_plan_json={out_json}")
    print(f"[done] search_v1_plan_md={out_md}")
    print(f"[done] search_v1_plan_csv={out_csv}")
    print(f"[done] search_v1_execution_json={exec_json}")


if __name__ == "__main__":
    main()
