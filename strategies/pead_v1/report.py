import os
import json
import sys
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime


def _try_import_scipy():
    try:
        from scipy import stats
        return stats
    except Exception:
        return None


def get_git_info(repo_root: str):
    try:
        commit = subprocess.check_output(['git', '-C', repo_root, 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL).decode().strip()
        dirty = subprocess.check_output(['git', '-C', repo_root, 'status', '--porcelain'], stderr=subprocess.DEVNULL).decode().strip()
        branch = subprocess.check_output(['git', '-C', repo_root, 'rev-parse', '--abbrev-ref', 'HEAD'], stderr=subprocess.DEVNULL).decode().strip()
        return {
            "commit": commit[:8],
            "commit_full": commit,
            "branch": branch,
            "dirty": bool(dirty),
            "uncommitted_files": len(dirty.splitlines()) if dirty else 0
        }
    except Exception:
        return {"error": "Not a git repository or git not available"}


def compare_data_manifest(curr, base):
    changes = []
    try:
        cp = curr.get('price_data', {})
        bp = base.get('price_data', {})
        if cp.get('total_price_files') != bp.get('total_price_files'):
            changes.append(f"Price files: {bp.get('total_price_files')} → {cp.get('total_price_files')}")
        if cp.get('last_updated') != bp.get('last_updated'):
            changes.append(f"Price updated: {bp.get('last_updated')} → {cp.get('last_updated')}")

        ce = curr.get('earnings_data', {})
        be = base.get('earnings_data', {})
        if ce.get('total_files') != be.get('total_files'):
            changes.append(f"Earnings files: {be.get('total_files')} → {ce.get('total_files')}")
        if ce.get('downloaded_at') != be.get('downloaded_at'):
            changes.append(f"Earnings updated: {be.get('downloaded_at')} → {ce.get('downloaded_at')}")

        cc = curr.get('code_version', {}).get('git', {})
        bc = base.get('code_version', {}).get('git', {})
        if cc.get('commit') != bc.get('commit'):
            changes.append(f"Code: {bc.get('commit')} → {cc.get('commit')}")
        if cc.get('dirty') != bc.get('dirty'):
            if cc.get('dirty'):
                changes.append("Code has uncommitted changes")
    except Exception as e:
        changes.append(f"Manifest compare error: {e}")
    return changes


def extract_exit_type_distribution(returns_df: pd.DataFrame):
    if returns_df is None or len(returns_df) == 0 or 'exit_type' not in returns_df.columns:
        return {"error": "exit_type missing", "total": 0, "quality_ok": False}

    total = len(returns_df)
    dist = returns_df['exit_type'].value_counts().to_dict()

    def pack(k):
        c = int(dist.get(k, 0))
        return {"count": c, "pct": (c / total * 100) if total > 0 else 0.0}

    normal_pct = pack('normal')["pct"]
    return {
        "normal": pack('normal'),
        "delisted": pack('delisted'),
        "no_data": pack('no_data'),
        "total": total,
        "quality_ok": (normal_pct >= 75.0)
    }


def calculate_ic_robust(signals_df: pd.DataFrame, returns_df: pd.DataFrame):
    """
    Robust IC significance:
      - overall IC (Pearson)
      - overall Spearman IC
      - IC-by-date series mean t-test (conservative)
    """
    if signals_df is None or returns_df is None or len(signals_df) == 0 or len(returns_df) == 0:
        return {"ic": None, "n_signals": 0, "warning": "No data"}

    merged = pd.merge(
        signals_df[['symbol', 'date', 'signal']],
        returns_df[['symbol', 'signal_date', 'return']],
        left_on=['symbol', 'date'],
        right_on=['symbol', 'signal_date'],
        how='inner'
    )
    if len(merged) < 5:
        return {"ic": None, "n_signals": int(len(merged)), "warning": "Too few merged rows"}

    merged = merged.copy()
    merged['date'] = pd.to_datetime(merged['date'])

    ic_overall = merged['signal'].corr(merged['return'])
    ic_spearman = merged['signal'].corr(merged['return'], method='spearman')
    n_total = int(len(merged))

    # Naive t-stat (independence assumption)
    t_naive = None
    if n_total > 2 and ic_overall is not None and not np.isnan(ic_overall) and abs(ic_overall) < 1:
        t_naive = float(ic_overall) * np.sqrt(n_total - 2) / np.sqrt(1 - float(ic_overall) ** 2)

    # Robust: IC series by date (requires cross-section per date)
    def _date_ic(x):
        if len(x) < 5:
            return np.nan
        return x['signal'].corr(x['return'])

    ic_by_date = merged.groupby('date').apply(_date_ic).dropna()
    n_dates_total = merged['date'].nunique()
    n_dates_valid = int(len(ic_by_date))

    stats = _try_import_scipy()
    t_robust = None
    p_robust = None
    ci95 = None

    if n_dates_valid >= 5:
        ic_mean = float(ic_by_date.mean())
        ic_std = float(ic_by_date.std()) if not np.isnan(ic_by_date.std()) else None
        if ic_std is not None and ic_std > 0:
            t_robust = ic_mean / (ic_std / np.sqrt(n_dates_valid))
            if stats is not None:
                p_robust = float(2 * (1 - stats.t.cdf(abs(t_robust), n_dates_valid - 1)))
                margin = float(stats.t.ppf(0.975, n_dates_valid - 1) * (ic_std / np.sqrt(n_dates_valid)))
                ci95 = [ic_mean - margin, ic_mean + margin]
    else:
        ic_mean = float(ic_by_date.mean()) if n_dates_valid > 0 else None
        ic_std = float(ic_by_date.std()) if n_dates_valid > 1 else None

    # Cross-section size diagnostics
    cs_n = merged.groupby('date').size()
    avg_cs_n = float(cs_n.mean()) if len(cs_n) else None

    out = {
        "ic": float(ic_overall) if ic_overall is not None and not np.isnan(ic_overall) else None,
        "ic_spearman": float(ic_spearman) if ic_spearman is not None and not np.isnan(ic_spearman) else None,
        "n_signals": n_total,

        "t_stat_naive": t_naive,
        "note_naive": "Assumes independence; optimistic",

        "ic_by_period": {
            "mean": float(ic_by_date.mean()) if n_dates_valid > 0 else None,
            "std": float(ic_by_date.std()) if n_dates_valid > 1 else None,
            "n_periods_valid": n_dates_valid,
            "n_periods_total": int(n_dates_total),
            "avg_cross_section_n": avg_cs_n
        },

        "t_stat_robust": float(t_robust) if t_robust is not None else None,
        "p_value_robust": float(p_robust) if p_robust is not None else None,
        "significant_robust": bool(p_robust < 0.05) if p_robust is not None else False,
        "confidence_interval_95": ci95,

        "note_robust": "Period-aggregated IC series; more realistic",
        "warning": f"Few valid periods (n={n_dates_valid})" if n_dates_valid < 20 else None
    }
    return out


def calculate_data_manifest(repo_root: str):
    price_active = os.path.join(repo_root, "data/prices")
    price_del = os.path.join(repo_root, "data/prices_delisted")
    earn_dir = os.path.join(repo_root, "data/Owner_Earnings")
    delisted_csv = os.path.join(repo_root, "data/delisted_companies_2010_2026.csv")

    def safe_count(path):
        try:
            return len([x for x in os.listdir(path) if x.endswith(".pkl")])
        except Exception:
            return None

    def safe_mtime(path):
        try:
            return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")
        except Exception:
            return None

    return {
        "generated_at": datetime.now().isoformat(),
        "price_data": {
            "active_stocks": safe_count(price_active),
            "delisted_stocks": safe_count(price_del),
            "total_price_files": (safe_count(price_active) or 0) + (safe_count(price_del) or 0),
            "last_updated": max(filter(None, [safe_mtime(price_active), safe_mtime(price_del)]), default=None)
        },
        "earnings_data": {
            "total_files": safe_count(earn_dir),
            "downloaded_at": safe_mtime(earn_dir),
            "api_endpoint": "https://financialmodelingprep.com/stable/earnings",
            "critical_fields": ["date", "epsActual", "epsEstimated"]
        },
        "delisted_info": {
            "file": os.path.basename(delisted_csv),
            "last_updated": safe_mtime(delisted_csv)
        }
    }


def calculate_data_coverage_correct(backtest_results, factor_engine, universe_builder, sue_threshold: float):
    """
    Use actual rebalance_dates from backtest_results.
    Tier breakdown:
      universe -> has_event -> calculable -> strong
    """
    reb_dates = backtest_results.get('rebalance_dates', [])
    if not reb_dates:
        return {"error": "rebalance_dates missing", "quality_ok": False}

    records = []
    total_fail = {'no_earnings_data': 0, 'no_event_on_date': 0, 'lookback_insufficient': 0, 'std_nan': 0}

    for d in reb_dates:
        universe = universe_builder.get_universe(d)
        u = len(universe)

        has_event = 0
        calculable = 0
        strong = 0

        fail = {'no_earnings_data': 0, 'no_event_on_date': 0, 'lookback_insufficient': 0, 'std_nan': 0}

        for sym in universe:
            info = factor_engine.pead_factor.get_sue_raw(sym, d)
            if info['has_event']:
                has_event += 1
                if info['sue'] is not None:
                    calculable += 1
                    if abs(info['sue']) > sue_threshold:
                        strong += 1
                else:
                    fail[info['reason']] += 1
            else:
                fail[info['reason']] += 1

        for k in total_fail:
            total_fail[k] += fail.get(k, 0)

        records.append({
            "date": d,
            "universe": u,
            "has_event": has_event,
            "calculable": calculable,
            "strong": strong,
            "event_rate": (has_event / u * 100) if u > 0 else 0.0,
            "calculable_rate": (calculable / u * 100) if u > 0 else 0.0,
            "strong_rate": (strong / u * 100) if u > 0 else 0.0,
        })

    df = pd.DataFrame(records)
    if len(df) == 0:
        return {"error": "coverage df empty", "quality_ok": False}

    event_rate = float(df['event_rate'].mean())
    calc_rate = float(df['calculable_rate'].mean())
    strong_rate = float(df['strong_rate'].mean())

    return {
        "rebalance_periods": int(len(df)),
        "avg_universe": float(df['universe'].mean()),
        "avg_has_event": float(df['has_event'].mean()),
        "avg_calculable": float(df['calculable'].mean()),
        "avg_strong": float(df['strong'].mean()),
        "rates": {
            "event_rate": event_rate,
            "calculable_rate": calc_rate,
            "strong_rate": strong_rate
        },
        "breakdown": {
            "has_event_but_not_calculable_pct": event_rate - calc_rate,
            "calculable_but_weak_pct": calc_rate - strong_rate
        },
        "failure_reasons": total_fail,
        "quality_ok": (calc_rate >= 10.0)
    }


def generate_report(repo_root: str, results, cfg, strategy_rules: dict):
    train = results['train']
    test = results['test']

    # IC robust
    perf_train = calculate_ic_robust(train['signals'], train['returns'])
    perf_test  = calculate_ic_robust(test['signals'], test['returns'])

    # Quality
    exit_dist = extract_exit_type_distribution(test['returns'])
    coverage = calculate_data_coverage_correct(
        test,
        factor_engine=results['_engine'].factor_engine,
        universe_builder=results['_engine'].universe_builder,
        sue_threshold=cfg.SUE_THRESHOLD
    )
    filtering_stats = test.get('filter_stats', {})

    report = {
        "metadata": {
            "strategy": cfg.STRATEGY_NAME,
            "version": cfg.STRATEGY_VERSION,
            "run_date": datetime.now().isoformat(),
        },
        "strategy_rules": strategy_rules,
        "data_manifest": {
            **calculate_data_manifest(repo_root),
            "code_version": {
                "git": get_git_info(repo_root),
                "python_version": sys.version.split()[0],
            }
        },
        "performance": {
            "train": perf_train,
            "test": perf_test,
            # legacy shortcuts
            "train_ic": perf_train.get("ic"),
            "test_ic": perf_test.get("ic"),
            "train_n": perf_train.get("n_signals", 0),
            "test_n": perf_test.get("n_signals", 0),
        },
        "yearly_breakdown": (
            test['analysis']['ic_yearly'].to_dict('records')
            if isinstance(test.get('analysis', {}).get('ic_yearly'), pd.DataFrame)
            else None
        ),
        "quality_metrics": {
            "exit_types": exit_dist,
            "data_coverage": coverage,
            "filtering_stats": filtering_stats,
            "mean_return": float(test['returns']['return'].mean()) if len(test['returns']) else None,
            "return_std": float(test['returns']['return'].std()) if len(test['returns']) else None,
        }
    }
    return report


def compare_with_baseline(current_report: dict, baseline_path: str):
    if not os.path.exists(baseline_path):
        return {
            "comparison_valid": False,
            "baseline_found": False,
            "manifest_changes": ["baseline.json not found"],
        }

    with open(baseline_path, 'r') as f:
        baseline = json.load(f)

    changes = compare_data_manifest(current_report.get('data_manifest', {}), baseline.get('data_manifest', {}))
    valid = (len(changes) == 0)

    curr_ic = current_report['performance']['test'].get('ic')
    base_ic = baseline['performance']['test'].get('ic')

    curr_n = current_report['performance']['test'].get('n_signals')
    base_n = baseline['performance']['test'].get('n_signals')

    # Exit type compare (if exists)
    curr_exit = current_report['quality_metrics']['exit_types']
    base_exit = baseline.get('quality_metrics', {}).get('exit_types', {})

    out = {
        "comparison_valid": valid,
        "baseline_found": True,
        "baseline_date": baseline.get('metadata', {}).get('run_date'),
        "manifest_changes": changes,
        "ic_difference": (None if curr_ic is None or base_ic is None else float(curr_ic) - float(base_ic)),
        "n_difference": (None if curr_n is None or base_n is None else int(curr_n) - int(base_n)),
        "exit_type_change": {
            "normal_pct": (
                None if 'normal' not in curr_exit or 'normal' not in base_exit
                else float(curr_exit['normal']['pct']) - float(base_exit['normal']['pct'])
            )
        }
    }
    return out
