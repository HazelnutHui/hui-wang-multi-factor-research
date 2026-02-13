"""
Main script to run professional backtest
"""

import sys
import pandas as pd
from datetime import datetime

# Import all components
import config
from pathlib import Path
from backtest_engine import BacktestEngine

def print_results(results: dict, title: str = "BACKTEST RESULTS"):
    """Pretty print backtest results"""
    print("\n" + "="*70)
    print(title)
    print("="*70)
    
    analysis = results['analysis']
    
    print(f"\nOverall Performance:")
    print(f"  IC: {analysis['ic']:.4f}" if analysis['ic'] else "  IC: N/A")
    print(f"  t-stat: {analysis['t_stat']:.2f}" if analysis['t_stat'] else "  t-stat: N/A")
    print(f"  p-value: {analysis['p_value']:.4f}" if analysis['p_value'] else "  p-value: N/A")
    print(f"  Signals: {analysis['n_signals']:,}")
    
    print(f"\nReturn Statistics:")
    if analysis['mean_return']:
        print(f"  Mean Return: {analysis['mean_return']*100:.2f}%")
        print(f"  Median Return: {analysis['median_return']*100:.2f}%")
        print(f"  Std Return: {analysis['std_return']*100:.2f}%")
        print(f"  Sharpe Ratio: {analysis['sharpe']:.2f}" if analysis['sharpe'] else "  Sharpe: N/A")
        print(f"  Win Rate: {analysis['win_rate']*100:.1f}%")
    
    # Yearly IC
    if 'ic_yearly' in analysis and len(analysis['ic_yearly']) > 0:
        print(f"\nYearly IC:")
        for _, row in analysis['ic_yearly'].iterrows():
            ic_str = f"{row['ic']:.4f}" if not pd.isna(row['ic']) else "N/A"
            print(f"  {row['period']}: {ic_str} (n={row['n']:,})")

def main():
    """Main execution"""
    
    # Configuration
    def _pick_price_dirs():
        try:
            use_adj = getattr(config, "USE_ADJ_PRICES", False)
            adj_active = Path(getattr(config, "PRICE_DIR_ACTIVE_ADJ", ""))
            adj_del = Path(getattr(config, "PRICE_DIR_DELISTED_ADJ", ""))
            if use_adj and adj_active.exists() and adj_del.exists():
                if any(adj_active.glob("*.pkl")) or any(adj_del.glob("*.pkl")):
                    return str(adj_active), str(adj_del)
        except Exception:
            pass
        return config.PRICE_DIR_ACTIVE, config.PRICE_DIR_DELISTED

    price_active, price_delisted = _pick_price_dirs()

    config_dict = {
        'PRICE_DIR_ACTIVE': price_active,
        'PRICE_DIR_DELISTED': price_delisted,
        'DELISTED_INFO': config.DELISTED_INFO,
        'MIN_MARKET_CAP': config.MIN_MARKET_CAP,
        'MIN_DOLLAR_VOLUME': config.MIN_DOLLAR_VOLUME,
        'MIN_PRICE': config.MIN_PRICE,
        'TRANSACTION_COST': config.TRANSACTION_COST,
        'EXECUTION_DELAY': config.EXECUTION_DELAY
    }
    
    # Initialize engine
    engine = BacktestEngine(config_dict)
    
    # Define factor to test
    factor_weights = {
        'momentum': 1.0,    # Pure momentum
        'reversal': 0.0,
        'low_vol': 0.0
    }
    
    # Run out-of-sample test
    results = engine.run_out_of_sample_test(
        train_start=config.TRAIN_START,
        train_end=config.TRAIN_END,
        test_start=config.TEST_START,
        test_end=config.TEST_END,
        factor_weights=factor_weights,
        rebalance_freq=config.REBALANCE_FREQUENCY,
        holding_period=20,
        long_pct=0.2,
        short_pct=0.0  # Long-only
    )
    
    # Print results
    print_results(results['train'], "TRAINING PERIOD RESULTS")
    print_results(results['test'], "TEST PERIOD RESULTS")
    
    print("\n" + "="*70)
    print("OUT-OF-SAMPLE COMPARISON")
    print("="*70)
    oos = results['oos_analysis']
    print(f"\nTrain IC: {oos['train_ic']:.4f} (n={oos['train_n']:,})")
    print(f"Test IC:  {oos['test_ic']:.4f} (n={oos['test_n']:,})")
    if oos['ic_degradation_pct']:
        print(f"Degradation: {oos['ic_degradation_pct']:+.1f}%")
    
    # Decision
    print("\n" + "="*70)
    print("DECISION")
    print("="*70)
    
    test_ic = oos['test_ic']
    if test_ic and test_ic > 0.03:
        print(f"✓ Test IC = {test_ic:.4f} > 0.03")
        print("✓ Strategy is potentially viable")
        print("✓ Recommend: Paper trading for 3-6 months")
    elif test_ic and test_ic > 0.02:
        print(f"⚠ Test IC = {test_ic:.4f} is marginal (0.02-0.03)")
        print("⚠ Strategy may work but has low margin of safety")
        print("⚠ Recommend: Extended paper trading or reconsider")
    else:
        print(f"✗ Test IC = {test_ic:.4f if test_ic else 'N/A'} < 0.02")
        print("✗ Strategy is not viable")
        print("✗ Recommend: Do not proceed to live trading")
    
    # Save results
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    results['train']['signals'].to_csv('../results/train_signals.csv', index=False)
    results['train']['returns'].to_csv('../results/train_returns.csv', index=False)
    results['test']['signals'].to_csv('../results/test_signals.csv', index=False)
    results['test']['returns'].to_csv('../results/test_returns.csv', index=False)
    
    # Save summary
    summary = {
        'train_ic': oos['train_ic'],
        'test_ic': oos['test_ic'],
        'degradation_pct': oos['ic_degradation_pct'],
        'train_signals': oos['train_n'],
        'test_signals': oos['test_n']
    }
    pd.DataFrame([summary]).to_csv('../results/oos_summary.csv', index=False)
    
    print("Saved to ../results/")
    print("  - train_signals.csv")
    print("  - train_returns.csv")
    print("  - test_signals.csv")
    print("  - test_returns.csv")
    print("  - oos_summary.csv")
    
    print("\n" + "="*70)
    print("BACKTEST COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
