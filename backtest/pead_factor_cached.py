"""PEAD Factor using local cached Owner_Earnings-labeled data"""
import pandas as pd
import numpy as np
import os
from typing import Optional

class CachedPEADFactor:
    """Fast PEAD using pre-downloaded earnings"""
    
    def __init__(self, earnings_dir: str = '../data/Owner_Earnings'):
        self.earnings_dir = earnings_dir
        self.sue_threshold = 0.5
        self.lookback_quarters = 8
    
    def get_earnings(self, symbol: str) -> pd.DataFrame:
        """Load from local cache"""
        file_path = f"{self.earnings_dir}/{symbol}.pkl"
        if os.path.exists(file_path):
            return pd.read_pickle(file_path)
        return pd.DataFrame()
    
    def calculate_sue(self, earnings_df: pd.DataFrame) -> pd.DataFrame:
        """Same SUE calculation"""
        df = earnings_df.copy()
        df = df.dropna(subset=['epsActual', 'epsEstimated'])
        df['surprise'] = df['epsActual'] - df['epsEstimated']
        df = df.sort_values('date')
        df['surprise_std'] = df['surprise'].rolling(
            window=self.lookback_quarters, 
            min_periods=self.lookback_quarters
        ).std()
        df['sue'] = df['surprise'] / (df['surprise_std'] + 1e-9)
        df['sue'] = df['sue'].clip(-10, 10)
        return df
    
    def get_sue_signal(self, symbol: str, date: str) -> Optional[float]:
        """Get SUE signal (now instant from cache)"""
        earnings = self.get_earnings(symbol)
        if earnings.empty:
            return None
        
        earnings_sue = self.calculate_sue(earnings)
        date_ts = pd.Timestamp(date)
        
        recent = earnings_sue[
            (earnings_sue['date'] <= date_ts) &
            (earnings_sue['date'] >= date_ts - pd.Timedelta(days=5))
        ]
        
        if recent.empty:
            return None
        
        latest = recent.iloc[-1]
        sue = latest['sue']
        
        if abs(sue) > self.sue_threshold:
            return sue
        return None
