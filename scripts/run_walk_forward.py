"""
Walk-forward validation runner (rolling train/test windows).
"""

import argparse
import gc
import json
from datetime import datetime
from pathlib import Path
import importlib.util as _ilu

import pandas as pd

from backtest.backtest_engine import BacktestEngine
from backtest.performance_analyzer import PerformanceAnalyzer
from backtest.walk_forward_validator import WalkForwardValidator
import backtest.config as core
from scripts.research_governance import (
    build_manifest,
    check_non_negative_int,
    check_path_exists,
    enforce_freeze,
    stable_hash,
    write_json,
)


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
    "pead": {
        "config_path": PROJECT_ROOT / "strategies" / "pead_v1" / "config.py",
        "weights": {"momentum": 0.0, "reversal": 0.0, "low_vol": 0.0, "pead": 1.0},
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
    return str((CORE_DIR / p).resolve())


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
        "SUE_THRESHOLD",
        "LOOKBACK_QUARTERS",
        "DATE_SHIFT_DAYS",
        "PEAD_USE_TRADING_DAY_SHIFT",
        "PEAD_EVENT_MAX_AGE_DAYS",
        "COMBO_FORMULA",
        "COMBO_GATE_K",
        "COMBO_GATE_CLIP",
        "COMBO_VALUE_KEEP_Q",
        "COMBO_MOM_DROP_Q",
    ]
    for key in optional_keys:
        if hasattr(cfg, key):
            value = getattr(cfg, key)
            if key in ("FUNDAMENTALS_DIR", "VALUE_DIR"):
                value = _resolve_path(value)
            cfg_dict[key] = value

    return cfg_dict


def _analyze(signals_df: pd.DataFrame, returns_df: pd.DataFrame):
    analyzer = PerformanceAnalyzer()
    ic_stats = analyzer.calculate_ic(signals_df, returns_df)
    summary = analyzer.analyze_backtest(signals_df, returns_df)
    return ic_stats, summary


def run_factor(factor: str, cfg, weights: dict, windows, args, out_dir: Path):
    factor_dir = out_dir / factor
    factor_dir.mkdir(parents=True, exist_ok=True)

    summary_path = factor_dir / "walk_forward_summary.csv"
    existing = None
    done_keys = set()
    if args.resume and summary_path.exists():
        try:
            existing = pd.read_csv(summary_path)
            for _, r in existing.iterrows():
                done_keys.add((r.get("train_start"), r.get("train_end"),
                               r.get("test_start"), r.get("test_end")))
        except Exception:
            existing = None

    rows = []
    audit_rows = []
    for w in windows:
        key = (w["train_start"], w["train_end"], w["test_start"], w["test_end"])
        if key in done_keys:
            continue
        cfg_dict = _make_engine_config(cfg)
        engine = BacktestEngine(cfg_dict)

        train = engine.run_backtest(
            w["train_start"],
            w["train_end"],
            factor_weights=weights,
            rebalance_freq=cfg.REBALANCE_FREQ,
            holding_period=cfg.HOLDING_PERIOD,
            long_pct=args.long_pct,
            short_pct=args.short_pct,
        )
        test = engine.run_backtest(
            w["test_start"],
            w["test_end"],
            factor_weights=weights,
            rebalance_freq=cfg.REBALANCE_FREQ,
            holding_period=cfg.HOLDING_PERIOD,
            long_pct=args.long_pct,
            short_pct=args.short_pct,
        )

        train_ret_for_ic = train.get("forward_returns")
        if train_ret_for_ic is None or len(train_ret_for_ic) == 0:
            train_ret_for_ic = train["returns"]
        test_ret_for_ic = test.get("forward_returns")
        if test_ret_for_ic is None or len(test_ret_for_ic) == 0:
            test_ret_for_ic = test["returns"]

        train_ic, train_sum = _analyze(train["signals"], train_ret_for_ic)
        test_ic, test_sum = _analyze(test["signals"], test_ret_for_ic)

        row = {
            "factor": factor,
            "train_start": w["train_start"],
            "train_end": w["train_end"],
            "test_start": w["test_start"],
            "test_end": w["test_end"],
            "test_year": w.get("test_year"),
            "train_ic": train_ic.get("ic"),
            "train_ic_overall": train_ic.get("ic_overall"),
            "train_n_dates": train_ic.get("n"),
            "train_n_signals": train_ic.get("n_merged"),
            "test_ic": test_ic.get("ic"),
            "test_ic_overall": test_ic.get("ic_overall"),
            "test_n_dates": test_ic.get("n"),
            "test_n_signals": test_ic.get("n_merged"),
            "test_sharpe": test_sum.get("sharpe"),
            "test_win_rate": test_sum.get("win_rate"),
            "rebalance_freq": cfg.REBALANCE_FREQ,
            "holding_period": cfg.HOLDING_PERIOD,
        }
        rows.append(row)

        train_aud = train.get("universe_audit")
        if train_aud is not None and len(train_aud) > 0:
            tdf = train_aud.copy()
            tdf["factor"] = factor
            tdf["window_train_start"] = w["train_start"]
            tdf["window_train_end"] = w["train_end"]
            tdf["window_test_start"] = w["test_start"]
            tdf["window_test_end"] = w["test_end"]
            tdf["window_test_year"] = w.get("test_year")
            tdf["phase"] = "train"
            audit_rows.extend(tdf.to_dict(orient="records"))
        test_aud = test.get("universe_audit")
        if test_aud is not None and len(test_aud) > 0:
            sdf = test_aud.copy()
            sdf["factor"] = factor
            sdf["window_train_start"] = w["train_start"]
            sdf["window_train_end"] = w["train_end"]
            sdf["window_test_start"] = w["test_start"]
            sdf["window_test_end"] = w["test_end"]
            sdf["window_test_year"] = w.get("test_year")
            sdf["phase"] = "test"
            audit_rows.extend(sdf.to_dict(orient="records"))

        if args.save_raw:
            tag = f"{w['train_start'].replace('-', '')}_{w['test_end'].replace('-', '')}"
            train["signals"].to_csv(factor_dir / f"train_signals_{tag}.csv", index=False)
            train["returns"].to_csv(factor_dir / f"train_returns_{tag}.csv", index=False)
            test["signals"].to_csv(factor_dir / f"test_signals_{tag}.csv", index=False)
            test["returns"].to_csv(factor_dir / f"test_returns_{tag}.csv", index=False)

        print(
            f"[{factor}] {w['train_start']}->{w['train_end']} | "
            f"test {w['test_start']}->{w['test_end']} | "
            f"test_ic={row['test_ic'] if row['test_ic'] is not None else 'N/A'}"
        )

        del engine
        gc.collect()

    df = pd.DataFrame(rows)
    if existing is not None:
        combined = pd.concat([existing, df], ignore_index=True)
        combined = combined.drop_duplicates(
            subset=["train_start", "train_end", "test_start", "test_end"]
        )
        combined.to_csv(summary_path, index=False)
        df = combined
    else:
        df.to_csv(summary_path, index=False)

    meta = {
        "factor": factor,
        "run_time": datetime.now().isoformat(),
        "train_years": args.train_years,
        "test_years": args.test_years,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "long_pct": args.long_pct,
        "short_pct": args.short_pct,
        "save_raw": bool(args.save_raw),
    }
    with open(factor_dir / "run_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    audit_path = factor_dir / "universe_filter_audit.csv"
    if len(audit_rows) > 0:
        aud = pd.DataFrame(audit_rows)
        if args.resume and audit_path.exists():
            try:
                old_aud = pd.read_csv(audit_path)
                aud = pd.concat([old_aud, aud], ignore_index=True)
                aud = aud.drop_duplicates(
                    subset=["factor", "phase", "window_train_start", "window_test_end", "rebalance_date"],
                    keep="last",
                )
            except Exception:
                pass
        aud.to_csv(audit_path, index=False)
    elif not audit_path.exists():
        pd.DataFrame().to_csv(audit_path, index=False)

    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--factors", type=str, default="momentum,reversal,quality,value")
    parser.add_argument("--train-years", type=int, default=3)
    parser.add_argument("--test-years", type=int, default=1)
    parser.add_argument("--start-year", type=int, default=2010)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--long-pct", type=float, default=0.2)
    parser.add_argument("--short-pct", type=float, default=0.0)
    parser.add_argument("--save-raw", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-windows", type=int, default=0)
    parser.add_argument("--only-years", type=str, default="")
    parser.add_argument("--out-dir", type=str, default="")
    parser.add_argument("--set", action="append", default=[], help="Override config: KEY=VALUE (repeatable)")
    parser.add_argument("--freeze-file", type=str, default="", help="Path to freeze json (enforce if exists)")
    parser.add_argument("--write-freeze", action="store_true", help="Create freeze file if missing")
    parser.add_argument("--skip-guardrails", action="store_true", help="Skip PIT/lag guardrails (not recommended)")
    args = parser.parse_args()

    factor_list = [f.strip().lower() for f in args.factors.split(",") if f.strip()]
    unknown = [f for f in factor_list if f not in FACTOR_SPECS]
    if unknown:
        raise SystemExit(f"Unknown factors: {unknown}. Supported: {sorted(FACTOR_SPECS.keys())}")

    validator = WalkForwardValidator(train_years=args.train_years, test_years=args.test_years)
    windows = validator.generate_windows(args.start_year, args.end_year)
    if not windows:
        raise SystemExit("No windows generated. Check start/end years and train/test lengths.")

    if args.only_years:
        year_set = {int(x) for x in args.only_years.split(",") if x.strip()}
        windows = [w for w in windows if int(w.get("test_year")) in year_set]

    if args.max_windows and args.max_windows > 0:
        windows = windows[: args.max_windows]

    if args.resume and not args.out_dir:
        raise SystemExit("--resume requires --out-dir pointing to an existing run folder")

    if args.out_dir:
        out_dir = Path(args.out_dir).expanduser().resolve()
    else:
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        out_dir = PROJECT_ROOT / "walk_forward_results" / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    run_plan = []
    for factor in factor_list:
        spec = FACTOR_SPECS[factor]
        cfg = _load_cfg(spec["config_path"])
        _apply_overrides(cfg, args.set)
        weights = dict(spec["weights"])
        if factor == "combo_v2" and hasattr(cfg, "COMBO_WEIGHTS"):
            weights = dict(getattr(cfg, "COMBO_WEIGHTS"))
        cfg_snapshot = {
            k: getattr(cfg, k)
            for k in dir(cfg)
            if k.isupper() and not k.startswith("__")
        }
        run_plan.append(
            {
                "factor": factor,
                "config_path": str(spec["config_path"]),
                "weights": weights,
                "cfg_snapshot": cfg_snapshot,
                "cfg_obj": cfg,
            }
        )

    governance_payload = {
        "windows": windows,
        "factors": [
            {
                "factor": p["factor"],
                "config_path": p["config_path"],
                "weights": p["weights"],
                "cfg_snapshot": p["cfg_snapshot"],
            }
            for p in run_plan
        ],
        "runtime": {
            "train_years": args.train_years,
            "test_years": args.test_years,
            "start_year": args.start_year,
            "end_year": args.end_year,
            "only_years": args.only_years,
            "max_windows": args.max_windows,
            "long_pct": args.long_pct,
            "short_pct": args.short_pct,
            "set_overrides": args.set,
            "resume": bool(args.resume),
        },
    }
    if not args.skip_guardrails:
        guard_errors = []
        for p in run_plan:
            factor = p["factor"]
            cfg = p["cfg_obj"]
            weights = p["weights"]
            active = {k for k, v in weights.items() if v is not None and float(v) != 0.0}
            prefix = f"{factor}"
            check_non_negative_int(f"{prefix}.FACTOR_LAG_DAYS", getattr(cfg, "FACTOR_LAG_DAYS", 0), guard_errors)
            check_non_negative_int(f"{prefix}.MOMENTUM_LAG_DAYS", getattr(cfg, "MOMENTUM_LAG_DAYS", 0), guard_errors)
            check_non_negative_int(f"{prefix}.REVERSAL_LAG_DAYS", getattr(cfg, "REVERSAL_LAG_DAYS", 0), guard_errors)
            check_non_negative_int(f"{prefix}.LOW_VOL_LAG_DAYS", getattr(cfg, "LOW_VOL_LAG_DAYS", 0), guard_errors)
            check_non_negative_int(f"{prefix}.BETA_LAG_DAYS", getattr(cfg, "BETA_LAG_DAYS", 0), guard_errors)
            check_non_negative_int(f"{prefix}.PEAD_LAG_DAYS", getattr(cfg, "PEAD_LAG_DAYS", 0), guard_errors)
            check_non_negative_int(f"{prefix}.QUALITY_LAG_DAYS", getattr(cfg, "QUALITY_LAG_DAYS", 0), guard_errors)
            check_non_negative_int(f"{prefix}.VALUE_LAG_DAYS", getattr(cfg, "VALUE_LAG_DAYS", 0), guard_errors)

            if "quality" in active:
                q_dir = getattr(cfg, "FUNDAMENTALS_DIR", str(PROJECT_ROOT / "data" / "fmp" / "ratios" / "quality"))
                check_path_exists(f"{prefix}.FUNDAMENTALS_DIR", _resolve_path(q_dir), guard_errors)
            if "value" in active:
                v_dir = getattr(cfg, "VALUE_DIR", str(PROJECT_ROOT / "data" / "fmp" / "ratios" / "value"))
                check_path_exists(f"{prefix}.VALUE_DIR", _resolve_path(v_dir), guard_errors)
            if "pead" in active:
                price_active = _resolve_path(core.PRICE_DIR_ACTIVE)
                e_dir = getattr(cfg, "EARNINGS_DIR", str(Path(price_active).resolve().parent / "Owner_Earnings"))
                check_path_exists(f"{prefix}.EARNINGS_DIR", _resolve_path(e_dir), guard_errors)
            mc = getattr(cfg, "MIN_MARKET_CAP", None)
            mc_strict = bool(getattr(cfg, "MARKET_CAP_STRICT", True))
            if mc is not None and mc_strict:
                mc_dir = getattr(cfg, "MARKET_CAP_DIR", None)
                if mc_dir is None:
                    guard_errors.append(f"{prefix}.MARKET_CAP_DIR is required when MIN_MARKET_CAP is set and strict mode is enabled")
                else:
                    check_path_exists(f"{prefix}.MARKET_CAP_DIR", _resolve_path(mc_dir), guard_errors)
        if guard_errors:
            raise SystemExit("Guardrails failed:\n- " + "\n- ".join(guard_errors))

    manifest = build_manifest(
        root=PROJECT_ROOT,
        runner="run_walk_forward",
        config_hash=stable_hash(governance_payload),
        run_scope={
            "factors": factor_list,
            "window_count": len(windows),
        },
        cli_args=vars(args),
        output_root=out_dir,
    )
    enforce_freeze(
        freeze_file=(args.freeze_file or None),
        manifest=manifest,
        write_freeze=bool(args.write_freeze),
    )
    write_json(out_dir / "run_manifest.json", manifest)

    all_rows = []
    for p in run_plan:
        factor = p["factor"]
        cfg = p["cfg_obj"]
        weights = p["weights"]
        df = run_factor(factor, cfg, weights, windows, args, out_dir)
        all_rows.append(df)

    if all_rows:
        combined_path = out_dir / "all_factors_walk_forward.csv"
        new_all = pd.concat(all_rows, ignore_index=True)
        if args.resume and combined_path.exists():
            try:
                old_all = pd.read_csv(combined_path)
                new_all = pd.concat([old_all, new_all], ignore_index=True)
                new_all = new_all.drop_duplicates(
                    subset=["factor", "train_start", "train_end", "test_start", "test_end"]
                )
            except Exception:
                pass
        new_all.to_csv(combined_path, index=False)

    write_json(out_dir / "run_manifest_latest.json", manifest)
    print(f"Saved results to: {out_dir}")


if __name__ == "__main__":
    main()
