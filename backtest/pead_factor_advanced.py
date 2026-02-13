"""
Advanced PEAD Factor with Standardized Unexpected Earnings (SUE)
Based on your proven implementation
"""

import pandas as pd
import numpy as np
import requests
import time
from typing import Optional, Dict
from datetime import datetime, timedelta

class AdvancedPEADFactor:
    """
    SUE-based PEAD factor (your proven methodology)
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/stable"
        self.cache = {}
        self.sue_threshold = 0.8
        self.lookback_quarters = 8
    
    def get_earnings(self, symbol: str) -> pd.DataFrame:
        """Get quarterly earnings data"""
        if symbol in self.cache:
            return self.cache[symbol]
        
        url = f"{self.base_url}/earnings"
        params = {'symbol': symbol, 'apikey': self.api_key}
        
        try:
            response = requests.get(url, params=params)
            time.sleep(0.12)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)
                    df['date'] = pd.to_datetime(df['date'])
                    self.cache[symbol] = df
                    return df
        except Exception as e:
            pass
        
        return pd.DataFrame()
    
    def calculate_sue(self, earnings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Standardized Unexpected Earnings (SUE)
        Your proven formula
        """
        df = earnings_df.copy()
        df = df.dropna(subset=['epsActual', 'epsEstimated'])
        
        # Raw surprise
        df['surprise'] = df['epsActual'] - df['epsEstimated']
        
        # Sort by date
        df = df.sort_values('date')
        
        # Rolling std of surprise (8 quarters)
        df['surprise_std'] = df['surprise'].rolling(
            window=self.lookback_quarters, 
            min_periods=self.lookback_quarters
        ).std()
        
        # Standardized SUE
        df['sue'] = df['surprise'] / (df['surprise_std'] + 1e-9)
        
        # Clip extreme values
        df['sue'] = df['sue'].clip(-10, 10)
        
        return df
    
    def get_sue_signal(self, symbol: str, date: str) -> Optional[float]:
        """
        Get SUE signal for symbol at date
        
        Returns:
            SUE value if earnings announced recently, else None
        """
        earnings = self.get_earnings(symbol)
        
        if earnings.empty:
            return None
        
        # Calculate SUE
        earnings_sue = self.calculate_sue(earnings)
        
        # Find most recent earnings before date
        date_ts = pd.Timestamp(date)
        recent = earnings_sue[
            (earnings_sue['date'] <= date_ts) &
            (earnings_sue['date'] >= date_ts - pd.Timedelta(days=5))  # Within 5 days
        ]
        
        if recent.empty:
            return None
        
        # Get most recent
        latest = recent.iloc[-1]
        
        # Only return signal if SUE is strong enough
        sue = latest['sue']
        if abs(sue) > self.sue_threshold:
            return sue
        
        return None
