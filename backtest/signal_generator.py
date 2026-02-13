"""
Signal Generator - Generate trading signals from factors
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from .data_engine import DataEngine
from .factor_engine import FactorEngine

class SignalGenerator:
    """
    Generate trading signals from factor values
    """
    
    def __init__(self, factor_engine: FactorEngine):
        self.factor_engine = factor_engine
    
    def generate_signals(self, universe: List[str], date: str,
                        factor_weights: Dict[str, float] = None) -> pd.DataFrame:
        """
        Generate signals for universe at date
        
        Args:
            universe: List of symbols
            date: Signal generation date (T day close)
            factor_weights: Dict of factor_name -> weight
        
        Returns:
            DataFrame with columns: symbol, signal, factor_values
        """
        if factor_weights is None:
            # Equal weight by default
            factor_weights = {
                'momentum': 1.0,
                'reversal': 0.0,
                'low_vol': 0.0
            }
        
        signals = []
        
        for symbol in universe:
            # Calculate all factors
            factors = self.factor_engine.calculate_all_factors(symbol, date)
            
            # Skip if no valid factors
            if all(v is None for v in factors.values()):
                continue
            
            # Calculate combined signal (weighted average)
            signal = 0.0
            total_weight = 0.0
            
            for factor_name, factor_value in factors.items():
                if factor_value is not None and factor_name in factor_weights:
                    weight = factor_weights[factor_name]
                    signal += factor_value * weight
                    total_weight += abs(weight)
            
            if total_weight > 0:
                signal = signal / total_weight
                
                signals.append({
                    'symbol': symbol,
                    'date': date,
                    'signal': signal,
                    **{f'factor_{k}': v for k, v in factors.items()}
                })
        
        df = pd.DataFrame(signals)
        
        # Rank signals (cross-sectional)
        if len(df) > 0:
            df['signal_rank'] = df['signal'].rank(pct=True)
        
        return df
    
    def generate_positions(self, signals_df: pd.DataFrame,
                          long_pct: float = 0.2,
                          short_pct: float = 0.0) -> pd.DataFrame:
        """
        Convert signals to positions
        
        Args:
            signals_df: DataFrame from generate_signals
            long_pct: Top X% to long
            short_pct: Bottom X% to short (0 = long-only)
        
        Returns:
            DataFrame with position column (-1/0/+1)
        """
        df = signals_df.copy()
        df['position'] = 0
        
        if len(df) == 0:
            return df
        
        # Long positions
        long_threshold = 1 - long_pct
        df.loc[df['signal_rank'] >= long_threshold, 'position'] = 1
        
        # Short positions (if enabled)
        if short_pct > 0:
            short_threshold = short_pct
            df.loc[df['signal_rank'] <= short_threshold, 'position'] = -1
        
        return df
