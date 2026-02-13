"""
Data Quality Validation - Check split/dividend adjustments
"""

import pandas as pd
import numpy as np
import os

def check_split_adjustment(symbol: str, data_dir: str = '../data/prices'):
    """
    Check if price data is properly adjusted for splits
    
    Method: Check for sudden price jumps that aren't accompanied by volume spikes
    """
    file_path = f"{data_dir}/{symbol}.pkl"
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_pickle(file_path)
    df = df.sort_values('date')
    
    # Calculate daily returns
    df['return'] = df['close'].pct_change()
    df['volume_change'] = df['volume'].pct_change()
    
    # Flag suspicious jumps (>50% change without volume spike)
    suspicious = df[
        (abs(df['return']) > 0.5) & 
        (abs(df['volume_change']) < 2.0)
    ]
    
    # Check open/close consistency
    df['open_close_ratio'] = df['open'] / df['close']
    ratio_mean = df['open_close_ratio'].mean()
    ratio_std = df['open_close_ratio'].std()
    
    # Flag if ratio is too far from 1.0
    inconsistent = df[abs(df['open_close_ratio'] - 1.0) > 0.2]
    
    return {
        'symbol': symbol,
        'suspicious_jumps': len(suspicious),
        'inconsistent_open_close': len(inconsistent),
        'open_close_ratio_mean': ratio_mean,
        'open_close_ratio_std': ratio_std
    }

def main():
    """Validate known split stocks"""
    
    print("="*70)
    print("DATA QUALITY VALIDATION")
    print("="*70)
    
    # Known stocks with splits
    test_symbols = [
        'AAPL',  # Multiple splits
        'TSLA',  # 5-for-1 in 2020, 3-for-1 in 2022
        'NVDA',  # 4-for-1 in 2021, 10-for-1 in 2024
        'GOOGL', # 20-for-1 in 2022
        'AMZN',  # 20-for-1 in 2022
    ]
    
    results = []
    for symbol in test_symbols:
        print(f"\nChecking {symbol}...")
        result = check_split_adjustment(symbol)
        if result:
            results.append(result)
            print(f"  Suspicious jumps: {result['suspicious_jumps']}")
            print(f"  Inconsistent O/C: {result['inconsistent_open_close']}")
            print(f"  O/C ratio: {result['open_close_ratio_mean']:.3f} ± {result['open_close_ratio_std']:.3f}")
    
    df_results = pd.DataFrame(results)
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(df_results.to_string(index=False))
    
    # Decision
    total_issues = df_results['suspicious_jumps'].sum() + df_results['inconsistent_open_close'].sum()
    
    print("\n" + "="*70)
    print("VERDICT")
    print("="*70)
    
    if total_issues == 0:
        print("✓ Data appears properly adjusted")
    elif total_issues < 10:
        print("⚠ Minor data issues detected (may be acceptable)")
    else:
        print("✗ Significant data quality issues detected")
        print("✗ FMP data may not be reliable for backtesting")

if __name__ == "__main__":
    main()
