#!/usr/bin/env python3
"""
Derive robust combination weights from segmented summary files.

Default universe:
  value_v2, momentum_v2, quality_v2

Scoring:
  score = max(ic_mean, 0) * max(pos_ratio, 0)
  stability = 1 / (1 + max(ic_std, 0))
  raw = score * stability

Then normalize to sum to 1 with floor/cap constraints.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


def _latest_stage2_merged(root: Path, factor: str) -> Path | None:
    candidates = list(root.glob(f"segment_results/**/merged/{factor}/segment_summary.csv"))
    if not candidates:
        return None
    candidates = [p for p in candidates if p.exists()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _fallback_stage1_merged(root: Path, factor: str) -> Path | None:
    p = root / "segment_results" / "stage1_v2_1_parallel" / "merged" / factor / "segment_summary.csv"
    return p if p.exists() else None


def _metrics(path: Path) -> tuple[float | None, float | None, float | None]:
    df = pd.read_csv(path)
    ic = pd.to_numeric(df.get("ic"), errors="coerce")
    valid = ic.dropna()
    if len(valid) == 0:
        return None, None, None
    ic_mean = float(valid.mean())
    ic_std = float(valid.std()) if len(valid) > 1 else 0.0
    pos_ratio = float((valid > 0).mean())
    return ic_mean, ic_std, pos_ratio


def _normalize_with_bounds(raw: dict[str, float], floor: float, cap: float) -> dict[str, float]:
    if not raw:
        return {}
    total = sum(max(v, 0.0) for v in raw.values())
    if total <= 0:
        eq = 1.0 / len(raw)
        return {k: eq for k in raw}
    w = {k: max(v, 0.0) / total for k, v in raw.items()}
    w = {k: min(max(v, floor), cap) for k, v in w.items()}
    s = sum(w.values())
    if s <= 0:
        eq = 1.0 / len(raw)
        return {k: eq for k in raw}
    return {k: v / s for k, v in w.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--factors", default="value_v2,momentum_v2,quality_v2")
    parser.add_argument("--min-weight", type=float, default=0.1)
    parser.add_argument("--max-weight", type=float, default=0.7)
    parser.add_argument("--out", default="segment_results/derived/combo_v2_weights_suggested.csv")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    factors = [f.strip() for f in args.factors.split(",") if f.strip()]
    rows = []
    raw = {}

    for f in factors:
        p = _latest_stage2_merged(root, f)
        source = "stage2_merged_latest"
        if p is None:
            p = _fallback_stage1_merged(root, f)
            source = "stage1_merged_fallback"
        if p is None:
            rows.append([f, None, None, None, 0.0, source, "NOT_FOUND"])
            raw[f] = 0.0
            continue

        ic_mean, ic_std, pos_ratio = _metrics(p)
        if ic_mean is None:
            rows.append([f, None, None, None, 0.0, source, str(p)])
            raw[f] = 0.0
            continue

        score = max(ic_mean, 0.0) * max(pos_ratio, 0.0)
        stability = 1.0 / (1.0 + max(ic_std or 0.0, 0.0))
        raw_score = score * stability
        raw[f] = raw_score
        rows.append([f, ic_mean, ic_std, pos_ratio, raw_score, source, str(p)])

    weights = _normalize_with_bounds(raw, floor=float(args.min_weight), cap=float(args.max_weight))
    out = pd.DataFrame(rows, columns=["factor", "ic_mean", "ic_std", "pos_ratio", "raw_score", "source", "file"])
    out["suggested_weight"] = out["factor"].map(weights).fillna(0.0)
    out = out.sort_values("suggested_weight", ascending=False).reset_index(drop=True)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    print(out.to_string(index=False))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
