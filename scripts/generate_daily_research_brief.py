#!/usr/bin/env python3
"""
Generate a concise daily brief:
- auto checks status (pass/fail)
- minimal manual decision section (if needed)
"""

from __future__ import annotations

import argparse
import glob
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _latest_glob(pattern: str) -> Path | None:
    xs = sorted(glob.glob(pattern))
    return Path(xs[-1]) if xs else None


def _load_json(p: Path | None) -> dict:
    if p is None or not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def _fmt_bool(v: bool | None) -> str:
    if v is True:
        return "PASS ✅"
    if v is False:
        return "FAIL ❌"
    return "N/A"


def _latest_gate_overall_pass(root: Path) -> tuple[bool | None, str]:
    p = _latest_glob(str(root / "gate_results" / "production_gates_*" / "production_gates_report.json"))
    if p is None:
        return (None, "")
    j = _load_json(p)
    if not j:
        return (None, str(p))
    top = j.get("overall_pass")
    if isinstance(top, bool):
        return (top, str(p))
    gates = j.get("gates")
    if isinstance(gates, dict) and isinstance(gates.get("overall_pass"), bool):
        return (gates.get("overall_pass"), str(p))
    return (None, str(p))


def _latest_command_surface_pass(root: Path) -> tuple[bool | None, str]:
    p = _latest_glob(str(root / "audit" / "command_surface" / "command_surface_check*.json"))
    if p is None:
        return (None, "")
    j = _load_json(p)
    if not j:
        return (None, str(p))
    v = j.get("overall_pass")
    return (v if isinstance(v, bool) else None, str(p))


def _latest_cleanup_status(root: Path) -> tuple[bool | None, int | None, str]:
    p = _latest_glob(str(root / "audit" / "cleanup" / "cleanup_report*.json"))
    if p is None:
        return (None, None, "")
    j = _load_json(p)
    if not j:
        return (None, None, str(p))
    overall = j.get("overall_pass")
    planned = j.get("planned_count")
    return (
        overall if isinstance(overall, bool) else None,
        planned if isinstance(planned, int) else None,
        str(p),
    )


def _latest_script_surface_status(root: Path) -> tuple[bool | None, int | None, str]:
    p = _latest_glob(str(root / "audit" / "script_surface" / "script_surface_check*.json"))
    if p is None:
        return (None, None, "")
    j = _load_json(p)
    if not j:
        return (None, None, str(p))
    overall = j.get("overall_pass")
    cnt = j.get("unreferenced_count")
    return (
        overall if isinstance(overall, bool) else None,
        cnt if isinstance(cnt, int) else None,
        str(p),
    )


def _official_run_status(root: Path) -> tuple[str, str, str]:
    """
    Returns:
    - status: in_progress/success/fail/none
    - run_dir: path string or ""
    - decision_tag: tag string or ""
    """
    run_dirs = sorted(glob.glob(str(root / "audit" / "workstation_runs" / "*_production_gates_*")))
    if not run_dirs:
        return ("none", "", "")
    # Prefer the latest run directory that has context.json (actual wrapper runtime started).
    selected: Path | None = None
    for d in reversed(run_dirs):
        p = Path(d)
        if (p / "context.json").exists():
            selected = p
            break
    if selected is None:
        selected = Path(run_dirs[-1])

    run_dir = selected
    ctx = _load_json(run_dir / "context.json")
    decision_tag = str(ctx.get("decision_tag", "")) if ctx else ""
    result = _load_json(run_dir / "result.json")
    if result:
        rc = result.get("exit_code")
        if rc == 0:
            return ("success", str(run_dir), decision_tag)
        return ("fail", str(run_dir), decision_tag)
    pre = _load_json(run_dir / "preflight.json")
    if pre and pre.get("status") == "fail":
        return ("preflight_fail", str(run_dir), decision_tag)
    if (run_dir / "run.log").exists():
        return ("in_progress", str(run_dir), decision_tag)
    return ("unknown", str(run_dir), decision_tag)


def _remote_official_run_status(host: str, remote_root: str, timeout_sec: int) -> tuple[str, str, str]:
    """
    Returns remote status in the same shape as _official_run_status.
    status can additionally be:
    - unreachable
    - remote_run_not_found
    - remote_parse_error
    """
    script = (
        "set -e;"
        f"cd {remote_root};"
        "RUN_DIR=$(ls -td audit/workstation_runs/*_production_gates_* 2>/dev/null | head -n1 || true);"
        "if [ -z \"$RUN_DIR\" ]; then echo status=remote_run_not_found; exit 0; fi;"
        "echo run_dir=$RUN_DIR;"
        "TAG=\"\";"
        "if [ -f \"$RUN_DIR/context.json\" ]; then "
        "  TAG=$(python3 -c \"import json,sys;print(json.load(open(sys.argv[1])).get('decision_tag',''))\" "
        "\"$RUN_DIR/context.json\" 2>/dev/null || true);"
        "fi;"
        "echo decision_tag=$TAG;"
        "if [ -f \"$RUN_DIR/result.json\" ]; then "
        "  RC=$(python3 -c \"import json,sys;print(json.load(open(sys.argv[1])).get('exit_code',''))\" "
        "\"$RUN_DIR/result.json\" 2>/dev/null || true);"
        "  if [ \"$RC\" = \"0\" ]; then echo status=success; else echo status=fail; fi;"
        "elif [ -f \"$RUN_DIR/preflight.json\" ]; then "
        "  PRE=$(python3 -c \"import json,sys;print(json.load(open(sys.argv[1])).get('status',''))\" "
        "\"$RUN_DIR/preflight.json\" 2>/dev/null || true);"
        "  if [ \"$PRE\" = \"fail\" ]; then echo status=preflight_fail; else echo status=in_progress; fi;"
        "elif [ -f \"$RUN_DIR/run.log\" ]; then "
        "  echo status=in_progress;"
        "else "
        "  echo status=unknown;"
        "fi;"
    )
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={timeout_sec}",
        host,
        script,
    ]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=max(2, timeout_sec + 1))
    except Exception:
        return ("unreachable", "", "")

    kv = {}
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            kv[k.strip()] = v.strip()
    status = kv.get("status")
    run_dir = kv.get("run_dir", "")
    tag = kv.get("decision_tag", "")
    if not status:
        return ("remote_parse_error", run_dir, tag)
    return (status, run_dir, tag)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate short daily dev/research brief.")
    ap.add_argument("--root", default=".", help="Project root")
    ap.add_argument("--out-md", default="audit/daily/daily_research_brief_latest.md")
    ap.add_argument("--decision-note", default="")
    ap.add_argument("--remote-host", default="")
    ap.add_argument("--remote-root", default="")
    ap.add_argument("--remote-timeout-sec", type=int, default=5)
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    out_md = (root / args.out_md).resolve() if not Path(args.out_md).is_absolute() else Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    dq_json = _latest_glob(str(root / "gate_results" / "data_quality*" / "data_quality_*" / "data_quality_report.json"))
    dq = _load_json(dq_json)
    dq_pass = dq.get("overall_pass") if dq else None

    fixed_plan = root / "audit" / "factor_registry" / "next_run_plan_fixed.json"
    plan = _load_json(fixed_plan)
    items = []
    if isinstance(plan, dict):
        if isinstance(plan.get("commands"), list):
            items = plan["commands"]
        elif isinstance(plan.get("items"), list):
            items = plan["items"]
    first_cmd = ""
    if items and isinstance(items[0], dict):
        first_cmd = str(items[0].get("command", ""))
    dry_ok = ("data/your_input.csv" not in first_cmd) and ("--workflow production_gates" in first_cmd)

    orch_json = _latest_glob(
        str(root / "audit" / "auto_research" / "*_orchestrator" / "auto_research_orchestrator_report.json")
    )
    orch = _load_json(orch_json)
    stopped_reason = orch.get("stopped_reason") if orch else None

    official_status, official_run_dir, official_tag = _official_run_status(root)
    official_status_source = "local"
    if args.remote_host and args.remote_root:
        r_status, r_run_dir, r_tag = _remote_official_run_status(
            host=args.remote_host,
            remote_root=args.remote_root,
            timeout_sec=max(2, args.remote_timeout_sec),
        )
        if r_status not in {"unreachable", "remote_parse_error"}:
            official_status, official_run_dir, official_tag = r_status, r_run_dir, r_tag
            official_status_source = "remote"
        else:
            official_status_source = f"local_fallback({r_status})"
    gate_overall_pass, gate_report_json = _latest_gate_overall_pass(root)
    command_surface_pass, command_surface_json = _latest_command_surface_pass(root)
    cleanup_ok, cleanup_planned_count, cleanup_json = _latest_cleanup_status(root)
    script_surface_ok, script_surface_unreferenced, script_surface_json = _latest_script_surface_status(root)

    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Daily Research Brief",
        "",
        f"- generated_at: {now}",
        "",
        "## Auto Checks",
        "",
        f"- dq_overall_pass: {_fmt_bool(dq_pass if isinstance(dq_pass, bool) else None)}",
        f"- plan_validation_ready: {_fmt_bool(dry_ok)}",
        f"- latest_orchestrator_stopped_reason: `{stopped_reason}`" if stopped_reason else "- latest_orchestrator_stopped_reason: N/A",
        f"- latest_official_wrapper_status: `{official_status}`",
        f"- latest_official_status_source: `{official_status_source}`",
        f"- latest_official_decision_tag: `{official_tag}`" if official_tag else "- latest_official_decision_tag: N/A",
        f"- latest_official_run_dir: `{official_run_dir}`" if official_run_dir else "- latest_official_run_dir: N/A",
        f"- latest_gate_overall_pass: {_fmt_bool(gate_overall_pass)}",
        f"- latest_gate_report_json: `{gate_report_json}`" if gate_report_json else "- latest_gate_report_json: N/A",
        f"- command_surface_ok: {_fmt_bool(command_surface_pass)}",
        f"- command_surface_report_json: `{command_surface_json}`" if command_surface_json else "- command_surface_report_json: N/A",
        f"- cleanup_preview_ok: {_fmt_bool(cleanup_ok)}",
        (
            f"- cleanup_preview_planned_count: `{cleanup_planned_count}`"
            if isinstance(cleanup_planned_count, int)
            else "- cleanup_preview_planned_count: N/A"
        ),
        f"- cleanup_report_json: `{cleanup_json}`" if cleanup_json else "- cleanup_report_json: N/A",
        f"- script_surface_ok: {_fmt_bool(script_surface_ok)}",
        (
            f"- script_surface_unreferenced_count: `{script_surface_unreferenced}`"
            if isinstance(script_surface_unreferenced, int)
            else "- script_surface_unreferenced_count: N/A"
        ),
        f"- script_surface_report_json: `{script_surface_json}`" if script_surface_json else "- script_surface_report_json: N/A",
        "",
        "## Manual Decisions Needed",
        "",
    ]

    manual = []
    if dq_pass is False:
        manual.append("DQ failed: decide whether to refresh source snapshot or relax policy thresholds.")
    if not dry_ok:
        manual.append("Plan not validation-ready: decide whether to block official run.")
    if stopped_reason in {"validation_failed"}:
        manual.append("Orchestrator validation failed: confirm whether to pause automation and inspect plan.")
    if gate_overall_pass is False:
        manual.append("Latest gate overall_pass is False: decide rerun scope vs hypothesis/data-boundary change.")
    if official_status == "fail":
        manual.append("Latest official run failed: decide rerun scope and whether to expand data boundary or adjust hypotheses.")
    if command_surface_pass is False:
        manual.append("Command surface drift detected in docs: decide whether to block doc merge until fixed.")
    if isinstance(cleanup_planned_count, int) and cleanup_planned_count > 0:
        manual.append("Cleanup preview found removable artifacts: decide whether to run `ops_entry.sh cleanup --apply`.")
    if isinstance(script_surface_unreferenced, int) and script_surface_unreferenced > 0:
        manual.append("Script surface found unreferenced candidates: decide whether to deprecate/delete them in batches.")
    if args.decision_note:
        manual.append(args.decision_note)

    if manual:
        for m in manual[:3]:
            lines.append(f"- {m}")
    else:
        lines.append("- none")

    out_md.write_text("\n".join(lines))
    print(f"[done] out_md={out_md}")


if __name__ == "__main__":
    main()
