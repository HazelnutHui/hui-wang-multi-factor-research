"""
Run segmented backtests (e.g., 2-year slices) for single-factor strategies.
"""

import argparse
import faulthandler
import gc
import json
from datetime import datetime
from pathlib import Path
import importlib.util as _ilu

import pandas as pd

from backtest.backtest_engine import BacktestEngine
from backtest.performance_analyzer import PerformanceAnalyzer
import backtest.config as core


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = Path(core.__file__).resolve().parent


FACTOR_SPECS = {
    "momentum": {
        "config_path": PROJECT_ROOT / "strategies" / "momentum_v1" / "config.py",
        "weights": {"momentum": 1.0, "reversal": 0.0, "low_vol": 0.0, "pead": 0.0},
    },
    "reversal": {
        "config_path": PROJECT_ROOT / "strategies" / "reversal_v1" / "config.py",
        "weights": {"momentum": 0.0, "reversal": 1.0, "low_vol": 0.0, "pead": 0.0},
    },
    "quality": {
        "config_path": PROJECT_ROOT / "strategies" / "quality_v1" / "config.py",
        "weights": {"momentum": 0.0, "reversal": 0.0, "low_vol": 0.0, "pead": 0.0, "quality": 1.0},
    },
    "value": {
        "config_path": PROJECT_ROOT / "strategies" / "value_v1" / "config.py",
        "weights": {"momentum": 0.0, "reversal": 0.0, "low_vol": 0.0, "pead": 0.0, "quality": 0.0, "value": 1.0},
    },
    "low_vol": {
        "config_path": PROJECT_ROOT / "strategies" / "low_vol_v1" / "config.py",
        "weights": {"momentum": 0.0, "reversal": 0.0, "low_vol": 1.0, "pead": 0.0},
    },
    "low_vol_simple": {
        "config_path": PROJECT_ROOT / "strategies" / "low_vol_simple_v1" / "config.py",
        "weights": {"momentum": 0.0, "reversal": 0.0, "low_vol": 1.0, "pead": 0.0},
    },
    "pead": {
        "config_path": PROJECT_ROOT / "strategies" / "pead_v1" / "config.py",
        "weights": {"momentum": 0.0, "reversal": 0.0, "low_vol": 0.0, "pead": 1.0},
    },
    "size": {
        "config_path": PROJECT_ROOT / "strategies" / "size_v1" / "config.py",
        "weights": {"size": -1.0},
    },
    "momentum_v2": {
        "config_path": PROJECT_ROOT / "strategies" / "momentum_v2" / "config.py",
        "weights": {"momentum": 1.0, "reversal": 0.0, "low_vol": 0.0, "pead": 0.0},
    },
    "reversal_v2": {
        "config_path": PROJECT_ROOT / "strategies" / "reversal_v2" / "config.py",
        "weights": {"momentum": 0.0, "reversal": 1.0, "low_vol": 0.0, "pead": 0.0},
    },
    "quality_v2": {
        "config_path": PROJECT_ROOT / "strategies" / "quality_v2" / "config.py",
        "weights": {"momentum": 0.0, "reversal": 0.0, "low_vol": 0.0, "pead": 0.0, "quality": 1.0},
    },
    "value_v2": {
        "config_path": PROJECT_ROOT / "strategies" / "value_v2" / "config.py",
        "weights": {"momentum": 0.0, "reversal": 0.0, "low_vol": 0.0, "pead": 0.0, "quality": 0.0, "value": 1.0},
    },
    "low_vol_v2": {
        "config_path": PROJECT_ROOT / "strategies" / "low_vol_v2" / "config.py",
        "weights": {"momentum": 0.0, "reversal": 0.0, "low_vol": 1.0, "pead": 0.0},
    },
    "pead_v2": {
        "config_path": PROJECT_ROOT / "strategies" / "pead_v2" / "config.py",
        "weights": {"momentum": 0.0, "reversal": 0.0, "low_vol": 0.0, "pead": 1.0},
    },
    "combo_v2": {
        "config_path": PROJECT_ROOT / "strategies" / "combo_v2" / "config.py",
        "weights": {
            "value": 0.50,
            "momentum": 0.30,
            "quality": 0.20,
            "reversal": 0.0,
            "low_vol": 0.0,
            "pead": 0.0,
        },
    },
}


def _load_cfg(path: Path):
    spec = _ilu.spec_from_file_location(path.stem, path)
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_override(s: str):
    if s is None:
        return None, None
    if "=" not in s:
        return s.strip(), None
    key, val = s.split("=", 1)
    key = key.strip()
    val = val.strip()
    if val.lower() in ("true", "false"):
        return key, val.lower() == "true"
    if val.lower() in ("none", "null"):
        return key, None
    try:
        if "." in val:
            return key, float(val)
        return key, int(val)
    except Exception:
        return key, val


def _apply_overrides(cfg, overrides):
    if not overrides:
        return
    applied = {}
    for item in overrides:
        key, val = _parse_override(item)
        if not key:
            continue
        setattr(cfg, key, val)
        applied[key] = val
    if applied:
        print(f"[config] overrides: {applied}", flush=True)


def _resolve_path(p: str) -> str:
    path = Path(p)
    if path.is_absolute():
        return str(path.resolve())
    # Prefer project root for data/* style paths
    if str(path).startswith("data/") or str(path).startswith("data\\"):
        return str((PROJECT_ROOT / path).resolve())
    return str((CORE_DIR / path).resolve())


def _pick_price_dirs(cfg):
    use_adj = bool(getattr(cfg, "USE_ADJ_PRICES", False) or getattr(core, "USE_ADJ_PRICES", False))
    adj_active = Path(_resolve_path(getattr(core, "PRICE_DIR_ACTIVE_ADJ", "")))
    adj_del = Path(_resolve_path(getattr(core, "PRICE_DIR_DELISTED_ADJ", "")))
    if use_adj and adj_active.exists() and adj_del.exists():
        if any(adj_active.glob("*.pkl")) or any(adj_del.glob("*.pkl")):
            return str(adj_active), str(adj_del)
    return _resolve_path(core.PRICE_DIR_ACTIVE), _resolve_path(core.PRICE_DIR_DELISTED)


def _make_engine_config(cfg):
    price_active, price_delisted = _pick_price_dirs(cfg)
    cfg_dict = {
        "PRICE_DIR_ACTIVE": price_active,
        "PRICE_DIR_DELISTED": price_delisted,
        "DELISTED_INFO": str(PROJECT_ROOT / "data" / "delisted_companies_2010_2026.csv"),
        "MIN_MARKET_CAP": getattr(cfg, "MIN_MARKET_CAP", core.MIN_MARKET_CAP),
        "MIN_DOLLAR_VOLUME": getattr(cfg, "MIN_DOLLAR_VOLUME", core.MIN_DOLLAR_VOLUME),
        "MIN_PRICE": getattr(cfg, "MIN_PRICE", core.MIN_PRICE),
        "TRANSACTION_COST": getattr(cfg, "TRANSACTION_COST", core.TRANSACTION_COST),
        "EXECUTION_DELAY": getattr(cfg, "EXECUTION_DELAY", core.EXECUTION_DELAY),
        "EXECUTION_USE_TRADING_DAYS": getattr(cfg, "EXECUTION_USE_TRADING_DAYS", False),
        "ENABLE_DYNAMIC_COST": getattr(cfg, "ENABLE_DYNAMIC_COST", False),
        "TRADE_SIZE_USD": getattr(cfg, "TRADE_SIZE_USD", 10000),
        "CALENDAR_SYMBOL": getattr(cfg, "CALENDAR_SYMBOL", getattr(core, "CALENDAR_SYMBOL", "SPY")),
    }

    optional_keys = [
        "MOMENTUM_LOOKBACK",
        "MOMENTUM_SKIP",
        "MOMENTUM_VOL_LOOKBACK",
        "MOMENTUM_USE_MONTHLY",
        "MOMENTUM_LOOKBACK_MONTHS",
        "MOMENTUM_SKIP_MONTHS",
        "MOMENTUM_ZSCORE",
        "MOMENTUM_WINSOR_Z",
        "MOMENTUM_USE_RESIDUAL",
        "MOMENTUM_BENCH_SYMBOL",
        "MOMENTUM_RESID_EST_WINDOW",
        "REBALANCE_MODE",
        "INDUSTRY_NEUTRAL",
        "INDUSTRY_MIN_GROUP",
        "INDUSTRY_COL",
        "INDUSTRY_MAP_PATH",
        "SIGNAL_ZSCORE",
        "SIGNAL_RANK",
        "SIGNAL_RANK_METHOD",
        "SIGNAL_RANK_PCT",
        "SIGNAL_WINSOR_Z",
        "SIGNAL_WINSOR_PCT_LOW",
        "SIGNAL_WINSOR_PCT_HIGH",
        "SIGNAL_MISSING_POLICY",
        "SIGNAL_MISSING_FILL",
        "SIGNAL_SMOOTH_WINDOW",
        "SIGNAL_SMOOTH_METHOD",
        "SIGNAL_SMOOTH_ALPHA",
        "UNIVERSE_MAX_VOL",
        "UNIVERSE_VOL_LOOKBACK",
        "REVERSAL_LOOKBACK",
        "REVERSAL_MODE",
        "REVERSAL_VOL_LOOKBACK",
        "REVERSAL_EARNINGS_FILTER_DAYS",
        "REVERSAL_MAX_GAP_PCT",
        "REVERSAL_MIN_DOLLAR_VOL",
        "QUALITY_WEIGHTS",
        "QUALITY_MAINSTREAM_COMPOSITE",
        "QUALITY_COMPONENT_TRANSFORM",
        "QUALITY_COMPONENT_INDUSTRY_ZSCORE",
        "QUALITY_COMPONENT_WINSOR_PCT_LOW",
        "QUALITY_COMPONENT_WINSOR_PCT_HIGH",
        "QUALITY_COMPONENT_MIN_COUNT",
        "QUALITY_COMPONENT_MISSING_POLICY",
        "VALUE_WEIGHTS",
        "VALUE_MAINSTREAM_COMPOSITE",
        "VALUE_COMPONENT_TRANSFORM",
        "VALUE_COMPONENT_INDUSTRY_ZSCORE",
        "VALUE_COMPONENT_WINSOR_PCT_LOW",
        "VALUE_COMPONENT_WINSOR_PCT_HIGH",
        "VALUE_COMPONENT_MIN_COUNT",
        "VALUE_COMPONENT_MISSING_POLICY",
        "FUNDAMENTALS_DIR",
        "VALUE_DIR",
        "LOW_VOL_WINDOW",
        "LOW_VOL_LOG_RETURN",
        "LOW_VOL_USE_RESIDUAL",
        "LOW_VOL_BENCH_SYMBOL",
        "LOW_VOL_DOWNSIDE_ONLY",
        "MARKET_CAP_DIR",
        "MARKET_CAP_STRICT",
        "SIGNAL_NEUTRALIZE_SIZE",
        "SIGNAL_NEUTRALIZE_BETA",
        "SIGNAL_NEUTRALIZE_COLS",
        "BETA_LOOKBACK",
        "BETA_BENCH_SYMBOL",
        "BETA_USE_LOG_RETURN",
        "COMBO_FORMULA",
        "COMBO_GATE_K",
        "COMBO_GATE_CLIP",
        "COMBO_VALUE_KEEP_Q",
        "COMBO_MOM_DROP_Q",
    ]
    for key in optional_keys:
        if hasattr(cfg, key):
            value = getattr(cfg, key)
            if key in ("FUNDAMENTALS_DIR", "VALUE_DIR", "INDUSTRY_MAP_PATH"):
                value = _resolve_path(value)
            cfg_dict[key] = value

    return cfg_dict


def _segment_ranges(start_date: str, end_date: str, years: int):
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    if start > end:
        raise ValueError("start_date must be <= end_date")

    segments = []
    cur = start
    while cur <= end:
        seg_end = cur + pd.DateOffset(years=years) - pd.Timedelta(days=1)
        if seg_end > end:
            seg_end = end
        segments.append((cur.strftime("%Y-%m-%d"), seg_end.strftime("%Y-%m-%d")))
        cur = seg_end + pd.Timedelta(days=1)
    return segments


def _analyze_segment(signals_df: pd.DataFrame, returns_df: pd.DataFrame):
    analyzer = PerformanceAnalyzer()
    ic_stats = analyzer.calculate_ic(signals_df, returns_df)
    summary = analyzer.analyze_backtest(signals_df, returns_df)
    return ic_stats, summary


def run_factor(factor: str, cfg, weights: dict, segments, args, out_dir: Path):
    factor_dir = out_dir / factor
    factor_dir.mkdir(parents=True, exist_ok=True)
    print(f"[{factor}] start | segments={len(segments)} out={factor_dir}", flush=True)

    summary_path = factor_dir / "segment_summary.csv"
    existing = None
    done_keys = set()
    if args.resume and summary_path.exists():
        try:
            existing = pd.read_csv(summary_path)
            for _, r in existing.iterrows():
                done_keys.add((r.get("segment_start"), r.get("segment_end")))
        except Exception:
            existing = None

    rows = []
    for seg_start, seg_end in segments:
        if (seg_start, seg_end) in done_keys:
            continue
        print(f"[{factor}] segment start {seg_start} -> {seg_end}", flush=True)
        cfg_dict = _make_engine_config(cfg)
        if args.use_cache:
            cache_root = Path(args.cache_dir).expanduser().resolve() if args.cache_dir else (PROJECT_ROOT / "cache" / "signals")
            cfg_dict["SIGNAL_CACHE_DIR"] = str(cache_root)
        cfg_dict["SIGNAL_CACHE_USE"] = bool(args.use_cache)
        cfg_dict["SIGNAL_CACHE_REFRESH"] = bool(args.refresh_cache)
        # Optional market cap history for PIT filtering
        mc_dir = getattr(cfg, "MARKET_CAP_DIR", None)
        if mc_dir:
            cfg_dict["MARKET_CAP_DIR"] = _resolve_path(mc_dir)
            cfg_dict["MARKET_CAP_STRICT"] = bool(getattr(cfg, "MARKET_CAP_STRICT", True))
        engine = BacktestEngine(cfg_dict)
        try:
            print(f"[{factor}] run_backtest enter", flush=True)
            results = engine.run_backtest(
                seg_start,
                seg_end,
                factor_weights=weights,
                rebalance_freq=cfg.REBALANCE_FREQ,
                holding_period=cfg.HOLDING_PERIOD,
                long_pct=args.long_pct,
                short_pct=args.short_pct,
            )
            print(f"[{factor}] run_backtest exit | keys={list(results.keys())}", flush=True)
        except Exception as e:
            print(f"[{factor}] segment error {seg_start} -> {seg_end}: {e}", flush=True)
            raise

        returns_for_ic = results.get("forward_returns")
        if returns_for_ic is None or len(returns_for_ic) == 0:
            returns_for_ic = results["returns"]
        ic_stats, summary = _analyze_segment(results["signals"], returns_for_ic)
        raw_returns = results.get("forward_returns_raw")
        ic_stats_raw = None
        if raw_returns is not None and len(raw_returns) > 0:
            ic_stats_raw, _ = _analyze_segment(results["signals"], raw_returns)

        row = {
            "factor": factor,
            "segment_start": seg_start,
            "segment_end": seg_end,
            "ic": ic_stats.get("ic"),
            "ic_raw": ic_stats_raw.get("ic") if ic_stats_raw else None,
            "ic_overall": ic_stats.get("ic_overall"),
            "ic_raw_overall": ic_stats_raw.get("ic_overall") if ic_stats_raw else None,
            "t_stat": ic_stats.get("t_stat"),
            "p_value": ic_stats.get("p_value"),
            "n_dates": ic_stats.get("n"),
            "n_signals": ic_stats.get("n_merged"),
            "mean_return": summary.get("mean_return"),
            "median_return": summary.get("median_return"),
            "std_return": summary.get("std_return"),
            "sharpe": summary.get("sharpe"),
            "win_rate": summary.get("win_rate"),
            "rebalance_freq": cfg.REBALANCE_FREQ,
            "holding_period": cfg.HOLDING_PERIOD,
        }
        rows.append(row)

        if args.save_raw:
            safe_tag = f"{seg_start.replace('-', '')}_{seg_end.replace('-', '')}"
            results["signals"].to_csv(factor_dir / f"signals_{safe_tag}.csv", index=False)
            results["returns"].to_csv(factor_dir / f"returns_{safe_tag}.csv", index=False)

        print(
            f"[{factor}] {seg_start} -> {seg_end} | "
            f"ic={row['ic'] if row['ic'] is not None else 'N/A'} "
            f"ic_raw={row['ic_raw'] if row['ic_raw'] is not None else 'N/A'} "
            f"n={row['n_signals'] if row['n_signals'] is not None else 0}"
        )

        del engine
        gc.collect()

    df = pd.DataFrame(rows)
    if existing is not None:
        combined = pd.concat([existing, df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["segment_start", "segment_end"])
        combined.to_csv(summary_path, index=False)
        df = combined
    else:
        df.to_csv(summary_path, index=False)
    print(f"[{factor}] done | rows={len(df)} summary={summary_path}", flush=True)

    meta = {
        "factor": factor,
        "run_time": datetime.now().isoformat(),
        "segments": len(segments),
        "segment_years": args.years,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "long_pct": args.long_pct,
        "short_pct": args.short_pct,
        "save_raw": bool(args.save_raw),
        "use_cache": bool(args.use_cache),
        "cache_dir": str(Path(args.cache_dir).expanduser().resolve()) if args.cache_dir else None,
        "refresh_cache": bool(args.refresh_cache),
    }
    with open(factor_dir / "run_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--factors", type=str, default="momentum,reversal,quality,value")
    parser.add_argument("--start-date", type=str, default=getattr(core, "TRAIN_START", "2015-01-01"))
    parser.add_argument("--end-date", type=str, default=getattr(core, "TEST_END", "2026-01-28"))
    parser.add_argument("--years", type=int, default=2)
    parser.add_argument("--long-pct", type=float, default=0.2)
    parser.add_argument("--short-pct", type=float, default=0.0)
    parser.add_argument("--save-raw", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-segments", type=int, default=0)
    parser.add_argument("--out-dir", type=str, default="")
    parser.add_argument("--invert-momentum", action="store_true")
    parser.add_argument("--set", action="append", default=[], help="Override config: KEY=VALUE (repeatable)")
    parser.add_argument("--use-cache", action="store_true", help="Enable Stage2 signal cache")
    parser.add_argument("--cache-dir", type=str, default="", help="Signal cache root directory")
    parser.add_argument("--refresh-cache", action="store_true", help="Recompute and overwrite existing cache")
    args = parser.parse_args()

    factor_list = [f.strip().lower() for f in args.factors.split(",") if f.strip()]
    unknown = [f for f in factor_list if f not in FACTOR_SPECS]
    if unknown:
        raise SystemExit(f"Unknown factors: {unknown}. Supported: {sorted(FACTOR_SPECS.keys())}")

    segments = _segment_ranges(args.start_date, args.end_date, args.years)
    if args.max_segments and args.max_segments > 0:
        segments = segments[: args.max_segments]

    if args.resume and not args.out_dir:
        raise SystemExit("--resume requires --out-dir pointing to an existing run folder")

    if args.out_dir:
        out_dir = Path(args.out_dir).expanduser().resolve()
    else:
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        out_dir = PROJECT_ROOT / "segment_results" / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    faulthandler.enable()
    print(f"[run] factors={factor_list} segments={len(segments)} out={out_dir}", flush=True)
    if args.use_cache:
        cache_root = Path(args.cache_dir).expanduser().resolve() if args.cache_dir else (PROJECT_ROOT / "cache" / "signals")
        print(f"[cache] enabled dir={cache_root} refresh={bool(args.refresh_cache)}", flush=True)

    all_rows = []
    for factor in factor_list:
        spec = FACTOR_SPECS[factor]
        if factor == "momentum" and args.invert_momentum:
            spec = dict(spec)
            spec["weights"] = dict(spec["weights"])
            spec["weights"]["momentum"] = -1.0
        cfg = _load_cfg(spec["config_path"])
        _apply_overrides(cfg, args.set)
        # combo_v2 weights must come from its config (COMBO_WEIGHTS), not hardcoded defaults.
        weights = dict(spec["weights"])
        if factor == "combo_v2" and hasattr(cfg, "COMBO_WEIGHTS"):
            weights = dict(getattr(cfg, "COMBO_WEIGHTS"))
        df = run_factor(factor, cfg, weights, segments, args, out_dir)
        all_rows.append(df)

    if all_rows:
        combined_path = out_dir / "all_factors_summary.csv"
        new_all = pd.concat(all_rows, ignore_index=True)
        if args.resume and combined_path.exists():
            try:
                old_all = pd.read_csv(combined_path)
                new_all = pd.concat([old_all, new_all], ignore_index=True)
                new_all = new_all.drop_duplicates(subset=["factor", "segment_start", "segment_end"])
            except Exception:
                pass
        new_all.to_csv(combined_path, index=False)

    print(f"Saved results to: {out_dir}")


if __name__ == "__main__":
    main()
