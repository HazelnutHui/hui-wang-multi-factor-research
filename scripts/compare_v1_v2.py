#!/usr/bin/env python3
"""
Compare v1 vs v2 factor results across three validation layers:
1) Segmented
2) Fixed train/test
3) Walk-forward

The script is resilient to partial/missing outputs and picks latest artifacts by mtime.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


FACTOR_BASES = ["value", "momentum", "reversal", "low_vol", "quality", "pead"]


@dataclass
class LayerMetric:
    ic_mean: Optional[float] = None
    ic_std: Optional[float] = None
    pos_ratio: Optional[float] = None
    n: int = 0
    source: str = ""


@dataclass
class TrainTestMetric:
    train_ic: Optional[float] = None
    test_ic: Optional[float] = None
    source: str = ""


@dataclass
class CompareRow:
    factor: str
    seg_v1: LayerMetric
    seg_v2: LayerMetric
    tt_v1: TrainTestMetric
    tt_v2: TrainTestMetric
    wf_v1: LayerMetric
    wf_v2: LayerMetric


def _to_float(v) -> Optional[float]:
    try:
        x = float(v)
        if pd.isna(x):
            return None
        return x
    except Exception:
        return None


def _latest_file(paths: list[Path]) -> Optional[Path]:
    if not paths:
        return None
    paths = [p for p in paths if p.exists()]
    if not paths:
        return None
    return max(paths, key=lambda p: p.stat().st_mtime)


def _metric_from_segment_files(paths: list[Path]) -> LayerMetric:
    if not paths:
        return LayerMetric()
    dfs = []
    used = []
    for p in paths:
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        if "ic" not in df.columns:
            continue
        dfs.append(df)
        used.append(str(p))
    if not dfs:
        return LayerMetric(source="; ".join(str(p) for p in paths))
    all_df = pd.concat(dfs, ignore_index=True)
    if {"segment_start", "segment_end"}.issubset(all_df.columns):
        all_df = all_df.drop_duplicates(subset=["segment_start", "segment_end"])
    ic = pd.to_numeric(all_df["ic"], errors="coerce")
    valid = ic.dropna()
    if len(valid) == 0:
        return LayerMetric(n=0, source="; ".join(used))
    return LayerMetric(
        ic_mean=_to_float(valid.mean()),
        ic_std=_to_float(valid.std()),
        pos_ratio=_to_float((valid > 0).mean()),
        n=int(len(valid)),
        source="; ".join(used),
    )


def _metric_from_walkforward_file(path: Optional[Path]) -> LayerMetric:
    if path is None:
        return LayerMetric()
    try:
        df = pd.read_csv(path)
    except Exception:
        return LayerMetric(source=str(path))
    col = "test_ic"
    if col not in df.columns:
        return LayerMetric(source=str(path))
    ic = pd.to_numeric(df[col], errors="coerce")
    valid = ic.dropna()
    if len(valid) == 0:
        return LayerMetric(n=0, source=str(path))
    return LayerMetric(
        ic_mean=_to_float(valid.mean()),
        ic_std=_to_float(valid.std()),
        pos_ratio=_to_float((valid > 0).mean()),
        n=int(len(valid)),
        source=str(path),
    )


def _metric_from_run_json(path: Optional[Path]) -> TrainTestMetric:
    if path is None:
        return TrainTestMetric()
    try:
        d = json.loads(path.read_text())
    except Exception:
        return TrainTestMetric(source=str(path))

    # Preferred: oos_analysis at top-level (run.py reports)
    train_ic = _to_float((d.get("performance", {}).get("oos", {}) or {}).get("train_ic"))
    test_ic = _to_float((d.get("performance", {}).get("oos", {}) or {}).get("test_ic"))

    # Fallback: analysis structure
    if train_ic is None:
        train_ic = _to_float((d.get("performance", {}).get("train", {}) or {}).get("ic"))
    if test_ic is None:
        test_ic = _to_float((d.get("performance", {}).get("test", {}) or {}).get("ic"))

    return TrainTestMetric(train_ic=train_ic, test_ic=test_ic, source=str(path))


def _find_segment_metric(root: Path, factor_name: str) -> LayerMetric:
    merged = list(root.glob(f"segment_results/**/merged/{factor_name}/segment_summary.csv"))
    if merged:
        return _metric_from_segment_files(merged)

    candidates = list(root.glob(f"segment_results/**/{factor_name}/segment_summary.csv"))
    return _metric_from_segment_files(candidates)


def _find_traintest_metric(root: Path, strategy_dir: str) -> TrainTestMetric:
    candidates = list(root.glob(f"strategies/{strategy_dir}/runs/*.json"))
    p = _latest_file(candidates)
    return _metric_from_run_json(p)


def _find_walkforward_metric(root: Path, factor_name: str) -> LayerMetric:
    candidates = list(root.glob(f"walk_forward_results/**/{factor_name}/walk_forward_summary.csv"))
    p = _latest_file(candidates)
    return _metric_from_walkforward_file(p)


def _fmt(v: Optional[float], nd: int = 6) -> str:
    if v is None:
        return "NA"
    return f"{v:.{nd}f}"


def _recommend(row: CompareRow) -> str:
    # Priority: segmented + walk-forward test_ic consistency, then train/test test_ic.
    score = 0

    if row.seg_v2.ic_mean is not None and row.seg_v1.ic_mean is not None:
        score += 1 if row.seg_v2.ic_mean > row.seg_v1.ic_mean else -1
    if row.wf_v2.ic_mean is not None and row.wf_v1.ic_mean is not None:
        score += 2 if row.wf_v2.ic_mean > row.wf_v1.ic_mean else -2
    if row.tt_v2.test_ic is not None and row.tt_v1.test_ic is not None:
        score += 1 if row.tt_v2.test_ic > row.tt_v1.test_ic else -1

    if score >= 2:
        return "Prefer v2"
    if score <= -2:
        return "Keep v1"
    return "Need more data"


def build_rows(root: Path) -> list[CompareRow]:
    rows: list[CompareRow] = []
    for f in FACTOR_BASES:
        seg_v1 = _find_segment_metric(root, f)
        seg_v2 = _find_segment_metric(root, f"{f}_v2")

        tt_v1 = _find_traintest_metric(root, f"{f}_v1")
        tt_v2 = _find_traintest_metric(root, f"{f}_v2")

        wf_v1 = _find_walkforward_metric(root, f)
        wf_v2 = _find_walkforward_metric(root, f"{f}_v2")

        rows.append(
            CompareRow(
                factor=f,
                seg_v1=seg_v1,
                seg_v2=seg_v2,
                tt_v1=tt_v1,
                tt_v2=tt_v2,
                wf_v1=wf_v1,
                wf_v2=wf_v2,
            )
        )
    return rows


def to_dataframe(rows: list[CompareRow]) -> pd.DataFrame:
    out = []
    for r in rows:
        out.append(
            {
                "factor": r.factor,
                "seg_ic_v1": r.seg_v1.ic_mean,
                "seg_ic_v2": r.seg_v2.ic_mean,
                "seg_delta_v2_minus_v1": None
                if r.seg_v1.ic_mean is None or r.seg_v2.ic_mean is None
                else r.seg_v2.ic_mean - r.seg_v1.ic_mean,
                "tt_test_ic_v1": r.tt_v1.test_ic,
                "tt_test_ic_v2": r.tt_v2.test_ic,
                "wf_test_ic_mean_v1": r.wf_v1.ic_mean,
                "wf_test_ic_mean_v2": r.wf_v2.ic_mean,
                "recommendation": _recommend(r),
            }
        )
    df = pd.DataFrame(out)
    return df


def print_report(rows: list[CompareRow], df: pd.DataFrame) -> None:
    print("=== V1 vs V2 Comparison (3-layer) ===")
    print(df.to_string(index=False))
    print()
    print("=== Detail (sources) ===")
    for r in rows:
        print(f"[{r.factor}]")
        print(
            "  segmented: "
            f"v1={_fmt(r.seg_v1.ic_mean)} (n={r.seg_v1.n}) | "
            f"v2={_fmt(r.seg_v2.ic_mean)} (n={r.seg_v2.n})"
        )
        print(
            "  train/test test_ic: "
            f"v1={_fmt(r.tt_v1.test_ic)} | v2={_fmt(r.tt_v2.test_ic)}"
        )
        print(
            "  walk-forward test_ic_mean: "
            f"v1={_fmt(r.wf_v1.ic_mean)} (n={r.wf_v1.n}) | "
            f"v2={_fmt(r.wf_v2.ic_mean)} (n={r.wf_v2.n})"
        )
        print(f"  recommendation: {_recommend(r)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Project root (default: .)")
    parser.add_argument("--out-csv", default="", help="Optional output csv path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rows = build_rows(root)
    df = to_dataframe(rows)
    print_report(rows, df)

    if args.out_csv:
        out = Path(args.out_csv)
        if not out.is_absolute():
            out = root / out
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False)
        print(f"\nSaved csv: {out}")


if __name__ == "__main__":
    main()
