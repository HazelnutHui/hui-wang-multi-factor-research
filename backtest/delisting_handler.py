"""
Delisting Handler - Smart delisting return calculation
"""

import pandas as pd
from typing import Optional

class DelistingHandler:
    """
    Handle delisted stocks with reason-based logic
    """
    
    def __init__(self):
        # Common delisting reasons
        self.merger_keywords = ['merger', 'acquisition', 'acquired', 'buyout', 'takeover']
        self.bankruptcy_keywords = ['bankruptcy', 'chapter', 'liquidation']
    
    def estimate_delisting_return(self, symbol: str, 
                                  entry_price: float,
                                  last_price: float,
                                  position: int,
                                  delisting_reason: Optional[str] = None) -> float:
        """
        Estimate return based on delisting reason
        
        Args:
            symbol: Stock symbol
            entry_price: Entry price
            last_price: Last available price before delisting
            position: 1 for long, -1 for short
            delisting_reason: Reason for delisting (if available)
        
        Returns:
            Estimated return
        """
        # Determine delisting type
        if delisting_reason:
            reason_lower = delisting_reason.lower()
            is_merger = any(kw in reason_lower for kw in self.merger_keywords)
            is_bankruptcy = any(kw in reason_lower for kw in self.bankruptcy_keywords)
        else:
            # Guess based on price action
            price_drop = (last_price - entry_price) / entry_price
            is_merger = price_drop > -0.2  # Price held relatively well
            is_bankruptcy = price_drop < -0.5  # Price collapsed
        
        if position > 0:  # Long position
            if is_merger:
                # Merger: typically get cash/stock at premium
                # Use last price with small haircut (10%)
                exit_price = last_price * 0.90
            elif is_bankruptcy:
                # Bankruptcy: assume 80% loss
                exit_price = entry_price * 0.20
            else:
                # Unknown: conservative 50% loss
                exit_price = entry_price * 0.50
            
            ret = (exit_price - entry_price) / entry_price
        
        else:  # Short position
            if is_merger:
                # Merger: short gets squeezed, forced to cover at premium
                exit_price = last_price * 1.10
            elif is_bankruptcy:
                # Bankruptcy: short wins big (stock goes to zero)
                exit_price = entry_price * 0.10
            else:
                # Unknown: conservative 50% gain
                exit_price = entry_price * 0.50
            
            ret = (entry_price - exit_price) / entry_price
        
        # Cap at reasonable limits
        ret = max(min(ret, 1.0), -0.95)
        
        return ret
