"""Fundamentals Engine - point-in-time fundamentals lookup"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict


class FundamentalsEngine:
    def __init__(self, fundamentals_dir: str):
        self.fundamentals_dir = Path(fundamentals_dir)
        self._cache: Dict[str, pd.DataFrame] = {}

    def _load_symbol(self, symbol: str) -> Optional[pd.DataFrame]:
        p = self.fundamentals_dir / f"{symbol}.pkl"
        if not p.exists():
            return None
        df = pd.read_pickle(p)
        if df is None or len(df) == 0:
            return None
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        if 'available_date' in df.columns:
            df['available_date'] = pd.to_datetime(df['available_date'])
        return df.sort_values('date').reset_index(drop=True)

    def get_latest_metrics(self, symbol: str, date: str) -> Optional[dict]:
        if symbol not in self._cache:
            self._cache[symbol] = self._load_symbol(symbol)
        df = self._cache.get(symbol)
        if df is None or len(df) == 0:
            return None

        d = pd.Timestamp(date)
        date_col = 'available_date' if 'available_date' in df.columns else 'date'
        df = df[df[date_col] <= d]
        if len(df) == 0:
            return None
        row = df.iloc[-1]
        out = {
            'roe': row.get('roe'),
            'roa': row.get('roa'),
            'gross_margin': row.get('gross_margin'),
            'cfo_to_assets': row.get('cfo_to_assets'),
            'debt_to_equity': row.get('debt_to_equity'),
            'asof_date': row.get(date_col)
        }
        return out
