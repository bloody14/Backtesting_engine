import pytest
import pandas as pd
import numpy as np
from src.backtest_engine import run_backtest

@pytest.fixture
def sample_data():
    """Provides a synthetic price and signal series for testing."""
    dates = pd.date_range("2024-01-01", periods=5)
    
    # Prices: 100 -> 110 (+10%) -> 100 (-9.09%) -> 120 (+20%) -> 120 (0%)
    prices = pd.DataFrame({
        'A': [100.0, 110.0, 100.0, 120.0, 120.0]
    }, index=dates)
    
    # Signals generated at close of day
    signals = pd.DataFrame({
        'A': [1, 1, -1, 1, 0]
    }, index=dates)
    
    return prices, signals

def test_signal_shift_is_applied(sample_data):
    """
    Asserts that the signal shift is actually doing something.
    If the engine didn't shift signals, the returns would be different.
    """
    prices, signals = sample_data
    
    # Run the backtest using our engine
    results = run_backtest(prices, signals, transaction_cost_bps=0.0)
    net_returns = results['returns_net']
    
    # Let's compute manually what it WOULD be without the shift (look-ahead bias)
    # i.e., day T signal multiplied by day T return
    biased_returns = (signals * prices.pct_change()).sum(axis=1)
    
    # They should not be equal. Specifically on day 1 (index 1), 
    # the unshifted return uses signal at index 1 (which is 1) * return at index 1 (+10%) = +10%.
    # But the properly shifted engine uses signal at index 0 (which is 1) * return at index 1 (+10%).
    # Let's look at day 2 (index 2):
    # Unshifted: signal[2] (-1) * return[2] (-9.09%) = +9.09% return.
    # Properly shifted: signal[1] (1) * return[2] (-9.09%) = -9.09% return.
    assert not np.allclose(net_returns.fillna(0), biased_returns.fillna(0)), \
        "Backtest returns match unshifted returns! Look-ahead bias detected."

def test_no_future_leakage(sample_data):
    """
    Asserts that a signal generated on day T does not affect the return of day T.
    It should only affect day T+1 and onwards.
    """
    prices, signals = sample_data
    results = run_backtest(prices, signals, transaction_cost_bps=0.0)
    positions = results['positions']
    
    # Check that position on day T is the signal from day T-1
    assert positions['A'].iloc[1] == signals['A'].iloc[0], "Position on T+1 should be signal from T"
    assert positions['A'].iloc[2] == signals['A'].iloc[1]
    assert positions['A'].iloc[3] == signals['A'].iloc[2]
    
    # On day 2 (index 2), our signal changes to -1.
    # Our return on day 2 should NOT be based on the -1 signal, it should be based on day 1's signal (1).
    # Return day 2 is 100/110 - 1 = -0.090909
    expected_return_day_2 = -0.09090909090909094
    assert np.isclose(results['returns_gross'].iloc[2], expected_return_day_2)
