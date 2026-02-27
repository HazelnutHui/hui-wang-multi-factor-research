#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Rule:
    name: str
    base: Path
    pattern: str
    min_age_days: int


def _iter_candidates(rule: Rule, now_ts: float) -> list[Path]:
    out: list[Path] = []
    if not rule.base.exists():
        return out
    for p in rule.base.glob(rule.pattern):
        try:
            age_days = max(0.0, (now_ts - p.stat().st_mtime) / 86400.0)
        except FileNotFoundError:
            continue
        if age_days >= rule.min_age_days:
            out.append(p)
    return sorted(out)


def _safe_delete_path(p: Path) -> int:
    if p.is_dir():
        size = 0
        for f in p.rglob("*"):
            if f.is_file():
                try:
                    size += f.stat().st_size
                except FileNotFoundError:
                    continue
        shutil.rmtree(p)
        return size
    if p.exists():
        size = p.stat().st_size if p.is_file() else 0
        p.unlink()
        return size
    return 0


def _bytes_h(n: int) -> str:
    x = float(max(0, n))
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if x < 1024.0 or unit == "TB":
            return f"{x:.2f}{unit}"
        x /= 1024.0
    return f"{n}B"


def main() -> int:
    ap = argparse.ArgumentParser(description="Safe cleanup for non-critical artifacts.")
    ap.add_argument("--root", default=".", help="Project root")
    ap.add_argument("--out-dir", default="audit/cleanup")
    ap.add_argument("--apply", action="store_true", help="Actually delete candidates (default: dry-run)")
    ap.add_argument("--max-delete-items", type=int, default=500, help="Safety cap for apply mode")
    args = ap.parse_args()

    root = (Path(args.root).expanduser().resolve())
    now = datetime.now(timezone.utc)
    now_ts = now.timestamp()

    rules = [
        Rule("wf_debug_dirs", root / "walk_forward_results", "debug_*", 3),
        Rule("dq_auto_daily_runs", root / "gate_results" / "data_quality_auto_daily", "data_quality_*", 7),
        Rule("dq_recheck_runs", root / "gate_results", "data_quality_recheck_*", 7),
        Rule("auto_research_alert_selftest", root / "audit" / "auto_research", "*_alert_selftest", 7),
        Rule("python_cache_dirs", root / "scripts", "__pycache__", 1),
    ]

    candidates: list[dict] = []
    for r in rules:
        for p in _iter_candidates(r, now_ts):
            candidates.append({"rule": r.name, "path": str(p)})

    planned_count = len(candidates)
    planned_paths = [Path(x["path"]) for x in candidates]

    deleted_count = 0
    deleted_bytes = 0
    errors: list[dict] = []

    if args.apply and planned_count > args.max_delete_items:
        errors.append(
            {
                "type": "safety_cap",
                "message": f"planned_count={planned_count} exceeds max_delete_items={args.max_delete_items}",
            }
        )
    elif args.apply:
        for p in planned_paths:
            try:
                deleted_bytes += _safe_delete_path(p)
                deleted_count += 1
            except Exception as e:
                errors.append({"type": "delete_error", "path": str(p), "message": str(e)})

    mode = "apply" if args.apply else "dry_run"
    out_dir = (root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y-%m-%d_%H%M%S")
    out_json = out_dir / f"cleanup_report_{stamp}.json"
    out_md = out_dir / f"cleanup_report_{stamp}.md"
    latest_json = out_dir / "cleanup_report_latest.json"
    latest_md = out_dir / "cleanup_report_latest.md"

    report = {
        "generated_at": now.isoformat(),
        "mode": mode,
        "overall_pass": len(errors) == 0,
        "planned_count": planned_count,
        "deleted_count": deleted_count,
        "deleted_bytes": deleted_bytes,
        "rules": [{"name": r.name, "base": str(r.base), "pattern": r.pattern, "min_age_days": r.min_age_days} for r in rules],
        "candidates": candidates[:1000],
        "errors": errors,
    }
    out_json.write_text(json.dumps(report, indent=2))
    latest_json.write_text(json.dumps(report, indent=2))

    lines = [
        "# Safe Artifact Cleanup Report",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- mode: `{mode}`",
        f"- overall_pass: {str(report['overall_pass']).lower()}",
        f"- planned_count: {planned_count}",
        f"- deleted_count: {deleted_count}",
        f"- deleted_bytes: {_bytes_h(deleted_bytes)}",
        "",
        "## Rules",
        "",
    ]
    for r in report["rules"]:
        lines.append(f"- `{r['name']}`: base=`{r['base']}`, pattern=`{r['pattern']}`, min_age_days={r['min_age_days']}")
    lines += ["", "## Candidates (first 30)", ""]
    if candidates:
        for c in candidates[:30]:
            lines.append(f"- `{c['rule']}` -> `{c['path']}`")
        if len(candidates) > 30:
            lines.append(f"- ... and {len(candidates) - 30} more")
    else:
        lines.append("- none")
    lines += ["", "## Errors", ""]
    if errors:
        for e in errors[:30]:
            lines.append(f"- `{e}`")
    else:
        lines.append("- none")

    out_md.write_text("\n".join(lines))
    latest_md.write_text("\n".join(lines))

    print(f"[done] report_json={out_json}")
    print(f"[done] report_md={out_md}")
    print(f"[done] report_json_latest={latest_json}")
    print(f"[done] report_md_latest={latest_md}")
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

