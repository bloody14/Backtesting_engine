import pytest
import pandas as pd
import numpy as np
from src.metrics import calculate_metrics

def test_metrics_accuracy():
    """
    Tests metric calculations against a hand-computed synthetic series 
    to ensure functions are mathematically correct.
    """
    # Create exactly 252 days (1 year)
    dates = pd.date_range("2023-01-01", periods=252)
    
    # A simple return series: alternating +1% and -1%, ending with +10% on the last day
    # Let's do something simpler: 252 days of exactly 0.1% daily return.
    rets = [0.001] * 252
    returns_series = pd.Series(rets, index=dates)
    
    metrics = calculate_metrics(returns_series, risk_free_rate=0.0)
    
    # Expected CAGR: (1.001^252) - 1
    expected_cagr = (1.001 ** 252) - 1
    assert np.isclose(metrics["CAGR"], expected_cagr)
    
    # Volatility should be 0 since returns are constant
    assert np.isclose(metrics["Annualized Volatility"], 0.0)
    
    # Sharpe ratio should be 0 because standard deviation is 0
    assert np.isclose(metrics["Sharpe Ratio"], 0.0)
    
    # Max drawdown should be 0 because it strictly goes up
    assert np.isclose(metrics["Max Drawdown"], 0.0)
    
    # Win rate should be 1.0 (100%) because all non-zero returns are positive
    assert np.isclose(metrics["Win Rate"], 1.0)

def test_drawdown_calculation():
    """Explicitly tests max drawdown with a known dip."""
    dates = pd.date_range("2023-01-01", periods=4)
    # Price path: 100 -> 110 (+10%) -> 55 (-50%) -> 110 (+100%)
    returns_series = pd.Series([0.10, -0.50, 1.0], index=dates[1:])
    
    metrics = calculate_metrics(returns_series)
    
    # Max drawdown is from 110 down to 55, which is exactly -50% (-0.5)
    assert np.isclose(metrics["Max Drawdown"], -0.5)
