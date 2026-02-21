#!/usr/bin/env python3
"""Generate actionable remediation steps from governance audit results."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _classify_failure(msg: str) -> tuple[str, str, str]:
    s = msg.lower()
    if "data quality" in s or "dq_" in s:
        return (
            "High",
            "DataQuality",
            "Re-run data quality gate with canonical input CSV, fix schema/freshness issues, then rerun official gate.",
        )
    if "decision_tag" in s:
        return (
            "High",
            "Consistency",
            "Align decision_tag across wrapper context and gate report inputs; rerun with single declared tag.",
        )
    if "exit_code" in s:
        return (
            "High",
            "Runtime",
            "Inspect run.log for first failing command, fix root cause, rerun with new decision_tag.",
        )
    if "stage log" in s:
        return (
            "Medium",
            "Ledger",
            "Run finalize script again and verify STAGE_AUDIT_LOG has the decision_tag row.",
        )
    if "report_json" in s or "report_md" in s or "final summary" in s:
        return (
            "High",
            "Artifacts",
            "Recover/sync missing report artifacts, then rerun post-run finalize and governance checks.",
        )
    if "missing required run artifact" in s:
        return (
            "High",
            "Artifacts",
            "Recover or regenerate missing run_dir artifacts (preflight/context/command/log/result).",
        )
    return (
        "Medium",
        "General",
        "Review failure detail and attach a concrete fix plus rerun evidence in incident/change records.",
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Generate remediation plan from governance_audit_check.json.")
    p.add_argument("--audit-json", required=True, help="Path to governance_audit_check.json")
    p.add_argument(
        "--output-dir",
        default="",
        help="Optional output dir. Default: same directory as --audit-json",
    )
    args = p.parse_args()

    audit_json = Path(args.audit_json).expanduser().resolve()
    if not audit_json.exists():
        raise SystemExit(f"audit json not found: {audit_json}")

    audit = _read_json(audit_json)
    failures = audit.get("failures") or []
    details = audit.get("details") or {}
    checks = audit.get("checks") or {}

    out_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else audit_json.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    generated_at = dt.datetime.now().isoformat()
    run_dir = details.get("run_dir")
    decision_tag = details.get("decision_tag")
    overall_pass = bool(audit.get("overall_pass"))

    remediation_items = []
    for idx, failure in enumerate(failures, start=1):
        severity, domain, action = _classify_failure(str(failure))
        remediation_items.append(
            {
                "id": f"RM-{idx:03d}",
                "severity": severity,
                "domain": domain,
                "failure": str(failure),
                "action": action,
            }
        )

    severity_order = {"High": 0, "Medium": 1, "Low": 2}
    remediation_items = sorted(remediation_items, key=lambda x: severity_order.get(x["severity"], 9))

    summary = {
        "generated_at": generated_at,
        "audit_json": str(audit_json),
        "run_dir": run_dir,
        "decision_tag": decision_tag,
        "audit_overall_pass": overall_pass,
        "n_failures": len(failures),
        "n_checks": len(checks),
        "remediation_items": remediation_items,
        "next_step": "No action required." if overall_pass else "Resolve High severity items first, then rerun governance audit.",
    }

    out_json = out_dir / "governance_remediation_plan.json"
    out_md = out_dir / "governance_remediation_plan.md"
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=True))

    lines = [
        "# Governance Remediation Plan",
        "",
        f"- generated_at: {generated_at}",
        f"- audit_json: `{audit_json}`",
        f"- run_dir: `{run_dir}`",
        f"- decision_tag: `{decision_tag}`",
        f"- audit_overall_pass: {overall_pass}",
        f"- n_failures: {len(failures)}",
        "",
        "## Actions",
        "",
    ]
    if remediation_items:
        for item in remediation_items:
            lines.append(
                f"- [{item['severity']}] {item['id']} ({item['domain']}): {item['failure']} -> {item['action']}"
            )
    else:
        lines.append("- none")
    lines += [
        "",
        "## Next Step",
        "",
        f"- {summary['next_step']}",
        "",
        f"- output_json: `{out_json}`",
    ]
    out_md.write_text("\n".join(lines) + "\n")

    print(f"[done] remediation_json={out_json}")
    print(f"[done] remediation_md={out_md}")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
