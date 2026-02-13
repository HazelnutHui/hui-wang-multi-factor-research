"""
Enhanced Execution Simulator with all improvements
Integrates: quality filtering, smart delisting, dynamic costs
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from .data_engine import DataEngine
from .data_quality_filter import DataQualityFilter
from .delisting_handler import DelistingHandler
from .cost_model import CostModel

class ExecutionSimulator:
    """
    Professional execution simulator with:
    - Data quality filtering (Priority 2)
    - Smart delisting handling (Priority 1)  
    - Dynamic cost model (Priority 3)
    """
    
    def __init__(self, data_engine: DataEngine, 
                 transaction_cost: float = 0.0020,
                 execution_delay: int = 1,
                 enable_quality_filter: bool = True,
                 enable_smart_delisting: bool = True,
                 enable_dynamic_cost: bool = True):
        
        self.data_engine = data_engine
        self.base_cost = transaction_cost
        self.execution_delay = execution_delay
        
        # Initialize enhancement modules
        self.quality_filter = DataQualityFilter() if enable_quality_filter else None
        self.delisting_handler = DelistingHandler() if enable_smart_delisting else None
        self.cost_model = CostModel(base_cost=transaction_cost) if enable_dynamic_cost else None
    
    def get_execution_price(self, symbol: str, signal_date: str,
                           side: str = 'buy') -> Optional[float]:
        """Get execution price with quality checks and dynamic costs"""
        
        execution_date = pd.Timestamp(signal_date) + pd.Timedelta(days=self.execution_delay)
        
        start_date = (execution_date - pd.Timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = (execution_date + pd.Timedelta(days=5)).strftime('%Y-%m-%d')
        
        df = self.data_engine.get_price(symbol, start_date=start_date, end_date=end_date)
        
        if df is None:
            return None
        
        # Quality check: filter abnormal price data
        if self.quality_filter and not self.quality_filter.validate_price_data(df, symbol):
            return None
        
        df = df[df['date'] >= execution_date]
        if len(df) == 0:
            return None
        
        execution_row = df.iloc[0]
        base_price = execution_row['open'] if 'open' in df.columns else execution_row['close']
        
        # Dynamic cost calculation
        if self.cost_model:
            volume = execution_row.get('volume', 0)
            
            # Calculate volatility
            hist_df = self.data_engine.get_price(symbol, 
                start_date=(execution_date - pd.Timedelta(days=60)).strftime('%Y-%m-%d'),
                end_date=execution_date.strftime('%Y-%m-%d'))
            
            if hist_df is not None and len(hist_df) > 20:
                hist_df = hist_df.copy()
                hist_df['return'] = hist_df['close'].pct_change()
                volatility = hist_df['return'].std()
            else:
                volatility = 0.02
            
            cost = self.cost_model.calculate_cost(
                price=base_price,
                volume=volume,
                volatility=volatility
            )
        else:
            cost = self.base_cost
        
        if side == 'buy':
            execution_price = base_price * (1 + cost)
        else:
            execution_price = base_price * (1 - cost)
        
        return execution_price
    
    def execute_trades(self, positions_df: pd.DataFrame) -> pd.DataFrame:
        """Execute trades with quality filtering"""
        
        results = []
        
        for _, row in positions_df.iterrows():
            symbol = row['symbol']
            signal_date = row['date']
            position = row['position']
            
            if position == 0:
                continue
            
            side = 'buy' if position > 0 else 'sell'
            exec_price = self.get_execution_price(symbol, signal_date, side)
            
            if exec_price is None:
                continue
            
            results.append({
                'symbol': symbol,
                'signal_date': signal_date,
                'position': position,
                'execution_price': exec_price,
                'executed': True
            })
        
        return pd.DataFrame(results)
    
    def calculate_returns(self, executed_trades: pd.DataFrame,
                         holding_period: int = 20) -> pd.DataFrame:
        """Calculate returns with smart delisting"""
        
        results = []
        
        for _, trade in executed_trades.iterrows():
            symbol = trade['symbol']
            signal_date = trade['signal_date']
            entry_price = trade['execution_price']
            position = trade['position']
            
            if entry_price < 1.0 or entry_price > 10000:
                continue
            
            exit_date = pd.Timestamp(signal_date) + pd.Timedelta(days=holding_period + self.execution_delay)
            
            exit_price = self.get_execution_price(
                symbol, 
                (exit_date - pd.Timedelta(days=self.execution_delay)).strftime('%Y-%m-%d'),
                side='sell' if position > 0 else 'buy'
            )
            
            if exit_price is None:
                if self.delisting_handler:
                    df = self.data_engine.get_price(symbol, end_date=exit_date.strftime('%Y-%m-%d'))
                    
                    if df is not None and len(df) > 0:
                        last_price = df.iloc[-1]['close']
                        ret = self.delisting_handler.estimate_delisting_return(
                            symbol=symbol,
                            entry_price=entry_price,
                            last_price=last_price,
                            position=position,
                            delisting_reason=None
                        )
                    else:
                        ret = -0.5
                else:
                    if position > 0:
                        exit_price = entry_price * 0.5
                    else:
                        exit_price = entry_price * 1.5
                    
                    ret = (exit_price - entry_price) / entry_price if position > 0 else (entry_price - exit_price) / entry_price
            else:
                if exit_price < 0.1 or exit_price > 10000:
                    continue
                
                if position > 0:
                    ret = (exit_price - entry_price) / entry_price
                else:
                    ret = (entry_price - exit_price) / entry_price
            
            ret = max(min(ret, 1.0), -0.95)
            
            results.append({
                'symbol': symbol,
                'signal_date': signal_date,
                'entry_price': entry_price,
                'exit_price': exit_price if exit_price else entry_price * (1 + ret),
                'position': position,
                'return': ret,
                'holding_period': holding_period
            })
        
        return pd.DataFrame(results)
