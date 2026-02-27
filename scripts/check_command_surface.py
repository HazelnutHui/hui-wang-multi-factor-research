#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _collect_md_files(root: Path) -> list[Path]:
    xs = list(root.glob("*.md"))
    xs += list((root / "docs").rglob("*.md"))
    return sorted({p.resolve() for p in xs if p.is_file()})


def main() -> int:
    ap = argparse.ArgumentParser(description="Check command-surface drift in docs.")
    ap.add_argument(
        "--out-dir",
        default="audit/command_surface",
        help="Output directory for check artifacts",
    )
    args = ap.parse_args()

    out_dir = (ROOT / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    patterns = [
        r"\bbash\s+scripts/daily_research_run\.sh\b",
        r"\bbash\s+scripts/workstation_official_run\.sh\b",
        r"\bpython\s+scripts/generate_daily_research_brief\.py\b",
    ]
    compiled = [re.compile(p) for p in patterns]

    allowed_files = {
        str((ROOT / "docs" / "production_research" / "CHANGELOG.md").resolve()),
    }

    violations: list[dict] = []
    scanned = _collect_md_files(ROOT)
    for p in scanned:
        if str(p) in allowed_files:
            continue
        txt = p.read_text(errors="ignore")
        for i, line in enumerate(txt.splitlines(), start=1):
            for cp in compiled:
                if cp.search(line):
                    violations.append(
                        {
                            "file": str(p.relative_to(ROOT)),
                            "line": i,
                            "match": line.strip(),
                        }
                    )

    now = datetime.now(timezone.utc).isoformat()
    report = {
        "generated_at": now,
        "overall_pass": len(violations) == 0,
        "violations_count": len(violations),
        "checked_md_files": len(scanned),
        "rules": patterns,
        "allowed_files": sorted(str(Path(x).relative_to(ROOT)) for x in allowed_files),
        "violations": violations,
    }

    out_json = out_dir / "command_surface_check.json"
    out_md = out_dir / "command_surface_check.md"
    out_json.write_text(json.dumps(report, indent=2))

    lines = [
        "# Command Surface Check",
        "",
        f"- generated_at: {now}",
        f"- overall_pass: {str(report['overall_pass']).lower()}",
        f"- violations_count: {report['violations_count']}",
        f"- checked_md_files: {report['checked_md_files']}",
        "",
        "## Rules",
        "",
    ]
    for r in patterns:
        lines.append(f"- `{r}`")
    lines += ["", "## Violations", ""]
    if violations:
        for v in violations[:30]:
            lines.append(f"- `{v['file']}:{v['line']}` -> `{v['match']}`")
        if len(violations) > 30:
            lines.append(f"- ... and {len(violations) - 30} more")
    else:
        lines.append("- none")
    out_md.write_text("\n".join(lines))

    print(f"[done] report_json={out_json}")
    print(f"[done] report_md={out_md}")
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

