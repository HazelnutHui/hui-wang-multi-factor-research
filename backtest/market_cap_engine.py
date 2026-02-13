"""
Market Cap Engine - Point-in-time market cap lookup.
"""

from __future__ import annotations

import os
from typing import Optional, Dict

import pandas as pd


class MarketCapEngine:
    def __init__(self, market_cap_dir: str, strict: bool = True):
        self.market_cap_dir = market_cap_dir
        self.strict = bool(strict)
        self._cache: Dict[str, pd.DataFrame] = {}

    def _load_symbol(self, symbol: str) -> Optional[pd.DataFrame]:
        path = os.path.join(self.market_cap_dir, f"{symbol}.csv")
        if not os.path.exists(path):
            return None
        df = pd.read_csv(path)
        if df is None or len(df) == 0 or 'date' not in df.columns:
            return None
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        if 'marketCap' not in df.columns:
            return None
        df = df.dropna(subset=['marketCap'])
        if len(df) == 0:
            return None
        return df.sort_values('date').reset_index(drop=True)

    def get_market_cap(self, symbol: str, date: str) -> Optional[float]:
        if symbol not in self._cache:
            df = self._load_symbol(symbol)
            if df is None:
                self._cache[symbol] = None
            else:
                self._cache[symbol] = df

        df = self._cache.get(symbol)
        if df is None or len(df) == 0:
            return None

        as_of = pd.Timestamp(date)
        df = df[df['date'] <= as_of]
        if len(df) == 0:
            return None
        return float(df.iloc[-1]['marketCap'])
