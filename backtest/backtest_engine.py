import hashlib
import json
import os
from pathlib import Path
import pandas as pd
import numpy as np

from .data_engine import DataEngine
from .factor_engine import FactorEngine
from .universe_builder import UniverseBuilder
from .execution_simulator import ExecutionSimulator
from .market_cap_engine import MarketCapEngine


class BacktestEngine:
    def __init__(self, config_dict):
        self.config = config_dict
        # DataEngine init (explicit args)
        self.data_engine = DataEngine(
            config_dict.get('PRICE_DIR_ACTIVE'),
            config_dict.get('PRICE_DIR_DELISTED'),
            config_dict.get('DELISTED_INFO')
        )
        market_cap_engine = None
        mc_dir = config_dict.get('MARKET_CAP_DIR')
        if mc_dir and os.path.isdir(mc_dir):
            has_csv = any(f.endswith('.csv') for f in os.listdir(mc_dir))
            if has_csv:
                market_cap_engine = MarketCapEngine(
                    mc_dir,
                    strict=bool(config_dict.get('MARKET_CAP_STRICT', True))
                )

        self.universe_builder = UniverseBuilder(
            self.data_engine,
            min_market_cap=config_dict.get('MIN_MARKET_CAP', 500e6),
            min_dollar_volume=config_dict.get('MIN_DOLLAR_VOLUME', 1e6),
            min_price=config_dict.get('MIN_PRICE', 5.0),
            market_cap_engine=market_cap_engine,
            market_cap_strict=bool(config_dict.get('MARKET_CAP_STRICT', True))
        )
        self.factor_engine = FactorEngine(self.data_engine, self.universe_builder, config_dict)
        self.execution_simulator = ExecutionSimulator(
            self.data_engine,
            transaction_cost=config_dict.get('TRANSACTION_COST', 0.0020),
            execution_delay=config_dict.get('EXECUTION_DELAY', 1),
            execution_use_trading_days=bool(config_dict.get('EXECUTION_USE_TRADING_DAYS', False)),
            enable_dynamic_cost=bool(config_dict.get('ENABLE_DYNAMIC_COST', False)),
            cost_multiplier=config_dict.get('COST_MULTIPLIER', 1.0),
            trade_size_usd=config_dict.get('TRADE_SIZE_USD', 10000),
            apply_limit_up_down=bool(config_dict.get('APPLY_LIMIT_UP_DOWN', False)),
            limit_up_down_pct=config_dict.get('LIMIT_UP_DOWN_PCT', 0.1),
            apply_stamp_tax=bool(config_dict.get('APPLY_STAMP_TAX', False)),
            stamp_tax_rate=config_dict.get('STAMP_TAX_RATE', 0.001),
        )
        self.last_rebalance_dates = []
        self._signal_cache_dir = self.config.get('SIGNAL_CACHE_DIR')
        self._signal_cache_use = bool(self.config.get('SIGNAL_CACHE_USE', False))
        self._signal_cache_refresh = bool(self.config.get('SIGNAL_CACHE_REFRESH', False))
        self._signal_cache_sig = None

    def _smooth_signals(self, signals_df: pd.DataFrame, history: dict) -> pd.DataFrame:
        window = int(self.config.get('SIGNAL_SMOOTH_WINDOW', 0) or 0)
        method = str(self.config.get('SIGNAL_SMOOTH_METHOD', 'sma')).lower()
        alpha = self.config.get('SIGNAL_SMOOTH_ALPHA')

        if window <= 1 and method != 'ema':
            return signals_df

        if method == 'ema' and (alpha is None or alpha <= 0 or alpha >= 1):
            # Default EMA alpha if not provided
            if window and window > 1:
                alpha = 2.0 / (window + 1.0)
            else:
                alpha = 0.2

        smoothed = []
        for _, row in signals_df.iterrows():
            sym = row['symbol']
            sig = row['signal']
            if pd.isna(sig):
                smoothed.append(sig)
                continue

            if method == 'ema':
                prev = history.get(sym)
                val = sig if prev is None else (alpha * sig + (1 - alpha) * prev)
                history[sym] = val
                smoothed.append(val)
            else:
                buf = history.get(sym, [])
                buf.append(sig)
                if window and len(buf) > window:
                    buf = buf[-window:]
                history[sym] = buf
                smoothed.append(float(np.mean(buf)))

        out = signals_df.copy()
        out['signal'] = smoothed
        return out

    def _get_trading_calendar(self, start_date: str, end_date: str) -> pd.DatetimeIndex:
        """
        Build a trading calendar from an existing liquid symbol in your price cache.
        Fallback order:
          1) config['CALENDAR_SYMBOL'] if exists
          2) SPY if exists in your data
          3) first universe symbol at start_date
        """
        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)

        candidates = []
        cal_sym = self.config.get('CALENDAR_SYMBOL')
        if cal_sym:
            candidates.append(cal_sym)
        candidates.append('SPY')

        # Try the candidates
        for sym in candidates:
            df = self.data_engine.get_price(sym, start_date=start_date, end_date=end_date)
            if df is not None and len(df) > 10:
                dates = pd.to_datetime(df['date']).sort_values().unique()
                return pd.DatetimeIndex(dates)

        # Fallback: pick one symbol from universe
        uni = self.universe_builder.get_universe(start_date)
        if not uni:
            # Last fallback: business days (least preferred)
            return pd.bdate_range(start=start_ts, end=end_ts)

        sym = uni[0]
        df = self.data_engine.get_price(sym, start_date=start_date, end_date=end_date)
        if df is None or len(df) == 0:
            return pd.bdate_range(start=start_ts, end=end_ts)

        dates = pd.to_datetime(df['date']).sort_values().unique()
        return pd.DatetimeIndex(dates)

    def _generate_rebalance_dates(self, start_date: str, end_date: str, rebalance_freq: int) -> list[str]:
        """
        Generate rebalance dates by stepping through the trading calendar (NOT calendar days).
        """
        cal = self._get_trading_calendar(start_date, end_date)
        if len(cal) == 0:
            return []
        # Ensure within bounds
        cal = cal[(cal >= pd.Timestamp(start_date)) & (cal <= pd.Timestamp(end_date))]
        if len(cal) == 0:
            return []

        mode = str(self.config.get('REBALANCE_MODE') or '').lower().strip()
        if mode == 'month_end':
            cal_df = pd.DataFrame({'date': cal})
            cal_df['month'] = cal_df['date'].dt.to_period('M')
            month_ends = cal_df.groupby('month')['date'].max().sort_values()
            if rebalance_freq and int(rebalance_freq) > 1:
                month_ends = month_ends.iloc[::int(rebalance_freq)]
            return [d.strftime('%Y-%m-%d') for d in month_ends]

        # Step every N trading days
        idx = list(range(0, len(cal), rebalance_freq))
        reb = cal[idx]
        return [d.strftime('%Y-%m-%d') for d in reb]

    def _stable_hash(self, obj) -> str:
        payload = json.dumps(obj, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.md5(payload.encode("utf-8")).hexdigest()

    def _cache_signature(self) -> str:
        if self._signal_cache_sig:
            return self._signal_cache_sig
        # Include full config so cache invalidates automatically if Stage2 rules change.
        self._signal_cache_sig = self._stable_hash(self.config)
        return self._signal_cache_sig

    def _signal_cache_path(self, date: str, factor_weights: dict) -> Path:
        cache_root = Path(self._signal_cache_dir).expanduser().resolve()
        sig = self._cache_signature()
        w_sig = self._stable_hash(factor_weights)
        safe_date = str(date).replace("-", "")
        return cache_root / sig / f"{safe_date}_{w_sig}.pkl"

    def _read_signal_cache(self, date: str, factor_weights: dict):
        if not self._signal_cache_use or not self._signal_cache_dir:
            return None
        path = self._signal_cache_path(date, factor_weights)
        if not path.exists():
            return None
        try:
            df = pd.read_pickle(path)
        except Exception:
            return None
        if df is None or len(df) == 0:
            return pd.DataFrame(columns=['symbol', 'date', 'signal'])
        need = {'symbol', 'date', 'signal'}
        if not need.issubset(df.columns):
            return None
        return df

    def _write_signal_cache(self, date: str, factor_weights: dict, signals_df: pd.DataFrame) -> None:
        if not self._signal_cache_use or not self._signal_cache_dir:
            return
        path = self._signal_cache_path(date, factor_weights)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            signals_df.to_pickle(path)
        except Exception:
            pass

    def _compute_signals_cached(self, date: str, factor_weights: dict) -> pd.DataFrame:
        if self._signal_cache_use and not self._signal_cache_refresh:
            cached = self._read_signal_cache(date, factor_weights)
            if cached is not None:
                return cached
        signals_df = self.factor_engine.compute_signals(date, factor_weights)
        if signals_df is None:
            signals_df = pd.DataFrame(columns=['symbol', 'date', 'signal'])
        self._write_signal_cache(date, factor_weights, signals_df)
        return signals_df

    def run_backtest(self,
                    start_date: str,
                    end_date: str,
                    factor_weights: dict,
                    rebalance_freq: int = 5,
                    holding_period: int = 10,
                    long_pct: float = 0.2,
                    short_pct: float = 0.0):

        # 1) Rebalance dates (TRADING-CALENDAR based)
        rebalance_dates = self._generate_rebalance_dates(start_date, end_date, rebalance_freq)
        self.last_rebalance_dates = rebalance_dates
        # Sync execution simulator calendar for trading-day execution (if enabled)
        try:
            cal = self._get_trading_calendar(start_date, end_date)
            self.execution_simulator.set_trading_calendar(cal)
        except Exception:
            pass

        all_signals = []
        all_positions = []
        signal_history = {}

        for d in rebalance_dates:
            signals_df = self._compute_signals_cached(d, factor_weights)
            if signals_df is None or len(signals_df) == 0:
                continue
            signals_df = self._smooth_signals(signals_df, signal_history)
            all_signals.append(signals_df)

            # Rank & pick positions inside factor engine / portfolio logic
            positions_df = self.factor_engine.build_positions(
                signals_df,
                long_pct=long_pct,
                short_pct=short_pct
            )
            if positions_df is None or len(positions_df) == 0:
                continue
            all_positions.append(positions_df)

        if len(all_signals) == 0:
            signals_df = pd.DataFrame(columns=['symbol', 'date', 'signal'])
        else:
            signals_df = pd.concat(all_signals, ignore_index=True)

        if len(all_positions) == 0:
            positions_df = pd.DataFrame(columns=['symbol', 'date', 'position'])
        else:
            positions_df = pd.concat(all_positions, ignore_index=True)

        # 2) Execute + returns
        executed = self.execution_simulator.execute_trades(positions_df)
        returns_df = self.execution_simulator.calculate_returns(executed, holding_period=holding_period)
        forward_returns_df = self.execution_simulator.calculate_forward_returns(
            signals_df,
            holding_period=holding_period,
            apply_quality_filter=True
        )
        forward_returns_raw_df = self.execution_simulator.calculate_forward_returns(
            signals_df,
            holding_period=holding_period,
            apply_quality_filter=False
        )

        analysis = {
            'ic': None,
            'ic_yearly': None,
            'ic_positions': None,
            'ic_yearly_positions': None
        }

        # IC on full signal cross-section (preferred)
        if len(signals_df) > 0 and len(forward_returns_df) > 0:
            merged = signals_df.merge(
                forward_returns_df[['symbol', 'signal_date', 'return']],
                left_on=['symbol', 'date'],
                right_on=['symbol', 'signal_date'],
                how='inner'
            )
            if len(merged) > 3:
                merged = merged.replace([np.inf, -np.inf], np.nan)
                merged = merged.dropna(subset=['signal', 'return'])
                if len(merged) > 3:
                    analysis['ic'] = merged['signal'].corr(merged['return'])

                merged['date_dt'] = pd.to_datetime(merged['date'])
                def _safe_corr(x):
                    if len(x) < 5:
                        return np.nan
                    return x['signal'].corr(x['return'])
                ic_y = merged.groupby(merged['date_dt'].dt.year).apply(_safe_corr).dropna()
                if len(ic_y) > 0:
                    analysis['ic_yearly'] = pd.DataFrame({
                        'period': ic_y.index.astype(str),
                        'ic': ic_y.values,
                        'n': merged.groupby(merged['date_dt'].dt.year).size().reindex(ic_y.index).values
                    })

        # IC on raw forward returns (no quality filter)
        if len(signals_df) > 0 and len(forward_returns_raw_df) > 0:
            merged_raw = signals_df.merge(
                forward_returns_raw_df[['symbol', 'signal_date', 'return']],
                left_on=['symbol', 'date'],
                right_on=['symbol', 'signal_date'],
                how='inner'
            )
            if len(merged_raw) > 3:
                merged_raw = merged_raw.replace([np.inf, -np.inf], np.nan)
                merged_raw = merged_raw.dropna(subset=['signal', 'return'])
                if len(merged_raw) > 3:
                    analysis['ic_raw'] = merged_raw['signal'].corr(merged_raw['return'])

        # IC on executed positions (legacy)
        if len(signals_df) > 0 and len(returns_df) > 0:
            merged = signals_df.merge(
                returns_df[['symbol', 'signal_date', 'return']],
                left_on=['symbol', 'date'],
                right_on=['symbol', 'signal_date'],
                how='inner'
            )
            if len(merged) > 3:
                merged = merged.replace([np.inf, -np.inf], np.nan)
                merged = merged.dropna(subset=['signal', 'return'])
                if len(merged) > 3:
                    analysis['ic_positions'] = merged['signal'].corr(merged['return'])

                merged['date_dt'] = pd.to_datetime(merged['date'])
                def _safe_corr_pos(x):
                    if len(x) < 5:
                        return np.nan
                    return x['signal'].corr(x['return'])
                ic_y = merged.groupby(merged['date_dt'].dt.year).apply(_safe_corr_pos).dropna()
                if len(ic_y) > 0:
                    analysis['ic_yearly_positions'] = pd.DataFrame({
                        'period': ic_y.index.astype(str),
                        'ic': ic_y.values,
                        'n': merged.groupby(merged['date_dt'].dt.year).size().reindex(ic_y.index).values
                    })

        # Filter stats
        filter_stats = self.execution_simulator.get_filter_stats()

        return {
            'signals': signals_df,
            'positions': positions_df,
            'returns': returns_df,
            'forward_returns': forward_returns_df,
            'forward_returns_raw': forward_returns_raw_df,
            'analysis': analysis,
            'rebalance_dates': rebalance_dates,
            'filter_stats': filter_stats
        }

    def run_out_of_sample_test(self, train_start, train_end, test_start, test_end,
                               factor_weights, rebalance_freq, holding_period,
                               long_pct=0.2, short_pct=0.0):
        train = self.run_backtest(train_start, train_end, factor_weights, rebalance_freq, holding_period, long_pct, short_pct)
        test = self.run_backtest(test_start, test_end, factor_weights, rebalance_freq, holding_period, long_pct, short_pct)

        train_ic = train['analysis'].get('ic')
        test_ic = test['analysis'].get('ic')

        # Keep backward compatible structure
        return {
            'train': train,
            'test': test,
            'oos_analysis': {
                'train_ic': float(train_ic) if train_ic is not None and not np.isnan(train_ic) else None,
                'test_ic': float(test_ic) if test_ic is not None and not np.isnan(test_ic) else None,
                'train_n': int(len(train['returns'])),
                'test_n': int(len(test['returns'])),
            }
        }
