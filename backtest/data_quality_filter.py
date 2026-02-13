"""
Data Quality Filter - Real-time data validation
"""

import pandas as pd
import numpy as np
from typing import List, Dict

class DataQualityFilter:
    """
    Filter out bad data in real-time
    """
    
    def __init__(self, min_universe_pct: float = 0.7):
        self.min_universe_pct = min_universe_pct
        self.quality_log = []
    
    def validate_price_data(self, df: pd.DataFrame, symbol: str) -> bool:
        """
        Check if price data is valid
        
        Returns:
            True if valid, False if should be excluded
        """
        if df is None or len(df) == 0:
            return False
        
        # Check for zero/negative prices
        if (df['close'] <= 0).any() or (df['open'] <= 0).any():
            self.quality_log.append(f"{symbol}: Zero/negative prices")
            return False
        
        # Check for zero volume
        if 'volume' in df.columns and (df['volume'] == 0).sum() > len(df) * 0.5:
            self.quality_log.append(f"{symbol}: >50% zero volume")
            return False
        
        # Check for extreme jumps (>100% in one day without valid reason)
        returns = df['close'].pct_change(fill_method=None)
        if (abs(returns) > 1.0).any():
            self.quality_log.append(f"{symbol}: Extreme jump detected")
            return False
        
        # Check open/close sanity
        if 'open' in df.columns:
            ratio = df['open'] / df['close']
            if (ratio > 2.0).any() or (ratio < 0.5).any():
                self.quality_log.append(f"{symbol}: Open/Close ratio abnormal")
                return False
        
        return True
    
    def validate_universe_size(self, universe: List[str], 
                              expected_size: int) -> bool:
        """
        Check if universe is large enough
        
        Returns:
            True if universe is acceptable, False if too small
        """
        actual_pct = len(universe) / expected_size if expected_size > 0 else 0
        
        if actual_pct < self.min_universe_pct:
            self.quality_log.append(
                f"Universe too small: {len(universe)}/{expected_size} "
                f"({actual_pct*100:.1f}% < {self.min_universe_pct*100:.0f}%)"
            )
            return False
        
        return True
    
    def get_log(self) -> List[str]:
        """Return quality issues log"""
        return self.quality_log
