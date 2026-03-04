"""
Factor Engine with Advanced SUE-based PEAD
Adds:
  - compute_signals(date, factor_weights)
  - build_positions(signals_df, long_pct, short_pct)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Iterable
import json
from pathlib import Path

from .data_engine import DataEngine
from .universe_builder import UniverseBuilder
from .fundamentals_engine import FundamentalsEngine
from .value_fundamentals_engine import ValueFundamentalsEngine
from . import pead_factor_cached
from .factor_factory import standardize_signal, resolve_factor_date

PROJECT_ROOT = Path(__file__).resolve().parents[1]

class FactorEngine:
    """
    Calculate factors including SUE-based PEAD and produce signals/positions.
    """

    def __init__(self,
                 data_engine: DataEngine,
                 universe_builder: Optional[UniverseBuilder] = None,
                 config_dict: Optional[dict] = None):
        self.data_engine = data_engine
        self.config = config_dict or {}

        # Universe builder
        self.universe_builder = universe_builder
        if self.universe_builder is None:
            exclude_symbols = []
            exclude_path = self.config.get('UNIVERSE_EXCLUDE_SYMBOLS_PATH')
            if exclude_path:
                try:
                    import os
                    if os.path.exists(exclude_path):
                        with open(exclude_path, 'r') as f:
                            exclude_symbols = [ln.strip() for ln in f.readlines() if ln.strip()]
                except Exception:
                    exclude_symbols = []

            self.universe_builder = UniverseBuilder(
                self.data_engine,
                min_market_cap=float(self.config.get('MIN_MARKET_CAP', 500e6)),
                min_dollar_volume=float(self.config.get('MIN_DOLLAR_VOLUME', 1e6)),
                min_price=float(self.config.get('MIN_PRICE', 5.0)),
                max_volatility=self.config.get('UNIVERSE_MAX_VOL'),
                vol_lookback=self.config.get('UNIVERSE_VOL_LOOKBACK'),
                exclude_symbols=exclude_symbols,
            )

        # Resolve earnings_dir robustly (avoid cwd relative path issues)
        earnings_dir = self.config.get('EARNINGS_DIR')
        if not earnings_dir:
            price_dir = self.config.get('PRICE_DIR_ACTIVE')
            if price_dir:
                try:
                    from pathlib import Path
                    earnings_dir = str(Path(price_dir).resolve().parent / "Owner_Earnings")
                except Exception:
                    earnings_dir = "../data/Owner_Earnings"
            else:
                earnings_dir = "../data/Owner_Earnings"

        factor_cls = self.config.get('PEAD_FACTOR_CLASS', pead_factor_cached.CachedPEADFactor)
        self.pead_factor = factor_cls(earnings_dir=earnings_dir)
        # Cache earnings dates per symbol for quick lookup
        self._earnings_date_cache = {}

        fundamentals_dir = self.config.get('FUNDAMENTALS_DIR', '../data/fmp/ratios/quality')
        self.fundamentals_engine = FundamentalsEngine(
            fundamentals_dir,
            max_staleness_days=self.config.get('QUALITY_MAX_STALENESS_DAYS', 270),
        )
        value_dir = self.config.get('VALUE_DIR', '../data/fmp/ratios/value')
        self.value_engine = ValueFundamentalsEngine(
            value_dir,
            max_staleness_days=self.config.get('VALUE_MAX_STALENESS_DAYS', 270),
        )
        self._institutional_summary_cache: Optional[Dict[str, pd.DataFrame]] = None
        self._owner_earnings_cache: Optional[Dict[str, pd.DataFrame]] = None
        self._earnings_calendar_cache: Optional[Dict[str, pd.DataFrame]] = None
        self._earnings_history_cache: Optional[Dict[str, pd.DataFrame]] = None

        # Optional industry neutralization
        self.industry_neutral = bool(self.config.get('INDUSTRY_NEUTRAL', False))
        self.industry_min_group = int(self.config.get('INDUSTRY_MIN_GROUP', 5))
        self.industry_col = self.config.get('INDUSTRY_COL')
        self.industry_map = self._load_industry_map(self.config.get('INDUSTRY_MAP_PATH'))

        # Optional tuning from config
        if hasattr(self.pead_factor, "sue_threshold") and self.config.get("SUE_THRESHOLD") is not None:
            self.pead_factor.sue_threshold = float(self.config.get("SUE_THRESHOLD"))
        if hasattr(self.pead_factor, "lookback_quarters") and self.config.get("LOOKBACK_QUARTERS") is not None:
            self.pead_factor.lookback_quarters = int(self.config.get("LOOKBACK_QUARTERS"))
        if hasattr(self.pead_factor, "date_shift_days") and self.config.get("DATE_SHIFT_DAYS") is not None:
            self.pead_factor.date_shift_days = int(self.config.get("DATE_SHIFT_DAYS"))
        if hasattr(self.pead_factor, "max_event_age_days") and self.config.get("PEAD_EVENT_MAX_AGE_DAYS") is not None:
            self.pead_factor.max_event_age_days = int(self.config.get("PEAD_EVENT_MAX_AGE_DAYS"))
        if hasattr(self.pead_factor, "use_trading_day_shift") and self.config.get("PEAD_USE_TRADING_DAY_SHIFT") is not None:
            self.pead_factor.use_trading_day_shift = bool(self.config.get("PEAD_USE_TRADING_DAY_SHIFT"))

    def _load_industry_map(self, path: Optional[str]) -> Dict[str, str]:
        if not path:
            return {}
        try:
            df = pd.read_csv(path)
        except Exception:
            return {}
        if df is None or len(df) == 0 or 'symbol' not in df.columns:
            return {}
        col = self.industry_col
        if not col:
            if 'industry' in df.columns:
                col = 'industry'
            elif 'sector' in df.columns:
                col = 'sector'
            else:
                return {}
        df = df[['symbol', col]].dropna()
        if len(df) == 0:
            return {}
        return dict(zip(df['symbol'].astype(str), df[col].astype(str)))

    def _resolve_data_path(self, path_value: Optional[str], default_rel: str) -> Path:
        raw = str(path_value).strip() if path_value else default_rel
        cand = Path(raw)
        if cand.exists():
            return cand
        cand2 = (PROJECT_ROOT / raw).resolve()
        if cand2.exists():
            return cand2
        if raw.startswith("../"):
            cand3 = (PROJECT_ROOT / raw.replace("../", "", 1)).resolve()
            if cand3.exists():
                return cand3
        return cand2

    def _load_symbol_payload_cache(self, path: Path, required_cols: set[str]) -> Dict[str, pd.DataFrame]:
        out: Dict[str, list[dict]] = {}
        if not path.exists():
            return {}
        with open(path, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                payload = obj.get("payload")
                sym_fallback = obj.get("symbol")
                if not isinstance(payload, list) or not payload:
                    continue
                for rec in payload:
                    if not isinstance(rec, dict):
                        continue
                    sym = rec.get("symbol") or sym_fallback
                    if not sym:
                        continue
                    keep = {k: rec.get(k) for k in required_cols}
                    keep["symbol"] = str(sym)
                    out.setdefault(str(sym), []).append(keep)
        built: Dict[str, pd.DataFrame] = {}
        for sym, rows in out.items():
            df = pd.DataFrame(rows)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.dropna(subset=["date"])
                df = df.sort_values("date").reset_index(drop=True)
            built[sym] = df
        return built

    def _load_institutional_summary(self) -> Dict[str, pd.DataFrame]:
        if self._institutional_summary_cache is None:
            p = self._resolve_data_path(
                self.config.get("INSTITUTIONAL_SUMMARY_PATH"),
                "data/fmp/institutional/institutional-ownership__symbol-positions-summary.jsonl",
            )
            self._institutional_summary_cache = self._load_symbol_payload_cache(
                p,
                {
                    "date",
                    "ownershipPercentChange",
                    "investorsHoldingChange",
                    "ownershipPercent",
                    "investorsHolding",
                },
            )
        return self._institutional_summary_cache

    def _load_owner_earnings(self) -> Dict[str, pd.DataFrame]:
        if self._owner_earnings_cache is None:
            p = self._resolve_data_path(
                self.config.get("OWNER_EARNINGS_PATH"),
                "data/fmp/owner_earnings/owner-earnings.jsonl",
            )
            self._owner_earnings_cache = self._load_symbol_payload_cache(
                p,
                {"date", "ownersEarningsPerShare", "ownersEarnings", "maintenanceCapex", "growthCapex"},
            )
        return self._owner_earnings_cache

    def _load_earnings_calendar(self) -> Dict[str, pd.DataFrame]:
        if self._earnings_calendar_cache is not None:
            return self._earnings_calendar_cache
        out: Dict[str, pd.DataFrame] = {}
        p = self._resolve_data_path(self.config.get("EARNINGS_CALENDAR_PATH"), "data/fmp/earnings/earnings_calendar.csv")
        if p.exists():
            try:
                df = pd.read_csv(p)
                if len(df) > 0 and "symbol" in df.columns and "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"], errors="coerce")
                    df = df.dropna(subset=["date"])
                    for sym, grp in df.groupby("symbol"):
                        out[str(sym)] = grp.sort_values("date").reset_index(drop=True)
            except Exception:
                out = {}
        self._earnings_calendar_cache = out
        return out

    def _load_symbol_data_cache(
        self,
        path: Path,
        required_cols: set[str],
        aliases: Optional[dict[str, list[str]]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Load symbol-level JSONL where each line uses the shape:
        {"symbol": "...", "ok": true, "data": [...]}
        """
        out: Dict[str, list[dict]] = {}
        if not path.exists():
            return {}
        aliases = aliases or {}
        with open(path, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                data = obj.get("data")
                sym_fallback = obj.get("symbol")
                if isinstance(data, dict):
                    data = [data]
                if not isinstance(data, list) or not data:
                    continue
                for rec in data:
                    if not isinstance(rec, dict):
                        continue
                    sym = rec.get("symbol") or sym_fallback
                    if not sym:
                        continue
                    keep: dict[str, object] = {"symbol": str(sym)}
                    for k in required_cols:
                        val = rec.get(k)
                        if val is None and k in aliases:
                            for ak in aliases[k]:
                                val = rec.get(ak)
                                if val is not None:
                                    break
                        keep[k] = val
                    out.setdefault(str(sym), []).append(keep)
        built: Dict[str, pd.DataFrame] = {}
        for sym, rows in out.items():
            df = pd.DataFrame(rows)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.dropna(subset=["date"])
                df = df.sort_values("date").reset_index(drop=True)
            built[sym] = df
        return built

    def _load_earnings_history(self) -> Dict[str, pd.DataFrame]:
        if self._earnings_history_cache is None:
            p = self._resolve_data_path(
                self.config.get("EARNINGS_HISTORY_PATH"),
                "data/fmp/earnings_history/earnings.jsonl",
            )
            self._earnings_history_cache = self._load_symbol_data_cache(
                p,
                {"date", "revenueActual", "revenueEstimated"},
                aliases={
                    "revenueActual": ["revenue", "revenueactual"],
                    "revenueEstimated": ["revenueEstimate", "revenueestimated"],
                },
            )
        return self._earnings_history_cache

    def calculate_momentum(self, symbol: str, date: str,
                           lookback: Optional[int] = None,
                           skip: Optional[int] = None) -> Optional[float]:
        if lookback is None:
            lookback = int(self.config.get('MOMENTUM_LOOKBACK', 120))
        if skip is None:
            skip = int(self.config.get('MOMENTUM_SKIP', 20))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=(lookback + skip) * 2)).strftime('%Y-%m-%d')
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < lookback + skip + 1:
            return None
        df = df.copy()
        df = df[df['date'] <= pd.Timestamp(date)]
        if len(df) < lookback + skip + 1:
            return None
        use_monthly = bool(self.config.get('MOMENTUM_USE_MONTHLY', False))
        fallback_daily = bool(self.config.get('MOMENTUM_FALLBACK_DAILY', True))

        def _daily_signal() -> Optional[float]:
            end_idx = -skip - 1
            start_idx = -skip - lookback - 1
            if abs(start_idx) > len(df) or abs(end_idx) > len(df):
                return None
            end_price = df.iloc[end_idx]['close']
            start_price = df.iloc[start_idx]['close']
            if end_price is None or start_price is None or start_price <= 0:
                return None
            return float(np.log(end_price / start_price))

        def _residual_daily_signal() -> Optional[float]:
            bench = self.config.get('MOMENTUM_BENCH_SYMBOL', 'SPY')
            est_window = int(self.config.get('MOMENTUM_RESID_EST_WINDOW', max(252, lookback + skip + 21)))
            start_days = max((lookback + skip + est_window) * 2, 252)
            rs = (pd.Timestamp(date) - pd.Timedelta(days=start_days)).strftime('%Y-%m-%d')
            mdf = self.data_engine.get_price(bench, start_date=rs, end_date=date)
            if mdf is None or len(mdf) < lookback + skip + est_window:
                return None
            mdf = mdf.copy()
            mdf['close'] = pd.to_numeric(mdf['close'], errors='coerce')
            mdf.loc[mdf['close'] <= 0, 'close'] = np.nan
            mdf['ret_m'] = np.log(mdf['close'] / mdf['close'].shift(1))

            sdf = df.copy()
            sdf['close'] = pd.to_numeric(sdf['close'], errors='coerce')
            sdf.loc[sdf['close'] <= 0, 'close'] = np.nan
            sdf['ret_s'] = np.log(sdf['close'] / sdf['close'].shift(1))

            merged = sdf[['date', 'ret_s']].merge(mdf[['date', 'ret_m']], on='date', how='inner').dropna()
            if len(merged) < lookback + skip + est_window:
                return None
            est = merged.tail(lookback + skip + est_window).head(est_window)
            frm = merged.tail(lookback + skip).head(lookback)
            if len(est) < 30 or len(frm) < max(lookback // 2, 20):
                return None
            var_m = est['ret_m'].var()
            if var_m is None or np.isnan(var_m) or var_m <= 0:
                return None
            beta = est['ret_s'].cov(est['ret_m']) / var_m
            if beta is None or np.isnan(beta):
                return None
            resid = frm['ret_s'] - float(beta) * frm['ret_m']
            return float(resid.sum())

        signal = None
        use_residual = bool(self.config.get('MOMENTUM_USE_RESIDUAL', False))
        if use_monthly:
            lookback_m = int(self.config.get('MOMENTUM_LOOKBACK_MONTHS', max(int(round(lookback / 21)), 1)))
            skip_m = int(self.config.get('MOMENTUM_SKIP_MONTHS', max(int(round(skip / 21)), 0)))

            monthly = df.set_index('date')['close'].resample('ME').last().dropna()
            if len(monthly) >= lookback_m + skip_m + 1:
                end_idx = -skip_m - 1
                start_idx = -skip_m - lookback_m - 1
                if abs(start_idx) <= len(monthly) and abs(end_idx) <= len(monthly):
                    end_price = monthly.iloc[end_idx]
                    start_price = monthly.iloc[start_idx]
                    if end_price is not None and start_price is not None and start_price > 0:
                        signal = float(np.log(end_price / start_price))

        if signal is None:
            if use_monthly and not fallback_daily:
                return None
            if use_residual:
                signal = _residual_daily_signal()
            if signal is None:
                signal = _daily_signal()
            if signal is None:
                return None

        vol_lookback = self.config.get('MOMENTUM_VOL_LOOKBACK')
        if vol_lookback:
            vol_lookback = int(vol_lookback)
            df['return'] = df['close'].pct_change(fill_method=None)
            vol = df.tail(vol_lookback)['return'].std()
            if vol and not np.isnan(vol) and vol > 0:
                signal = float(signal / vol)

        return float(signal)

    def calculate_residual_mom_12_1(self, symbol: str, date: str) -> Optional[float]:
        bak = self.config.get("MOMENTUM_USE_RESIDUAL")
        self.config["MOMENTUM_USE_RESIDUAL"] = True
        try:
            return self.calculate_momentum(symbol, date, lookback=252, skip=21)
        finally:
            if bak is None:
                self.config.pop("MOMENTUM_USE_RESIDUAL", None)
            else:
                self.config["MOMENTUM_USE_RESIDUAL"] = bak

    def calculate_idio_mom_vs_sector(self, symbol: str, date: str) -> Optional[float]:
        # Distinct proxy: long-minus-medium plain momentum spread.
        bak = self.config.get("MOMENTUM_USE_RESIDUAL")
        self.config["MOMENTUM_USE_RESIDUAL"] = False
        try:
            long_mom = self.calculate_momentum(symbol, date, lookback=252, skip=21)
            med_mom = self.calculate_momentum(symbol, date, lookback=126, skip=21)
        finally:
            if bak is None:
                self.config.pop("MOMENTUM_USE_RESIDUAL", None)
            else:
                self.config["MOMENTUM_USE_RESIDUAL"] = bak
        if long_mom is not None and pd.isna(long_mom):
            long_mom = None
        if med_mom is not None and pd.isna(med_mom):
            med_mom = None
        if long_mom is None and med_mom is None:
            return None
        if long_mom is None:
            return float(-med_mom)
        if med_mom is None:
            return float(long_mom)
        return float(float(long_mom) - float(med_mom))

    def calculate_reversal(self, symbol: str, date: str,
                           lookback: Optional[int] = None) -> Optional[float]:
        if lookback is None:
            lookback = int(self.config.get('REVERSAL_LOOKBACK', 5))
        # Optional earnings-day filter
        filter_days = self.config.get('REVERSAL_EARNINGS_FILTER_DAYS')
        if filter_days is not None:
            if self._has_earnings_near_date(symbol, date, int(filter_days)):
                return None

        mode = self.config.get('REVERSAL_MODE', 'multi_day')
        vol_lookback = self.config.get('REVERSAL_VOL_LOOKBACK')
        vol_lookback = int(vol_lookback) if vol_lookback else None

        max_gap = self.config.get('REVERSAL_MAX_GAP_PCT')
        min_dollar_vol = self.config.get('REVERSAL_MIN_DOLLAR_VOL')

        if mode == 'intraday':
            start_days = max(lookback * 3, (vol_lookback or 0) * 2, 30)
            start_date = (pd.Timestamp(date) - pd.Timedelta(days=start_days)).strftime('%Y-%m-%d')
            df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
            if df is None or len(df) == 0:
                return None
            df = df.copy()
            df = df[df['date'] <= pd.Timestamp(date)]
            if len(df) == 0:
                return None
            if 'open' not in df.columns or 'close' not in df.columns:
                return None
            intraday = df[['open', 'close']].copy()
            intraday['open'] = pd.to_numeric(intraday['open'], errors='coerce')
            intraday['close'] = pd.to_numeric(intraday['close'], errors='coerce')
            intraday = intraday.dropna(subset=['open', 'close'])
            intraday = intraday[intraday['open'] > 0]
            if len(intraday) < lookback:
                return None
            if max_gap is not None:
                prev_close = intraday['close'].shift(1)
                gap = (intraday['open'] / prev_close - 1.0).abs()
                if gap.tail(lookback).max(skipna=True) > float(max_gap):
                    return None
            intraday_ret = (intraday['close'] / intraday['open']) - 1.0
            signal = float(-intraday_ret.tail(lookback).mean())
        else:
            start_date = (pd.Timestamp(date) - pd.Timedelta(days=lookback * 3)).strftime('%Y-%m-%d')
            df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
            if df is None or len(df) < lookback:
                return None
            df = df.copy()
            df['return'] = df['close'].pct_change()
            if max_gap is not None and 'open' in df.columns:
                op = pd.to_numeric(df['open'], errors='coerce')
                prev_close = pd.to_numeric(df['close'], errors='coerce').shift(1)
                gap = (op / prev_close - 1.0).abs()
                if gap.tail(lookback).max(skipna=True) > float(max_gap):
                    return None
            recent_return = df.tail(lookback)['return'].sum()
            signal = float(-recent_return)

        if min_dollar_vol is not None and df is not None and 'volume' in df.columns:
            px = pd.to_numeric(df.get('close'), errors='coerce')
            vol = pd.to_numeric(df.get('volume'), errors='coerce')
            adv = (px * vol).tail(max(lookback, 20)).mean()
            if adv is None or np.isnan(adv) or adv < float(min_dollar_vol):
                return None

        if vol_lookback and df is not None and len(df) >= vol_lookback:
            if 'return' not in df.columns:
                df = df.copy()
                df['return'] = df['close'].pct_change(fill_method=None)
            vol = df.tail(vol_lookback)['return'].std()
            if vol and not np.isnan(vol) and vol > 0:
                signal = float(signal / vol)

        return float(signal)

    def calculate_extreme_reversal_ex_earnings(self, symbol: str, date: str) -> Optional[float]:
        ret1 = self.calculate_reversal(symbol, date, lookback=1)
        if ret1 is None or pd.isna(ret1):
            return None
        if self._has_earnings_near_date(symbol, date, days=2):
            return None
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=126 * 3)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < 60:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work.loc[work["close"] <= 0, "close"] = np.nan
        r = np.log(work["close"] / work["close"].shift(1)).dropna().tail(126)
        if len(r) < 60:
            return None
        thr = float(r.abs().quantile(0.95))
        return float(ret1 if abs(float(r.iloc[-1])) >= thr else 0.0)

    def calculate_intraday_reversion_proxy(self, symbol: str, date: str) -> Optional[float]:
        window = int(self.config.get("INTRADAY_REV_WINDOW", 10))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window:
            return None
        work = df.copy()
        work["open"] = pd.to_numeric(work["open"], errors="coerce")
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work = work[(work["open"] > 0) & (work["close"] > 0)].dropna(subset=["open", "close"])
        if len(work) < window:
            return None
        intraday = ((work["close"] - work["open"]) / work["open"]).tail(window)
        return float(-intraday.sum())

    def calculate_range_followthrough(self, symbol: str, date: str) -> Optional[float]:
        window = int(self.config.get("RANGE_FOLLOW_WINDOW", 20))
        ret_w = int(self.config.get("RANGE_FOLLOW_RET_WINDOW", 5))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=max(window, ret_w) * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < max(window, ret_w) + 1:
            return None
        work = df.copy()
        for c in ("high", "low", "close"):
            work[c] = pd.to_numeric(work[c], errors="coerce")
        work = work.dropna(subset=["high", "low", "close"])
        work = work[(work["close"] > 0) & (work["high"] > 0) & (work["low"] > 0)]
        if len(work) < max(window, ret_w) + 1:
            return None
        range_pct = ((work["high"] - work["low"]) / work["close"]).tail(window)
        rp_std = float(range_pct.std(ddof=1))
        if not np.isfinite(rp_std) or rp_std <= 0:
            return None
        rp_z = (float(range_pct.iloc[-1]) - float(range_pct.mean())) / rp_std
        ret5 = np.log(work["close"] / work["close"].shift(ret_w)).iloc[-1]
        if pd.isna(ret5):
            return None
        return float(rp_z * np.sign(float(ret5)))

    def calculate_st_reversal_liquidity_filtered(self, symbol: str, date: str) -> Optional[float]:
        bak = self.config.get("REVERSAL_MIN_DOLLAR_VOL")
        self.config["REVERSAL_MIN_DOLLAR_VOL"] = float(self.config.get("ST_REV_MIN_DOLLAR_VOL", 2e6))
        try:
            return self.calculate_reversal(symbol, date, lookback=5)
        finally:
            if bak is None:
                self.config.pop("REVERSAL_MIN_DOLLAR_VOL", None)
            else:
                self.config["REVERSAL_MIN_DOLLAR_VOL"] = bak

    def calculate_post_spike_cooldown(self, symbol: str, date: str) -> Optional[float]:
        vol_w = int(self.config.get("POST_SPIKE_VOL_WINDOW", 20))
        z_thr = float(self.config.get("POST_SPIKE_VOL_Z", 2.0))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=vol_w * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < vol_w + 2:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work["volume"] = pd.to_numeric(work["volume"], errors="coerce")
        work = work[(work["close"] > 0) & (work["volume"] >= 0)].dropna(subset=["close", "volume"])
        if len(work) < vol_w + 2:
            return None
        vol = work["volume"].tail(vol_w)
        std = float(vol.std(ddof=1))
        if not np.isfinite(std) or std <= 0:
            return None
        vz = (float(vol.iloc[-1]) - float(vol.mean())) / std
        ret1 = np.log(work["close"] / work["close"].shift(1)).iloc[-1]
        if pd.isna(ret1):
            return None
        return float(-ret1 if vz > z_thr else 0.0)

    def calculate_overreaction_volume_adjusted(self, symbol: str, date: str) -> Optional[float]:
        ret_w = int(self.config.get("OVERREACT_RET_WINDOW", 3))
        vol_w = int(self.config.get("OVERREACT_VOL_WINDOW", 20))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=max(ret_w, vol_w) * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < max(ret_w, vol_w) + 1:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work["volume"] = pd.to_numeric(work["volume"], errors="coerce")
        work = work[(work["close"] > 0) & (work["volume"] >= 0)].dropna(subset=["close", "volume"])
        if len(work) < max(ret_w, vol_w) + 1:
            return None
        ret = np.log(work["close"] / work["close"].shift(ret_w)).iloc[-1]
        vol = work["volume"].tail(vol_w)
        std = float(vol.std(ddof=1))
        if not np.isfinite(std) or std <= 0 or pd.isna(ret):
            return None
        vz = (float(vol.iloc[-1]) - float(vol.mean())) / std
        return float(-float(ret) / (1.0 + max(0.0, vz)))

    def calculate_failed_breakout_reversal(self, symbol: str, date: str) -> Optional[float]:
        window = int(self.config.get("FAILED_BREAKOUT_WINDOW", 20))
        atr_w = int(self.config.get("FAILED_BREAKOUT_ATR_WINDOW", 20))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=max(window, atr_w) * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < max(window, atr_w) + 1:
            return None
        work = df.copy()
        for c in ("high", "low", "close"):
            work[c] = pd.to_numeric(work[c], errors="coerce")
        work = work.dropna(subset=["high", "low", "close"])
        work = work[(work["close"] > 0) & (work["high"] > 0) & (work["low"] > 0)]
        if len(work) < max(window, atr_w) + 1:
            return None
        prev_high = float(work["high"].tail(window + 1).iloc[:-1].max())
        close_now = float(work["close"].iloc[-1])
        if close_now >= prev_high:
            return 0.0
        tr = pd.concat(
            [
                (work["high"] - work["low"]).abs(),
                (work["high"] - work["close"].shift(1)).abs(),
                (work["low"] - work["close"].shift(1)).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr = float(tr.tail(atr_w).mean())
        if not np.isfinite(atr) or atr <= 0:
            return None
        return float(-(close_now - prev_high) / atr)

    def calculate_compression_reversal(self, symbol: str, date: str) -> Optional[float]:
        short_w = int(self.config.get("COMPRESSION_SHORT_WINDOW", 20))
        long_w = int(self.config.get("COMPRESSION_LONG_WINDOW", 120))
        rev_w = int(self.config.get("COMPRESSION_REV_WINDOW", 5))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=max(short_w, long_w, rev_w) * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < long_w + 1:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work.loc[work["close"] <= 0, "close"] = np.nan
        r = np.log(work["close"] / work["close"].shift(1)).dropna()
        if len(r) < long_w:
            return None
        vol_short = float(r.tail(short_w).std(ddof=1))
        vol_long = float(r.tail(long_w).std(ddof=1))
        if not np.isfinite(vol_short) or not np.isfinite(vol_long) or vol_long <= 0:
            return None
        if vol_short >= vol_long:
            return 0.0
        rev = float(-r.tail(rev_w).sum())
        return float(rev)

    def calculate_skew_reversal(self, symbol: str, date: str) -> Optional[float]:
        skew_w = int(self.config.get("SKEW_REV_SKEW_WINDOW", 20))
        rev_w = int(self.config.get("SKEW_REV_RET_WINDOW", 2))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=max(skew_w, rev_w) * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < skew_w + 1:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work.loc[work["close"] <= 0, "close"] = np.nan
        r = np.log(work["close"] / work["close"].shift(1)).dropna()
        if len(r) < skew_w:
            return None
        skew = float(r.tail(skew_w).skew())
        if not np.isfinite(skew):
            return None
        rev = float(-r.tail(rev_w).sum())
        return float(rev if skew < 0 else 0.0)

    def calculate_three_red_days_rebound(self, symbol: str, date: str) -> Optional[float]:
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=30)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < 6:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work.loc[work["close"] <= 0, "close"] = np.nan
        r = np.log(work["close"] / work["close"].shift(1)).dropna()
        if len(r) < 5:
            return None
        last3 = r.tail(3)
        if (last3 < 0).all():
            return float(abs(last3.sum()))
        return 0.0

    def calculate_large_gap_reversal(self, symbol: str, date: str) -> Optional[float]:
        window = int(self.config.get("LARGE_GAP_WINDOW", 60))
        q = float(self.config.get("LARGE_GAP_Q", 0.9))
        q = min(max(q, 0.5), 0.99)
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window + 1:
            return None
        work = df.copy()
        work["open"] = pd.to_numeric(work["open"], errors="coerce")
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work = work[(work["open"] > 0) & (work["close"] > 0)].dropna(subset=["open", "close"])
        if len(work) < window + 1:
            return None
        gap = np.log(work["open"] / work["close"].shift(1)).dropna().tail(window)
        if len(gap) < window:
            return None
        thr = float(gap.abs().quantile(q))
        g = float(gap.iloc[-1])
        return float(-g if abs(g) > thr else 0.0)

    def calculate_flow_autocorr_20(self, symbol: str, date: str) -> Optional[float]:
        window = int(self.config.get("FLOW_AUTOCORR_WINDOW", 20))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 8)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window + 2:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work["volume"] = pd.to_numeric(work["volume"], errors="coerce")
        work = work[(work["close"] > 0) & (work["volume"] >= 0)].dropna(subset=["close", "volume"])
        if len(work) < window + 2:
            return None
        ret = np.log(work["close"] / work["close"].shift(1))
        flow = (ret * work["volume"]).dropna().tail(window + 1)
        if len(flow) < window + 1:
            return None
        return float(flow.autocorr(lag=1))

    def calculate_spread_proxy_stability(self, symbol: str, date: str) -> Optional[float]:
        window = int(self.config.get("SPREAD_STABILITY_WINDOW", 60))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window:
            return None
        work = df.copy()
        for c in ("high", "low", "close"):
            work[c] = pd.to_numeric(work[c], errors="coerce")
        work = work[(work["high"] > 0) & (work["low"] > 0) & (work["close"] > 0)].dropna(subset=["high", "low", "close"])
        if len(work) < window:
            return None
        sp = ((work["high"] - work["low"]) / work["close"]).tail(window)
        v = float(sp.std(ddof=1))
        if not np.isfinite(v):
            return None
        return float(-v)

    def calculate_vol_of_vol_126(self, symbol: str, date: str) -> Optional[float]:
        short_w = int(self.config.get("VOL_OF_VOL_SHORT", 20))
        long_w = int(self.config.get("VOL_OF_VOL_LONG", 126))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=long_w * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < long_w + short_w:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work.loc[work["close"] <= 0, "close"] = np.nan
        r = np.log(work["close"] / work["close"].shift(1)).dropna()
        if len(r) < long_w + short_w:
            return None
        rv = r.rolling(short_w).std(ddof=1).dropna().tail(long_w)
        if len(rv) < long_w:
            return None
        vv = float(rv.std(ddof=1))
        if not np.isfinite(vv):
            return None
        return float(-vv)

    def calculate_jump_risk_proxy(self, symbol: str, date: str) -> Optional[float]:
        window = int(self.config.get("JUMP_RISK_WINDOW", 126))
        z_thr = float(self.config.get("JUMP_RISK_Z", 2.0))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window + 1:
            return None
        work = df.copy()
        work["open"] = pd.to_numeric(work["open"], errors="coerce")
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work = work[(work["open"] > 0) & (work["close"] > 0)].dropna(subset=["open", "close"])
        if len(work) < window + 1:
            return None
        gap = np.log(work["open"] / work["close"].shift(1)).dropna().tail(window)
        if len(gap) < window:
            return None
        std = float(gap.std(ddof=1))
        if not np.isfinite(std) or std <= 0:
            return None
        cnt = int((gap.abs() > (z_thr * std)).sum())
        return float(-cnt)

    def calculate_trend_regime_switch(self, symbol: str, date: str) -> Optional[float]:
        mom = self.calculate_momentum(symbol, date)
        if mom is None or pd.isna(mom):
            return None
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=800)).strftime("%Y-%m-%d")
        mkt = self.data_engine.get_price("SPY", start_date=start_date, end_date=date)
        if mkt is None or len(mkt) < 200:
            return None
        m = mkt.copy()
        m["close"] = pd.to_numeric(m["close"], errors="coerce")
        m = m[m["close"] > 0].dropna(subset=["close"])
        if len(m) < 200:
            return None
        ma50 = float(m["close"].rolling(50).mean().iloc[-1])
        ma200 = float(m["close"].rolling(200).mean().iloc[-1])
        if not np.isfinite(ma50) or not np.isfinite(ma200):
            return None
        return float(mom if ma50 > ma200 else -mom)

    def calculate_vol_regime_switch(self, symbol: str, date: str) -> Optional[float]:
        lv = self.calculate_low_volatility(symbol, date, window=60)
        vr = self.calculate_vol_regime(symbol, date)
        if lv is None or vr is None or pd.isna(lv) or pd.isna(vr):
            return None
        gate = 1.0 if float(vr) > 0 else -1.0
        return float(float(lv) * gate)

    def calculate_liquidity_regime_switch(self, symbol: str, date: str) -> Optional[float]:
        val = self.calculate_value(symbol, date)
        ts = self.calculate_turnover_shock(symbol, date)
        if val is None or ts is None or pd.isna(val) or pd.isna(ts):
            return None
        gate = 1.0 if float(ts) < 0 else -1.0
        return float(float(val) * gate)

    def calculate_earnings_season_alpha(self, symbol: str, date: str) -> Optional[float]:
        d = pd.Timestamp(date)
        in_season = 1.0 if d.month in (1, 2, 4, 5, 7, 8, 10, 11) else 0.0
        sue = self.calculate_sue_eps_basic(symbol, date)
        if sue is None or pd.isna(sue):
            return None
        return float(float(sue) * in_season)

    def calculate_state_weighted_meta_signal(self, symbol: str, date: str) -> Optional[float]:
        v = self.calculate_value(symbol, date)
        q = self.calculate_quality(symbol, date)
        e = self.calculate_sue_eps_basic(symbol, date)
        vr = self.calculate_vol_regime(symbol, date)
        if any(x is None or pd.isna(x) for x in (v, q, e, vr)):
            return None
        # high calm-regime -> emphasize value/quality; turbulent -> emphasize event
        calm = min(max(float(vr), -1.0), 1.0)
        w_v = 0.4 + 0.2 * max(calm, 0.0)
        w_q = 0.4 + 0.2 * max(calm, 0.0)
        w_e = 0.2 + 0.4 * max(-calm, 0.0)
        denom = w_v + w_q + w_e
        return float((w_v * float(v) + w_q * float(q) + w_e * float(e)) / denom)

    def _compress_component(self, value: float) -> float:
        # Signed log compression to reduce metric scale dominance.
        return float(np.sign(value) * np.log1p(abs(value)))

    def _transform_component(self, value: float, mode: str) -> float:
        m = str(mode or "signed_log").lower()
        if m in ("signed_log", "log1p_signed"):
            return self._compress_component(value)
        if m in ("identity", "raw", "none"):
            return float(value)
        return self._compress_component(value)

    def _zscore_series(self, s: pd.Series) -> pd.Series:
        std = s.std(ddof=0)
        if std is None or np.isnan(std) or std <= 0:
            return pd.Series(np.nan, index=s.index, dtype=float)
        return (s - s.mean()) / std

    def _winsorize_series_pct(self, s: pd.Series, low: Optional[float], high: Optional[float]) -> pd.Series:
        if low is None or high is None:
            return s
        try:
            low_q = float(low)
            high_q = float(high)
        except Exception:
            return s
        if np.isnan(low_q) or np.isnan(high_q) or low_q <= 0 or high_q >= 1 or low_q >= high_q:
            return s
        lo = s.quantile(low_q)
        hi = s.quantile(high_q)
        return s.clip(lower=lo, upper=hi)

    def _zscore_by_group(
        self,
        s: pd.Series,
        symbols: pd.Series,
        min_group: int,
    ) -> pd.Series:
        if not self.industry_map:
            return self._zscore_series(s)
        groups = symbols.map(self.industry_map)
        z = pd.Series(np.nan, index=s.index, dtype=float)
        grouped = pd.DataFrame({"v": s, "g": groups}).dropna(subset=["g"])
        for g, grp in grouped.groupby("g"):
            if len(grp) < int(min_group):
                continue
            z.loc[grp.index] = self._zscore_series(grp["v"])
        miss = z.isna()
        if miss.any():
            z.loc[miss] = self._zscore_series(s.loc[miss])
        return z

    def _build_mainstream_composite_signal(
        self,
        universe: Iterable[str],
        signal_date: str,
        factor_date: str,
        weights: Dict[str, float],
        kind: str,
    ) -> pd.DataFrame:
        rows = []
        if kind == "quality":
            engine = self.fundamentals_engine
        elif kind == "value":
            engine = self.value_engine
        else:
            engine = None

        if engine is None or not weights:
            return pd.DataFrame(columns=["symbol", "date", "signal", kind])

        prefix = "QUALITY" if kind == "quality" else "VALUE"
        use_industry_z = bool(self.config.get(f"{prefix}_COMPONENT_INDUSTRY_ZSCORE", False))
        winsor_low = self.config.get(f"{prefix}_COMPONENT_WINSOR_PCT_LOW")
        winsor_high = self.config.get(f"{prefix}_COMPONENT_WINSOR_PCT_HIGH")
        min_count = int(self.config.get(f"{prefix}_COMPONENT_MIN_COUNT", 1) or 1)
        missing_policy = str(self.config.get(f"{prefix}_COMPONENT_MISSING_POLICY", "drop")).lower()
        min_group = int(self.config.get("INDUSTRY_MIN_GROUP", 3))

        keys = list(weights.keys())
        for sym in universe:
            metrics = engine.get_latest_metrics(sym, factor_date)
            if not metrics:
                continue
            row = {"symbol": sym}
            has_any = False
            for k in keys:
                v = metrics.get(k)
                if v is None or pd.isna(v):
                    row[k] = np.nan
                    continue
                row[k] = float(v)
                has_any = True
            if has_any:
                rows.append(row)

        if not rows:
            return pd.DataFrame(columns=["symbol", "date", "signal", kind])

        df = pd.DataFrame(rows)
        score = pd.Series(0.0, index=df.index, dtype=float)
        wsum = pd.Series(0.0, index=df.index, dtype=float)
        comp_count = pd.Series(0, index=df.index, dtype=int)

        for k, w in weights.items():
            if k not in df.columns:
                continue
            x = pd.to_numeric(df[k], errors="coerce")
            x = self._winsorize_series_pct(x, winsor_low, winsor_high)
            if use_industry_z:
                z = self._zscore_by_group(x, df["symbol"], min_group=min_group)
            else:
                z = self._zscore_series(x)
            raw_valid = z.notna()
            comp_count.loc[raw_valid] += 1
            if missing_policy == "fill_zero":
                z = z.fillna(0.0)
            elif missing_policy == "fill_median":
                med = z.median(skipna=True)
                if med is not None and not np.isnan(med):
                    z = z.fillna(float(med))
            wf = float(w)
            valid = z.notna()
            score.loc[valid] += wf * z.loc[valid]
            wsum.loc[valid] += abs(wf)

        df["signal"] = np.where(wsum > 0, score / wsum, np.nan)
        df.loc[comp_count < min_count, "signal"] = np.nan
        df["date"] = signal_date
        df[kind] = df["signal"]
        out = df[["symbol", "date", "signal", kind]].dropna(subset=["signal"]).reset_index(drop=True)
        return out

    def _has_earnings_near_date(self, symbol: str, date: str, days: int) -> bool:
        if symbol not in self._earnings_date_cache:
            if not self.pead_factor:
                self._earnings_date_cache[symbol] = set()
            else:
                earnings = self.pead_factor.get_earnings(symbol)
                if earnings is None or len(earnings) == 0:
                    self._earnings_date_cache[symbol] = set()
                else:
                    dates = pd.to_datetime(earnings['date']).dt.normalize()
                    self._earnings_date_cache[symbol] = set(dates.tolist())
        d = pd.Timestamp(date).normalize()
        for i in range(-days, days + 1):
            if (d + pd.Timedelta(days=i)) in self._earnings_date_cache[symbol]:
                return True
        return False

    def calculate_low_volatility(self, symbol: str, date: str,
                                 window: int = 60) -> Optional[float]:
        if self.config.get('LOW_VOL_WINDOW') is not None:
            try:
                window = int(self.config.get('LOW_VOL_WINDOW'))
            except Exception:
                window = window
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 2)).strftime('%Y-%m-%d')
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window:
            return None
        df = df.copy()
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        use_log = bool(self.config.get('LOW_VOL_LOG_RETURN', True))
        if use_log:
            df.loc[df['close'] <= 0, 'close'] = np.nan
            df['return'] = np.log(df['close'] / df['close'].shift(1))
        else:
            df['return'] = df['close'].pct_change()
        use_residual = bool(self.config.get('LOW_VOL_USE_RESIDUAL', False))
        downside_only = bool(self.config.get('LOW_VOL_DOWNSIDE_ONLY', False))
        if use_residual:
            bench = self.config.get('LOW_VOL_BENCH_SYMBOL', 'SPY')
            mdf = self.data_engine.get_price(bench, start_date=start_date, end_date=date)
            if mdf is None or len(mdf) < window:
                return None
            mdf = mdf.copy()
            mdf['close'] = pd.to_numeric(mdf['close'], errors='coerce')
            if use_log:
                mdf.loc[mdf['close'] <= 0, 'close'] = np.nan
                mdf['return'] = np.log(mdf['close'] / mdf['close'].shift(1))
            else:
                mdf['return'] = mdf['close'].pct_change()
            merged = df[['date', 'return']].merge(
                mdf[['date', 'return']],
                on='date',
                how='inner',
                suffixes=('', '_m')
            )
            if len(merged) < window:
                return None
            merged = merged.tail(window)
            r = merged['return']
            rm = merged['return_m']
            var_m = rm.var()
            if var_m is None or np.isnan(var_m) or var_m <= 0:
                return None
            beta = r.cov(rm) / var_m
            resid = r - beta * rm
            if downside_only:
                resid = resid.where(resid < 0, 0.0)
            volatility = resid.std()
        else:
            r = df.tail(window)['return']
            if downside_only:
                r = r.where(r < 0, 0.0)
            volatility = r.std()
        if volatility is None or np.isnan(volatility):
            return None
        return float(-volatility)

    def calculate_beta(self, symbol: str, date: str,
                       window: int = 252) -> Optional[float]:
        if self.config.get('BETA_LOOKBACK') is not None:
            try:
                window = int(self.config.get('BETA_LOOKBACK'))
            except Exception:
                window = window
        bench = self.config.get('BETA_BENCH_SYMBOL', 'SPY')
        use_log = bool(self.config.get('BETA_USE_LOG_RETURN', True))

        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 3)).strftime('%Y-%m-%d')
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        mdf = self.data_engine.get_price(bench, start_date=start_date, end_date=date)
        if df is None or mdf is None or len(df) < window or len(mdf) < window:
            return None

        df = df.copy()
        mdf = mdf.copy()
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        mdf['close'] = pd.to_numeric(mdf['close'], errors='coerce')
        if use_log:
            df.loc[df['close'] <= 0, 'close'] = np.nan
            mdf.loc[mdf['close'] <= 0, 'close'] = np.nan
            df['return'] = np.log(df['close'] / df['close'].shift(1))
            mdf['return'] = np.log(mdf['close'] / mdf['close'].shift(1))
        else:
            df['return'] = df['close'].pct_change()
            mdf['return'] = mdf['close'].pct_change()

        merged = df[['date', 'return']].merge(
            mdf[['date', 'return']],
            on='date',
            how='inner',
            suffixes=('', '_m')
        )
        if len(merged) < window:
            return None
        merged = merged.tail(window)
        r = merged['return']
        rm = merged['return_m']
        var_m = rm.var()
        if var_m is None or np.isnan(var_m) or var_m <= 0:
            return None
        beta = r.cov(rm) / var_m
        if beta is None or np.isnan(beta):
            return None
        return float(beta)

    def calculate_idiosyncratic_vol_63(self, symbol: str, date: str) -> Optional[float]:
        window = int(self.config.get("IDIO_VOL_WINDOW", 63))
        bench = self.config.get("BETA_BENCH_SYMBOL", "SPY")
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 6)).strftime("%Y-%m-%d")
        s = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        m = self.data_engine.get_price(bench, start_date=start_date, end_date=date)
        if s is None or m is None or len(s) < window + 1 or len(m) < window + 1:
            return None
        sdf = s.copy()
        mdf = m.copy()
        for df in (sdf, mdf):
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            df.loc[df["close"] <= 0, "close"] = np.nan
        sdf["ret_s"] = np.log(sdf["close"] / sdf["close"].shift(1))
        mdf["ret_m"] = np.log(mdf["close"] / mdf["close"].shift(1))
        merged = sdf[["date", "ret_s"]].merge(mdf[["date", "ret_m"]], on="date", how="inner").dropna().tail(window)
        if len(merged) < window:
            return None
        var_m = float(merged["ret_m"].var())
        if not np.isfinite(var_m) or var_m <= 0:
            return None
        beta = float(merged["ret_s"].cov(merged["ret_m"]) / var_m)
        resid = merged["ret_s"] - beta * merged["ret_m"]
        v = float(resid.std(ddof=1))
        if not np.isfinite(v):
            return None
        return float(-v)

    def calculate_beta_instability_126(self, symbol: str, date: str) -> Optional[float]:
        long_w = int(self.config.get("BETA_INSTAB_WINDOW", 126))
        roll_w = int(self.config.get("BETA_INSTAB_ROLL", 63))
        bench = self.config.get("BETA_BENCH_SYMBOL", "SPY")
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=(long_w + roll_w) * 6)).strftime("%Y-%m-%d")
        s = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        m = self.data_engine.get_price(bench, start_date=start_date, end_date=date)
        if s is None or m is None:
            return None
        sdf = s.copy()
        mdf = m.copy()
        for df in (sdf, mdf):
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            df.loc[df["close"] <= 0, "close"] = np.nan
        sdf["ret_s"] = np.log(sdf["close"] / sdf["close"].shift(1))
        mdf["ret_m"] = np.log(mdf["close"] / mdf["close"].shift(1))
        merged = sdf[["date", "ret_s"]].merge(mdf[["date", "ret_m"]], on="date", how="inner").dropna().tail(long_w + roll_w + 5)
        if len(merged) < long_w + roll_w:
            return None
        betas = []
        r = merged.reset_index(drop=True)
        for i in range(roll_w, len(r) + 1):
            w = r.iloc[i - roll_w:i]
            var_m = float(w["ret_m"].var())
            if not np.isfinite(var_m) or var_m <= 0:
                continue
            betas.append(float(w["ret_s"].cov(w["ret_m"]) / var_m))
        if len(betas) < 10:
            return None
        bstd = float(np.std(betas, ddof=1))
        if not np.isfinite(bstd):
            return None
        return float(-bstd)

    def calculate_downside_beta_crash(self, symbol: str, date: str) -> Optional[float]:
        window = int(self.config.get("DOWNSIDE_BETA_WINDOW", 252))
        bench = self.config.get("BETA_BENCH_SYMBOL", "SPY")
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 6)).strftime("%Y-%m-%d")
        s = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        m = self.data_engine.get_price(bench, start_date=start_date, end_date=date)
        if s is None or m is None:
            return None
        sdf = s.copy()
        mdf = m.copy()
        for df in (sdf, mdf):
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            df.loc[df["close"] <= 0, "close"] = np.nan
        sdf["ret_s"] = np.log(sdf["close"] / sdf["close"].shift(1))
        mdf["ret_m"] = np.log(mdf["close"] / mdf["close"].shift(1))
        merged = sdf[["date", "ret_s"]].merge(mdf[["date", "ret_m"]], on="date", how="inner").dropna().tail(window)
        if len(merged) < 60:
            return None
        q = float(merged["ret_m"].quantile(0.2))
        crash = merged[merged["ret_m"] <= q]
        if len(crash) < 20:
            return None
        var_m = float(crash["ret_m"].var())
        if not np.isfinite(var_m) or var_m <= 0:
            return None
        beta = float(crash["ret_s"].cov(crash["ret_m"]) / var_m)
        if not np.isfinite(beta):
            return None
        return float(-beta)

    def calculate_pead(self, symbol: str, date: str) -> Optional[float]:
        if not self.pead_factor:
            return None
        return self.pead_factor.get_sue_signal(symbol, date)

    def calculate_size(self, symbol: str, date: str) -> Optional[float]:
        mc_engine = getattr(self.universe_builder, "market_cap_engine", None)
        if mc_engine is None:
            return None
        return mc_engine.get_market_cap(symbol, date)

    def calculate_quality(self, symbol: str, date: str) -> Optional[float]:
        if not self.fundamentals_engine:
            return None
        metrics = self.fundamentals_engine.get_latest_metrics(symbol, date)
        if not metrics:
            return None
        weights = self.config.get('QUALITY_WEIGHTS') or {}
        min_count = int(self.config.get("QUALITY_COMPONENT_MIN_COUNT", 1) or 1)
        score = 0.0
        wsum = 0.0
        valid_count = 0
        transform_mode = self.config.get("QUALITY_COMPONENT_TRANSFORM", "signed_log")
        for k, w in weights.items():
            v = metrics.get(k)
            if v is None or pd.isna(v):
                continue
            wf = float(w)
            vf = self._transform_component(float(v), transform_mode)
            score += wf * vf
            wsum += abs(wf)
            valid_count += 1
        if valid_count < min_count:
            return None
        if wsum <= 0:
            return None
        return float(score / wsum)

    def calculate_value(self, symbol: str, date: str) -> Optional[float]:
        if not self.value_engine:
            return None
        metrics = self.value_engine.get_latest_metrics(symbol, date)
        if not metrics:
            return None
        weights = self.config.get('VALUE_WEIGHTS') or {}
        min_count = int(self.config.get("VALUE_COMPONENT_MIN_COUNT", 1) or 1)
        score = 0.0
        wsum = 0.0
        valid_count = 0
        transform_mode = self.config.get("VALUE_COMPONENT_TRANSFORM", "signed_log")
        for k, w in weights.items():
            v = metrics.get(k)
            if v is None or pd.isna(v):
                continue
            wf = float(w)
            vf = self._transform_component(float(v), transform_mode)
            score += wf * vf
            wsum += abs(wf)
            valid_count += 1
        if valid_count < min_count:
            return None
        if wsum <= 0:
            return None
        return float(score / wsum)

    def calculate_turnover_shock(self, symbol: str, date: str) -> Optional[float]:
        """
        Liquidity regime proxy:
        log(ADV_short / ADV_long), where ADV is close * volume.
        Positive means recent turnover is stronger than long-run baseline.
        """
        short_w = int(self.config.get("TURNOVER_SHOCK_SHORT", 20))
        long_w = int(self.config.get("TURNOVER_SHOCK_LONG", 120))
        min_obs = int(self.config.get("TURNOVER_SHOCK_MIN_OBS", max(long_w, 60)))
        if short_w <= 1 or long_w <= short_w:
            return None

        start_date = (pd.Timestamp(date) - pd.Timedelta(days=long_w * 4)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < min_obs:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work["volume"] = pd.to_numeric(work["volume"], errors="coerce")
        work = work.dropna(subset=["close", "volume"])
        work = work[(work["close"] > 0) & (work["volume"] >= 0)]
        if len(work) < min_obs:
            return None
        work["dollar_vol"] = work["close"] * work["volume"]
        hist = work["dollar_vol"].tail(long_w)
        if len(hist) < long_w:
            return None
        adv_short = float(hist.tail(short_w).mean())
        adv_long = float(hist.mean())
        if adv_short <= 0 or adv_long <= 0:
            return None
        return float(np.log(adv_short / adv_long))

    def calculate_vol_regime(self, symbol: str, date: str) -> Optional[float]:
        """
        Volatility regime score:
        (vol_long - vol_short) / vol_long.
        Positive means short-term vol is below long-run vol.
        """
        short_w = int(self.config.get("VOL_REGIME_SHORT", 20))
        long_w = int(self.config.get("VOL_REGIME_LONG", 120))
        min_obs = int(self.config.get("VOL_REGIME_MIN_OBS", max(long_w, 60)))
        if short_w <= 1 or long_w <= short_w:
            return None

        start_date = (pd.Timestamp(date) - pd.Timedelta(days=long_w * 4)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < min_obs:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work.loc[work["close"] <= 0, "close"] = np.nan
        work["ret"] = np.log(work["close"] / work["close"].shift(1))
        r = work["ret"].dropna()
        if len(r) < min_obs:
            return None
        long_r = r.tail(long_w)
        if len(long_r) < long_w:
            return None
        short_r = long_r.tail(short_w)
        vol_short = float(short_r.std(ddof=1))
        vol_long = float(long_r.std(ddof=1))
        if not np.isfinite(vol_short) or not np.isfinite(vol_long) or vol_long <= 0:
            return None
        return float((vol_long - vol_short) / vol_long)

    def calculate_trend_tstat(self, symbol: str, date: str) -> Optional[float]:
        """Trend strength via slope t-stat on log price."""
        window = int(self.config.get("TREND_TSTAT_WINDOW", 126))
        if window < 20:
            return None
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 3)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window:
            return None
        work = df.copy().tail(window)
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work = work[(work["close"] > 0)].dropna(subset=["close"])
        if len(work) < max(20, int(window * 0.8)):
            return None
        y = np.log(work["close"].values.astype(float))
        x = np.arange(len(y), dtype=float)
        xm = x.mean()
        ym = y.mean()
        sxx = np.sum((x - xm) ** 2)
        if sxx <= 0:
            return None
        slope = float(np.sum((x - xm) * (y - ym)) / sxx)
        yhat = ym + slope * (x - xm)
        resid = y - yhat
        dof = len(y) - 2
        if dof <= 0:
            return None
        sigma2 = float(np.sum(resid ** 2) / dof)
        if not np.isfinite(sigma2) or sigma2 <= 0:
            return None
        se = float(np.sqrt(sigma2 / sxx))
        if se <= 0:
            return None
        return float(slope / se)

    def calculate_high_52w_proximity(self, symbol: str, date: str) -> Optional[float]:
        """Close proximity to 52-week high: close / rolling_max(252)."""
        window = int(self.config.get("HIGH_52W_WINDOW", 252))
        if window < 50:
            return None
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 3)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window:
            return None
        work = df.copy().tail(window)
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work = work[(work["close"] > 0)].dropna(subset=["close"])
        if len(work) < window:
            return None
        px = float(work.iloc[-1]["close"])
        hi = float(work["close"].max())
        if hi <= 0:
            return None
        return float(px / hi)

    def calculate_breakout_persistence(self, symbol: str, date: str) -> Optional[float]:
        """
        Breakout persistence proxy:
        (close - rolling_max(window)) / ATR(atr_window)
        """
        window = int(self.config.get("BREAKOUT_WINDOW", 252))
        atr_window = int(self.config.get("BREAKOUT_ATR_WINDOW", 20))
        lookback_days = max(window, atr_window) * 3
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < max(window, atr_window):
            return None
        work = df.copy()
        for c in ("high", "low", "close"):
            work[c] = pd.to_numeric(work[c], errors="coerce")
        work = work.dropna(subset=["high", "low", "close"])
        work = work[(work["close"] > 0) & (work["high"] > 0) & (work["low"] > 0)]
        if len(work) < max(window, atr_window):
            return None
        hist = work.tail(window)
        close_now = float(hist.iloc[-1]["close"])
        high_ref = float(hist["high"].max())
        tr = pd.concat(
            [
                (work["high"] - work["low"]).abs(),
                (work["high"] - work["close"].shift(1)).abs(),
                (work["low"] - work["close"].shift(1)).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr = tr.tail(atr_window).mean()
        if atr is None or np.isnan(atr) or float(atr) <= 0:
            return None
        return float((close_now - high_ref) / float(atr))

    def calculate_pullback_in_uptrend(self, symbol: str, date: str) -> Optional[float]:
        """Pullback score: -distance to MA20 when MA50 > MA200."""
        lookback = 220
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=lookback * 3)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < 200:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work = work[(work["close"] > 0)].dropna(subset=["close"])
        if len(work) < 200:
            return None
        close = work["close"]
        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()
        ma200 = close.rolling(200).mean()
        if np.isnan(ma20.iloc[-1]) or np.isnan(ma50.iloc[-1]) or np.isnan(ma200.iloc[-1]):
            return None
        if float(ma50.iloc[-1]) <= float(ma200.iloc[-1]):
            return None
        denom = float(ma20.iloc[-1])
        if denom == 0:
            return None
        return float(-(float(close.iloc[-1]) - denom) / abs(denom))

    def calculate_momentum_crash_adjusted(self, symbol: str, date: str) -> Optional[float]:
        """Momentum adjusted by short-horizon downside tail risk."""
        mom = self.calculate_momentum(symbol, date)
        if mom is None or pd.isna(mom):
            return None
        tail_w = int(self.config.get("MOM_CRASH_TAIL_WINDOW", 21))
        q = float(self.config.get("MOM_CRASH_TAIL_QUANTILE", 0.1))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=tail_w * 8)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < tail_w:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work.loc[work["close"] <= 0, "close"] = np.nan
        r = np.log(work["close"] / work["close"].shift(1)).dropna().tail(tail_w)
        if len(r) < tail_w:
            return None
        q = min(max(q, 0.01), 0.49)
        left = float(abs(r.quantile(q)))
        scale = float(r.std(ddof=1))
        if not np.isfinite(scale) or scale <= 0:
            return float(mom)
        tail_risk = left / scale
        return float(float(mom) * (1.0 - tail_risk))

    def calculate_overnight_drift(self, symbol: str, date: str) -> Optional[float]:
        """Sum of overnight log returns over window."""
        window = int(self.config.get("OVERNIGHT_DRIFT_WINDOW", 63))
        if window < 5:
            return None
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 4)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window + 1:
            return None
        work = df.copy()
        work["open"] = pd.to_numeric(work["open"], errors="coerce")
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work = work[(work["open"] > 0) & (work["close"] > 0)].dropna(subset=["open", "close"])
        if len(work) < window + 1:
            return None
        overnight = np.log(work["open"] / work["close"].shift(1)).dropna().tail(window)
        if len(overnight) < window:
            return None
        return float(overnight.sum())

    def calculate_gap_fill_propensity(self, symbol: str, date: str) -> Optional[float]:
        """Negative z-score of recent opening gaps (larger gap -> stronger mean-reversion propensity)."""
        window = int(self.config.get("GAP_FILL_WINDOW", 20))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window + 1:
            return None
        work = df.copy()
        work["open"] = pd.to_numeric(work["open"], errors="coerce")
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work = work[(work["open"] > 0) & (work["close"] > 0)].dropna(subset=["open", "close"])
        if len(work) < window + 1:
            return None
        gap = np.log(work["open"] / work["close"].shift(1)).dropna().tail(window)
        if len(gap) < window:
            return None
        std = float(gap.std(ddof=1))
        if not np.isfinite(std) or std <= 0:
            return None
        z = (float(gap.iloc[-1]) - float(gap.mean())) / std
        return float(-z)

    def calculate_amihud_illiquidity(self, symbol: str, date: str) -> Optional[float]:
        """Amihud illiquidity: mean(|ret| / dollar_volume, window)."""
        window = int(self.config.get("AMIHUD_WINDOW", 20))
        if window < 5:
            return None
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window + 1:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work["volume"] = pd.to_numeric(work["volume"], errors="coerce")
        work = work[(work["close"] > 0) & (work["volume"] >= 0)].dropna(subset=["close", "volume"])
        if len(work) < window + 1:
            return None
        work["ret"] = work["close"].pct_change()
        work["dollar_vol"] = work["close"] * work["volume"]
        tail = work.tail(window + 1).dropna(subset=["ret", "dollar_vol"])
        tail = tail[tail["dollar_vol"] > 0]
        if len(tail) < window:
            return None
        illiq = (tail["ret"].abs() / tail["dollar_vol"]).tail(window).mean()
        if illiq is None or np.isnan(illiq):
            return None
        return float(illiq)

    def calculate_amihud_improving(self, symbol: str, date: str) -> Optional[float]:
        """-delta(amihud, delta_window): positive means improving liquidity."""
        delta_window = int(self.config.get("AMIHUD_DELTA_WINDOW", 20))
        if delta_window < 1:
            return None
        cur = self.calculate_amihud_illiquidity(symbol, date)
        if cur is None or pd.isna(cur):
            return None
        past_date = (pd.Timestamp(date) - pd.Timedelta(days=delta_window)).strftime("%Y-%m-%d")
        past = self.calculate_amihud_illiquidity(symbol, past_date)
        if past is None or pd.isna(past):
            return None
        return float(-(float(cur) - float(past)))

    def calculate_dollar_volume_trend(self, symbol: str, date: str) -> Optional[float]:
        """Slope of log(ADV) over trend_window."""
        adv_window = int(self.config.get("DOLLAR_VOL_ADV_WINDOW", 20))
        trend_window = int(self.config.get("DOLLAR_VOL_TREND_WINDOW", 63))
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=max(adv_window, trend_window) * 6)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < adv_window + trend_window:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work["volume"] = pd.to_numeric(work["volume"], errors="coerce")
        work = work[(work["close"] > 0) & (work["volume"] >= 0)].dropna(subset=["close", "volume"])
        if len(work) < adv_window + trend_window:
            return None
        work["adv"] = (work["close"] * work["volume"]).rolling(adv_window).mean()
        s = np.log(work["adv"]).replace([np.inf, -np.inf], np.nan).dropna().tail(trend_window)
        if len(s) < trend_window:
            return None
        x = np.arange(len(s), dtype=float)
        xm = x.mean()
        ym = float(s.mean())
        sxx = float(np.sum((x - xm) ** 2))
        if sxx <= 0:
            return None
        slope = float(np.sum((x - xm) * (s.values - ym)) / sxx)
        return float(slope)

    def calculate_downside_volatility(self, symbol: str, date: str) -> Optional[float]:
        """Negative downside volatility over window."""
        window = int(self.config.get("DOWNSIDE_VOL_WINDOW", 60))
        if window < 5:
            return None
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 4)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window + 1:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work.loc[work["close"] <= 0, "close"] = np.nan
        r = np.log(work["close"] / work["close"].shift(1)).dropna().tail(window)
        if len(r) < window:
            return None
        r_down = r.where(r < 0, 0.0)
        vol = float(r_down.std(ddof=1))
        if not np.isfinite(vol):
            return None
        return float(-vol)

    def calculate_left_tail_es5(self, symbol: str, date: str) -> Optional[float]:
        """Negative expected shortfall at 5% tail over window."""
        window = int(self.config.get("LEFT_TAIL_WINDOW", 126))
        q = float(self.config.get("LEFT_TAIL_Q", 0.05))
        q = min(max(q, 0.01), 0.20)
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 4)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window + 1:
            return None
        work = df.copy()
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work.loc[work["close"] <= 0, "close"] = np.nan
        r = np.log(work["close"] / work["close"].shift(1)).dropna().tail(window)
        if len(r) < window:
            return None
        threshold = float(r.quantile(q))
        tail = r[r <= threshold]
        if len(tail) == 0:
            return None
        es = float(tail.mean())
        return float(-es)

    def calculate_max_drawdown_126(self, symbol: str, date: str) -> Optional[float]:
        """Negative max drawdown over rolling window."""
        window = int(self.config.get("MAX_DRAWDOWN_WINDOW", 126))
        if window < 20:
            return None
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 4)).strftime("%Y-%m-%d")
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        if df is None or len(df) < window:
            return None
        work = df.copy().tail(window)
        work["close"] = pd.to_numeric(work["close"], errors="coerce")
        work = work[(work["close"] > 0)].dropna(subset=["close"])
        if len(work) < window:
            return None
        px = work["close"]
        running_max = px.cummax()
        dd = (px / running_max) - 1.0
        mdd = float(dd.min())
        if not np.isfinite(mdd):
            return None
        return float(-abs(mdd))

    def calculate_quality_trend(self, symbol: str, date: str) -> Optional[float]:
        """
        Fundamental improvement score:
        quality(t) - quality(t-lookback_days).
        """
        lookback_days = int(self.config.get("QUALITY_TREND_LOOKBACK_DAYS", 252))
        if lookback_days <= 0:
            return None
        cur = self.calculate_quality(symbol, date)
        if cur is None or pd.isna(cur):
            return None
        past_date = (pd.Timestamp(date) - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        past = self.calculate_quality(symbol, past_date)
        if past is None or pd.isna(past):
            return None
        return float(cur - past)

    def calculate_quality_component(self, symbol: str, date: str) -> Optional[float]:
        if not self.fundamentals_engine:
            return None
        metric = str(self.config.get("QUALITY_COMPONENT_METRIC", "roe"))
        metrics = self.fundamentals_engine.get_latest_metrics(symbol, date)
        if not metrics:
            return None
        v = metrics.get(metric)
        if v is None or pd.isna(v):
            return None
        return float(v)

    def calculate_value_component(self, symbol: str, date: str) -> Optional[float]:
        if not self.value_engine:
            return None
        metric = str(self.config.get("VALUE_COMPONENT_METRIC", "earnings_yield"))
        metrics = self.value_engine.get_latest_metrics(symbol, date)
        if not metrics:
            return None
        v = metrics.get(metric)
        if v is None or pd.isna(v):
            return None
        return float(v)

    def calculate_value_quality_blend(self, symbol: str, date: str) -> Optional[float]:
        v = self.calculate_value(symbol, date)
        q = self.calculate_quality(symbol, date)
        if v is None or q is None or pd.isna(v) or pd.isna(q):
            return None
        wv = float(self.config.get("VALUE_BLEND_WEIGHT", 0.5))
        wq = float(self.config.get("QUALITY_BLEND_WEIGHT", 0.5))
        denom = abs(wv) + abs(wq)
        if denom <= 0:
            return None
        return float((wv * float(v) + wq * float(q)) / denom)

    def calculate_profitability_minus_leverage(self, symbol: str, date: str) -> Optional[float]:
        if not self.fundamentals_engine:
            return None
        metrics = self.fundamentals_engine.get_latest_metrics(symbol, date)
        if not metrics:
            return None
        a = metrics.get("cfo_to_assets")
        b = metrics.get("debt_to_equity")
        if a is None or b is None or pd.isna(a) or pd.isna(b):
            return None
        return float(float(a) - float(b))

    def calculate_quality_metric_trend(self, symbol: str, date: str) -> Optional[float]:
        metric = str(self.config.get("QUALITY_TREND_METRIC", "roe"))
        lookback_days = int(self.config.get("QUALITY_TREND_LOOKBACK_DAYS", 252))
        if lookback_days <= 0:
            return None
        if not self.fundamentals_engine:
            return None
        cur = self.fundamentals_engine.get_latest_metrics(symbol, date)
        if not cur:
            return None
        cur_v = cur.get(metric)
        if cur_v is None or pd.isna(cur_v):
            return None
        past_date = (pd.Timestamp(date) - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        past = self.fundamentals_engine.get_latest_metrics(symbol, past_date)
        if not past:
            return None
        past_v = past.get(metric)
        if past_v is None or pd.isna(past_v):
            return None
        return float(float(cur_v) - float(past_v))

    def calculate_value_metric_trend(self, symbol: str, date: str) -> Optional[float]:
        metric = str(self.config.get("VALUE_TREND_METRIC", "earnings_yield"))
        lookback_days = int(self.config.get("VALUE_TREND_LOOKBACK_DAYS", 252))
        if lookback_days <= 0:
            return None
        if not self.value_engine:
            return None
        cur = self.value_engine.get_latest_metrics(symbol, date)
        if not cur:
            return None
        cur_v = cur.get(metric)
        if cur_v is None or pd.isna(cur_v):
            return None
        past_date = (pd.Timestamp(date) - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        past = self.value_engine.get_latest_metrics(symbol, past_date)
        if not past:
            return None
        past_v = past.get(metric)
        if past_v is None or pd.isna(past_v):
            return None
        return float(float(cur_v) - float(past_v))

    def calculate_earnings_yield_ttm(self, symbol: str, date: str) -> Optional[float]:
        metric_bak = self.config.get("VALUE_COMPONENT_METRIC")
        self.config["VALUE_COMPONENT_METRIC"] = "earnings_yield"
        try:
            return self.calculate_value_component(symbol, date)
        finally:
            if metric_bak is None:
                self.config.pop("VALUE_COMPONENT_METRIC", None)
            else:
                self.config["VALUE_COMPONENT_METRIC"] = metric_bak

    def calculate_ocf_yield_ttm(self, symbol: str, date: str) -> Optional[float]:
        # Distinct proxy under current field scope:
        # combine FCF yield with earnings yield to approximate OCF-based valuation.
        fcfy = self.calculate_fcf_yield_ttm(symbol, date)
        ey = self.calculate_earnings_yield_ttm(symbol, date)
        if fcfy is None and ey is None:
            return None
        if fcfy is None:
            return float(ey)
        if ey is None:
            return float(fcfy)
        return float(0.75 * float(fcfy) + 0.25 * float(ey))

    def calculate_fcf_yield_ttm(self, symbol: str, date: str) -> Optional[float]:
        metric_bak = self.config.get("VALUE_COMPONENT_METRIC")
        self.config["VALUE_COMPONENT_METRIC"] = "fcf_yield"
        try:
            return self.calculate_value_component(symbol, date)
        finally:
            if metric_bak is None:
                self.config.pop("VALUE_COMPONENT_METRIC", None)
            else:
                self.config["VALUE_COMPONENT_METRIC"] = metric_bak

    def calculate_ebitda_ev_yield(self, symbol: str, date: str) -> Optional[float]:
        metric_bak = self.config.get("VALUE_COMPONENT_METRIC")
        self.config["VALUE_COMPONENT_METRIC"] = "ev_ebitda_yield"
        try:
            return self.calculate_value_component(symbol, date)
        finally:
            if metric_bak is None:
                self.config.pop("VALUE_COMPONENT_METRIC", None)
            else:
                self.config["VALUE_COMPONENT_METRIC"] = metric_bak

    def calculate_sales_ev_yield(self, symbol: str, date: str) -> Optional[float]:
        # Distinct proxy: combine EV-based and earnings-based yields.
        ev_y = self.calculate_ebitda_ev_yield(symbol, date)
        ey = self.calculate_earnings_yield_ttm(symbol, date)
        if ev_y is None and ey is None:
            return None
        if ev_y is None:
            return float(ey)
        if ey is None:
            return float(ev_y)
        return float(0.6 * float(ev_y) + 0.4 * float(ey))

    def calculate_book_to_market(self, symbol: str, date: str) -> Optional[float]:
        # Distinct proxy when book-equity is unavailable:
        # blend earnings and FCF yields.
        ey = self.calculate_earnings_yield_ttm(symbol, date)
        fcfy = self.calculate_fcf_yield_ttm(symbol, date)
        if ey is None and fcfy is None:
            return None
        if ey is None:
            return float(fcfy)
        if fcfy is None:
            return float(ey)
        return float(0.5 * float(ey) + 0.5 * float(fcfy))

    def calculate_shareholder_yield(self, symbol: str, date: str) -> Optional[float]:
        # Distinct proxy: owner-earnings yield plus cash-flow yield component.
        oey = self.calculate_owner_earnings_yield_proxy(symbol, date)
        fcfy = self.calculate_fcf_yield_ttm(symbol, date)
        if oey is None and fcfy is None:
            return None
        if oey is None:
            return float(fcfy)
        if fcfy is None:
            return float(oey)
        return float(0.7 * float(oey) + 0.3 * float(fcfy))

    def calculate_net_payout_yield(self, symbol: str, date: str) -> Optional[float]:
        # Distinct proxy: owner-earnings yield plus earnings-yield component.
        oey = self.calculate_owner_earnings_yield_proxy(symbol, date)
        ey = self.calculate_earnings_yield_ttm(symbol, date)
        if oey is None and ey is None:
            return None
        if oey is None:
            return float(ey)
        if ey is None:
            return float(oey)
        return float(0.7 * float(oey) + 0.3 * float(ey))

    def calculate_value_composite_sector_neutral(self, symbol: str, date: str) -> Optional[float]:
        return self.calculate_value(symbol, date)

    def calculate_value_rerating_trend(self, symbol: str, date: str) -> Optional[float]:
        metric_bak = self.config.get("VALUE_TREND_METRIC")
        self.config["VALUE_TREND_METRIC"] = "earnings_yield"
        try:
            return self.calculate_value_metric_trend(symbol, date)
        finally:
            if metric_bak is None:
                self.config.pop("VALUE_TREND_METRIC", None)
            else:
                self.config["VALUE_TREND_METRIC"] = metric_bak

    def calculate_roe_ttm(self, symbol: str, date: str) -> Optional[float]:
        metric_bak = self.config.get("QUALITY_COMPONENT_METRIC")
        self.config["QUALITY_COMPONENT_METRIC"] = "roe"
        try:
            return self.calculate_quality_component(symbol, date)
        finally:
            if metric_bak is None:
                self.config.pop("QUALITY_COMPONENT_METRIC", None)
            else:
                self.config["QUALITY_COMPONENT_METRIC"] = metric_bak

    def calculate_gross_profitability(self, symbol: str, date: str) -> Optional[float]:
        # Distinct proxy: combine margin level and cash-flow efficiency.
        gm = self.calculate_gross_margin_level(symbol, date)
        cfoa = self.calculate_cfo_to_assets(symbol, date)
        if gm is None and cfoa is None:
            return None
        if gm is None:
            return float(cfoa)
        if cfoa is None:
            return float(gm)
        return float(0.7 * float(gm) + 0.3 * float(cfoa))

    def calculate_roic_ttm(self, symbol: str, date: str) -> Optional[float]:
        # Proxy with ROE/ROA blend under current fields.
        roe = self.calculate_roe_ttm(symbol, date)
        roa = self.calculate_roa_ttm(symbol, date)
        if roe is None and roa is None:
            return None
        if roe is None:
            return float(roa)
        if roa is None:
            return float(roe)
        return float(0.6 * float(roe) + 0.4 * float(roa))

    def calculate_accruals_inverse(self, symbol: str, date: str) -> Optional[float]:
        roa = self.calculate_roa_ttm(symbol, date)
        cfoa = self.calculate_cfo_to_assets(symbol, date)
        if roa is None or cfoa is None or pd.isna(roa) or pd.isna(cfoa):
            return None
        return float(-(float(roa) - float(cfoa)))

    def calculate_roa_ttm(self, symbol: str, date: str) -> Optional[float]:
        metric_bak = self.config.get("QUALITY_COMPONENT_METRIC")
        self.config["QUALITY_COMPONENT_METRIC"] = "roa"
        try:
            return self.calculate_quality_component(symbol, date)
        finally:
            if metric_bak is None:
                self.config.pop("QUALITY_COMPONENT_METRIC", None)
            else:
                self.config["QUALITY_COMPONENT_METRIC"] = metric_bak

    def calculate_gross_profitability_proxy(self, symbol: str, date: str) -> Optional[float]:
        metric_bak = self.config.get("QUALITY_COMPONENT_METRIC")
        self.config["QUALITY_COMPONENT_METRIC"] = "gross_margin"
        try:
            return self.calculate_quality_component(symbol, date)
        finally:
            if metric_bak is None:
                self.config.pop("QUALITY_COMPONENT_METRIC", None)
            else:
                self.config["QUALITY_COMPONENT_METRIC"] = metric_bak

    def calculate_qmj_proxy_composite(self, symbol: str, date: str) -> Optional[float]:
        q = self.calculate_quality(symbol, date)
        v = self.calculate_value(symbol, date)
        if q is None or v is None or pd.isna(q) or pd.isna(v):
            return None
        wq = float(self.config.get("QMJ_PROXY_QUALITY_WEIGHT", 0.7))
        wv = float(self.config.get("QMJ_PROXY_VALUE_WEIGHT", 0.3))
        denom = abs(wq) + abs(wv)
        if denom <= 0:
            return None
        return float((wq * float(q) + wv * float(v)) / denom)

    def _collect_quality_metric_series(self, symbol: str, date: str, metric: str, n_points: int = 12, step_days: int = 90) -> list[float]:
        vals = []
        for i in range(n_points):
            dt = (pd.Timestamp(date) - pd.Timedelta(days=i * step_days)).strftime("%Y-%m-%d")
            if not self.fundamentals_engine:
                break
            m = self.fundamentals_engine.get_latest_metrics(symbol, dt)
            if not m:
                continue
            v = m.get(metric)
            if v is None or pd.isna(v):
                continue
            vals.append(float(v))
        return list(reversed(vals))

    def calculate_margin_stability_12q(self, symbol: str, date: str) -> Optional[float]:
        vals = self._collect_quality_metric_series(symbol, date, metric="gross_margin", n_points=12, step_days=90)
        if len(vals) < 6:
            return None
        v = float(np.std(vals, ddof=1))
        if not np.isfinite(v):
            return None
        return float(-v)

    def calculate_earnings_stability_12q(self, symbol: str, date: str) -> Optional[float]:
        vals = self._collect_quality_metric_series(symbol, date, metric="roa", n_points=12, step_days=90)
        if len(vals) < 6:
            return None
        v = float(np.std(vals, ddof=1))
        if not np.isfinite(v):
            return None
        return float(-v)

    def calculate_interest_coverage(self, symbol: str, date: str) -> Optional[float]:
        # Proxy with profitability-to-leverage composite.
        pml = self.calculate_profitability_minus_leverage(symbol, date)
        return float(pml) if pml is not None and not pd.isna(pml) else None

    def calculate_revenue_growth_quality_adj(self, symbol: str, date: str) -> Optional[float]:
        qtrend = self.calculate_quality_metric_trend(symbol, date)
        qual = self.calculate_quality(symbol, date)
        if qtrend is None or qual is None or pd.isna(qtrend) or pd.isna(qual):
            return None
        return float(float(qtrend) * float(qual))

    def calculate_eps_growth_quality_adj(self, symbol: str, date: str) -> Optional[float]:
        return self.calculate_revenue_growth_quality_adj(symbol, date)

    def calculate_fcf_growth_persistence(self, symbol: str, date: str) -> Optional[float]:
        vtrend = self.calculate_value_metric_trend(symbol, date)
        if vtrend is None or pd.isna(vtrend):
            return None
        past = self.calculate_value_metric_trend(symbol, (pd.Timestamp(date) - pd.Timedelta(days=252)).strftime("%Y-%m-%d"))
        if past is None or pd.isna(past):
            return float(vtrend)
        return float(float(vtrend) + float(past))

    def calculate_asset_growth_anomaly_inv(self, symbol: str, date: str) -> Optional[float]:
        # Distinct proxy with current field scope: trend in CFO/Assets.
        metric_bak = self.config.get("QUALITY_TREND_METRIC")
        self.config["QUALITY_TREND_METRIC"] = "cfo_to_assets"
        try:
            v = self.calculate_quality_metric_trend(symbol, date)
            if v is None or pd.isna(v):
                return None
            return float(v)
        finally:
            if metric_bak is None:
                self.config.pop("QUALITY_TREND_METRIC", None)
            else:
                self.config["QUALITY_TREND_METRIC"] = metric_bak

    def calculate_capex_discipline(self, symbol: str, date: str) -> Optional[float]:
        # Distinct proxy: persistent FCF improvement.
        return self.calculate_fcf_growth_persistence(symbol, date)

    def calculate_nwc_change_inverse(self, symbol: str, date: str) -> Optional[float]:
        # Distinct proxy: cashflow efficiency relative to margin level.
        cfoa = self.calculate_cfo_to_assets(symbol, date)
        gm = self.calculate_gross_margin_level(symbol, date)
        if cfoa is None or gm is None or pd.isna(cfoa) or pd.isna(gm):
            return None
        return float(float(cfoa) - float(gm))

    def calculate_profitability_trend_4q(self, symbol: str, date: str) -> Optional[float]:
        metric_bak = self.config.get("QUALITY_TREND_METRIC")
        self.config["QUALITY_TREND_METRIC"] = "roa"
        try:
            return self.calculate_quality_metric_trend(symbol, date)
        finally:
            if metric_bak is None:
                self.config.pop("QUALITY_TREND_METRIC", None)
            else:
                self.config["QUALITY_TREND_METRIC"] = metric_bak

    def calculate_margin_trend_4q(self, symbol: str, date: str) -> Optional[float]:
        metric_bak = self.config.get("QUALITY_TREND_METRIC")
        self.config["QUALITY_TREND_METRIC"] = "gross_margin"
        try:
            return self.calculate_quality_metric_trend(symbol, date)
        finally:
            if metric_bak is None:
                self.config.pop("QUALITY_TREND_METRIC", None)
            else:
                self.config["QUALITY_TREND_METRIC"] = metric_bak

    def calculate_cash_conversion_improve(self, symbol: str, date: str) -> Optional[float]:
        cfoa = self.calculate_cfo_to_assets(symbol, date)
        roa = self.calculate_roa_ttm(symbol, date)
        if cfoa is None or roa is None or pd.isna(cfoa) or pd.isna(roa):
            return None
        return float(float(cfoa) - float(roa))

    def calculate_investment_conservatism(self, symbol: str, date: str) -> Optional[float]:
        # Distinct proxy: combine deleveraging and asset-growth-anomaly inverse.
        d = self.calculate_deleveraging_quality(symbol, date)
        a = self.calculate_asset_growth_anomaly_inv(symbol, date)
        if d is None and a is None:
            return None
        if d is None:
            return float(a)
        if a is None:
            return float(d)
        return float(0.5 * float(d) + 0.5 * float(a))

    def calculate_post_event_liquidity_gap(self, symbol: str, date: str) -> Optional[float]:
        sue = self.calculate_sue_eps_basic(symbol, date)
        illiq = self.calculate_amihud_illiquidity(symbol, date)
        if sue is None or illiq is None or pd.isna(sue) or pd.isna(illiq):
            return None
        return float(float(sue) * (-float(illiq)))

    def calculate_ownership_acceleration(self, symbol: str, date: str) -> Optional[float]:
        cur = self.calculate_institutional_ownership_change(symbol, date)
        if cur is None or pd.isna(cur):
            return None
        prev1 = self.calculate_institutional_ownership_change(symbol, (pd.Timestamp(date) - pd.Timedelta(days=90)).strftime("%Y-%m-%d"))
        prev2 = self.calculate_institutional_ownership_change(symbol, (pd.Timestamp(date) - pd.Timedelta(days=180)).strftime("%Y-%m-%d"))
        if prev1 is None or prev2 is None or pd.isna(prev1) or pd.isna(prev2):
            return None
        return float((float(cur) - float(prev1)) - (float(prev1) - float(prev2)))

    def calculate_crowded_value_trap_avoid(self, symbol: str, date: str) -> Optional[float]:
        val = self.calculate_value(symbol, date)
        crowd = self.calculate_crowding_turnover_x_inst(symbol, date)
        if val is None or crowd is None or pd.isna(val) or pd.isna(crowd):
            return None
        return float(float(val) - float(crowd))

    def calculate_ownership_dispersion_proxy(self, symbol: str, date: str) -> Optional[float]:
        cache = self._load_institutional_summary()
        df = cache.get(symbol)
        if df is None or len(df) < 4 or "investorsHoldingChange" not in df.columns:
            return None
        d = pd.Timestamp(date)
        w = df[df["date"] <= d].tail(4)
        if len(w) < 3:
            return None
        x = pd.to_numeric(w["investorsHoldingChange"], errors="coerce").dropna()
        if len(x) < 3:
            return None
        v = float(x.std(ddof=1))
        if not np.isfinite(v):
            return None
        return float(-v)

    def calculate_risk_on_off_breadth(self, symbol: str, date: str) -> Optional[float]:
        # Per-symbol proxy: market trend - market volatility
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=400)).strftime("%Y-%m-%d")
        mkt = self.data_engine.get_price("SPY", start_date=start_date, end_date=date)
        if mkt is None or len(mkt) < 120:
            return None
        m = mkt.copy()
        m["close"] = pd.to_numeric(m["close"], errors="coerce")
        m.loc[m["close"] <= 0, "close"] = np.nan
        r = np.log(m["close"] / m["close"].shift(1)).dropna()
        if len(r) < 120:
            return None
        trend = float(np.log(m["close"].iloc[-1] / m["close"].iloc[-63]))
        vol = float(r.tail(63).std(ddof=1))
        if not np.isfinite(trend) or not np.isfinite(vol):
            return None
        return float(trend - vol)

    def calculate_cross_section_dispersion_regime(self, symbol: str, date: str) -> Optional[float]:
        # Proxy with market realized volatility regime.
        return self.calculate_risk_on_off_breadth(symbol, date)

    def calculate_correlation_regime_proxy(self, symbol: str, date: str) -> Optional[float]:
        qual = self.calculate_quality(symbol, date)
        beta = self.calculate_beta(symbol, date)
        if qual is None or beta is None or pd.isna(qual) or pd.isna(beta):
            return None
        return float(float(qual) * (1.0 - abs(float(beta))))

    def calculate_defensive_rotation_proxy(self, symbol: str, date: str) -> Optional[float]:
        qual = self.calculate_quality(symbol, date)
        beta = self.calculate_beta(symbol, date)
        if qual is None or beta is None or pd.isna(qual) or pd.isna(beta):
            return None
        return float(float(qual) - float(beta))

    def calculate_smallcap_seasonality_proxy(self, symbol: str, date: str) -> Optional[float]:
        mcap = self.calculate_size(symbol, date)
        if mcap is None or pd.isna(mcap) or float(mcap) <= 0:
            return None
        month = pd.Timestamp(date).month
        seasonal = 1.0 if month in (1, 12) else 0.5
        return float((-np.log(float(mcap))) * seasonal)

    def calculate_sue_eps_basic(self, symbol: str, date: str) -> Optional[float]:
        if not self.pead_factor:
            return None
        earnings = self.pead_factor.get_earnings(symbol)
        if earnings is None or len(earnings) == 0:
            return None
        work = earnings.copy()
        if "date" not in work.columns:
            return None
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        work = work.dropna(subset=["date", "epsActual", "epsEstimated"])
        if len(work) == 0:
            return None
        d = pd.Timestamp(date)
        max_age = int(self.config.get("SUE_EVENT_MAX_AGE_DAYS", 7))
        floor = float(self.config.get("SUE_EPS_FLOOR", 0.01))
        work = work[(work["date"] <= d) & (work["date"] >= d - pd.Timedelta(days=max_age))]
        if len(work) == 0:
            return None
        row = work.sort_values("date").iloc[-1]
        est = float(row["epsEstimated"])
        act = float(row["epsActual"])
        denom = max(abs(est), floor)
        return float((act - est) / denom)

    def calculate_sue_revenue_basic(self, symbol: str, date: str) -> Optional[float]:
        cal = self._load_earnings_calendar()
        df = cal.get(symbol)
        use_fallback = df is None or len(df) == 0
        if not use_fallback and ("revenueActual" not in df.columns or "revenueEstimated" not in df.columns):
            use_fallback = True
        if use_fallback:
            hist = self._load_earnings_history()
            df = hist.get(symbol)
        if df is None or len(df) == 0:
            return None
        d = pd.Timestamp(date)
        max_age = int(self.config.get("SUE_EVENT_MAX_AGE_DAYS", 7))
        floor = float(self.config.get("SUE_REVENUE_FLOOR", 1e6))
        work = df[(df["date"] <= d) & (df["date"] >= d - pd.Timedelta(days=max_age))].copy()
        if len(work) == 0:
            return None
        if "revenueActual" not in work.columns or "revenueEstimated" not in work.columns:
            return None
        work["revenueActual"] = pd.to_numeric(work["revenueActual"], errors="coerce")
        work["revenueEstimated"] = pd.to_numeric(work["revenueEstimated"], errors="coerce")
        work = work.dropna(subset=["revenueActual", "revenueEstimated"])
        if len(work) == 0:
            return None
        row = work.sort_values("date").iloc[-1]
        act = float(row["revenueActual"])
        est = float(row["revenueEstimated"])
        denom = max(abs(est), floor)
        return float((act - est) / denom)

    def calculate_pead_short_window(self, symbol: str, date: str) -> Optional[float]:
        """PEAD short-window proxy: recent EPS surprise with age decay over 1-20 days."""
        if not self.pead_factor:
            return None
        earnings = self.pead_factor.get_earnings(symbol)
        if earnings is None or len(earnings) == 0 or "date" not in earnings.columns:
            return None
        work = earnings.copy()
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        work = work.dropna(subset=["date", "epsActual", "epsEstimated"])
        if len(work) == 0:
            return None

        d = pd.Timestamp(date)
        min_age = int(self.config.get("PEAD_SHORT_MIN_AGE_DAYS", 1))
        max_age = int(self.config.get("PEAD_SHORT_MAX_AGE_DAYS", 20))
        floor = float(self.config.get("SUE_EPS_FLOOR", 0.01))
        if max_age < min_age:
            return None

        lb = d - pd.Timedelta(days=max_age)
        ub = d - pd.Timedelta(days=min_age)
        work = work[(work["date"] >= lb) & (work["date"] <= ub)]
        if len(work) == 0:
            return None

        row = work.sort_values("date").iloc[-1]
        est = float(row["epsEstimated"])
        act = float(row["epsActual"])
        age = int((d.normalize() - pd.Timestamp(row["date"]).normalize()).days)
        denom = max(abs(est), floor)
        surprise = float((act - est) / denom)
        decay = max(0.0, float(max_age - age + 1) / float(max_age))
        return float(surprise * decay)

    def _latest_from_symbol_cache(
        self,
        cache: Dict[str, pd.DataFrame],
        symbol: str,
        date: str,
        min_rows: int = 1,
    ) -> Optional[pd.Series]:
        df = cache.get(symbol)
        if df is None or len(df) == 0 or "date" not in df.columns:
            return None
        d = pd.Timestamp(date)
        work = df[df["date"] <= d]
        if len(work) < max(1, int(min_rows)):
            return None
        return work.iloc[-1]

    def calculate_institutional_ownership_change(self, symbol: str, date: str) -> Optional[float]:
        cache = self._load_institutional_summary()
        min_rows = int(self.config.get("INSTITUTIONAL_MIN_ROWS", 1))
        row = self._latest_from_symbol_cache(cache, symbol, date, min_rows=min_rows)
        if row is None:
            return None
        v = row.get("ownershipPercentChange")
        if v is None or pd.isna(v):
            return None
        return float(v)

    def calculate_institutional_breadth_change(self, symbol: str, date: str) -> Optional[float]:
        cache = self._load_institutional_summary()
        min_rows = int(self.config.get("INSTITUTIONAL_MIN_ROWS", 1))
        row = self._latest_from_symbol_cache(cache, symbol, date, min_rows=min_rows)
        if row is None:
            return None
        v = row.get("investorsHoldingChange")
        if v is None or pd.isna(v):
            return None
        return float(v)

    def calculate_institutional_ownership_level(self, symbol: str, date: str) -> Optional[float]:
        cache = self._load_institutional_summary()
        row = self._latest_from_symbol_cache(cache, symbol, date, min_rows=1)
        if row is None:
            return None
        v = row.get("ownershipPercent")
        if v is None or pd.isna(v):
            return None
        return float(v)

    def calculate_owner_earnings_yield_proxy(self, symbol: str, date: str) -> Optional[float]:
        cache = self._load_owner_earnings()
        row = self._latest_from_symbol_cache(cache, symbol, date)
        if row is None:
            return None
        oeps = row.get("ownersEarningsPerShare")
        if oeps is None or pd.isna(oeps):
            return None
        align_days = int(self.config.get("OWNER_EARNINGS_PRICE_ALIGN_DAYS", 0))
        px_end = (pd.Timestamp(date) - pd.Timedelta(days=max(0, align_days))).strftime("%Y-%m-%d")
        start_date = (pd.Timestamp(px_end) - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
        px = self.data_engine.get_price(symbol, start_date=start_date, end_date=px_end)
        if px is None or len(px) == 0:
            return None
        px = px.copy()
        px["date"] = pd.to_datetime(px["date"], errors="coerce")
        px["close"] = pd.to_numeric(px["close"], errors="coerce")
        px = px.dropna(subset=["date", "close"])
        px = px[(px["date"] <= pd.Timestamp(px_end)) & (px["close"] > 0)]
        if len(px) == 0:
            return None
        close = float(px.sort_values("date").iloc[-1]["close"])
        return float(float(oeps) / close)

    def calculate_sue_eps(self, symbol: str, date: str) -> Optional[float]:
        return self.calculate_sue_eps_basic(symbol, date)

    def calculate_sue_revenue(self, symbol: str, date: str) -> Optional[float]:
        return self.calculate_sue_revenue_basic(symbol, date)

    def calculate_pead_1_20(self, symbol: str, date: str) -> Optional[float]:
        return self.calculate_pead_short_window(symbol, date)

    def calculate_pead_21_60(self, symbol: str, date: str) -> Optional[float]:
        """Medium-window PEAD proxy: latest EPS surprise with event age in [21,60] days."""
        if not self.pead_factor:
            return None
        earnings = self.pead_factor.get_earnings(symbol)
        if earnings is None or len(earnings) == 0 or "date" not in earnings.columns:
            return None
        work = earnings.copy()
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        work = work.dropna(subset=["date", "epsActual", "epsEstimated"])
        if len(work) == 0:
            return None
        d = pd.Timestamp(date)
        min_age = int(self.config.get("PEAD_MEDIUM_MIN_AGE_DAYS", 21))
        max_age = int(self.config.get("PEAD_MEDIUM_MAX_AGE_DAYS", 60))
        lb = d - pd.Timedelta(days=max_age)
        ub = d - pd.Timedelta(days=min_age)
        work = work[(work["date"] >= lb) & (work["date"] <= ub)]
        if len(work) == 0:
            return None
        row = work.sort_values("date").iloc[-1]
        est = float(row["epsEstimated"])
        act = float(row["epsActual"])
        floor = float(self.config.get("SUE_EPS_FLOOR", 0.01))
        denom = max(abs(est), floor)
        return float((act - est) / denom)

    def calculate_earnings_gap_strength(self, symbol: str, date: str) -> Optional[float]:
        """Opening gap on most recent earnings date normalized by gap std."""
        cal = self._load_earnings_calendar()
        events = cal.get(symbol)
        if events is None or len(events) == 0 or "date" not in events.columns:
            return None
        d = pd.Timestamp(date)
        max_age = int(self.config.get("EARNINGS_GAP_MAX_AGE_DAYS", 10))
        ev = events[(events["date"] <= d) & (events["date"] >= d - pd.Timedelta(days=max_age))]
        if len(ev) == 0:
            return None
        ev_date = pd.Timestamp(ev.sort_values("date").iloc[-1]["date"])
        start_date = (ev_date - pd.Timedelta(days=120)).strftime("%Y-%m-%d")
        end_date = d.strftime("%Y-%m-%d")
        px = self.data_engine.get_price(symbol, start_date=start_date, end_date=end_date)
        if px is None or len(px) < 30:
            return None
        px = px.copy()
        px["date"] = pd.to_datetime(px["date"], errors="coerce")
        px["open"] = pd.to_numeric(px["open"], errors="coerce")
        px["close"] = pd.to_numeric(px["close"], errors="coerce")
        px = px.dropna(subset=["date", "open", "close"])
        px = px[(px["open"] > 0) & (px["close"] > 0)].sort_values("date")
        if len(px) < 30:
            return None
        px["gap"] = np.log(px["open"] / px["close"].shift(1))
        day = px[px["date"].dt.normalize() == ev_date.normalize()]
        if len(day) == 0:
            return None
        g = float(day.iloc[-1]["gap"]) if pd.notna(day.iloc[-1]["gap"]) else None
        hist = px["gap"].dropna().tail(60)
        if g is None or len(hist) < 20:
            return None
        std = float(hist.std(ddof=1))
        if not np.isfinite(std) or std <= 0:
            return None
        return float(g / std)

    def calculate_surprise_persistence(self, symbol: str, date: str) -> Optional[float]:
        """Latest two EPS surprises sum (persistence proxy)."""
        if not self.pead_factor:
            return None
        earnings = self.pead_factor.get_earnings(symbol)
        if earnings is None or len(earnings) == 0 or "date" not in earnings.columns:
            return None
        work = earnings.copy()
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        work = work.dropna(subset=["date", "epsActual", "epsEstimated"]).sort_values("date")
        d = pd.Timestamp(date)
        work = work[work["date"] <= d]
        if len(work) < 2:
            return None
        floor = float(self.config.get("SUE_EPS_FLOOR", 0.01))
        last2 = work.tail(2)
        vals = []
        for _, r in last2.iterrows():
            est = float(r["epsEstimated"])
            act = float(r["epsActual"])
            vals.append((act - est) / max(abs(est), floor))
        return float(vals[-1] + vals[-2])

    def calculate_beat_with_revenue_confirm(self, symbol: str, date: str) -> Optional[float]:
        """1 if both EPS and revenue surprises are positive on latest event, else 0/negative."""
        sue_eps = self.calculate_sue_eps_basic(symbol, date)
        sue_rev = self.calculate_sue_revenue_basic(symbol, date)
        if sue_eps is None or sue_rev is None or pd.isna(sue_eps) or pd.isna(sue_rev):
            return None
        return float((1.0 if sue_eps > 0 else -1.0) + (1.0 if sue_rev > 0 else -1.0))

    def calculate_institutional_ownership_delta(self, symbol: str, date: str) -> Optional[float]:
        return self.calculate_institutional_ownership_change(symbol, date)

    def calculate_institutional_breadth_delta(self, symbol: str, date: str) -> Optional[float]:
        return self.calculate_institutional_breadth_change(symbol, date)

    def calculate_owner_earnings_yield(self, symbol: str, date: str) -> Optional[float]:
        return self.calculate_owner_earnings_yield_proxy(symbol, date)

    def calculate_low_vol_60(self, symbol: str, date: str) -> Optional[float]:
        return self.calculate_low_volatility(symbol, date, window=60)

    def calculate_turnover_shock_20_120(self, symbol: str, date: str) -> Optional[float]:
        return self.calculate_turnover_shock(symbol, date)

    def calculate_cfo_to_assets(self, symbol: str, date: str) -> Optional[float]:
        metric_bak = self.config.get("QUALITY_COMPONENT_METRIC")
        self.config["QUALITY_COMPONENT_METRIC"] = "cfo_to_assets"
        try:
            return self.calculate_quality_component(symbol, date)
        finally:
            if metric_bak is None:
                self.config.pop("QUALITY_COMPONENT_METRIC", None)
            else:
                self.config["QUALITY_COMPONENT_METRIC"] = metric_bak

    def calculate_gross_margin_level(self, symbol: str, date: str) -> Optional[float]:
        metric_bak = self.config.get("QUALITY_COMPONENT_METRIC")
        self.config["QUALITY_COMPONENT_METRIC"] = "gross_margin"
        try:
            return self.calculate_quality_component(symbol, date)
        finally:
            if metric_bak is None:
                self.config.pop("QUALITY_COMPONENT_METRIC", None)
            else:
                self.config["QUALITY_COMPONENT_METRIC"] = metric_bak

    def calculate_deleveraging_quality(self, symbol: str, date: str) -> Optional[float]:
        metric_bak = self.config.get("QUALITY_TREND_METRIC")
        self.config["QUALITY_TREND_METRIC"] = "debt_to_equity"
        try:
            v = self.calculate_quality_metric_trend(symbol, date)
            if v is None or pd.isna(v):
                return None
            return float(-float(v))
        finally:
            if metric_bak is None:
                self.config.pop("QUALITY_TREND_METRIC", None)
            else:
                self.config["QUALITY_TREND_METRIC"] = metric_bak

    def calculate_low_beta_252(self, symbol: str, date: str) -> Optional[float]:
        beta = self.calculate_beta(symbol, date)
        if beta is None or pd.isna(beta):
            return None
        return float(-float(beta))

    def calculate_illiq_size_interaction(self, symbol: str, date: str) -> Optional[float]:
        illiq = self.calculate_amihud_illiquidity(symbol, date)
        mcap = self.calculate_size(symbol, date)
        if illiq is None or mcap is None or pd.isna(illiq) or pd.isna(mcap) or float(mcap) <= 0:
            return None
        return float(float(illiq) * (-np.log(float(mcap))))

    def calculate_liquidity_regime_score(self, symbol: str, date: str) -> Optional[float]:
        ts = self.calculate_turnover_shock(symbol, date)
        illiq = self.calculate_amihud_illiquidity(symbol, date)
        if ts is None or illiq is None or pd.isna(ts) or pd.isna(illiq):
            return None
        return float(float(ts) - float(illiq))

    def calculate_turnover_spike_decay(self, symbol: str, date: str) -> Optional[float]:
        delta_days = int(self.config.get("TURNOVER_SPIKE_DECAY_DAYS", 5))
        if delta_days < 1:
            return None
        cur = self.calculate_turnover_shock(symbol, date)
        if cur is None or pd.isna(cur):
            return None
        past_date = (pd.Timestamp(date) - pd.Timedelta(days=delta_days)).strftime("%Y-%m-%d")
        past = self.calculate_turnover_shock(symbol, past_date)
        if past is None or pd.isna(past):
            return None
        return float(-(float(cur) - float(past)))

    def calculate_crowding_turnover_x_inst(self, symbol: str, date: str) -> Optional[float]:
        ts = self.calculate_turnover_shock(symbol, date)
        own = self.calculate_institutional_ownership_level(symbol, date)
        if ts is None or own is None or pd.isna(ts) or pd.isna(own):
            return None
        return float(float(ts) + float(own))

    def calculate_event_underreaction_low_own(self, symbol: str, date: str) -> Optional[float]:
        sue = self.calculate_sue_eps_basic(symbol, date)
        own = self.calculate_institutional_ownership_level(symbol, date)
        if sue is None or own is None or pd.isna(sue) or pd.isna(own):
            return None
        own01 = min(max(float(own), 0.0), 1.0)
        return float(float(sue) * (1.0 - own01))

    def calculate_event_underreaction_value_anchor(self, symbol: str, date: str) -> Optional[float]:
        sue = self.calculate_sue_eps_basic(symbol, date)
        val = self.calculate_value(symbol, date)
        if sue is None or val is None or pd.isna(sue) or pd.isna(val):
            return None
        return float(float(sue) * float(val))

    def calculate_ownership_x_quality(self, symbol: str, date: str) -> Optional[float]:
        own_delta = self.calculate_institutional_ownership_change(symbol, date)
        qual = self.calculate_quality(symbol, date)
        if own_delta is None or qual is None or pd.isna(own_delta) or pd.isna(qual):
            return None
        return float(float(own_delta) * float(qual))

    def calculate_ownership_x_value(self, symbol: str, date: str) -> Optional[float]:
        own_delta = self.calculate_institutional_ownership_change(symbol, date)
        val = self.calculate_value(symbol, date)
        if own_delta is None or val is None or pd.isna(own_delta) or pd.isna(val):
            return None
        return float(float(own_delta) * float(val))

    def calculate_owner_earnings_trend(self, symbol: str, date: str) -> Optional[float]:
        lookback_days = int(self.config.get("OWNER_EARNINGS_TREND_LOOKBACK_DAYS", 252))
        if lookback_days < 30:
            return None
        cur = self.calculate_owner_earnings_yield_proxy(symbol, date)
        if cur is None or pd.isna(cur):
            return None
        past_date = (pd.Timestamp(date) - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        past = self.calculate_owner_earnings_yield_proxy(symbol, past_date)
        if past is None or pd.isna(past):
            return None
        return float(float(cur) - float(past))

    def calculate_de_crowding_momentum(self, symbol: str, date: str) -> Optional[float]:
        mom = self.calculate_momentum(symbol, date)
        own_delta = self.calculate_institutional_ownership_change(symbol, date)
        if mom is None or own_delta is None or pd.isna(mom) or pd.isna(own_delta):
            return None
        return float(float(mom) - float(own_delta))

    def calculate_all_factors(self, symbol: str, date: str,
                              needed: Optional[set] = None) -> Dict[str, Optional[float]]:
        """
        Calculate factor values for a symbol.
        If `needed` is provided, only compute those factors to avoid unnecessary work.
        """
        if needed is not None:
            needed = set(needed)

        global_lag = self.config.get('FACTOR_LAG_DAYS', 0)
        factors: Dict[str, Optional[float]] = {}

        if needed is None or 'momentum' in needed:
            mom_date = resolve_factor_date(date, global_lag, self.config.get('MOMENTUM_LAG_DAYS'))
            factors['momentum'] = self.calculate_momentum(symbol, mom_date)
        if needed is None or 'reversal' in needed:
            rev_date = resolve_factor_date(date, global_lag, self.config.get('REVERSAL_LAG_DAYS'))
            factors['reversal'] = self.calculate_reversal(symbol, rev_date)
        if needed is None or 'low_vol' in needed:
            lowvol_date = resolve_factor_date(date, global_lag, self.config.get('LOW_VOL_LAG_DAYS'))
            factors['low_vol'] = self.calculate_low_volatility(symbol, lowvol_date)
        if needed is None or 'beta' in needed:
            beta_date = resolve_factor_date(date, global_lag, self.config.get('BETA_LAG_DAYS'))
            factors['beta'] = self.calculate_beta(symbol, beta_date)
        if needed is None or 'size' in needed:
            size_date = resolve_factor_date(date, global_lag, self.config.get('SIZE_LAG_DAYS'))
            factors['size'] = self.calculate_size(symbol, size_date)
        if (needed is None or 'pead' in needed) and self.pead_factor:
            pead_date = resolve_factor_date(date, global_lag, self.config.get('PEAD_LAG_DAYS'))
            factors['pead'] = self.calculate_pead(symbol, pead_date)
        if (needed is None or 'quality' in needed) and self.fundamentals_engine:
            qual_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['quality'] = self.calculate_quality(symbol, qual_date)
        if (needed is None or 'value' in needed) and self.value_engine:
            val_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_LAG_DAYS'))
            factors['value'] = self.calculate_value(symbol, val_date)
        if needed is None or 'turnover_shock' in needed:
            ts_date = resolve_factor_date(date, global_lag, self.config.get('TURNOVER_SHOCK_LAG_DAYS'))
            factors['turnover_shock'] = self.calculate_turnover_shock(symbol, ts_date)
        if needed is None or 'vol_regime' in needed:
            vr_date = resolve_factor_date(date, global_lag, self.config.get('VOL_REGIME_LAG_DAYS'))
            factors['vol_regime'] = self.calculate_vol_regime(symbol, vr_date)
        if (needed is None or 'quality_trend' in needed) and self.fundamentals_engine:
            qt_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_TREND_LAG_DAYS'))
            factors['quality_trend'] = self.calculate_quality_trend(symbol, qt_date)
        if (needed is None or 'quality_component' in needed) and self.fundamentals_engine:
            qc_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_COMPONENT_LAG_DAYS'))
            factors['quality_component'] = self.calculate_quality_component(symbol, qc_date)
        if (needed is None or 'value_component' in needed) and self.value_engine:
            vc_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_COMPONENT_LAG_DAYS'))
            factors['value_component'] = self.calculate_value_component(symbol, vc_date)
        if (needed is None or 'value_quality_blend' in needed) and self.fundamentals_engine and self.value_engine:
            vq_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_QUALITY_BLEND_LAG_DAYS'))
            factors['value_quality_blend'] = self.calculate_value_quality_blend(symbol, vq_date)
        if (needed is None or 'profitability_minus_leverage' in needed) and self.fundamentals_engine:
            pml_date = resolve_factor_date(date, global_lag, self.config.get('PML_LAG_DAYS'))
            factors['profitability_minus_leverage'] = self.calculate_profitability_minus_leverage(symbol, pml_date)
        if (needed is None or 'quality_metric_trend' in needed) and self.fundamentals_engine:
            qmt_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_TREND_LAG_DAYS'))
            factors['quality_metric_trend'] = self.calculate_quality_metric_trend(symbol, qmt_date)
        if (needed is None or 'value_metric_trend' in needed) and self.value_engine:
            vmt_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_TREND_LAG_DAYS'))
            factors['value_metric_trend'] = self.calculate_value_metric_trend(symbol, vmt_date)
        if needed is None or 'sue_eps_basic' in needed:
            see_date = resolve_factor_date(date, global_lag, self.config.get('SUE_LAG_DAYS'))
            factors['sue_eps_basic'] = self.calculate_sue_eps_basic(symbol, see_date)
        if needed is None or 'sue_revenue_basic' in needed:
            srv_date = resolve_factor_date(date, global_lag, self.config.get('SUE_REVENUE_LAG_DAYS'))
            factors['sue_revenue_basic'] = self.calculate_sue_revenue_basic(symbol, srv_date)
        if needed is None or 'pead_short_window' in needed:
            psw_date = resolve_factor_date(date, global_lag, self.config.get('PEAD_SHORT_WINDOW_LAG_DAYS'))
            factors['pead_short_window'] = self.calculate_pead_short_window(symbol, psw_date)
        if needed is None or 'institutional_ownership_change' in needed:
            ioc_date = resolve_factor_date(date, global_lag, self.config.get('INSTITUTIONAL_LAG_DAYS'))
            factors['institutional_ownership_change'] = self.calculate_institutional_ownership_change(symbol, ioc_date)
        if needed is None or 'institutional_breadth_change' in needed:
            ibc_date = resolve_factor_date(date, global_lag, self.config.get('INSTITUTIONAL_LAG_DAYS'))
            factors['institutional_breadth_change'] = self.calculate_institutional_breadth_change(symbol, ibc_date)
        if needed is None or 'owner_earnings_yield_proxy' in needed:
            oey_date = resolve_factor_date(date, global_lag, self.config.get('OWNER_EARNINGS_LAG_DAYS'))
            factors['owner_earnings_yield_proxy'] = self.calculate_owner_earnings_yield_proxy(symbol, oey_date)
        if needed is None or 'trend_tstat_126' in needed:
            tt_date = resolve_factor_date(date, global_lag, self.config.get('TREND_TSTAT_LAG_DAYS'))
            factors['trend_tstat_126'] = self.calculate_trend_tstat(symbol, tt_date)
        if needed is None or 'high_52w_proximity' in needed:
            h52_date = resolve_factor_date(date, global_lag, self.config.get('HIGH_52W_LAG_DAYS'))
            factors['high_52w_proximity'] = self.calculate_high_52w_proximity(symbol, h52_date)
        if needed is None or 'breakout_persistence' in needed:
            bop_date = resolve_factor_date(date, global_lag, self.config.get('BREAKOUT_LAG_DAYS'))
            factors['breakout_persistence'] = self.calculate_breakout_persistence(symbol, bop_date)
        if needed is None or 'pullback_in_uptrend' in needed:
            pbu_date = resolve_factor_date(date, global_lag, self.config.get('PULLBACK_LAG_DAYS'))
            factors['pullback_in_uptrend'] = self.calculate_pullback_in_uptrend(symbol, pbu_date)
        if needed is None or 'momentum_crash_adjusted' in needed:
            mca_date = resolve_factor_date(date, global_lag, self.config.get('MOM_CRASH_ADJ_LAG_DAYS'))
            factors['momentum_crash_adjusted'] = self.calculate_momentum_crash_adjusted(symbol, mca_date)
        if needed is None or 'overnight_drift_63' in needed:
            od_date = resolve_factor_date(date, global_lag, self.config.get('OVERNIGHT_DRIFT_LAG_DAYS'))
            factors['overnight_drift_63'] = self.calculate_overnight_drift(symbol, od_date)
        if needed is None or 'gap_fill_propensity' in needed:
            gfp_date = resolve_factor_date(date, global_lag, self.config.get('GAP_FILL_LAG_DAYS'))
            factors['gap_fill_propensity'] = self.calculate_gap_fill_propensity(symbol, gfp_date)
        if needed is None or 'amihud_illiquidity_20' in needed:
            ami_date = resolve_factor_date(date, global_lag, self.config.get('AMIHUD_LAG_DAYS'))
            factors['amihud_illiquidity_20'] = self.calculate_amihud_illiquidity(symbol, ami_date)
        if needed is None or 'amihud_improving' in needed:
            ami2_date = resolve_factor_date(date, global_lag, self.config.get('AMIHUD_LAG_DAYS'))
            factors['amihud_improving'] = self.calculate_amihud_improving(symbol, ami2_date)
        if needed is None or 'dollar_volume_trend' in needed:
            dvt_date = resolve_factor_date(date, global_lag, self.config.get('DOLLAR_VOL_TREND_LAG_DAYS'))
            factors['dollar_volume_trend'] = self.calculate_dollar_volume_trend(symbol, dvt_date)
        if needed is None or 'downside_vol_60' in needed:
            dsv_date = resolve_factor_date(date, global_lag, self.config.get('DOWNSIDE_VOL_LAG_DAYS'))
            factors['downside_vol_60'] = self.calculate_downside_volatility(symbol, dsv_date)
        if needed is None or 'left_tail_es5_126' in needed:
            les_date = resolve_factor_date(date, global_lag, self.config.get('LEFT_TAIL_LAG_DAYS'))
            factors['left_tail_es5_126'] = self.calculate_left_tail_es5(symbol, les_date)
        if needed is None or 'max_drawdown_126' in needed:
            mdd_date = resolve_factor_date(date, global_lag, self.config.get('MAX_DRAWDOWN_LAG_DAYS'))
            factors['max_drawdown_126'] = self.calculate_max_drawdown_126(symbol, mdd_date)
        if needed is None or 'low_beta_252' in needed:
            lb_date = resolve_factor_date(date, global_lag, self.config.get('LOW_BETA_LAG_DAYS'))
            factors['low_beta_252'] = self.calculate_low_beta_252(symbol, lb_date)
        if needed is None or 'illiq_size_interaction' in needed:
            isi_date = resolve_factor_date(date, global_lag, self.config.get('ILLIQ_SIZE_LAG_DAYS'))
            factors['illiq_size_interaction'] = self.calculate_illiq_size_interaction(symbol, isi_date)
        if needed is None or 'liquidity_regime_score' in needed:
            lrs_date = resolve_factor_date(date, global_lag, self.config.get('LIQ_REGIME_LAG_DAYS'))
            factors['liquidity_regime_score'] = self.calculate_liquidity_regime_score(symbol, lrs_date)
        if needed is None or 'turnover_spike_decay' in needed:
            tsd_date = resolve_factor_date(date, global_lag, self.config.get('TURNOVER_SPIKE_LAG_DAYS'))
            factors['turnover_spike_decay'] = self.calculate_turnover_spike_decay(symbol, tsd_date)
        if needed is None or 'crowding_turnover_x_inst' in needed:
            ctxi_date = resolve_factor_date(date, global_lag, self.config.get('CROWDING_LAG_DAYS'))
            factors['crowding_turnover_x_inst'] = self.calculate_crowding_turnover_x_inst(symbol, ctxi_date)
        if needed is None or 'event_underreaction_low_own' in needed:
            eulo_date = resolve_factor_date(date, global_lag, self.config.get('EVENT_UNDERREACTION_LAG_DAYS'))
            factors['event_underreaction_low_own'] = self.calculate_event_underreaction_low_own(symbol, eulo_date)
        if needed is None or 'event_underreaction_value_anchor' in needed:
            euva_date = resolve_factor_date(date, global_lag, self.config.get('EVENT_UNDERREACTION_LAG_DAYS'))
            factors['event_underreaction_value_anchor'] = self.calculate_event_underreaction_value_anchor(symbol, euva_date)
        if needed is None or 'ownership_x_quality' in needed:
            oxq_date = resolve_factor_date(date, global_lag, self.config.get('OWNERSHIP_INTERACT_LAG_DAYS'))
            factors['ownership_x_quality'] = self.calculate_ownership_x_quality(symbol, oxq_date)
        if needed is None or 'ownership_x_value' in needed:
            oxv_date = resolve_factor_date(date, global_lag, self.config.get('OWNERSHIP_INTERACT_LAG_DAYS'))
            factors['ownership_x_value'] = self.calculate_ownership_x_value(symbol, oxv_date)
        if needed is None or 'owner_earnings_trend' in needed:
            oet_date = resolve_factor_date(date, global_lag, self.config.get('OWNER_EARNINGS_LAG_DAYS'))
            factors['owner_earnings_trend'] = self.calculate_owner_earnings_trend(symbol, oet_date)
        if needed is None or 'de_crowding_momentum' in needed:
            dcm_date = resolve_factor_date(date, global_lag, self.config.get('DE_CROWDING_LAG_DAYS'))
            factors['de_crowding_momentum'] = self.calculate_de_crowding_momentum(symbol, dcm_date)
        if needed is None or 'earnings_yield_ttm' in needed:
            eyt_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_LAG_DAYS'))
            factors['earnings_yield_ttm'] = self.calculate_earnings_yield_ttm(symbol, eyt_date)
        if needed is None or 'fcf_yield_ttm' in needed:
            fyt_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_LAG_DAYS'))
            factors['fcf_yield_ttm'] = self.calculate_fcf_yield_ttm(symbol, fyt_date)
        if needed is None or 'ebitda_ev_yield' in needed:
            eev_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_LAG_DAYS'))
            factors['ebitda_ev_yield'] = self.calculate_ebitda_ev_yield(symbol, eev_date)
        if needed is None or 'value_composite_sector_neutral' in needed:
            vcsn_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_LAG_DAYS'))
            factors['value_composite_sector_neutral'] = self.calculate_value_composite_sector_neutral(symbol, vcsn_date)
        if needed is None or 'value_rerating_trend' in needed:
            vrt_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_TREND_LAG_DAYS'))
            factors['value_rerating_trend'] = self.calculate_value_rerating_trend(symbol, vrt_date)
        if needed is None or 'roe_ttm' in needed:
            roe_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['roe_ttm'] = self.calculate_roe_ttm(symbol, roe_date)
        if needed is None or 'roa_ttm' in needed:
            roa_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['roa_ttm'] = self.calculate_roa_ttm(symbol, roa_date)
        if needed is None or 'gross_profitability_proxy' in needed:
            gp_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['gross_profitability_proxy'] = self.calculate_gross_profitability_proxy(symbol, gp_date)
        if needed is None or 'qmj_proxy_composite' in needed:
            qmj_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['qmj_proxy_composite'] = self.calculate_qmj_proxy_composite(symbol, qmj_date)
        if needed is None or 'sue_eps' in needed:
            se_date = resolve_factor_date(date, global_lag, self.config.get('SUE_LAG_DAYS'))
            factors['sue_eps'] = self.calculate_sue_eps(symbol, se_date)
        if needed is None or 'sue_revenue' in needed:
            sr_date = resolve_factor_date(date, global_lag, self.config.get('SUE_REVENUE_LAG_DAYS'))
            factors['sue_revenue'] = self.calculate_sue_revenue(symbol, sr_date)
        if needed is None or 'pead_1_20' in needed:
            p120_date = resolve_factor_date(date, global_lag, self.config.get('PEAD_SHORT_WINDOW_LAG_DAYS'))
            factors['pead_1_20'] = self.calculate_pead_1_20(symbol, p120_date)
        if needed is None or 'pead_21_60' in needed:
            p2160_date = resolve_factor_date(date, global_lag, self.config.get('PEAD_SHORT_WINDOW_LAG_DAYS'))
            factors['pead_21_60'] = self.calculate_pead_21_60(symbol, p2160_date)
        if needed is None or 'earnings_gap_strength' in needed:
            egs_date = resolve_factor_date(date, global_lag, self.config.get('SUE_LAG_DAYS'))
            factors['earnings_gap_strength'] = self.calculate_earnings_gap_strength(symbol, egs_date)
        if needed is None or 'surprise_persistence' in needed:
            sp_date = resolve_factor_date(date, global_lag, self.config.get('SUE_LAG_DAYS'))
            factors['surprise_persistence'] = self.calculate_surprise_persistence(symbol, sp_date)
        if needed is None or 'beat_with_revenue_confirm' in needed:
            bwr_date = resolve_factor_date(date, global_lag, self.config.get('SUE_LAG_DAYS'))
            factors['beat_with_revenue_confirm'] = self.calculate_beat_with_revenue_confirm(symbol, bwr_date)
        if needed is None or 'institutional_ownership_delta' in needed:
            iod_date = resolve_factor_date(date, global_lag, self.config.get('INSTITUTIONAL_LAG_DAYS'))
            factors['institutional_ownership_delta'] = self.calculate_institutional_ownership_delta(symbol, iod_date)
        if needed is None or 'institutional_breadth_delta' in needed:
            ibd_date = resolve_factor_date(date, global_lag, self.config.get('INSTITUTIONAL_LAG_DAYS'))
            factors['institutional_breadth_delta'] = self.calculate_institutional_breadth_delta(symbol, ibd_date)
        if needed is None or 'owner_earnings_yield' in needed:
            oey2_date = resolve_factor_date(date, global_lag, self.config.get('OWNER_EARNINGS_LAG_DAYS'))
            factors['owner_earnings_yield'] = self.calculate_owner_earnings_yield(symbol, oey2_date)
        if needed is None or 'low_vol_60' in needed:
            lv60_date = resolve_factor_date(date, global_lag, self.config.get('LOW_VOL_LAG_DAYS'))
            factors['low_vol_60'] = self.calculate_low_vol_60(symbol, lv60_date)
        if needed is None or 'turnover_shock_20_120' in needed:
            ts20120_date = resolve_factor_date(date, global_lag, self.config.get('TURNOVER_SHOCK_LAG_DAYS'))
            factors['turnover_shock_20_120'] = self.calculate_turnover_shock_20_120(symbol, ts20120_date)
        if needed is None or 'cfo_to_assets' in needed:
            cfoa_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['cfo_to_assets'] = self.calculate_cfo_to_assets(symbol, cfoa_date)
        if needed is None or 'gross_margin_level' in needed:
            gml_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['gross_margin_level'] = self.calculate_gross_margin_level(symbol, gml_date)
        if needed is None or 'deleveraging_quality' in needed:
            dq_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_TREND_LAG_DAYS'))
            factors['deleveraging_quality'] = self.calculate_deleveraging_quality(symbol, dq_date)
        if needed is None or 'residual_mom_12_1' in needed:
            rm_date = resolve_factor_date(date, global_lag, self.config.get('MOMENTUM_LAG_DAYS'))
            factors['residual_mom_12_1'] = self.calculate_residual_mom_12_1(symbol, rm_date)
        if needed is None or 'range_followthrough' in needed:
            rf_date = resolve_factor_date(date, global_lag, self.config.get('RANGE_FOLLOW_LAG_DAYS'))
            factors['range_followthrough'] = self.calculate_range_followthrough(symbol, rf_date)
        if needed is None or 'st_reversal_liquidity_filtered' in needed:
            srl_date = resolve_factor_date(date, global_lag, self.config.get('REVERSAL_LAG_DAYS'))
            factors['st_reversal_liquidity_filtered'] = self.calculate_st_reversal_liquidity_filtered(symbol, srl_date)
        if needed is None or 'post_spike_cooldown' in needed:
            psc_date = resolve_factor_date(date, global_lag, self.config.get('POST_SPIKE_LAG_DAYS'))
            factors['post_spike_cooldown'] = self.calculate_post_spike_cooldown(symbol, psc_date)
        if needed is None or 'overreaction_volume_adjusted' in needed:
            ova_date = resolve_factor_date(date, global_lag, self.config.get('OVERREACT_LAG_DAYS'))
            factors['overreaction_volume_adjusted'] = self.calculate_overreaction_volume_adjusted(symbol, ova_date)
        if needed is None or 'failed_breakout_reversal' in needed:
            fbr_date = resolve_factor_date(date, global_lag, self.config.get('FAILED_BREAKOUT_LAG_DAYS'))
            factors['failed_breakout_reversal'] = self.calculate_failed_breakout_reversal(symbol, fbr_date)
        if needed is None or 'compression_reversal' in needed:
            cr_date = resolve_factor_date(date, global_lag, self.config.get('COMPRESSION_LAG_DAYS'))
            factors['compression_reversal'] = self.calculate_compression_reversal(symbol, cr_date)
        if needed is None or 'skew_reversal' in needed:
            skr_date = resolve_factor_date(date, global_lag, self.config.get('SKEW_REV_LAG_DAYS'))
            factors['skew_reversal'] = self.calculate_skew_reversal(symbol, skr_date)
        if needed is None or 'three_red_days_rebound' in needed:
            trd_date = resolve_factor_date(date, global_lag, self.config.get('THREE_RED_LAG_DAYS'))
            factors['three_red_days_rebound'] = self.calculate_three_red_days_rebound(symbol, trd_date)
        if needed is None or 'large_gap_reversal' in needed:
            lgr_date = resolve_factor_date(date, global_lag, self.config.get('LARGE_GAP_LAG_DAYS'))
            factors['large_gap_reversal'] = self.calculate_large_gap_reversal(symbol, lgr_date)
        if needed is None or 'flow_autocorr_20' in needed:
            fac_date = resolve_factor_date(date, global_lag, self.config.get('FLOW_AUTOCORR_LAG_DAYS'))
            factors['flow_autocorr_20'] = self.calculate_flow_autocorr_20(symbol, fac_date)
        if needed is None or 'spread_proxy_stability' in needed:
            sps_date = resolve_factor_date(date, global_lag, self.config.get('SPREAD_STAB_LAG_DAYS'))
            factors['spread_proxy_stability'] = self.calculate_spread_proxy_stability(symbol, sps_date)
        if needed is None or 'vol_of_vol_126' in needed:
            vov_date = resolve_factor_date(date, global_lag, self.config.get('VOL_OF_VOL_LAG_DAYS'))
            factors['vol_of_vol_126'] = self.calculate_vol_of_vol_126(symbol, vov_date)
        if needed is None or 'jump_risk_proxy' in needed:
            jrp_date = resolve_factor_date(date, global_lag, self.config.get('JUMP_RISK_LAG_DAYS'))
            factors['jump_risk_proxy'] = self.calculate_jump_risk_proxy(symbol, jrp_date)
        if needed is None or 'trend_regime_switch' in needed:
            trs_date = resolve_factor_date(date, global_lag, self.config.get('REGIME_LAG_DAYS'))
            factors['trend_regime_switch'] = self.calculate_trend_regime_switch(symbol, trs_date)
        if needed is None or 'vol_regime_switch' in needed:
            vrs_date = resolve_factor_date(date, global_lag, self.config.get('REGIME_LAG_DAYS'))
            factors['vol_regime_switch'] = self.calculate_vol_regime_switch(symbol, vrs_date)
        if needed is None or 'liquidity_regime_switch' in needed:
            lrsw_date = resolve_factor_date(date, global_lag, self.config.get('REGIME_LAG_DAYS'))
            factors['liquidity_regime_switch'] = self.calculate_liquidity_regime_switch(symbol, lrsw_date)
        if needed is None or 'earnings_season_alpha' in needed:
            esa_date = resolve_factor_date(date, global_lag, self.config.get('SUE_LAG_DAYS'))
            factors['earnings_season_alpha'] = self.calculate_earnings_season_alpha(symbol, esa_date)
        if needed is None or 'state_weighted_meta_signal' in needed:
            swm_date = resolve_factor_date(date, global_lag, self.config.get('REGIME_LAG_DAYS'))
            factors['state_weighted_meta_signal'] = self.calculate_state_weighted_meta_signal(symbol, swm_date)
        if needed is None or 'idio_mom_vs_sector' in needed:
            ims_date = resolve_factor_date(date, global_lag, self.config.get('MOMENTUM_LAG_DAYS'))
            factors['idio_mom_vs_sector'] = self.calculate_idio_mom_vs_sector(symbol, ims_date)
        if needed is None or 'extreme_reversal_ex_earnings' in needed:
            ere_date = resolve_factor_date(date, global_lag, self.config.get('REVERSAL_LAG_DAYS'))
            factors['extreme_reversal_ex_earnings'] = self.calculate_extreme_reversal_ex_earnings(symbol, ere_date)
        if needed is None or 'intraday_reversion_proxy' in needed:
            irp_date = resolve_factor_date(date, global_lag, self.config.get('REVERSAL_LAG_DAYS'))
            factors['intraday_reversion_proxy'] = self.calculate_intraday_reversion_proxy(symbol, irp_date)
        if needed is None or 'idiosyncratic_vol_63' in needed:
            iv63_date = resolve_factor_date(date, global_lag, self.config.get('BETA_LAG_DAYS'))
            factors['idiosyncratic_vol_63'] = self.calculate_idiosyncratic_vol_63(symbol, iv63_date)
        if needed is None or 'beta_instability_126' in needed:
            bi126_date = resolve_factor_date(date, global_lag, self.config.get('BETA_LAG_DAYS'))
            factors['beta_instability_126'] = self.calculate_beta_instability_126(symbol, bi126_date)
        if needed is None or 'downside_beta_crash' in needed:
            dbc_date = resolve_factor_date(date, global_lag, self.config.get('BETA_LAG_DAYS'))
            factors['downside_beta_crash'] = self.calculate_downside_beta_crash(symbol, dbc_date)
        if needed is None or 'ocf_yield_ttm' in needed:
            ocfy_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_LAG_DAYS'))
            factors['ocf_yield_ttm'] = self.calculate_ocf_yield_ttm(symbol, ocfy_date)
        if needed is None or 'sales_ev_yield' in needed:
            sey_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_LAG_DAYS'))
            factors['sales_ev_yield'] = self.calculate_sales_ev_yield(symbol, sey_date)
        if needed is None or 'book_to_market' in needed:
            btm_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_LAG_DAYS'))
            factors['book_to_market'] = self.calculate_book_to_market(symbol, btm_date)
        if needed is None or 'shareholder_yield' in needed:
            shy_date = resolve_factor_date(date, global_lag, self.config.get('OWNER_EARNINGS_LAG_DAYS'))
            factors['shareholder_yield'] = self.calculate_shareholder_yield(symbol, shy_date)
        if needed is None or 'net_payout_yield' in needed:
            npy_date = resolve_factor_date(date, global_lag, self.config.get('OWNER_EARNINGS_LAG_DAYS'))
            factors['net_payout_yield'] = self.calculate_net_payout_yield(symbol, npy_date)
        if needed is None or 'gross_profitability' in needed:
            gp_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['gross_profitability'] = self.calculate_gross_profitability(symbol, gp_date)
        if needed is None or 'roic_ttm' in needed:
            roic_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['roic_ttm'] = self.calculate_roic_ttm(symbol, roic_date)
        if needed is None or 'accruals_inverse' in needed:
            acc_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['accruals_inverse'] = self.calculate_accruals_inverse(symbol, acc_date)
        if needed is None or 'margin_stability_12q' in needed:
            ms12q_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['margin_stability_12q'] = self.calculate_margin_stability_12q(symbol, ms12q_date)
        if needed is None or 'earnings_stability_12q' in needed:
            es12q_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['earnings_stability_12q'] = self.calculate_earnings_stability_12q(symbol, es12q_date)
        if needed is None or 'interest_coverage' in needed:
            icov_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_LAG_DAYS'))
            factors['interest_coverage'] = self.calculate_interest_coverage(symbol, icov_date)
        if needed is None or 'revenue_growth_quality_adj' in needed:
            rgq_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_TREND_LAG_DAYS'))
            factors['revenue_growth_quality_adj'] = self.calculate_revenue_growth_quality_adj(symbol, rgq_date)
        if needed is None or 'eps_growth_quality_adj' in needed:
            egq_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_TREND_LAG_DAYS'))
            factors['eps_growth_quality_adj'] = self.calculate_eps_growth_quality_adj(symbol, egq_date)
        if needed is None or 'fcf_growth_persistence' in needed:
            fgp_date = resolve_factor_date(date, global_lag, self.config.get('VALUE_TREND_LAG_DAYS'))
            factors['fcf_growth_persistence'] = self.calculate_fcf_growth_persistence(symbol, fgp_date)
        if needed is None or 'asset_growth_anomaly_inv' in needed:
            aga_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_TREND_LAG_DAYS'))
            factors['asset_growth_anomaly_inv'] = self.calculate_asset_growth_anomaly_inv(symbol, aga_date)
        if needed is None or 'capex_discipline' in needed:
            capd_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_TREND_LAG_DAYS'))
            factors['capex_discipline'] = self.calculate_capex_discipline(symbol, capd_date)
        if needed is None or 'nwc_change_inverse' in needed:
            nwc_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_TREND_LAG_DAYS'))
            factors['nwc_change_inverse'] = self.calculate_nwc_change_inverse(symbol, nwc_date)
        if needed is None or 'profitability_trend_4q' in needed:
            pt4q_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_TREND_LAG_DAYS'))
            factors['profitability_trend_4q'] = self.calculate_profitability_trend_4q(symbol, pt4q_date)
        if needed is None or 'margin_trend_4q' in needed:
            mt4q_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_TREND_LAG_DAYS'))
            factors['margin_trend_4q'] = self.calculate_margin_trend_4q(symbol, mt4q_date)
        if needed is None or 'cash_conversion_improve' in needed:
            cci_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_TREND_LAG_DAYS'))
            factors['cash_conversion_improve'] = self.calculate_cash_conversion_improve(symbol, cci_date)
        if needed is None or 'investment_conservatism' in needed:
            icon_date = resolve_factor_date(date, global_lag, self.config.get('QUALITY_TREND_LAG_DAYS'))
            factors['investment_conservatism'] = self.calculate_investment_conservatism(symbol, icon_date)
        if needed is None or 'post_event_liquidity_gap' in needed:
            pelg_date = resolve_factor_date(date, global_lag, self.config.get('EVENT_UNDERREACTION_LAG_DAYS'))
            factors['post_event_liquidity_gap'] = self.calculate_post_event_liquidity_gap(symbol, pelg_date)
        if needed is None or 'ownership_acceleration' in needed:
            oacc_date = resolve_factor_date(date, global_lag, self.config.get('INSTITUTIONAL_LAG_DAYS'))
            factors['ownership_acceleration'] = self.calculate_ownership_acceleration(symbol, oacc_date)
        if needed is None or 'crowded_value_trap_avoid' in needed:
            cvta_date = resolve_factor_date(date, global_lag, self.config.get('CROWDING_LAG_DAYS'))
            factors['crowded_value_trap_avoid'] = self.calculate_crowded_value_trap_avoid(symbol, cvta_date)
        if needed is None or 'ownership_dispersion_proxy' in needed:
            odp_date = resolve_factor_date(date, global_lag, self.config.get('INSTITUTIONAL_LAG_DAYS'))
            factors['ownership_dispersion_proxy'] = self.calculate_ownership_dispersion_proxy(symbol, odp_date)
        if needed is None or 'risk_on_off_breadth' in needed:
            roob_date = resolve_factor_date(date, global_lag, self.config.get('REGIME_LAG_DAYS'))
            factors['risk_on_off_breadth'] = self.calculate_risk_on_off_breadth(symbol, roob_date)
        if needed is None or 'cross_section_dispersion_regime' in needed:
            csd_date = resolve_factor_date(date, global_lag, self.config.get('REGIME_LAG_DAYS'))
            factors['cross_section_dispersion_regime'] = self.calculate_cross_section_dispersion_regime(symbol, csd_date)
        if needed is None or 'correlation_regime_proxy' in needed:
            crp_date = resolve_factor_date(date, global_lag, self.config.get('REGIME_LAG_DAYS'))
            factors['correlation_regime_proxy'] = self.calculate_correlation_regime_proxy(symbol, crp_date)
        if needed is None or 'defensive_rotation_proxy' in needed:
            drp_date = resolve_factor_date(date, global_lag, self.config.get('REGIME_LAG_DAYS'))
            factors['defensive_rotation_proxy'] = self.calculate_defensive_rotation_proxy(symbol, drp_date)
        if needed is None or 'smallcap_seasonality_proxy' in needed:
            ssp_date = resolve_factor_date(date, global_lag, self.config.get('REGIME_LAG_DAYS'))
            factors['smallcap_seasonality_proxy'] = self.calculate_smallcap_seasonality_proxy(symbol, ssp_date)
        return factors

    def compute_signals(self, date: str, factor_weights: dict) -> pd.DataFrame:
        """
        Build cross-sectional signal on a rebalance date.
        Output columns: ['symbol','date','signal'] (+ optional factor columns)
        """
        universe = self.universe_builder.get_universe(date)
        if not universe:
            return pd.DataFrame(columns=['symbol', 'date', 'signal'])

        needed = {k for k, w in factor_weights.items() if w is not None and float(w) != 0.0}
        neutralize_cols = self.config.get('SIGNAL_NEUTRALIZE_COLS')
        if neutralize_cols is None:
            neutralize_cols = []
            if self.config.get('SIGNAL_NEUTRALIZE_SIZE'):
                neutralize_cols.append('size')
            if self.config.get('SIGNAL_NEUTRALIZE_BETA'):
                neutralize_cols.append('beta')
        if neutralize_cols:
            for c in neutralize_cols:
                needed.add(c)

        # Optional mainstream cross-sectional composite for single-factor runs.
        # This is mainly for v2 research baselines and is off by default.
        if len(needed) == 1 and 'quality' in needed and bool(self.config.get('QUALITY_MAINSTREAM_COMPOSITE', False)):
            qual_date = resolve_factor_date(date, self.config.get('FACTOR_LAG_DAYS', 0), self.config.get('QUALITY_LAG_DAYS'))
            q_weights = self.config.get('QUALITY_WEIGHTS') or {}
            df = self._build_mainstream_composite_signal(
                universe=universe,
                signal_date=date,
                factor_date=qual_date,
                weights=q_weights,
                kind='quality',
            )
            if len(df) > 0:
                rows = df.to_dict(orient='records')
            else:
                rows = []
        elif len(needed) == 1 and 'value' in needed and bool(self.config.get('VALUE_MAINSTREAM_COMPOSITE', False)):
            val_date = resolve_factor_date(date, self.config.get('FACTOR_LAG_DAYS', 0), self.config.get('VALUE_LAG_DAYS'))
            v_weights = self.config.get('VALUE_WEIGHTS') or {}
            df = self._build_mainstream_composite_signal(
                universe=universe,
                signal_date=date,
                factor_date=val_date,
                weights=v_weights,
                kind='value',
            )
            if len(df) > 0:
                rows = df.to_dict(orient='records')
            else:
                rows = []
        else:
            rows = []
            for sym in universe:
                f = self.calculate_all_factors(sym, date, needed=needed)

                sig = 0.0
                used = False
                for k, w in factor_weights.items():
                    if w is None or float(w) == 0.0:
                        continue
                    v = f.get(k, None)
                    if v is None or pd.isna(v):
                        continue
                    sig += float(w) * float(v)
                    used = True

                if not used:
                    continue

                row = {
                    "symbol": sym,
                    "date": date,
                    "signal": float(sig),
                    "pead": f.get("pead"),
                    "momentum": f.get("momentum"),
                    "reversal": f.get("reversal"),
                    "low_vol": f.get("low_vol"),
                    "size": f.get("size"),
                    "beta": f.get("beta"),
                    "quality": f.get("quality"),
                    "value": f.get("value"),
                    "turnover_shock": f.get("turnover_shock"),
                    "vol_regime": f.get("vol_regime"),
                    "quality_trend": f.get("quality_trend"),
                    "quality_component": f.get("quality_component"),
                    "value_component": f.get("value_component"),
                    "value_quality_blend": f.get("value_quality_blend"),
                    "profitability_minus_leverage": f.get("profitability_minus_leverage"),
                    "quality_metric_trend": f.get("quality_metric_trend"),
                    "value_metric_trend": f.get("value_metric_trend"),
                    "sue_eps_basic": f.get("sue_eps_basic"),
                    "sue_revenue_basic": f.get("sue_revenue_basic"),
                    "pead_short_window": f.get("pead_short_window"),
                    "institutional_ownership_change": f.get("institutional_ownership_change"),
                    "institutional_breadth_change": f.get("institutional_breadth_change"),
                    "owner_earnings_yield_proxy": f.get("owner_earnings_yield_proxy"),
                    "trend_tstat_126": f.get("trend_tstat_126"),
                    "high_52w_proximity": f.get("high_52w_proximity"),
                    "breakout_persistence": f.get("breakout_persistence"),
                    "pullback_in_uptrend": f.get("pullback_in_uptrend"),
                    "momentum_crash_adjusted": f.get("momentum_crash_adjusted"),
                    "overnight_drift_63": f.get("overnight_drift_63"),
                    "gap_fill_propensity": f.get("gap_fill_propensity"),
                    "amihud_illiquidity_20": f.get("amihud_illiquidity_20"),
                    "amihud_improving": f.get("amihud_improving"),
                    "dollar_volume_trend": f.get("dollar_volume_trend"),
                    "downside_vol_60": f.get("downside_vol_60"),
                    "left_tail_es5_126": f.get("left_tail_es5_126"),
                    "max_drawdown_126": f.get("max_drawdown_126"),
                    "low_beta_252": f.get("low_beta_252"),
                    "illiq_size_interaction": f.get("illiq_size_interaction"),
                    "liquidity_regime_score": f.get("liquidity_regime_score"),
                    "turnover_spike_decay": f.get("turnover_spike_decay"),
                    "crowding_turnover_x_inst": f.get("crowding_turnover_x_inst"),
                    "event_underreaction_low_own": f.get("event_underreaction_low_own"),
                    "event_underreaction_value_anchor": f.get("event_underreaction_value_anchor"),
                    "ownership_x_quality": f.get("ownership_x_quality"),
                    "ownership_x_value": f.get("ownership_x_value"),
                    "owner_earnings_trend": f.get("owner_earnings_trend"),
                    "de_crowding_momentum": f.get("de_crowding_momentum"),
                    "earnings_yield_ttm": f.get("earnings_yield_ttm"),
                    "fcf_yield_ttm": f.get("fcf_yield_ttm"),
                    "ebitda_ev_yield": f.get("ebitda_ev_yield"),
                    "value_composite_sector_neutral": f.get("value_composite_sector_neutral"),
                    "value_rerating_trend": f.get("value_rerating_trend"),
                    "roe_ttm": f.get("roe_ttm"),
                    "roa_ttm": f.get("roa_ttm"),
                    "gross_profitability_proxy": f.get("gross_profitability_proxy"),
                    "qmj_proxy_composite": f.get("qmj_proxy_composite"),
                    "sue_eps": f.get("sue_eps"),
                    "sue_revenue": f.get("sue_revenue"),
                    "pead_1_20": f.get("pead_1_20"),
                    "pead_21_60": f.get("pead_21_60"),
                    "earnings_gap_strength": f.get("earnings_gap_strength"),
                    "surprise_persistence": f.get("surprise_persistence"),
                    "beat_with_revenue_confirm": f.get("beat_with_revenue_confirm"),
                    "institutional_ownership_delta": f.get("institutional_ownership_delta"),
                    "institutional_breadth_delta": f.get("institutional_breadth_delta"),
                    "owner_earnings_yield": f.get("owner_earnings_yield"),
                    "low_vol_60": f.get("low_vol_60"),
                    "turnover_shock_20_120": f.get("turnover_shock_20_120"),
                    "cfo_to_assets": f.get("cfo_to_assets"),
                    "gross_margin_level": f.get("gross_margin_level"),
                    "deleveraging_quality": f.get("deleveraging_quality"),
                    "residual_mom_12_1": f.get("residual_mom_12_1"),
                    "range_followthrough": f.get("range_followthrough"),
                    "st_reversal_liquidity_filtered": f.get("st_reversal_liquidity_filtered"),
                    "post_spike_cooldown": f.get("post_spike_cooldown"),
                    "overreaction_volume_adjusted": f.get("overreaction_volume_adjusted"),
                    "failed_breakout_reversal": f.get("failed_breakout_reversal"),
                    "compression_reversal": f.get("compression_reversal"),
                    "skew_reversal": f.get("skew_reversal"),
                    "three_red_days_rebound": f.get("three_red_days_rebound"),
                    "large_gap_reversal": f.get("large_gap_reversal"),
                    "flow_autocorr_20": f.get("flow_autocorr_20"),
                    "spread_proxy_stability": f.get("spread_proxy_stability"),
                    "vol_of_vol_126": f.get("vol_of_vol_126"),
                    "jump_risk_proxy": f.get("jump_risk_proxy"),
                    "trend_regime_switch": f.get("trend_regime_switch"),
                    "vol_regime_switch": f.get("vol_regime_switch"),
                    "liquidity_regime_switch": f.get("liquidity_regime_switch"),
                    "earnings_season_alpha": f.get("earnings_season_alpha"),
                    "state_weighted_meta_signal": f.get("state_weighted_meta_signal"),
                }
                rows.append(row)

        if not rows:
            return pd.DataFrame(columns=['symbol', 'date', 'signal'])

        df = pd.DataFrame(rows)

        # Optional combo-level formula overrides (mainly for value+momentum research).
        combo_formula = str(self.config.get("COMBO_FORMULA", "linear")).lower()
        if combo_formula != "linear":
            v = pd.to_numeric(df.get("value"), errors="coerce")
            m = pd.to_numeric(df.get("momentum"), errors="coerce")
            v_z = self._zscore_series(v)
            m_z = self._zscore_series(m)

            if combo_formula in ("value_momentum_gated", "gated_value_momentum", "gated"):
                gate_k = float(self.config.get("COMBO_GATE_K", 0.25))
                gate_clip = float(self.config.get("COMBO_GATE_CLIP", 1.0))
                gate = 1.0 + gate_k * m_z.clip(lower=-gate_clip, upper=gate_clip)
                df["signal"] = v_z * gate
            elif combo_formula in ("value_momentum_two_stage", "two_stage"):
                value_keep_q = float(self.config.get("COMBO_VALUE_KEEP_Q", 0.50))
                mom_drop_q = float(self.config.get("COMBO_MOM_DROP_Q", 0.30))
                value_keep_q = min(max(value_keep_q, 0.01), 0.99)
                mom_drop_q = min(max(mom_drop_q, 0.00), 0.95)

                keep_threshold = v_z.quantile(1.0 - value_keep_q)
                keep_mask = v_z >= keep_threshold
                if keep_mask.any():
                    mom_cut = m_z[keep_mask].quantile(mom_drop_q)
                    keep_mask = keep_mask & (m_z >= mom_cut)
                df["signal"] = v_z.where(keep_mask)

        # Drop NaN signals
        df = df.dropna(subset=["signal"])
        if len(df) == 0:
            return pd.DataFrame(columns=['symbol', 'date', 'signal'])

        use_signal_z = bool(self.config.get('SIGNAL_ZSCORE', False))
        use_signal_rank = bool(self.config.get('SIGNAL_RANK', True))
        if not use_signal_z:
            only_mom = all((k == 'momentum' or float(w) == 0.0) for k, w in factor_weights.items())
            use_signal_z = bool(self.config.get('MOMENTUM_ZSCORE', False)) and only_mom

        if use_signal_z or use_signal_rank:
            use_industry = bool(self.industry_neutral) and bool(self.industry_map)
            only_mom = all((k == 'momentum' or float(w) == 0.0) for k, w in factor_weights.items())

            winsor_z = self.config.get('SIGNAL_WINSOR_Z')
            if winsor_z is None and only_mom:
                winsor_z = self.config.get('MOMENTUM_WINSOR_Z')
            winsor_pct_low = self.config.get('SIGNAL_WINSOR_PCT_LOW')
            winsor_pct_high = self.config.get('SIGNAL_WINSOR_PCT_HIGH')
            if (winsor_pct_low is None or winsor_pct_high is None) and use_signal_rank:
                winsor_pct_low = 0.01
                winsor_pct_high = 0.99

            df = standardize_signal(
                df,
                value_col="signal",
                use_zscore=use_signal_z,
                use_rank=use_signal_rank,
                rank_method=str(self.config.get('SIGNAL_RANK_METHOD', 'average')),
                rank_pct=bool(self.config.get('SIGNAL_RANK_PCT', True)),
                winsor_z=winsor_z,
                winsor_pct_low=winsor_pct_low,
                winsor_pct_high=winsor_pct_high,
                industry_neutral=use_industry,
                industry_map=self.industry_map,
                industry_col=self.industry_col or "industry",
                industry_min_group=self.industry_min_group,
                neutralize_cols=neutralize_cols,
                missing_policy=str(self.config.get('SIGNAL_MISSING_POLICY', 'drop')),
                fill_value=self.config.get('SIGNAL_MISSING_FILL'),
            )
        if bool(self.config.get('SIGNALS_INCLUDE_FACTORS', False)):
            cols = ["symbol", "date", "signal"]
            for c in [
                "pead",
                "momentum",
                "reversal",
                "low_vol",
                "size",
                "beta",
                "quality",
                "value",
                "turnover_shock",
                "vol_regime",
                "quality_trend",
                "quality_component",
                "value_component",
                "value_quality_blend",
                "profitability_minus_leverage",
                "quality_metric_trend",
                "value_metric_trend",
                "sue_eps_basic",
                "sue_revenue_basic",
                "pead_short_window",
                "institutional_ownership_change",
                "institutional_breadth_change",
                "owner_earnings_yield_proxy",
                "trend_tstat_126",
                "high_52w_proximity",
                "breakout_persistence",
                "pullback_in_uptrend",
                "momentum_crash_adjusted",
                "overnight_drift_63",
                "gap_fill_propensity",
                "amihud_illiquidity_20",
                "amihud_improving",
                "dollar_volume_trend",
                "downside_vol_60",
                "left_tail_es5_126",
                "max_drawdown_126",
                "low_beta_252",
                "illiq_size_interaction",
                "liquidity_regime_score",
                "turnover_spike_decay",
                "crowding_turnover_x_inst",
                "event_underreaction_low_own",
                "event_underreaction_value_anchor",
                "ownership_x_quality",
                "ownership_x_value",
                "owner_earnings_trend",
                "de_crowding_momentum",
                "earnings_yield_ttm",
                "fcf_yield_ttm",
                "ebitda_ev_yield",
                "value_composite_sector_neutral",
                "value_rerating_trend",
                "roe_ttm",
                "roa_ttm",
                "gross_profitability_proxy",
                "qmj_proxy_composite",
                "sue_eps",
                "sue_revenue",
                "pead_1_20",
                "pead_21_60",
                "earnings_gap_strength",
                "surprise_persistence",
                "beat_with_revenue_confirm",
                "institutional_ownership_delta",
                "institutional_breadth_delta",
                "owner_earnings_yield",
                "low_vol_60",
                "turnover_shock_20_120",
                "cfo_to_assets",
                "gross_margin_level",
                "deleveraging_quality",
                "residual_mom_12_1",
                "range_followthrough",
                "st_reversal_liquidity_filtered",
                "post_spike_cooldown",
                "overreaction_volume_adjusted",
                "failed_breakout_reversal",
                "compression_reversal",
                "skew_reversal",
                "three_red_days_rebound",
                "large_gap_reversal",
                "flow_autocorr_20",
                "spread_proxy_stability",
                "vol_of_vol_126",
                "jump_risk_proxy",
                "trend_regime_switch",
                "vol_regime_switch",
                "liquidity_regime_switch",
                "earnings_season_alpha",
                "state_weighted_meta_signal",
            ]:
                if c in df.columns:
                    cols.append(c)
            return df[cols].reset_index(drop=True)
        return df[['symbol', 'date', 'signal']].reset_index(drop=True)

    def build_positions(self, signals_df: pd.DataFrame, long_pct: float = 0.2, short_pct: float = 0.0) -> pd.DataFrame:
        """
        Convert signals to positions.
        Output columns: ['symbol','date','position']
        """
        if signals_df is None or len(signals_df) == 0:
            return pd.DataFrame(columns=['symbol', 'date', 'position'])

        df = signals_df[['symbol', 'date', 'signal']].copy()
        df = df.dropna(subset=['signal'])

        if len(df) == 0:
            return pd.DataFrame(columns=['symbol', 'date', 'position'])

        df = df.sort_values('signal', ascending=False).reset_index(drop=True)
        n = len(df)

        n_long = int(np.floor(n * float(long_pct))) if long_pct and long_pct > 0 else 0
        n_short = int(np.floor(n * float(short_pct))) if short_pct and short_pct > 0 else 0

        # At least 1 long if long_pct>0 and there is data
        if n_long == 0 and long_pct and long_pct > 0 and n > 0:
            n_long = 1

        df['position'] = 0
        if n_long > 0:
            df.loc[:n_long - 1, 'position'] = 1
        if n_short > 0:
            df.loc[n - n_short:, 'position'] = -1

        return df[['symbol', 'date', 'position']].reset_index(drop=True)
