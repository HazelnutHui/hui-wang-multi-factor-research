"""
Data Engine - Point-in-time data management
"""

import pandas as pd
import numpy as np
import os
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import pickle

class DataEngine:
    """
    Professional data management with point-in-time correctness
    """
    
    def __init__(self, active_dir: str, delisted_dir: str, delisted_info: str):
        self.active_dir = active_dir
        self.delisted_dir = delisted_dir
        self.price_cache = {}
        
        # Load delisted information
        df = pd.read_csv(delisted_info)
        df['delistedDate'] = pd.to_datetime(df['delistedDate'])
        self.delisted_info = dict(zip(df['symbol'], df['delistedDate']))
        
        # Build symbol inventory
        self._build_inventory()
    
    def _build_inventory(self):
        """Build complete symbol inventory"""
        self.symbols = {
            'active': set(),
            'delisted': set()
        }
        
        # Active stocks
        if os.path.exists(self.active_dir):
            for file in os.listdir(self.active_dir):
                if file.endswith('.pkl'):
                    symbol = file.replace('.pkl', '')
                    self.symbols['active'].add(symbol)
        
        # Delisted stocks
        if os.path.exists(self.delisted_dir):
            for file in os.listdir(self.delisted_dir):
                if file.endswith('.pkl'):
                    symbol = file.replace('.pkl', '')
                    self.symbols['delisted'].add(symbol)
        
        print(f"Inventory: {len(self.symbols['active'])} active, "
              f"{len(self.symbols['delisted'])} delisted")
    
    def get_price(self, symbol: str, start_date: Optional[str] = None,
                  end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Get price data - point-in-time correct
        
        Args:
            symbol: Stock symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive, point-in-time cutoff)
        
        Returns:
            DataFrame with OHLCV data, or None if not available
        """
        # Check if delisted before end_date
        if symbol in self.delisted_info:
            delisted_date = self.delisted_info[symbol]
            if end_date and pd.Timestamp(end_date) > delisted_date:
                # Stock was delisted before end_date, adjust cutoff
                end_date = delisted_date.strftime('%Y-%m-%d')
        
        # Load from cache or disk
        if symbol not in self.price_cache:
            df = self._load_symbol(symbol)
            if df is None:
                return None
            self.price_cache[symbol] = df
        
        df = self.price_cache[symbol].copy()
        
        # Filter by date range
        if start_date:
            df = df[df['date'] >= pd.Timestamp(start_date)]
        if end_date:
            df = df[df['date'] <= pd.Timestamp(end_date)]
        
        return df if len(df) > 0 else None
    
    def _load_symbol(self, symbol: str) -> Optional[pd.DataFrame]:
        """Load symbol from disk"""
        # Try active first
        path = f"{self.active_dir}/{symbol}.pkl"
        if os.path.exists(path):
            df = pd.read_pickle(path)
            df = self._normalize_price_df(df)
            return df.sort_values('date').reset_index(drop=True)
        
        # Try delisted
        path = f"{self.delisted_dir}/{symbol}.pkl"
        if os.path.exists(path):
            df = pd.read_pickle(path)
            df = self._normalize_price_df(df)
            return df.sort_values('date').reset_index(drop=True)
        
        return None

    def _normalize_price_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure standard OHLC column names exist even for adjusted-price data."""
        if df is None or len(df) == 0:
            return df
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        # Map adjusted columns to standard OHLC if needed
        if 'close' not in df.columns and 'adjClose' in df.columns:
            if 'adjOpen' in df.columns:
                df['open'] = df['adjOpen']
            if 'adjHigh' in df.columns:
                df['high'] = df['adjHigh']
            if 'adjLow' in df.columns:
                df['low'] = df['adjLow']
            df['close'] = df['adjClose']

        return df
    
    def get_all_symbols(self) -> List[str]:
        """Get all available symbols"""
        return list(self.symbols['active'] | self.symbols['delisted'])
    
    def is_delisted(self, symbol: str, date: str) -> bool:
        """Check if stock is delisted at given date"""
        if symbol not in self.delisted_info:
            return False
        return pd.Timestamp(date) >= self.delisted_info[symbol]
