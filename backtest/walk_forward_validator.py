"""
Walk-Forward Validation
"""

import pandas as pd
from typing import Dict, List

class WalkForwardValidator:
    """
    Rolling window validation
    """
    
    def __init__(self, train_years: int = 3, test_years: int = 1):
        self.train_years = train_years
        self.test_years = test_years
    
    def generate_windows(self, start_year: int, end_year: int) -> List[Dict]:
        """
        Generate train/test windows
        
        Example:
            Train: 2015-2017, Test: 2018
            Train: 2016-2018, Test: 2019
            Train: 2017-2019, Test: 2020
            ...
        
        Returns:
            List of {train_start, train_end, test_start, test_end}
        """
        windows = []
        
        for test_year in range(start_year + self.train_years, end_year + 1):
            train_start = test_year - self.train_years
            train_end = test_year - 1
            test_start = test_year
            test_end = test_year
            
            windows.append({
                'train_start': f'{train_start}-01-01',
                'train_end': f'{train_end}-12-31',
                'test_start': f'{test_start}-01-01',
                'test_end': f'{test_end}-12-31',
                'test_year': test_year
            })
        
        return windows
