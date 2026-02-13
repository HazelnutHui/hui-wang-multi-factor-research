"""
Performance Analyzer - Backtest performance analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from scipy import stats

class PerformanceAnalyzer:
    """
    Analyze backtest performance with IC, Sharpe, etc.
    """
    
    def __init__(self):
        pass
    
    def calculate_ic(self, signals_df: pd.DataFrame, returns_df: pd.DataFrame) -> Dict:
        """
        Calculate Information Coefficient
        
        Args:
            signals_df: DataFrame with columns [symbol, date, signal]
            returns_df: DataFrame with columns [symbol, signal_date, return]
        
        Returns:
            Dict with IC statistics
        """
        required_signal_cols = {'symbol', 'date', 'signal'}
        required_return_cols = {'symbol', 'signal_date', 'return'}
        if (
            signals_df is None
            or returns_df is None
            or not required_signal_cols.issubset(set(signals_df.columns))
            or not required_return_cols.issubset(set(returns_df.columns))
        ):
            return {'ic': None, 't_stat': None, 'p_value': None, 'n': 0}
        # Merge signals and returns
        merged = pd.merge(
            signals_df[['symbol', 'date', 'signal']],
            returns_df[['symbol', 'signal_date', 'return']],
            left_on=['symbol', 'date'],
            right_on=['symbol', 'signal_date'],
            how='inner'
        )
        
        if len(merged) == 0:
            return {'ic': None, 't_stat': None, 'p_value': None, 'n': 0}
        
        # Per-date IC (cross-sectional), then aggregate
        merged['date'] = pd.to_datetime(merged['date'])
        ic_by_date = merged.groupby('date')[['signal', 'return']].apply(lambda g: g['signal'].corr(g['return']))
        ic_by_date = ic_by_date.dropna()

        ic_overall = merged['signal'].corr(merged['return'])
        n = len(ic_by_date)
        if n > 1:
            ic = float(ic_by_date.mean())
            std = float(ic_by_date.std(ddof=1))
            t_stat = ic / (std / np.sqrt(n)) if std > 0 else None
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 1)) if t_stat is not None else None
        else:
            ic = None
            t_stat = None
            p_value = None
        
        return {
            'ic': ic,
            'ic_overall': ic_overall,
            't_stat': t_stat,
            'p_value': p_value,
            'n': int(n),
            'n_merged': int(len(merged))
        }
    
    def calculate_ic_by_period(self, signals_df: pd.DataFrame,
                               returns_df: pd.DataFrame,
                               freq: str = 'M') -> pd.DataFrame:
        """
        Calculate IC by time period (monthly/yearly)
        
        Args:
            signals_df: Signals DataFrame
            returns_df: Returns DataFrame
            freq: 'M' for monthly, 'Y' for yearly
        
        Returns:
            DataFrame with period, ic, t_stat
        """
        required_signal_cols = {'symbol', 'date', 'signal'}
        required_return_cols = {'symbol', 'signal_date', 'return'}
        if (
            signals_df is None
            or returns_df is None
            or not required_signal_cols.issubset(set(signals_df.columns))
            or not required_return_cols.issubset(set(returns_df.columns))
        ):
            return pd.DataFrame()
        # Merge
        merged = pd.merge(
            signals_df[['symbol', 'date', 'signal']],
            returns_df[['symbol', 'signal_date', 'return']],
            left_on=['symbol', 'date'],
            right_on=['symbol', 'signal_date'],
            how='inner'
        )
        
        if len(merged) == 0:
            return pd.DataFrame()
        
        merged['date'] = pd.to_datetime(merged['date'])
        merged['period'] = merged['date'].dt.to_period(freq)
        
        # Calculate IC by period
        results = []
        for period, group in merged.groupby('period'):
            ic = group[['signal', 'return']]['signal'].corr(group[['signal', 'return']]['return'])
            n = len(group)
            
            if n > 2 and not np.isnan(ic):
                t_stat = ic * np.sqrt(n - 2) / np.sqrt(1 - ic**2)
            else:
                t_stat = None
            
            results.append({
                'period': str(period),
                'ic': ic,
                't_stat': t_stat,
                'n': n
            })
        
        return pd.DataFrame(results)
    
    def calculate_sharpe(self, returns: pd.Series, periods_per_year: int = 252) -> float:
        """
        Calculate Sharpe Ratio
        
        Args:
            returns: Series of returns
            periods_per_year: Trading periods per year
        
        Returns:
            Annualized Sharpe Ratio
        """
        if len(returns) == 0:
            return None
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        if std_return == 0:
            return None
        
        sharpe = (mean_return / std_return) * np.sqrt(periods_per_year)
        return sharpe
    
    def analyze_backtest(self, signals_df: pd.DataFrame,
                        returns_df: pd.DataFrame) -> Dict:
        """
        Comprehensive backtest analysis
        
        Returns:
            Dict with all performance metrics
        """
        # Overall IC
        ic_stats = self.calculate_ic(signals_df, returns_df)
        
        # IC by year
        ic_yearly = self.calculate_ic_by_period(signals_df, returns_df, freq='Y')
        
        # IC by month
        ic_monthly = self.calculate_ic_by_period(signals_df, returns_df, freq='M')
        
        # Return statistics
        if len(returns_df) > 0:
            mean_return = returns_df['return'].mean()
            median_return = returns_df['return'].median()
            std_return = returns_df['return'].std()
            sharpe = self.calculate_sharpe(returns_df['return'])
            win_rate = (returns_df['return'] > 0).mean()
        else:
            mean_return = None
            median_return = None
            std_return = None
            sharpe = None
            win_rate = None
        
        return {
            'ic': ic_stats['ic'],
            't_stat': ic_stats['t_stat'],
            'p_value': ic_stats['p_value'],
            'n_signals': ic_stats['n'],
            'ic_yearly': ic_yearly,
            'ic_monthly': ic_monthly,
            'mean_return': mean_return,
            'median_return': median_return,
            'std_return': std_return,
            'sharpe': sharpe,
            'win_rate': win_rate
        }
    
    def out_of_sample_test(self, train_signals: pd.DataFrame, train_returns: pd.DataFrame,
                          test_signals: pd.DataFrame, test_returns: pd.DataFrame) -> Dict:
        """
        Out-of-sample validation
        
        Returns:
            Dict comparing train vs test performance
        """
        train_stats = self.calculate_ic(train_signals, train_returns)
        test_stats = self.calculate_ic(test_signals, test_returns)
        
        if train_stats['ic'] and test_stats['ic']:
            degradation = (test_stats['ic'] / train_stats['ic'] - 1) * 100
        else:
            degradation = None
        
        return {
            'train_ic': train_stats['ic'],
            'train_t_stat': train_stats['t_stat'],
            'train_n': train_stats['n'],
            'test_ic': test_stats['ic'],
            'test_t_stat': test_stats['t_stat'],
            'test_n': test_stats['n'],
            'ic_degradation_pct': degradation
        }
