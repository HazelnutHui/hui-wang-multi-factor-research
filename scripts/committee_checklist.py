#!/usr/bin/env python3
"""
Committee-grade checklist (non-invasive).
Aggregates:
  - latest segment stability (IC mean/std/positive%)
  - latest Train/Test IC
  - post-hoc diagnostics (beta/turnover/industry/size)

Does NOT modify any backtest outputs.
"""

import json
from pathlib import Path
from datetime import datetime

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

STRATEGY_TO_FACTOR = {
    "value_v1": "value",
    "quality_v1": "quality",
    "low_vol_v1": "low_vol",
    "momentum_v1": "momentum",
    "reversal_v1": "reversal",
    "pead_v1": "pead",
}


def _latest_run_json(strategy_dir: Path) -> Path | None:
    runs = strategy_dir / "runs"
    if not runs.exists():
        return None
    files = sorted(runs.glob("*.json"))
    return files[-1] if files else None


def _latest_segment_summaries(factor: str, k: int = 2):
    seg_root = PROJECT_ROOT / "segment_results"
    files = sorted(seg_root.glob(f"*/{factor}/segment_summary.csv"), key=lambda p: p.stat().st_mtime)
    return files[-k:] if files else []


def _segment_stats(path: Path):
    df = pd.read_csv(path)
    if "ic" not in df.columns:
        return {}
    ic = pd.to_numeric(df["ic"], errors="coerce").dropna()
    if len(ic) == 0:
        return {"ic_mean": None, "ic_std": None, "ic_pos_pct": None, "n_segments": 0}
    return {
        "ic_mean": float(ic.mean()),
        "ic_std": float(ic.std(ddof=1)) if len(ic) > 1 else 0.0,
        "ic_pos_pct": float((ic > 0).mean()),
        "n_segments": int(len(ic)),
    }


def _load_json(path: Path):
    return json.loads(path.read_text())


def _read_diagnostics(strategy_dir: Path):
    reports = strategy_dir / "reports"
    if not reports.exists():
        return None
    files = sorted(reports.glob("diagnostics_*.json"))
    if not files:
        return None
    return _load_json(files[-1])


def _ensure_diagnostics(strategy_dir: Path):
    # Lazy import to avoid circular dependency on startup
    from scripts.posthoc_factor_diagnostics import run_diagnostics
    out_dir = strategy_dir / "reports"
    return run_diagnostics(strategy_dir, out_dir)


def _format_summary_row(name, seg_paths, seg_stats, run_json, diag):
    test_ic = None
    train_ic = None
    if run_json:
        perf = run_json.get("performance", {})
        test_ic = perf.get("test", {}).get("ic")
        train_ic = perf.get("train", {}).get("ic")

    diag_info = {}
    if diag:
        d = diag.get("diagnostics", {})
        diag_info = {
            "beta_vs_spy": d.get("beta_vs_spy"),
            "turnover_top_pct_overlap": d.get("turnover_top_pct_overlap"),
            "size_signal_corr_log_mcap": d.get("size_signal_corr_log_mcap"),
        }

    return {
        "strategy": name,
        "segment_summaries": [str(p) for p in seg_paths],
        **seg_stats,
        "train_ic": train_ic,
        "test_ic": test_ic,
        **diag_info,
    }


def main():
    strategies = sorted((PROJECT_ROOT / "strategies").glob("*_v1"))
    results = []
    notes = []

    for strat in strategies:
        factor = STRATEGY_TO_FACTOR.get(strat.name)
        if not factor:
            continue

        results_dir = strat / "results"
        if not results_dir.exists():
            continue

        seg_paths = _latest_segment_summaries(factor, k=2)
        seg_stats = _segment_stats(seg_paths[-1]) if seg_paths else {}
        run_path = _latest_run_json(strat)
        run_json = _load_json(run_path) if run_path else None

        diag = _read_diagnostics(strat)
        if diag is None:
            try:
                _, _ = _ensure_diagnostics(strat)
                diag = _read_diagnostics(strat)
            except Exception as e:
                notes.append(f"{strat.name}: diagnostics skipped ({e})")

        results.append(_format_summary_row(strat.name, seg_paths, seg_stats, run_json, diag))

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = PROJECT_ROOT / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"committee_checklist_{ts}.json"
    md_path = out_dir / f"committee_checklist_{ts}.md"

    json_path.write_text(json.dumps({"generated_at": datetime.now().isoformat(), "rows": results, "notes": notes}, indent=2))

    # Markdown summary
    lines = [
        "# Committee Checklist",
        "",
        f"- Generated at: {datetime.now().isoformat()}",
        "- Segment summaries are chosen as the most recent files by mtime (heuristic).",
        "",
        "| Strategy | Segments (latest) | IC mean | IC std | % positive | Train IC | Test IC | Beta | Turnover(overlap) | Size corr |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        seg = r.get("segment_summaries", [])
        seg_latest = seg[-1] if seg else ""
        lines.append(
            f"| {r.get('strategy')} | {seg_latest} | "
            f"{r.get('ic_mean')} | {r.get('ic_std')} | {r.get('ic_pos_pct')} | "
            f"{r.get('train_ic')} | {r.get('test_ic')} | "
            f"{r.get('beta_vs_spy')} | {r.get('turnover_top_pct_overlap')} | {r.get('size_signal_corr_log_mcap')} |"
        )

    if notes:
        lines += ["", "## Notes"] + [f"- {n}" for n in notes]

    md_path.write_text("\n".join(lines))
    print(f"[ok] {md_path}")


if __name__ == "__main__":
    main()
