"""
Advanced Cost Model - Volatility and liquidity adjusted
"""

import pandas as pd
import numpy as np

class CostModel:
    """
    More realistic transaction cost model
    """
    
    def __init__(self, base_cost: float = 0.0020):
        self.base_cost = base_cost
    
    def calculate_cost(self, price: float, 
                      volume: float,
                      volatility: float,
                      trade_size_usd: float = 10000) -> float:
        """
        Calculate transaction cost based on market conditions
        
        Args:
            price: Stock price
            volume: Daily volume
            volatility: Recent volatility (std of returns)
            trade_size_usd: Trade size in USD
        
        Returns:
            Transaction cost as decimal (e.g., 0.0030 = 30bps)
        """
        # Base cost
        cost = self.base_cost
        
        # Liquidity adjustment
        dollar_volume = price * volume
        pct_of_volume = trade_size_usd / dollar_volume if dollar_volume > 0 else 1.0
        
        # If trade is >1% of daily volume, add impact cost
        if pct_of_volume > 0.01:
            impact = min(pct_of_volume * 0.10, 0.0050)  # Cap at 50bps
            cost += impact
        
        # Volatility adjustment (higher vol = wider spreads)
        if volatility > 0.02:  # >2% daily vol
            vol_cost = min((volatility - 0.02) * 0.50, 0.0030)  # Cap at 30bps
            cost += vol_cost
        
        return cost
    
    def stress_test_cost(self, base_cost: float) -> float:
        """
        Stress test: what if costs are higher?
        
        Returns:
            Stressed cost (50% higher)
        """
        return base_cost * 1.5
