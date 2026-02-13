"""PEAD with -1 day shift (assume date is T, trade on T-1)"""
import pandas as pd
from .pead_factor_cached import CachedPEADFactor

class ShiftedPEADFactor(CachedPEADFactor):
    """Assume FMP date is day AFTER market reaction"""
    
    def get_sue_signal(self, symbol: str, date: str):
        """
        Shift backwards: if checking signal on 2024-02-02,
        look for earnings on 2024-02-01
        """
        # Look 1 day forward in earnings data
        date_ts = pd.Timestamp(date)
        target_date = date_ts + pd.Timedelta(days=1)
        
        earnings = self.get_earnings(symbol)
        if earnings.empty:
            return None
        
        earnings_sue = self.calculate_sue(earnings)
        
        # Check if earnings exists 1 day in future
        recent = earnings_sue[
            (earnings_sue['date'] == target_date)
        ]
        
        if recent.empty:
            return None
        
        sue = recent.iloc[0]['sue']
        if abs(sue) > self.sue_threshold:
            return sue
        return None
