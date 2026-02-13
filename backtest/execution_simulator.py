import pandas as pd
import numpy as np
from typing import Optional

from .data_engine import DataEngine
from .data_quality_filter import DataQualityFilter
from .delisting_handler import DelistingHandler
from .cost_model import CostModel


class ExecutionSimulator:
    def __init__(self,
                 data_engine: DataEngine,
                 transaction_cost: float = 0.0020,
                 execution_delay: int = 1,
                 execution_use_trading_days: bool = False,
                 trading_calendar: Optional[pd.DatetimeIndex] = None,
                 enable_quality_filter: bool = True,
                 enable_smart_delisting: bool = True,
                 enable_dynamic_cost: bool = False,
                 cost_multiplier: float = 1.0,
                 trade_size_usd: float = 10000,
                 apply_limit_up_down: bool = False,
                 limit_up_down_pct: float = 0.1,
                 apply_stamp_tax: bool = False,
                 stamp_tax_rate: float = 0.001):

        self.data_engine = data_engine
        self.base_cost = transaction_cost
        self.cost_multiplier = float(cost_multiplier) if cost_multiplier is not None else 1.0
        self.apply_limit_up_down = bool(apply_limit_up_down)
        self.limit_up_down_pct = float(limit_up_down_pct) if limit_up_down_pct is not None else 0.1
        self.apply_stamp_tax = bool(apply_stamp_tax)
        self.stamp_tax_rate = float(stamp_tax_rate) if stamp_tax_rate is not None else 0.001
        self.execution_delay = execution_delay
        self.execution_use_trading_days = bool(execution_use_trading_days)
        self.trade_size_usd = float(trade_size_usd) if trade_size_usd is not None else 10000.0
        self._trading_calendar = None
        self._trading_index = None
        if trading_calendar is not None:
            self.set_trading_calendar(trading_calendar)

        self.quality_filter = DataQualityFilter() if enable_quality_filter else None
        self.delisting_handler = DelistingHandler() if enable_smart_delisting else None
        base_cost = float(transaction_cost) * self.cost_multiplier
        self.cost_model = CostModel(base_cost=base_cost) if enable_dynamic_cost else None

        self.volatility_cache = {}

        # Categorized counters
        self.filter_stats = {
            # Execution-related calls (apply_cost=True)
            'execution_price_calls': 0,
            'quality_filter_dropped': 0,
            'no_price_data': 0,
            'no_trade_date_found': 0,
            'limit_up_down_blocked': 0,

            'entry_sanity_dropped': 0,
            'exit_sanity_dropped': 0,

            # Auxiliary calls (apply_cost=False or volatility)
            'aux_volatility_calls': 0,
            'aux_data_calls': 0,

            # Cost diagnostics
            'pct_of_volume_sum': 0.0,
            'pct_of_volume_count': 0,
        }

    def set_trading_calendar(self, calendar: pd.DatetimeIndex):
        if calendar is None or len(calendar) == 0:
            self._trading_calendar = None
            self._trading_index = None
            return
        cal = pd.DatetimeIndex(pd.to_datetime(calendar)).sort_values().unique()
        self._trading_calendar = cal
        self._trading_index = pd.DatetimeIndex(cal)

    def _shift_date(self, base_date: pd.Timestamp, n_days: int) -> pd.Timestamp:
        if not self.execution_use_trading_days or self._trading_index is None:
            return base_date + pd.Timedelta(days=int(n_days))

        cal = self._trading_index
        base = pd.Timestamp(base_date)
        # Use next trading date if base is not a trading day
        pos = cal.searchsorted(base)
        if pos >= len(cal):
            return cal[-1]
        if cal[pos] != base and pos < len(cal):
            base_pos = pos
        else:
            base_pos = pos

        target = base_pos + int(n_days)
        if target < 0:
            target = 0
        if target >= len(cal):
            target = len(cal) - 1
        return cal[target]

    def _get_volatility(self, symbol: str, end_date: pd.Timestamp) -> float:
        self.filter_stats['aux_volatility_calls'] += 1

        key = f"{symbol}_{end_date.strftime('%Y-%m-%d')}"
        if key in self.volatility_cache:
            return self.volatility_cache[key]

        start_date = (end_date - pd.Timedelta(days=90)).strftime('%Y-%m-%d')
        hist = self.data_engine.get_price(symbol, start_date=start_date, end_date=end_date.strftime('%Y-%m-%d'))

        if hist is not None and len(hist) > 20:
            hist = hist.copy()
            hist['ret'] = hist['close'].pct_change()
            vol = hist.tail(60)['ret'].std()
            if pd.isna(vol) or vol <= 0:
                vol = 0.02
        else:
            vol = 0.02

        self.volatility_cache[key] = float(vol)
        return float(vol)

    def get_execution_price(self,
                            symbol: str,
                            signal_date: str,
                            side: str = 'buy',
                            apply_cost: bool = True,
                            apply_quality_filter: bool = True) -> Optional[float]:

        # Count calls
        if apply_cost:
            self.filter_stats['execution_price_calls'] += 1
        else:
            self.filter_stats['aux_data_calls'] += 1

        execution_date = self._shift_date(pd.Timestamp(signal_date), self.execution_delay)

        start_date = (execution_date - pd.Timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = (execution_date + pd.Timedelta(days=5)).strftime('%Y-%m-%d')

        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=end_date)
        if df is None or len(df) == 0:
            self.filter_stats['no_price_data'] += 1
            return None

        # Quality filter
        if apply_quality_filter and self.quality_filter and not self.quality_filter.validate_price_data(df, symbol):
            if apply_cost:
                self.filter_stats['quality_filter_dropped'] += 1
            return None

        df = df[df['date'] >= execution_date]
        if len(df) == 0:
            self.filter_stats['no_trade_date_found'] += 1
            return None

        row = df.iloc[0]
        base_price = row['open'] if 'open' in df.columns else row['close']
        if base_price is None or pd.isna(base_price) or base_price <= 0:
            return None

        if self.apply_limit_up_down:
            prev = df[df['date'] < execution_date]
            if len(prev) > 0 and 'close' in prev.columns:
                prev_close = prev.iloc[-1]['close']
                if prev_close is not None and not pd.isna(prev_close) and prev_close > 0:
                    up_limit = float(prev_close) * (1 + float(self.limit_up_down_pct))
                    down_limit = float(prev_close) * (1 - float(self.limit_up_down_pct))
                    if side == 'buy' and float(base_price) >= up_limit:
                        if apply_cost:
                            self.filter_stats['limit_up_down_blocked'] += 1
                        return None
                    if side == 'sell' and float(base_price) <= down_limit:
                        if apply_cost:
                            self.filter_stats['limit_up_down_blocked'] += 1
                        return None

        if not apply_cost:
            return float(base_price)

        # Cost
        if self.cost_model:
            volume = row.get('volume', 0)
            vol = self._get_volatility(symbol, execution_date)
            cost = self.cost_model.calculate_cost(
                price=float(base_price),
                volume=float(volume),
                volatility=float(vol),
                trade_size_usd=float(self.trade_size_usd)
            )
            dollar_volume = float(base_price) * float(volume) if volume is not None else 0.0
            if dollar_volume > 0:
                pct = float(self.trade_size_usd) / dollar_volume
                self.filter_stats['pct_of_volume_sum'] += float(pct)
                self.filter_stats['pct_of_volume_count'] += 1
        else:
            cost = self.base_cost * self.cost_multiplier

        if side == 'buy':
            return float(base_price) * (1 + float(cost))
        else:
            if self.apply_stamp_tax:
                cost = float(cost) + float(self.stamp_tax_rate)
            return float(base_price) * (1 - float(cost))

    def execute_trades(self, positions_df: pd.DataFrame) -> pd.DataFrame:
        results = []
        if positions_df is None or len(positions_df) == 0:
            return pd.DataFrame(results)

        for _, row in positions_df.iterrows():
            symbol = row['symbol']
            signal_date = row['date']
            position = row['position']
            if position == 0:
                continue

            side = 'buy' if position > 0 else 'sell'
            px = self.get_execution_price(symbol, signal_date, side=side, apply_cost=True)
            if px is None:
                continue

            results.append({
                'symbol': symbol,
                'signal_date': signal_date,
                'position': position,
                'execution_price': px,
                'executed': True
            })

        return pd.DataFrame(results)

    def calculate_returns(self, executed_trades: pd.DataFrame, holding_period: int = 10) -> pd.DataFrame:
        results = []
        if executed_trades is None or len(executed_trades) == 0:
            return pd.DataFrame(results)

        for _, tr in executed_trades.iterrows():
            symbol = tr['symbol']
            signal_date = tr['signal_date']
            entry = float(tr['execution_price'])  # includes entry cost
            position = tr['position']

            # Entry sanity
            if entry < 1.0 or entry > 10000:
                self.filter_stats['entry_sanity_dropped'] += 1
                continue

            exit_date = self._shift_date(pd.Timestamp(signal_date), holding_period + self.execution_delay)
            exit_signal_date = self._shift_date(exit_date, -self.execution_delay)

            exit_px = self.get_execution_price(
                symbol,
                exit_signal_date.strftime('%Y-%m-%d'),
                side='sell' if position > 0 else 'buy',
                apply_cost=True
            )

            # Normal exit
            if exit_px is not None and not pd.isna(exit_px) and exit_px > 0:
                if exit_px < 0.1 or exit_px > 10000:
                    self.filter_stats['exit_sanity_dropped'] += 1
                    continue
                exit_type = 'normal'
            else:
                # Delisted/no data path
                exit_type = 'no_data'
                if self.delisting_handler:
                    last_raw = self.get_execution_price(
                        symbol,
                        exit_date.strftime('%Y-%m-%d'),
                        side='sell',
                        apply_cost=False
                    )
                    if last_raw is not None and last_raw > 0:
                        r = self.delisting_handler.estimate_delisting_return(
                            symbol=symbol,
                            entry_price=entry,
                            last_price=float(last_raw),
                            position=position,
                            delisting_reason=None
                        )
                        r = max(min(float(r), 1.0), -0.95)
                        results.append({
                            'symbol': symbol,
                            'signal_date': signal_date,
                            'entry_price': entry,
                            'exit_price': float(last_raw),
                            'position': position,
                            'return': r,
                            'holding_period': holding_period,
                            'exit_type': 'delisted'
                        })
                        continue

                # Conservative fallback
                r = -0.5
                results.append({
                    'symbol': symbol,
                    'signal_date': signal_date,
                    'entry_price': entry,
                    'exit_price': None,
                    'position': position,
                    'return': float(r),
                    'holding_period': holding_period,
                    'exit_type': exit_type
                })
                continue

            # Return
            if position > 0:
                r = (float(exit_px) - entry) / entry
            else:
                r = (entry - float(exit_px)) / entry

            r = max(min(float(r), 1.0), -0.95)

            results.append({
                'symbol': symbol,
                'signal_date': signal_date,
                'entry_price': entry,
                'exit_price': float(exit_px),
                'position': position,
                'return': r,
                'holding_period': holding_period,
                'exit_type': exit_type
            })

        return pd.DataFrame(results)

    def calculate_forward_returns(self,
                                  signals_df: pd.DataFrame,
                                  holding_period: int = 10,
                                  apply_quality_filter: bool = True) -> pd.DataFrame:
        """
        Compute forward returns for the full signal cross-section (no position filtering).
        Uses execution_delay and holding_period, but does NOT apply transaction costs.
        """
        results = []
        if signals_df is None or len(signals_df) == 0:
            return pd.DataFrame(columns=[
                'symbol', 'signal_date', 'entry_price', 'exit_price',
                'position', 'return', 'holding_period', 'exit_type', 'method'
            ])

        for _, row in signals_df.iterrows():
            symbol = row['symbol']
            signal_date = row['date']

            entry = self.get_execution_price(
                symbol,
                signal_date,
                side='buy',
                apply_cost=False,
                apply_quality_filter=apply_quality_filter
            )
            if entry is None or pd.isna(entry) or entry <= 0:
                continue

            exit_date = self._shift_date(pd.Timestamp(signal_date), holding_period + self.execution_delay)
            exit_signal_date = self._shift_date(exit_date, -self.execution_delay)
            exit_px = self.get_execution_price(
                symbol,
                exit_signal_date.strftime('%Y-%m-%d'),
                side='sell',
                apply_cost=False,
                apply_quality_filter=apply_quality_filter
            )

            if exit_px is not None and not pd.isna(exit_px) and exit_px > 0:
                exit_type = 'normal'
                r = (float(exit_px) - float(entry)) / float(entry)
                r = max(min(float(r), 1.0), -0.95)
                results.append({
                    'symbol': symbol,
                    'signal_date': signal_date,
                    'entry_price': float(entry),
                    'exit_price': float(exit_px),
                    'position': 1,
                    'return': float(r),
                    'holding_period': holding_period,
                    'exit_type': exit_type,
                    'method': 'forward_full'
                })
                continue

            # Delisted/no data path
            if self.delisting_handler:
                last_raw = self.get_execution_price(
                    symbol,
                    exit_date.strftime('%Y-%m-%d'),
                    side='sell',
                    apply_cost=False,
                    apply_quality_filter=apply_quality_filter
                )
                if last_raw is not None and last_raw > 0:
                    r = self.delisting_handler.estimate_delisting_return(
                        symbol=symbol,
                        entry_price=float(entry),
                        last_price=float(last_raw),
                        position=1,
                        delisting_reason=None
                    )
                    r = max(min(float(r), 1.0), -0.95)
                    results.append({
                        'symbol': symbol,
                        'signal_date': signal_date,
                        'entry_price': float(entry),
                        'exit_price': float(last_raw),
                        'position': 1,
                        'return': float(r),
                        'holding_period': holding_period,
                        'exit_type': 'delisted',
                        'method': 'forward_full'
                    })
            # If we still cannot compute, skip the row (return is undefined).

        if not results:
            return pd.DataFrame(columns=[
                'symbol', 'signal_date', 'entry_price', 'exit_price',
                'position', 'return', 'holding_period', 'exit_type', 'method'
            ])
        return pd.DataFrame(results)

    def get_filter_stats(self):
        exec_calls = self.filter_stats['execution_price_calls']
        aux_calls = self.filter_stats['aux_volatility_calls'] + self.filter_stats['aux_data_calls']
        q = self.filter_stats['quality_filter_dropped']

        avg_pct = None
        if self.filter_stats['pct_of_volume_count'] > 0:
            avg_pct = self.filter_stats['pct_of_volume_sum'] / self.filter_stats['pct_of_volume_count']

        return {
            "execution_attempts": int(exec_calls),
            "auxiliary_calls": int(aux_calls),

            "dropped": {
                "quality_filter": int(q),
                "no_price_data": int(self.filter_stats['no_price_data']),
                "no_trade_date_found": int(self.filter_stats['no_trade_date_found']),
                "entry_sanity": int(self.filter_stats['entry_sanity_dropped']),
                "exit_sanity": int(self.filter_stats['exit_sanity_dropped']),
            },

            "drop_rates": {
                "quality_filter_pct": (q / exec_calls * 100) if exec_calls > 0 else 0.0,
                "no_price_data_pct": (self.filter_stats['no_price_data'] / exec_calls * 100) if exec_calls > 0 else 0.0,
                "no_trade_date_found_pct": (self.filter_stats['no_trade_date_found'] / exec_calls * 100) if exec_calls > 0 else 0.0,
                "entry_sanity_pct": (self.filter_stats['entry_sanity_dropped'] / exec_calls * 100) if exec_calls > 0 else 0.0,
                "exit_sanity_pct": (self.filter_stats['exit_sanity_dropped'] / exec_calls * 100) if exec_calls > 0 else 0.0,
            },

            "diagnostics": {
                "avg_pct_of_volume": avg_pct
            },
            "note": "Drop rates use execution_attempts only (aux calls excluded)"
        }
