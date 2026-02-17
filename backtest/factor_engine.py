"""
Factor Engine with Advanced SUE-based PEAD
Adds:
  - compute_signals(date, factor_weights)
  - build_positions(signals_df, long_pct, short_pct)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Iterable

from .data_engine import DataEngine
from .universe_builder import UniverseBuilder
from .fundamentals_engine import FundamentalsEngine
from .value_fundamentals_engine import ValueFundamentalsEngine
from . import pead_factor_cached
from .factor_factory import standardize_signal, resolve_factor_date
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
                if v is None or (isinstance(v, float) and np.isnan(v)):
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
        score = 0.0
        wsum = 0.0
        transform_mode = self.config.get("QUALITY_COMPONENT_TRANSFORM", "signed_log")
        for k, w in weights.items():
            v = metrics.get(k)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                continue
            wf = float(w)
            vf = self._transform_component(float(v), transform_mode)
            score += wf * vf
            wsum += abs(wf)
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
        score = 0.0
        wsum = 0.0
        transform_mode = self.config.get("VALUE_COMPONENT_TRANSFORM", "signed_log")
        for k, w in weights.items():
            v = metrics.get(k)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                continue
            wf = float(w)
            vf = self._transform_component(float(v), transform_mode)
            score += wf * vf
            wsum += abs(wf)
        if wsum <= 0:
            return None
        return float(score / wsum)

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
                    if v is None or (isinstance(v, float) and np.isnan(v)):
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
            for c in ["pead", "momentum", "reversal", "low_vol", "size", "beta", "quality", "value"]:
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
