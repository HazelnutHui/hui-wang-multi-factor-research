#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def latex_escape(text: str) -> str:
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    out = []
    for ch in str(text):
        out.append(repl.get(ch, ch))
    return "".join(out)


def pct(v: float) -> str:
    return f"{v * 100:.2f}\\%"


def dec(v: float, n: int = 6) -> str:
    return f"{v:.{n}f}"


def build_en_tex(run_id: str, metrics: dict, deciles_df: pd.DataFrame) -> str:
    rows = []
    for _, r in deciles_df.iterrows():
        rows.append(
            f"{latex_escape(r['decile'])} & {int(r['count'])} & {dec(float(r['mean']), 5)} & "
            f"{dec(float(r['std']), 5) if pd.notna(r['std']) else 'NA'} \\\\"
        )
    deciles_table = "\n".join(rows)
    return rf"""\documentclass[11pt]{{article}}
\usepackage[margin=1in]{{geometry}}
\usepackage{{booktabs}}
\usepackage{{longtable}}
\title{{Daily Live Trading Report}}
\date{{}}
\begin{{document}}
\maketitle
\section*{{Run Overview}}
\begin{{itemize}}
\item run\_id: \texttt{{{latex_escape(run_id)}}}
\item signal date (T): {latex_escape(metrics['signal_date'])}
\item trade date (T+1): {latex_escape(metrics['trade_date'])}
\item universe size: {int(metrics['n_total'])}
\item matched symbols: {int(metrics['n_matched'])}
\item coverage: {pct(float(metrics['coverage']))}
\end{{itemize}}

\section*{{Core Metrics}}
\begin{{itemize}}
\item IC (Pearson): {dec(float(metrics['ic_pearson']), 6)}
\item IC (Spearman): {dec(float(metrics['ic_spearman']), 6)}
\item Top bucket mean return: {pct(float(metrics['top_mean_ret']))}
\item Bottom bucket mean return: {pct(float(metrics['bottom_mean_ret']))}
\item Top-Bottom spread: {pct(float(metrics['top_bottom_spread']))}
\item Top win rate: {pct(float(metrics['top_win_rate']))}
\item Bottom win rate: {pct(float(metrics['bottom_win_rate']))}
\end{{itemize}}

\section*{{Decile Return Table}}
\begin{{center}}
\begin{{tabular}}{{lrrr}}
\toprule
Decile & Count & Mean Return & Std Dev \\
\midrule
{deciles_table}
\bottomrule
\end{{tabular}}
\end{{center}}

\section*{{Method Note}}
All metrics are computed from previous-day scores and next-trading-day realized returns.
\end{{document}}
"""


def build_zh_tex(run_id: str, metrics: dict, deciles_df: pd.DataFrame) -> str:
    rows = []
    for _, r in deciles_df.iterrows():
        rows.append(
            f"{latex_escape(r['decile'])} & {int(r['count'])} & {dec(float(r['mean']), 5)} & "
            f"{dec(float(r['std']), 5) if pd.notna(r['std']) else 'NA'} \\\\"
        )
    deciles_table = "\n".join(rows)
    return rf"""\documentclass[11pt]{{article}}
\usepackage{{xeCJK}}
\usepackage[margin=1in]{{geometry}}
\usepackage{{booktabs}}
\setCJKmainfont{{Songti SC}}
\title{{实战单日可读报告}}
\date{{}}
\begin{{document}}
\maketitle
\section*{{运行概览}}
\begin{{itemize}}
\item 运行ID: \texttt{{{latex_escape(run_id)}}}
\item 打分日(T): {latex_escape(metrics['signal_date'])}
\item 交易日(T+1): {latex_escape(metrics['trade_date'])}
\item 股票总数: {int(metrics['n_total'])}
\item 成功匹配数: {int(metrics['n_matched'])}
\item 覆盖率: {pct(float(metrics['coverage']))}
\end{{itemize}}

\section*{{核心指标}}
\begin{{itemize}}
\item IC(Pearson): {dec(float(metrics['ic_pearson']), 6)}
\item IC(Spearman): {dec(float(metrics['ic_spearman']), 6)}
\item 头部分组平均收益: {pct(float(metrics['top_mean_ret']))}
\item 尾部分组平均收益: {pct(float(metrics['bottom_mean_ret']))}
\item 头尾收益差: {pct(float(metrics['top_bottom_spread']))}
\item 头部分组胜率: {pct(float(metrics['top_win_rate']))}
\item 尾部分组胜率: {pct(float(metrics['bottom_win_rate']))}
\end{{itemize}}

\section*{{十分位收益表}}
\begin{{center}}
\begin{{tabular}}{{lrrr}}
\toprule
分组 & 样本数 & 平均收益 & 标准差 \\
\midrule
{deciles_table}
\bottomrule
\end{{tabular}}
\end{{center}}

\section*{{方法说明}}
全部指标基于“前一交易日打分 + 下一交易日真实收益”计算。
\end{{document}}
"""


def compile_tex(engine: str, tex_path: Path, out_dir: Path) -> None:
    cmd = [engine, "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={out_dir}", str(tex_path)]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    stem = tex_path.stem
    for ext in (".aux", ".log"):
        p = out_dir / f"{stem}{ext}"
        if p.exists():
            p.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate daily live-trading readable PDF reports in EN/ZH.")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--root", default=str(ROOT / "live_trading"))
    args = ap.parse_args()

    live_root = Path(args.root).resolve()
    run_id = args.run_id
    acc_dir = live_root / "accuracy" / run_id
    if not acc_dir.exists():
        raise FileNotFoundError(f"accuracy run folder not found: {acc_dir}")

    metrics_df = pd.read_csv(acc_dir / "metrics_T_Tplus1.csv")
    deciles_df = pd.read_csv(acc_dir / "deciles_T_Tplus1.csv")
    if metrics_df.empty:
        raise ValueError("metrics_T_Tplus1.csv is empty")
    m = metrics_df.iloc[0].to_dict()

    en_dir = live_root / "reports" / "daily" / "en" / run_id
    zh_dir = live_root / "reports" / "daily" / "zh" / run_id
    en_dir.mkdir(parents=True, exist_ok=True)
    zh_dir.mkdir(parents=True, exist_ok=True)

    en_tex = en_dir / "daily_report_en.tex"
    zh_tex = zh_dir / "daily_report_zh.tex"
    en_tex.write_text(build_en_tex(run_id, m, deciles_df), encoding="utf-8")
    zh_tex.write_text(build_zh_tex(run_id, m, deciles_df), encoding="utf-8")

    compile_tex("pdflatex", en_tex, en_dir)
    compile_tex("xelatex", zh_tex, zh_dir)

    print(f"EN PDF: {en_dir / 'daily_report_en.pdf'}")
    print(f"ZH PDF: {zh_dir / 'daily_report_zh.pdf'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
