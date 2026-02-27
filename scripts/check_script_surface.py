#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _rg_count(token: str) -> int:
    cmd = [
        "rg",
        "-n",
        "--fixed-strings",
        token,
        str(ROOT),
        "--glob",
        "!scripts/*",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode not in (0, 1):
        return -1
    if not p.stdout:
        return 0
    return len([ln for ln in p.stdout.splitlines() if ln.strip()])


def main() -> int:
    ap = argparse.ArgumentParser(description="Check script reference surface in repository.")
    ap.add_argument("--out-dir", default="audit/script_surface")
    args = ap.parse_args()

    scripts_dir = ROOT / "scripts"
    scripts = sorted([p for p in scripts_dir.iterdir() if p.is_file()])
    rows = []
    for p in scripts:
        bn = p.name
        cnt = _rg_count(bn)
        rows.append({"script": bn, "ref_count_excluding_scripts_dir": cnt})

    unreferenced = [r["script"] for r in rows if r["ref_count_excluding_scripts_dir"] == 0]
    now = datetime.now(timezone.utc).isoformat()
    report = {
        "generated_at": now,
        "overall_pass": True,
        "scripts_total": len(rows),
        "unreferenced_count": len(unreferenced),
        "unreferenced_scripts": unreferenced,
        "rows": rows,
        "note": "unreferenced means not found outside scripts/ by filename token; manual usage may still exist",
    }

    out_dir = (ROOT / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "script_surface_check.json"
    out_md = out_dir / "script_surface_check.md"

    out_json.write_text(json.dumps(report, indent=2))
    lines = [
        "# Script Surface Check",
        "",
        f"- generated_at: {now}",
        f"- scripts_total: {report['scripts_total']}",
        f"- unreferenced_count: {report['unreferenced_count']}",
        f"- overall_pass: {str(report['overall_pass']).lower()}",
        "",
        "## Unreferenced Candidates",
        "",
    ]
    if unreferenced:
        for s in unreferenced[:60]:
            lines.append(f"- `{s}`")
        if len(unreferenced) > 60:
            lines.append(f"- ... and {len(unreferenced) - 60} more")
    else:
        lines.append("- none")
    lines += ["", "## Note", "", f"- {report['note']}"]
    out_md.write_text("\n".join(lines))

    print(f"[done] report_json={out_json}")
    print(f"[done] report_md={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

