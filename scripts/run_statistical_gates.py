import argparse
import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _two_sided_p_from_z(z: float) -> float:
    return max(0.0, min(1.0, 2.0 * (1.0 - _norm_cdf(abs(float(z))))))


def _bh_qvalues(pvals: pd.Series) -> pd.Series:
    p = pd.to_numeric(pvals, errors="coerce")
    m = int(p.notna().sum())
    out = pd.Series(np.nan, index=p.index, dtype=float)
    if m == 0:
        return out
    ranked = p.dropna().sort_values()
    q = pd.Series(index=ranked.index, dtype=float)
    prev = 1.0
    for rank in range(m, 0, -1):
        idx = ranked.index[rank - 1]
        val = float(ranked.iloc[rank - 1]) * m / rank
        prev = min(prev, val)
        q.loc[idx] = prev
    out.loc[q.index] = q.values
    return out.clip(lower=0.0, upper=1.0)


def _latest_segment_summary(root: Path, factor: str = "") -> Path | None:
    cands = sorted(root.glob("segment_results/*/all_factors_summary.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not factor:
        return cands[0] if cands else None
    for p in cands:
        try:
            df = pd.read_csv(p, usecols=["factor"])
            vals = set(df["factor"].astype(str).tolist())
            if factor in vals:
                return p
        except Exception:
            continue
    # fallback to per-factor summary if available
    single = sorted(root.glob(f"segment_results/*/{factor}/segment_summary.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return single[0] if single else (cands[0] if cands else None)


def _aggregate(df: pd.DataFrame) -> pd.DataFrame:
    req = {"factor", "ic"}
    if not req.issubset(df.columns):
        raise SystemExit(f"Missing required columns {req} in summary csv")
    g = df.groupby("factor", dropna=False)
    out = g["ic"].agg(["mean", "std", "count"]).reset_index().rename(
        columns={"mean": "ic_mean", "std": "ic_std", "count": "n"}
    )
    pos = g["ic"].apply(lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean()))
    out = out.merge(pos.rename("pos_ratio").reset_index(), on="factor", how="left")
    out["ic_std"] = pd.to_numeric(out["ic_std"], errors="coerce")
    out["z_stat"] = out.apply(
        lambda r: (float(r["ic_mean"]) / (float(r["ic_std"]) / math.sqrt(float(r["n"]))))
        if pd.notna(r["ic_std"]) and float(r["ic_std"]) > 0 and float(r["n"]) >= 2
        else np.nan,
        axis=1,
    )
    out["p_value"] = out["z_stat"].apply(lambda z: _two_sided_p_from_z(z) if pd.notna(z) else np.nan)
    out["q_value_bh"] = _bh_qvalues(out["p_value"])
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Statistical gates with multiple-testing control (BH-FDR).")
    p.add_argument("--summary-csv", default="", help="Segmented summary csv (default: latest segment_results/*/all_factors_summary.csv)")
    p.add_argument("--factor", default="", help="Optional factor focus for pass/fail")
    p.add_argument("--alpha", type=float, default=0.10, help="FDR threshold on q-value")
    p.add_argument("--min-pos-ratio", type=float, default=0.60)
    p.add_argument("--min-ic-mean", type=float, default=0.0)
    p.add_argument("--out-dir", default="gate_results")
    args = p.parse_args()

    summary_path = Path(args.summary_csv).resolve() if args.summary_csv else _latest_segment_summary(ROOT, args.factor)
    if summary_path is None or not summary_path.exists():
        raise SystemExit("No segmented summary found. Provide --summary-csv.")

    df = pd.read_csv(summary_path)
    agg = _aggregate(df)

    agg["gate_qvalue"] = agg["q_value_bh"] <= float(args.alpha)
    agg["gate_pos_ratio"] = agg["pos_ratio"] >= float(args.min_pos_ratio)
    agg["gate_ic_mean"] = agg["ic_mean"] > float(args.min_ic_mean)
    agg["gate_pass"] = agg["gate_qvalue"] & agg["gate_pos_ratio"] & agg["gate_ic_mean"]

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_root = (ROOT / args.out_dir / f"statistical_gates_{ts}").resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    table_csv = out_root / "statistical_gates_table.csv"
    agg.sort_values(["gate_pass", "q_value_bh", "ic_mean"], ascending=[False, True, False]).to_csv(table_csv, index=False)

    focus = None
    if args.factor:
        hit = agg.loc[agg["factor"] == args.factor]
        if len(hit) == 0:
            focus = {"factor": args.factor, "found": False, "gate_pass": False}
        else:
            r = hit.iloc[0]
            focus = {
                "factor": args.factor,
                "found": True,
                "ic_mean": float(r["ic_mean"]) if pd.notna(r["ic_mean"]) else None,
                "pos_ratio": float(r["pos_ratio"]) if pd.notna(r["pos_ratio"]) else None,
                "p_value": float(r["p_value"]) if pd.notna(r["p_value"]) else None,
                "q_value_bh": float(r["q_value_bh"]) if pd.notna(r["q_value_bh"]) else None,
                "gate_pass": bool(r["gate_pass"]),
            }

    report = {
        "generated_at": datetime.now().isoformat(),
        "inputs": vars(args),
        "summary_csv": str(summary_path),
        "table_csv": str(table_csv),
        "n_factors": int(agg["factor"].nunique()),
        "n_pass": int(pd.to_numeric(agg["gate_pass"], errors="coerce").fillna(False).sum()),
        "focus": focus,
    }
    json_path = out_root / "statistical_gates_report.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    md_path = out_root / "statistical_gates_report.md"
    lines = [
        "# Statistical Gates Report",
        "",
        f"- summary_csv: `{summary_path}`",
        f"- table_csv: `{table_csv}`",
        f"- n_factors: {report['n_factors']}",
        f"- n_pass: {report['n_pass']}",
        "",
    ]
    if focus:
        lines += [
            "## Focus Factor",
            "",
            f"- factor: {focus.get('factor')}",
            f"- found: {focus.get('found')}",
            f"- gate_pass: {focus.get('gate_pass')}",
            f"- ic_mean: {focus.get('ic_mean')}",
            f"- pos_ratio: {focus.get('pos_ratio')}",
            f"- p_value: {focus.get('p_value')}",
            f"- q_value_bh: {focus.get('q_value_bh')}",
        ]
    md_path.write_text("\n".join(lines))

    print(f"[done] table_csv={table_csv}")
    print(f"[done] report_json={json_path}")
    print(f"[done] report_md={md_path}")


if __name__ == "__main__":
    main()
