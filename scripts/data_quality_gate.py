import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def _split_csv_list(v: str) -> list[str]:
    return [x.strip() for x in str(v).split(",") if x.strip()]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc(dt_series: pd.Series) -> pd.Series:
    ts = pd.to_datetime(dt_series, errors="coerce", utc=True)
    return ts


def main() -> None:
    p = argparse.ArgumentParser(description="Data quality hard gate for production research inputs.")
    p.add_argument("--input-csv", required=True, help="Input dataset CSV path.")
    p.add_argument("--required-columns", default="", help="Comma-separated required columns.")
    p.add_argument("--numeric-columns", default="", help="Comma-separated numeric columns.")
    p.add_argument("--key-columns", default="", help="Comma-separated key columns used for duplicate checks.")
    p.add_argument("--date-column", default="", help="Optional date column for freshness checks.")
    p.add_argument("--min-rows", type=int, default=1000)
    p.add_argument("--max-missing-ratio", type=float, default=0.05)
    p.add_argument("--max-duplicate-ratio", type=float, default=0.01)
    p.add_argument("--max-staleness-days", type=float, default=7.0)
    p.add_argument("--out-dir", default="gate_results/data_quality")
    args = p.parse_args()

    input_path = Path(args.input_csv).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"input csv not found: {input_path}")

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_root = Path(args.out_dir).expanduser().resolve() / f"data_quality_{ts}"
    out_root.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    row_count = int(len(df))
    col_count = int(len(df.columns))
    required_columns = _split_csv_list(args.required_columns)
    numeric_columns = _split_csv_list(args.numeric_columns)
    key_columns = _split_csv_list(args.key_columns)

    checks: dict[str, bool] = {}
    metrics: dict[str, object] = {
        "row_count": row_count,
        "column_count": col_count,
        "input_csv": str(input_path),
    }
    failures: list[str] = []

    # 1) Schema presence
    missing_required = [c for c in required_columns if c not in df.columns]
    checks["required_columns_present"] = len(missing_required) == 0
    metrics["missing_required_columns"] = missing_required
    if missing_required:
        failures.append(f"missing required columns: {missing_required}")

    # 2) Minimum row count
    checks["min_rows"] = row_count >= int(args.min_rows)
    metrics["min_rows_threshold"] = int(args.min_rows)
    if not checks["min_rows"]:
        failures.append(f"row_count={row_count} below min_rows={args.min_rows}")

    # 3) Duplicate ratio
    duplicate_ratio = None
    if row_count > 0:
        if key_columns:
            if all(c in df.columns for c in key_columns):
                dup_n = int(df.duplicated(subset=key_columns, keep=False).sum())
                duplicate_ratio = float(dup_n / row_count)
            else:
                missing_keys = [c for c in key_columns if c not in df.columns]
                failures.append(f"key columns missing for duplicate check: {missing_keys}")
        else:
            dup_n = int(df.duplicated(keep=False).sum())
            duplicate_ratio = float(dup_n / row_count)
    metrics["duplicate_ratio"] = duplicate_ratio
    metrics["max_duplicate_ratio_threshold"] = float(args.max_duplicate_ratio)
    checks["duplicate_ratio"] = duplicate_ratio is not None and duplicate_ratio <= float(args.max_duplicate_ratio)
    if not checks["duplicate_ratio"]:
        failures.append(
            f"duplicate_ratio={duplicate_ratio} exceeds max_duplicate_ratio={args.max_duplicate_ratio}"
        )

    # 4) Missing ratio by column
    missing_ratio_map: dict[str, float] = {}
    if row_count > 0:
        for c in df.columns:
            missing_ratio_map[c] = float(df[c].isna().mean())
    metrics["missing_ratio_by_column"] = missing_ratio_map
    failing_missing_cols = [c for c, r in missing_ratio_map.items() if r > float(args.max_missing_ratio)]
    checks["missing_ratio"] = len(failing_missing_cols) == 0
    metrics["max_missing_ratio_threshold"] = float(args.max_missing_ratio)
    metrics["missing_ratio_violations"] = failing_missing_cols
    if failing_missing_cols:
        failures.append(f"missing ratio exceeded: {failing_missing_cols}")

    # 5) Numeric integrity
    numeric_issues: dict[str, str] = {}
    for c in numeric_columns:
        if c not in df.columns:
            numeric_issues[c] = "column missing"
            continue
        s = pd.to_numeric(df[c], errors="coerce")
        nan_ratio = float(s.isna().mean()) if len(s) else 1.0
        has_inf = bool((s == float("inf")).any() or (s == float("-inf")).any())
        if nan_ratio > 0 or has_inf:
            numeric_issues[c] = f"nan_ratio={nan_ratio:.6f}, has_inf={has_inf}"
    checks["numeric_integrity"] = len(numeric_issues) == 0
    metrics["numeric_issues"] = numeric_issues
    if numeric_issues:
        failures.append(f"numeric issues: {numeric_issues}")

    # 6) Freshness
    freshness_days = None
    checks["freshness"] = True
    if args.date_column:
        if args.date_column not in df.columns:
            checks["freshness"] = False
            failures.append(f"date column missing: {args.date_column}")
        else:
            ts_col = _to_utc(df[args.date_column])
            max_ts = ts_col.max()
            if pd.isna(max_ts):
                checks["freshness"] = False
                failures.append(f"date column invalid or empty: {args.date_column}")
            else:
                freshness_days = (_utc_now() - max_ts.to_pydatetime()).total_seconds() / 86400.0
                checks["freshness"] = freshness_days <= float(args.max_staleness_days)
                if not checks["freshness"]:
                    failures.append(
                        f"staleness={freshness_days:.2f} days exceeds max_staleness_days={args.max_staleness_days}"
                    )
    metrics["freshness_days"] = freshness_days
    metrics["max_staleness_days_threshold"] = float(args.max_staleness_days)

    overall_pass = all(bool(v) for v in checks.values())
    report = {
        "generated_at": _utc_now().isoformat(),
        "inputs": vars(args),
        "checks": checks,
        "metrics": metrics,
        "overall_pass": overall_pass,
        "failures": failures,
    }

    report_json = out_root / "data_quality_report.json"
    report_md = out_root / "data_quality_report.md"
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=True))

    lines = [
        "# Data Quality Gate Report",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- overall_pass: {overall_pass}",
        f"- input_csv: `{input_path}`",
        "",
        "## Checks",
        "",
    ]
    for k, v in checks.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Failures", ""]
    if failures:
        for x in failures:
            lines.append(f"- {x}")
    else:
        lines.append("- none")
    lines += [
        "",
        "## Key Metrics",
        "",
        f"- row_count: {row_count}",
        f"- column_count: {col_count}",
        f"- duplicate_ratio: {duplicate_ratio}",
        f"- freshness_days: {freshness_days}",
        "",
        f"- report_json: `{report_json}`",
    ]
    report_md.write_text("\n".join(lines))

    print(f"[done] report_json={report_json}")
    print(f"[done] report_md={report_md}")

    if overall_pass:
        raise SystemExit(0)
    raise SystemExit(2)


if __name__ == "__main__":
    main()
