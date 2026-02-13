"""
Universe Builder - Tradable universe construction
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from .data_engine import DataEngine
from .market_cap_engine import MarketCapEngine

class UniverseBuilder:
    """
    Build tradable universe with liquidity filters
    Point-in-time correct
    """
    
    def __init__(self, data_engine: DataEngine, 
                 min_market_cap: float = 500e6,
                 min_dollar_volume: float = 1e6,
                 min_price: float = 5.0,
                 max_volatility: float = None,
                 vol_lookback: int = None,
                 exclude_symbols: List[str] = None,
                 market_cap_engine: Optional[MarketCapEngine] = None,
                 market_cap_strict: bool = True):
        self.data_engine = data_engine
        self.min_market_cap = min_market_cap
        self.min_dollar_volume = min_dollar_volume
        self.min_price = min_price
        self.max_volatility = max_volatility
        self.vol_lookback = vol_lookback
        self.exclude_symbols = set(exclude_symbols or [])
        self.market_cap_engine = market_cap_engine
        self.market_cap_strict = bool(market_cap_strict)
    
    def get_universe(self, date: str, lookback: int = 20) -> List[str]:
        """
        Get tradable universe at specific date
        
        Args:
            date: As-of date
            lookback: Days to calculate average liquidity
        
        Returns:
            List of tradable symbols
        """
        universe = []
        date_ts = pd.Timestamp(date)
        start_date = (date_ts - pd.Timedelta(days=lookback * 2)).strftime('%Y-%m-%d')
        
        for symbol in self.data_engine.get_all_symbols():
            if symbol in self.exclude_symbols:
                continue
            # Check if delisted
            if self.data_engine.is_delisted(symbol, date):
                continue
            
            # Get recent price data
            df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
            if df is None or len(df) < lookback:
                continue
            
            # Check price filter
            recent = df.tail(lookback)
            avg_price = recent['close'].mean()
            if avg_price < self.min_price:
                continue
            
            # Check liquidity (dollar volume)
            if 'volume' in recent.columns:
                recent_dollar_volume = (recent['close'] * recent['volume']).mean()
                if recent_dollar_volume < self.min_dollar_volume:
                    continue

            # Check volatility filter (optional)
            if self.max_volatility is not None and self.vol_lookback:
                if len(df) < int(self.vol_lookback) + 1:
                    continue
                df_ret = df.copy()
                df_ret['return'] = df_ret['close'].pct_change(fill_method=None)
                vol = df_ret.tail(int(self.vol_lookback))['return'].std()
                if vol is None or np.isnan(vol):
                    continue
                if float(vol) > float(self.max_volatility):
                    continue

            # Check market cap (optional; requires market cap engine)
            if self.min_market_cap is not None and self.market_cap_engine is not None:
                mc = self.market_cap_engine.get_market_cap(symbol, date)
                if mc is None:
                    if self.market_cap_strict:
                        continue
                else:
                    if float(mc) < float(self.min_market_cap):
                        continue
            
            universe.append(symbol)
        
        return universe
    
    def get_universe_history(self, start_date: str, end_date: str,
                            frequency: int = 20) -> Dict[str, List[str]]:
        """
        Get universe at multiple dates
        
        Args:
            start_date: Start date
            end_date: End date
            frequency: Rebalance frequency (days)
        
        Returns:
            Dict mapping date -> list of symbols
        """
        dates = pd.date_range(start=start_date, end=end_date, freq=f'{frequency}D')
        universe_history = {}
        
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            universe = self.get_universe(date_str)
            universe_history[date_str] = universe
            print(f"{date_str}: {len(universe)} stocks")
        
        return universe_history
