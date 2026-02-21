#!/usr/bin/env python3
"""Repair freeze-file and dq-input-csv paths in next_run_plan commands."""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import re
import shlex
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True))


def _find_flag(tokens: list[str], flag: str) -> int:
    for i, t in enumerate(tokens):
        if t == flag:
            return i
    return -1


def _pick_freeze(strategy_path: str, factor: str) -> str | None:
    # Prefer latest commit-tagged freeze, fallback to generic factor freeze.
    base = Path("runs/freeze")
    if not base.exists():
        return None

    names: list[str] = []
    if factor:
        names.extend(
            [
                f"{factor}_prod_*_g*.freeze.json",
                f"{factor}_prod.freeze.json",
                f"{factor}*.freeze.json",
            ]
        )
    if strategy_path:
        stem = Path(strategy_path).name.replace(".yaml", "")
        names.extend([f"{stem}_*_g*.freeze.json", f"{stem}.freeze.json"])
    names.append("*.freeze.json")

    cands: list[Path] = []
    for pat in names:
        cands.extend(Path(p).resolve() for p in glob.glob(str(base / pat)))
        if cands:
            break
    if not cands:
        return None
    cands = sorted(cands, key=lambda p: p.stat().st_mtime)
    return str(cands[-1])


def _replace_or_add(tokens: list[str], flag: str, value: str) -> list[str]:
    out = list(tokens)
    i = _find_flag(out, flag)
    if i >= 0:
        if i + 1 < len(out):
            out[i + 1] = value
        else:
            out.append(value)
        return out
    out.extend([flag, value])
    return out


def _existing_run_names() -> list[str]:
    base = Path("audit/workstation_runs")
    if not base.exists():
        return []
    return [p.name for p in base.glob("*") if p.is_dir()]


def _tag_exists(tag: str, run_names: list[str], reserved: set[str]) -> bool:
    if tag in reserved:
        return True
    needle = f"_{tag}"
    return any(needle in n for n in run_names)


def _next_standard_tag(*, run_names: list[str], reserved: set[str], tag_prefix: str, tag_date: str) -> str:
    pat = re.compile(rf"{re.escape(tag_prefix)}_{re.escape(tag_date)}_run(\d+)$")
    max_n = 0
    for n in run_names:
        m = pat.search(n)
        if m:
            try:
                max_n = max(max_n, int(m.group(1)))
            except Exception:
                pass
    for t in reserved:
        m = pat.search(t)
        if m:
            try:
                max_n = max(max_n, int(m.group(1)))
            except Exception:
                pass
    n = max_n + 1
    while True:
        cand = f"{tag_prefix}_{tag_date}_run{n}"
        if not _tag_exists(cand, run_names, reserved):
            reserved.add(cand)
            return cand
        n += 1


def main() -> None:
    p = argparse.ArgumentParser(description="Repair next_run_plan command paths.")
    p.add_argument("--plan-json", default="audit/factor_registry/next_run_plan.json")
    p.add_argument("--out-json", default="audit/factor_registry/next_run_plan_fixed.json")
    p.add_argument("--out-md", default="audit/factor_registry/next_run_plan_fixed.md")
    p.add_argument("--dq-input-csv", default="", help="Canonical DQ input CSV path to inject.")
    p.add_argument("--allow-missing-dq", action="store_true")
    p.add_argument("--normalize-tag", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--tag-prefix", default="committee")
    p.add_argument("--tag-date", default=dt.date.today().isoformat())
    args = p.parse_args()

    plan_json = Path(args.plan_json).resolve()
    if not plan_json.exists():
        raise SystemExit(f"plan json not found: {plan_json}")
    plan = _read_json(plan_json)
    commands = plan.get("commands") or []

    fixed_cmds = []
    issues: list[str] = []
    fixed_count = 0
    tag_fixed_count = 0
    run_names = _existing_run_names()
    reserved_tags: set[str] = set()
    for row in commands:
        cmd = str(row.get("command") or "").strip()
        if not cmd:
            fixed_cmds.append(row)
            continue
        try:
            tokens = shlex.split(cmd)
        except Exception:
            issues.append(f"unparseable command rank={row.get('rank')}")
            fixed_cmds.append(row)
            continue

        factor = str(row.get("factor") or "")
        strategy = ""
        si = _find_flag(tokens, "--strategy")
        if si >= 0 and si + 1 < len(tokens):
            strategy = tokens[si + 1]

        # Repair freeze path.
        fi = _find_flag(tokens, "--freeze-file")
        freeze_ok = False
        if fi >= 0 and fi + 1 < len(tokens):
            fpath = Path(tokens[fi + 1]).expanduser()
            if not fpath.is_absolute():
                fpath = (Path(".").resolve() / fpath).resolve()
            freeze_ok = fpath.exists()
        if not freeze_ok:
            picked = _pick_freeze(strategy, factor)
            if picked:
                tokens = _replace_or_add(tokens, "--freeze-file", picked)
                fixed_count += 1
            else:
                issues.append(f"no freeze file candidate found for factor={factor} strategy={strategy}")

        # Standardize and deconflict decision tag.
        if args.normalize_tag:
            new_tag = _next_standard_tag(
                run_names=run_names,
                reserved=reserved_tags,
                tag_prefix=str(args.tag_prefix),
                tag_date=str(args.tag_date),
            )
            tokens = _replace_or_add(tokens, "--tag", new_tag)
            row["proposed_decision_tag"] = new_tag
            fixed_count += 1
            tag_fixed_count += 1

        # Repair dq path.
        dqi = _find_flag(tokens, "--dq-input-csv")
        dq_value = ""
        if dqi >= 0 and dqi + 1 < len(tokens):
            dq_value = tokens[dqi + 1]
        dq_bad = (not dq_value) or (dq_value == "data/your_input.csv")
        if args.dq_input_csv:
            dqp = Path(args.dq_input_csv).expanduser()
            if dq_bad or not (dqp.resolve().exists() if dqp.is_absolute() else (Path(".").resolve() / dqp).resolve().exists()):
                tokens = _replace_or_add(tokens, "--dq-input-csv", args.dq_input_csv)
                fixed_count += 1
        else:
            # no injected dq path; validate current
            if dq_bad and not args.allow_missing_dq:
                issues.append(f"dq-input-csv unresolved for factor={factor}")

        fixed_row = dict(row)
        fixed_row["command"] = " ".join(shlex.quote(t) for t in tokens)
        fixed_cmds.append(fixed_row)

    out = dict(plan)
    out["generated_at"] = dt.datetime.now().isoformat()
    out["source_plan_json"] = str(plan_json)
    out["commands"] = fixed_cmds
    out["repair_summary"] = {
        "fixed_count": fixed_count,
        "tag_fixed_count": tag_fixed_count,
        "issue_count": len(issues),
        "issues": issues,
    }

    out_json = Path(args.out_json).resolve()
    _write_json(out_json, out)

    out_md = Path(args.out_md).resolve()
    lines = [
        "# Next Run Plan (Fixed Paths)",
        "",
        f"- generated_at: {out['generated_at']}",
        f"- source_plan_json: `{plan_json}`",
        f"- fixed_count: {fixed_count}",
        f"- tag_fixed_count: {tag_fixed_count}",
        f"- issue_count: {len(issues)}",
        "",
        "## Issues",
        "",
    ]
    if issues:
        for x in issues:
            lines.append(f"- {x}")
    else:
        lines.append("- none")
    lines += ["", "## Commands", ""]
    for c in fixed_cmds:
        lines.append(f"- rank {c.get('rank')} `{c.get('factor')}`: `{c.get('command')}`")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n")

    print(f"[done] fixed_plan_json={out_json}")
    print(f"[done] fixed_plan_md={out_md}")
    print(f"[done] fixed_count={fixed_count} issue_count={len(issues)}")


if __name__ == "__main__":
    main()
