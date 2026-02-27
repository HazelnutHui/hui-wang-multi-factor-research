#!/usr/bin/env python3
"""
Build canonical DQ input CSV from the latest score snapshot.

Output schema is fixed:
- date
- ticker
- score
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _find_latest_scores_csv(root: Path) -> Path:
    scores_root = root / "live_trading" / "scores"
    candidates = sorted(scores_root.glob("trade_*/scores_full_ranked.csv"))
    if not candidates:
        raise FileNotFoundError(f"no scores_full_ranked.csv under {scores_root}")
    # latest by folder name convention trade_YYYY-MM-DD_from_signal_YYYY-MM-DD
    return candidates[-1]


def _build(df: pd.DataFrame) -> pd.DataFrame:
    required = {"symbol", "date", "signal"}
    miss = [c for c in required if c not in df.columns]
    if miss:
        raise ValueError(f"input missing required columns: {miss}")
    out = df.loc[:, ["date", "symbol", "signal"]].copy()
    out = out.rename(columns={"symbol": "ticker", "signal": "score"})
    # Keep deterministic order and remove key duplicates if any.
    out = out.drop_duplicates(subset=["date", "ticker"], keep="last")
    out = out.sort_values(["date", "ticker"]).reset_index(drop=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Prepare canonical DQ input CSV from latest scores.")
    ap.add_argument("--root", default=".", help="Project root")
    ap.add_argument(
        "--input-csv",
        default="",
        help="Optional explicit source scores csv (must contain symbol,date,signal).",
    )
    ap.add_argument(
        "--out-csv",
        default="data/research_inputs/combo_v2_dq_input_latest.csv",
        help="Output canonical DQ input path",
    )
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    src = Path(args.input_csv).expanduser().resolve() if args.input_csv else _find_latest_scores_csv(root)
    if not src.exists():
        raise SystemExit(f"input csv not found: {src}")

    out_csv = (root / args.out_csv).resolve() if not Path(args.out_csv).is_absolute() else Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(src)
    out = _build(df)
    out.to_csv(out_csv, index=False)

    print(f"[done] source_csv={src}")
    print(f"[done] out_csv={out_csv}")
    print(f"[done] rows={len(out)}")
    print(f"[done] max_date={out['date'].max() if len(out) else None}")


if __name__ == "__main__":
    main()

