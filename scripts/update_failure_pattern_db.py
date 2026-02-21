#!/usr/bin/env python3
"""Update failure pattern database from governance remediation outputs."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _latest(pattern: str) -> Path | None:
    cands = sorted(Path(".").glob(pattern), key=lambda p: p.stat().st_mtime)
    return cands[-1] if cands else None


def _load_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _build_rows(rem: dict[str, Any], audit: dict[str, Any], source_remediation: Path) -> list[dict[str, Any]]:
    run_dir = str(rem.get("run_dir") or "")
    decision_tag = str(rem.get("decision_tag") or "")
    out: list[dict[str, Any]] = []
    for it in rem.get("remediation_items") or []:
        rid = str(it.get("id") or "")
        severity = str(it.get("severity") or "")
        domain = str(it.get("domain") or "")
        failure = str(it.get("failure") or "")
        action = str(it.get("action") or "")
        key = f"{decision_tag}|{domain}|{failure}"
        out.append(
            {
                "recorded_at": dt.datetime.now().isoformat(),
                "decision_tag": decision_tag,
                "run_dir": run_dir,
                "severity": severity,
                "domain": domain,
                "failure": failure,
                "action": action,
                "remediation_id": rid,
                "audit_overall_pass": audit.get("overall_pass"),
                "source_remediation_json": str(source_remediation),
                "pattern_key": key,
            }
        )
    return out


def _write_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sev = Counter(str(r.get("severity", "")) for r in rows)
    dom = Counter(str(r.get("domain", "")) for r in rows)
    fail = Counter(str(r.get("failure", "")) for r in rows)
    lines = [
        "# Failure Pattern Summary",
        "",
        f"- generated_at: {dt.datetime.now().isoformat()}",
        f"- total_records: {len(rows)}",
        "",
        "## By Severity",
        "",
    ]
    if sev:
        for k, v in sev.most_common():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- none")
    lines += ["", "## By Domain", ""]
    if dom:
        for k, v in dom.most_common():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- none")
    lines += ["", "## Top Failures", ""]
    if fail:
        for k, v in fail.most_common(10):
            lines.append(f"- ({v}) {k}")
    else:
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description="Update failure pattern DB from remediation artifacts.")
    p.add_argument("--remediation-json", default="")
    p.add_argument("--audit-json", default="")
    p.add_argument("--db-csv", default="audit/failure_patterns/failure_patterns.csv")
    p.add_argument("--summary-md", default="audit/failure_patterns/failure_pattern_summary.md")
    args = p.parse_args()

    rem_json = (
        Path(args.remediation_json).resolve()
        if args.remediation_json
        else _latest("audit/workstation_runs/*/governance_remediation_plan.json")
    )
    if rem_json is None or not rem_json.exists():
        raise SystemExit("remediation json not found")
    audit_json = (
        Path(args.audit_json).resolve()
        if args.audit_json
        else (rem_json.parent / "governance_audit_check.json")
    )

    rem = _read_json(rem_json)
    audit = _read_json(audit_json) if audit_json.exists() else {}
    new_rows = _build_rows(rem, audit, rem_json)

    db_csv = Path(args.db_csv).resolve()
    old_rows = _load_csv(db_csv)
    keep: dict[str, dict[str, Any]] = {}
    for r in old_rows:
        keep[str(r.get("pattern_key") or "")] = r
    for r in new_rows:
        keep[str(r.get("pattern_key") or "")] = r
    rows = list(keep.values())
    rows = sorted(rows, key=lambda x: str(x.get("recorded_at", "")))
    _write_csv(db_csv, rows)

    summary_md = Path(args.summary_md).resolve()
    _write_summary(summary_md, rows)
    print(f"[done] failure_db_csv={db_csv}")
    print(f"[done] failure_summary_md={summary_md}")
    print(f"[done] rows_total={len(rows)} added={len(new_rows)}")


if __name__ == "__main__":
    main()
