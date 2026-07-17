import pytest
import pandas as pd
from src.backtest_engine import run_backtest

def test_transaction_costs_always_reduce_returns():
    """
    Asserts that applying a transaction cost always results in equal or worse 
    daily returns compared to the gross return, never better. 
    A broken cost model where costs increase returns is a classic quant bug.
    """
    # Synthetic data where trades definitely happen
    dates = pd.date_range("2023-01-01", periods=10)
    
    # Prices moving around
    prices = pd.DataFrame({
        'A': [100, 101, 102, 95, 100, 105, 110, 108, 105, 110]
    }, index=dates)
    
    # High turnover signal: alternating 1 and -1 every day
    signals = pd.DataFrame({
        'A': [1, -1, 1, -1, 1, -1, 1, -1, 1, -1]
    }, index=dates)
    
    results = run_backtest(prices, signals, transaction_cost_bps=10.0)
    
    gross_returns = results['returns_gross']
    net_returns = results['returns_net']
    
    # Cost should always be non-negative, meaning net <= gross always
    difference = gross_returns - net_returns
    
    # Due to floating point math, we use a small tolerance
    assert (difference >= -1e-12).all(), \
        "Found days where net return was higher than gross return! Transaction costs are broken."
    
    # Also verify that on days with trades, the difference is strictly positive
    turnover = results['turnover']
    days_with_trades = turnover > 0.0
    
    assert (difference[days_with_trades] > 0).all(), \
        "Found days with trades but no transaction costs were applied."
