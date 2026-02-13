"""
Factor Engine with Advanced SUE-based PEAD
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from .data_engine import DataEngine
from pead_factor_advanced import AdvancedPEADFactor

class FactorEngine:
    """
    Calculate factors including SUE-based PEAD
    """
    
    def __init__(self, data_engine: DataEngine, api_key: Optional[str] = None):
        self.data_engine = data_engine
        self.pead_factor = AdvancedPEADFactor(api_key) if api_key else None
    
    def calculate_momentum(self, symbol: str, date: str,
                          lookback: int = 120, skip: int = 20) -> Optional[float]:
        """Calculate momentum factor"""
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=(lookback + skip) * 2)).strftime('%Y-%m-%d')
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        
        if df is None or len(df) < lookback + skip:
            return None
        
        df = df.copy()
        df['return'] = df['close'].pct_change()
        
        if len(df) >= lookback + skip:
            momentum_return = df.iloc[-(lookback+skip):-skip]['return'].sum()
            return momentum_return
        
        return None
    
    def calculate_reversal(self, symbol: str, date: str,
                          lookback: int = 5) -> Optional[float]:
        """Calculate short-term reversal factor"""
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=lookback * 3)).strftime('%Y-%m-%d')
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        
        if df is None or len(df) < lookback:
            return None
        
        df = df.copy()
        df['return'] = df['close'].pct_change()
        
        recent_return = df.tail(lookback)['return'].sum()
        return -recent_return
    
    def calculate_low_volatility(self, symbol: str, date: str,
                                 window: int = 60) -> Optional[float]:
        """Calculate low volatility factor"""
        start_date = (pd.Timestamp(date) - pd.Timedelta(days=window * 2)).strftime('%Y-%m-%d')
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=date)
        
        if df is None or len(df) < window:
            return None
        
        df = df.copy()
        df['return'] = df['close'].pct_change()
        
        volatility = df.tail(window)['return'].std()
        return -volatility if not np.isnan(volatility) else None
    
    def calculate_pead(self, symbol: str, date: str) -> Optional[float]:
        """
        Calculate SUE-based PEAD signal (your proven method)
        """
        if not self.pead_factor:
            return None
        
        return self.pead_factor.get_sue_signal(symbol, date)
    
    def calculate_all_factors(self, symbol: str, date: str) -> Dict[str, Optional[float]]:
        """Calculate all factors"""
        factors = {
            'momentum': self.calculate_momentum(symbol, date),
            'reversal': self.calculate_reversal(symbol, date),
            'low_vol': self.calculate_low_volatility(symbol, date),
        }
        
        if self.pead_factor:
            factors['pead'] = self.calculate_pead(symbol, date)
        
        return factors
