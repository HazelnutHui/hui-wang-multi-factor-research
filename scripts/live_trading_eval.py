#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class EvalConfig:
    signals_path: Path
    signal_date: str
    trade_date: str
    prices_dir: Path
    out_root: Path
    run_id: str
    symbol_col: str
    date_col: str
    score_col: str
    price_col: str
    top_pct: float
    realized_file: Optional[Path]


def _pick_score_col(df: pd.DataFrame, score_col: str) -> str:
    if score_col != "auto":
        if score_col not in df.columns:
            raise ValueError(f"score column not found: {score_col}")
        return score_col
    for c in ("signal", "score"):
        if c in df.columns:
            return c
    raise ValueError("no score column found, expected one of: signal/score")


def _load_signals(cfg: EvalConfig) -> pd.DataFrame:
    if not cfg.signals_path.exists():
        raise FileNotFoundError(f"signals file not found: {cfg.signals_path}")
    df = pd.read_csv(cfg.signals_path)
    if cfg.symbol_col not in df.columns:
        raise ValueError(f"symbol column not found: {cfg.symbol_col}")
    score_col = _pick_score_col(df, cfg.score_col)

    if cfg.date_col in df.columns:
        dates = pd.to_datetime(df[cfg.date_col], errors="coerce").dt.date
        target = pd.to_datetime(cfg.signal_date).date()
        df = df[dates == target].copy()

    df = df[[cfg.symbol_col, score_col]].copy()
    df.columns = ["symbol", "score"]
    df["symbol"] = df["symbol"].astype(str).str.upper().str.strip()
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df = df.dropna(subset=["symbol", "score"])
    df = df.sort_values("score", ascending=False).drop_duplicates(subset=["symbol"], keep="first")
    df = df.reset_index(drop=True)
    df["rank"] = np.arange(1, len(df) + 1)
    return df


def _one_day_return(prices_dir: Path, symbol: str, signal_date: pd.Timestamp, trade_date: pd.Timestamp, price_col: str):
    pkl_path = prices_dir / f"{symbol}.pkl"
    if not pkl_path.exists():
        return np.nan, np.nan, np.nan
    try:
        df = pd.read_pickle(pkl_path)
    except Exception:
        return np.nan, np.nan, np.nan
    if "date" not in df.columns or price_col not in df.columns:
        return np.nan, np.nan, np.nan

    d = pd.to_datetime(df["date"], errors="coerce").dt.date
    px = pd.to_numeric(df[price_col], errors="coerce")
    tmp = pd.DataFrame({"d": d, "px": px}).dropna(subset=["d", "px"])
    if tmp.empty:
        return np.nan, np.nan, np.nan

    a = tmp[tmp["d"] == signal_date.date()]
    b = tmp[tmp["d"] == trade_date.date()]
    if a.empty or b.empty:
        return np.nan, np.nan, np.nan

    p0 = float(a.iloc[-1]["px"])
    p1 = float(b.iloc[-1]["px"])
    if p0 == 0:
        return np.nan, p0, p1
    return float(p1 / p0 - 1.0), p0, p1


def _build_realized(signals: pd.DataFrame, cfg: EvalConfig) -> pd.DataFrame:
    signal_date = pd.to_datetime(cfg.signal_date)
    trade_date = pd.to_datetime(cfg.trade_date)
    rows = []
    for sym in signals["symbol"]:
        ret, p0, p1 = _one_day_return(cfg.prices_dir, sym, signal_date, trade_date, cfg.price_col)
        rows.append(
            {
                "symbol": sym,
                "signal_date": cfg.signal_date,
                "trade_date": cfg.trade_date,
                "price_signal": p0,
                "price_trade": p1,
                "ret_1d": ret,
                "matched": bool(np.isfinite(ret)),
            }
        )
    return pd.DataFrame(rows)


def _load_realized_file(cfg: EvalConfig) -> pd.DataFrame:
    if cfg.realized_file is None:
        raise ValueError("realized_file is None")
    if not cfg.realized_file.exists():
        raise FileNotFoundError(f"realized file not found: {cfg.realized_file}")
    df = pd.read_csv(cfg.realized_file)
    for c in ("symbol", "ret_1d"):
        if c not in df.columns:
            raise ValueError(f"realized file missing required column: {c}")
    out = df[["symbol", "ret_1d"]].copy()
    out["symbol"] = out["symbol"].astype(str).str.upper().str.strip()
    out["ret_1d"] = pd.to_numeric(out["ret_1d"], errors="coerce")
    out = out.dropna(subset=["symbol"]).drop_duplicates(subset=["symbol"], keep="first")
    out["signal_date"] = cfg.signal_date
    out["trade_date"] = cfg.trade_date
    out["price_signal"] = np.nan
    out["price_trade"] = np.nan
    out["matched"] = out["ret_1d"].notna()
    return out[["symbol", "signal_date", "trade_date", "price_signal", "price_trade", "ret_1d", "matched"]]


def _deciles_from_rank(matched: pd.DataFrame) -> pd.DataFrame:
    if matched.empty:
        return pd.DataFrame(columns=["decile", "count", "mean", "std"])
    matched = matched.sort_values("score", ascending=False).reset_index(drop=True)
    n = len(matched)
    boundaries = np.linspace(0, n, 11, dtype=int)
    out = []
    for i in range(10):
        s = matched.iloc[boundaries[i] : boundaries[i + 1]]
        out.append(
            {
                "decile": f"D{i+1}",
                "count": int(len(s)),
                "mean": float(s["ret_1d"].mean()) if len(s) else np.nan,
                "std": float(s["ret_1d"].std(ddof=1)) if len(s) > 1 else np.nan,
            }
        )
    return pd.DataFrame(out)


def _metrics(signals: pd.DataFrame, matched: pd.DataFrame, cfg: EvalConfig) -> pd.DataFrame:
    total = len(signals)
    valid = len(matched)
    coverage = float(valid / total) if total > 0 else np.nan

    ic_p = matched["score"].corr(matched["ret_1d"], method="pearson") if valid > 1 else np.nan
    if valid > 1:
        # Spearman without scipy dependency: Pearson correlation on ranks.
        s_rank = matched["score"].rank(method="average")
        r_rank = matched["ret_1d"].rank(method="average")
        ic_s = s_rank.corr(r_rank, method="pearson")
    else:
        ic_s = np.nan

    q = max(1, int(valid * cfg.top_pct)) if valid > 0 else 0
    top = matched.head(q) if q > 0 else matched.iloc[0:0]
    bottom = matched.tail(q) if q > 0 else matched.iloc[0:0]

    top_mean = float(top["ret_1d"].mean()) if not top.empty else np.nan
    bottom_mean = float(bottom["ret_1d"].mean()) if not bottom.empty else np.nan

    row = {
        "run_id": cfg.run_id,
        "signal_date": cfg.signal_date,
        "trade_date": cfg.trade_date,
        "n_total": int(total),
        "n_matched": int(valid),
        "coverage": coverage,
        "ic_pearson": float(ic_p) if pd.notna(ic_p) else np.nan,
        "ic_spearman": float(ic_s) if pd.notna(ic_s) else np.nan,
        "top_pct": float(cfg.top_pct),
        "top_n": int(len(top)),
        "bottom_n": int(len(bottom)),
        "top_mean_ret": top_mean,
        "bottom_mean_ret": bottom_mean,
        "top_bottom_spread": float(top_mean - bottom_mean) if pd.notna(top_mean) and pd.notna(bottom_mean) else np.nan,
        "top_win_rate": float((top["ret_1d"] > 0).mean()) if not top.empty else np.nan,
        "bottom_win_rate": float((bottom["ret_1d"] > 0).mean()) if not bottom.empty else np.nan,
    }
    return pd.DataFrame([row])


def _append_panel(panel_path: Path, metrics_df: pd.DataFrame):
    if panel_path.exists():
        old = pd.read_csv(panel_path)
        panel = pd.concat([old, metrics_df], ignore_index=True)
        panel = panel.drop_duplicates(subset=["run_id"], keep="last")
    else:
        panel = metrics_df.copy()
    panel["trade_date_sort"] = pd.to_datetime(panel["trade_date"], errors="coerce")
    panel = panel.sort_values(["trade_date_sort", "run_id"]).drop(columns=["trade_date_sort"])
    panel.to_csv(panel_path, index=False)


def _build_markdown(metrics_df: pd.DataFrame, out_md: Path):
    m = metrics_df.iloc[0].to_dict()
    lines = [
        "# Live Trading Daily Accuracy Record",
        "",
        f"- run_id: `{m.get('run_id')}`",
        f"- signal_date: `{m.get('signal_date')}`",
        f"- trade_date: `{m.get('trade_date')}`",
        "",
        "## Metrics",
        f"- n_total: `{int(m.get('n_total', 0))}`",
        f"- n_matched: `{int(m.get('n_matched', 0))}`",
        f"- coverage: `{m.get('coverage')}`",
        f"- ic_pearson: `{m.get('ic_pearson')}`",
        f"- ic_spearman: `{m.get('ic_spearman')}`",
        f"- top_mean_ret: `{m.get('top_mean_ret')}`",
        f"- bottom_mean_ret: `{m.get('bottom_mean_ret')}`",
        f"- top_bottom_spread: `{m.get('top_bottom_spread')}`",
        f"- top_win_rate: `{m.get('top_win_rate')}`",
        f"- bottom_win_rate: `{m.get('bottom_win_rate')}`",
        "",
        "## Files",
        "- `signals_T.csv`",
        "- `realized_Tplus1.csv`",
        "- `match_T_Tplus1.csv`",
        "- `metrics_T_Tplus1.csv`",
        "- `deciles_T_Tplus1.csv`",
    ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> EvalConfig:
    p = argparse.ArgumentParser(description="Daily live-trading score vs realized-return evaluation.")
    p.add_argument("--signals", required=True, help="CSV of signal snapshot")
    p.add_argument("--signal-date", required=True, help="Signal date T, format YYYY-MM-DD")
    p.add_argument("--trade-date", required=True, help="Realized date T+1, format YYYY-MM-DD")
    p.add_argument("--prices-dir", default=str(ROOT / "data" / "prices_divadj"))
    p.add_argument("--out-root", default=str(ROOT / "live_trading"))
    p.add_argument("--run-id", default="", help="Default: trade_{trade_date}_from_signal_{signal_date}")
    p.add_argument("--symbol-col", default="symbol")
    p.add_argument("--date-col", default="date")
    p.add_argument("--score-col", default="auto", help="auto/signal/score/your_column")
    p.add_argument("--price-col", default="adjClose")
    p.add_argument("--top-pct", type=float, default=0.10)
    p.add_argument("--realized-file", default="", help="Optional CSV with symbol,ret_1d to bypass pickle price reading")
    args = p.parse_args()

    run_id = args.run_id.strip() or f"trade_{args.trade_date}_from_signal_{args.signal_date}"
    return EvalConfig(
        signals_path=Path(args.signals).resolve(),
        signal_date=args.signal_date,
        trade_date=args.trade_date,
        prices_dir=Path(args.prices_dir).resolve(),
        out_root=Path(args.out_root).resolve(),
        run_id=run_id,
        symbol_col=args.symbol_col,
        date_col=args.date_col,
        score_col=args.score_col,
        price_col=args.price_col,
        top_pct=float(args.top_pct),
        realized_file=Path(args.realized_file).resolve() if args.realized_file.strip() else None,
    )


def main() -> int:
    cfg = parse_args()

    score_dir = cfg.out_root / "scores" / cfg.run_id
    acc_dir = cfg.out_root / "accuracy" / cfg.run_id
    panel_dir = cfg.out_root / "accuracy"
    score_dir.mkdir(parents=True, exist_ok=True)
    acc_dir.mkdir(parents=True, exist_ok=True)
    panel_dir.mkdir(parents=True, exist_ok=True)

    signals = _load_signals(cfg)
    signals.to_csv(score_dir / "signals_T.csv", index=False)

    realized = _load_realized_file(cfg) if cfg.realized_file is not None else _build_realized(signals, cfg)
    realized.to_csv(acc_dir / "realized_Tplus1.csv", index=False)

    match_df = signals.merge(realized[["symbol", "price_signal", "price_trade", "ret_1d", "matched"]], on="symbol", how="left")
    match_df = match_df.sort_values("score", ascending=False).reset_index(drop=True)
    match_df.to_csv(acc_dir / "match_T_Tplus1.csv", index=False)

    matched = match_df[match_df["matched"] == True].copy()  # noqa: E712
    metrics_df = _metrics(signals, matched, cfg)
    metrics_df.to_csv(acc_dir / "metrics_T_Tplus1.csv", index=False)

    deciles_df = _deciles_from_rank(matched)
    deciles_df.to_csv(acc_dir / "deciles_T_Tplus1.csv", index=False)

    _append_panel(panel_dir / "metrics_panel.csv", metrics_df)
    _build_markdown(metrics_df, acc_dir / "README.md")

    print(f"run_id={cfg.run_id}")
    print(f"signals={len(signals)} matched={len(matched)}")
    print(metrics_df.to_dict(orient="records")[0])
    print(f"saved: {score_dir}")
    print(f"saved: {acc_dir}")
    print(f"saved: {panel_dir / 'metrics_panel.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
