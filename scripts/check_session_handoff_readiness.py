#!/usr/bin/env python3
"""Check whether session handoff docs/artifacts are readable and linked."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


def _section_lines(lines: list[str], start_pat: str, end_pat: str) -> list[str]:
    start = -1
    end = len(lines)
    for i, line in enumerate(lines):
        if re.search(start_pat, line):
            start = i + 1
            break
    if start < 0:
        return []
    for i in range(start, len(lines)):
        if re.search(end_pat, lines[i]):
            end = i
            break
    return lines[start:end]


def _extract_ordered_paths(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        m = re.match(r"^\s*\d+\.\s+`([^`]+)`\s*$", line.strip())
        if m:
            out.append(m.group(1).strip())
    return out


def _extract_backtick_paths(lines: list[str]) -> list[str]:
    paths: list[str] = []
    for line in lines:
        for m in re.finditer(r"`([^`]+)`", line):
            candidate = m.group(1).strip()
            if "/" in candidate or candidate.endswith(".md"):
                paths.append(candidate)
    dedup: list[str] = []
    seen: set[str] = set()
    for p in paths:
        if p not in seen:
            dedup.append(p)
            seen.add(p)
    return dedup


def _exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _check_index_linkage(index_text: str, paths: list[str]) -> dict[str, bool]:
    exempt = {"DOCS_INDEX.md", "CODEX_SESSION_GUIDE.md"}
    out: dict[str, bool] = {}
    for p in paths:
        if p in exempt:
            out[p] = True
            continue
        out[p] = p in index_text
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Session handoff readiness checker.")
    p.add_argument("--guide", default="CODEX_SESSION_GUIDE.md")
    p.add_argument("--docs-index", default="DOCS_INDEX.md")
    p.add_argument("--out-json", default="audit/session_handoff/handoff_readiness.json")
    p.add_argument("--out-md", default="audit/session_handoff/handoff_readiness.md")
    args = p.parse_args()

    root = Path(".").resolve()
    guide = (root / args.guide).resolve()
    docs_index = (root / args.docs_index).resolve()
    if not guide.exists():
        raise SystemExit(f"guide not found: {guide}")
    if not docs_index.exists():
        raise SystemExit(f"docs index not found: {docs_index}")

    guide_lines = _load_text(guide).splitlines()
    docs_index_text = _load_text(docs_index)

    read_block = _section_lines(
        guide_lines,
        r"^##\s*3\)\s*Mandatory Read Sequence With Completion Checks",
        r"^##\s*4\)",
    )
    read_paths = _extract_ordered_paths(read_block)

    completion_block = []
    in_completion = False
    for line in read_block:
        if line.strip().lower().startswith("completion check"):
            in_completion = True
            continue
        if in_completion:
            completion_block.append(line)
    completion_paths = _extract_backtick_paths(completion_block)

    read_exists = {p: _exists(root, p) for p in read_paths}
    completion_exists = {p: _exists(root, p) for p in completion_paths}
    read_linked = _check_index_linkage(docs_index_text, read_paths)
    completion_linked = _check_index_linkage(docs_index_text, completion_paths)

    read_missing = [k for k, v in read_exists.items() if not v]
    completion_missing = [k for k, v in completion_exists.items() if not v]
    read_unlinked = [k for k, v in read_linked.items() if not v]
    completion_unlinked = [k for k, v in completion_linked.items() if not v]

    summary = {
        "read_count": len(read_paths),
        "completion_ref_count": len(completion_paths),
        "read_missing_count": len(read_missing),
        "completion_missing_count": len(completion_missing),
        "read_unlinked_count": len(read_unlinked),
        "completion_unlinked_count": len(completion_unlinked),
    }
    overall_pass = (
        summary["read_count"] > 0
        and summary["read_missing_count"] == 0
        and summary["completion_missing_count"] == 0
        and summary["read_unlinked_count"] == 0
    )

    payload: dict[str, Any] = {
        "generated_at": dt.datetime.now().isoformat(),
        "guide": str(guide),
        "docs_index": str(docs_index),
        "summary": summary,
        "overall_pass": overall_pass,
        "read_paths": read_paths,
        "completion_paths": completion_paths,
        "read_exists": read_exists,
        "completion_exists": completion_exists,
        "read_linked_in_docs_index": read_linked,
        "completion_linked_in_docs_index": completion_linked,
        "issues": {
            "read_missing": read_missing,
            "completion_missing": completion_missing,
            "read_unlinked": read_unlinked,
            "completion_unlinked": completion_unlinked,
        },
    }

    out_json = (root / args.out_json).resolve()
    out_md = (root / args.out_md).resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=True))

    lines = [
        "# Session Handoff Readiness",
        "",
        f"- generated_at: {payload['generated_at']}",
        f"- overall_pass: {overall_pass}",
        f"- guide: `{guide}`",
        f"- docs_index: `{docs_index}`",
        "",
        "## Summary",
        "",
        f"- read_count: {summary['read_count']}",
        f"- completion_ref_count: {summary['completion_ref_count']}",
        f"- read_missing_count: {summary['read_missing_count']}",
        f"- completion_missing_count: {summary['completion_missing_count']}",
        f"- read_unlinked_count: {summary['read_unlinked_count']}",
        f"- completion_unlinked_count: {summary['completion_unlinked_count']}",
        "",
        "## Issues",
        "",
    ]
    if any(payload["issues"].values()):
        for k, vals in payload["issues"].items():
            if not vals:
                continue
            lines.append(f"- {k}:")
            for v in vals:
                lines.append(f"  - `{v}`")
    else:
        lines.append("- none")
    lines += ["", f"- output_json: `{out_json}`"]
    out_md.write_text("\n".join(lines) + "\n")

    print(f"[done] handoff_readiness_json={out_json}")
    print(f"[done] handoff_readiness_md={out_md}")
    raise SystemExit(0 if overall_pass else 2)


if __name__ == "__main__":
    main()
