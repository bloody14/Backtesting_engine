import pandas as pd
import numpy as np
from typing import Optional

def ma_crossover_strategy(prices: pd.DataFrame, fast_window: int = 20, slow_window: int = 50) -> pd.DataFrame:
    """
    Generates signals for a Moving Average Crossover strategy.
    
    Why this exists: To provide a basic trend-following signal. It goes long when the fast moving average 
    is above the slow moving average, and short when it is below.
    
    Args:
        prices: DataFrame of daily prices (columns are tickers, index is dates).
        fast_window: Number of days for the fast simple moving average.
        slow_window: Number of days for the slow simple moving average.
        
    Returns:
        DataFrame of target positions (1 for long, -1 for short, 0 for flat).
    """
    fast_sma = prices.rolling(window=fast_window).mean()
    slow_sma = prices.rolling(window=slow_window).mean()
    
    # 1 if fast > slow, -1 if fast < slow, NaN if not enough data
    signal = pd.DataFrame(np.where(fast_sma > slow_sma, 1, 
                          np.where(fast_sma < slow_sma, -1, np.nan)), 
                          index=prices.index, columns=prices.columns)
    
    # Forward fill signals so we hold positions until a cross happens
    signal = signal.ffill().fillna(0)
    
    return signal

def mean_reversion_strategy(prices: pd.DataFrame, window: int = 20, z_threshold: float = 2.0) -> pd.DataFrame:
    """
    Generates signals for a Z-Score Mean Reversion strategy.
    
    Why this exists: To provide a mean-reverting signal. It assumes prices reverting to a rolling mean. 
    It goes long when price drops unusually low (z < -threshold) and short when unusually high (z > threshold).
    It exits positions (goes flat) when the z-score crosses back over 0.
    
    Args:
        prices: DataFrame of daily prices (columns are tickers, index is dates).
        window: Number of days for calculating the rolling mean and standard deviation.
        z_threshold: The z-score magnitude required to enter a trade.
        
    Returns:
        DataFrame of target positions (1 for long, -1 for short, 0 for flat).
    """
    rolling_mean = prices.rolling(window=window).mean()
    rolling_std = prices.rolling(window=window).std()
    
    # Avoid division by zero
    z_score = (prices - rolling_mean) / rolling_std.replace(0, np.nan)
    
    # Initialize signals with NaN
    signals = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    
    # Entry conditions
    signals[z_score < -z_threshold] = 1   # Long
    signals[z_score > z_threshold] = -1   # Short
    
    # Exit conditions (crossing 0)
    # If we are long and z crosses above 0, exit. If short and z crosses below 0, exit.
    # To keep it fully vectorized, we mark flat conditions as 0, then forward fill.
    # Since we want to exit when crossing 0, any z-score between -threshold and 0 for a long, 
    # or 0 and threshold for a short, we just hold. Once the sign flips, we want to go 0.
    
    # Actually, a simpler vectorized approach:
    # If z > 0, previous long exits. If z < 0, previous short exits.
    # We can explicitly set 0 where z_score is near 0 or crosses.
    # Let's set 0 where sign of z_score is opposite to our needed hold direction, 
    # but a simpler robust way is setting 0 if z_score is between -0.5 and 0.5 (as a buffer).
    # Let's use exactly 0 as crossing point.
    signals[(z_score >= 0) & (z_score.shift(1) < 0)] = 0
    signals[(z_score <= 0) & (z_score.shift(1) > 0)] = 0
    
    # Forward fill to hold the position
    signals = signals.ffill().fillna(0)
    
    return signals

def momentum_strategy(prices: pd.DataFrame, lookback: int = 60, top_k: int = 3, rebalance_freq: str = 'ME') -> pd.DataFrame:
    """
    Generates signals for a cross-sectional Momentum strategy.
    
    Why this exists: To capture cross-sectional momentum by going long the top performing stocks 
    over a trailing window, rebalancing periodically. Note this ranks stocks against each other.
    
    Args:
        prices: DataFrame of daily prices (columns are tickers, index is dates).
        lookback: Number of days to calculate trailing returns.
        top_k: Number of top stocks to go long.
        rebalance_freq: Resampling frequency (e.g., 'M' for monthly, 'W' for weekly).
        
    Returns:
        DataFrame of target positions (1 for long, 0 for flat).
    """
    # Calculate rolling lookback return
    trailing_returns = prices.pct_change(periods=lookback)
    
    # Create an empty signal dataframe
    signals = pd.DataFrame(0, index=prices.index, columns=prices.columns)
    
    # Get the dates where we need to rebalance based on the frequency
    # We will resample the dates to find the end of the period
    rebalance_dates = prices.resample(rebalance_freq).last().index
    
    # Find valid rebalance dates that exist in the price index
    valid_rebalance_dates = rebalance_dates.intersection(prices.index)
    
    for date in valid_rebalance_dates:
        # Cross-sectional ranking at this date
        row = trailing_returns.loc[date]
        
        # Drop NaNs to rank valid stocks
        valid_row = row.dropna()
        if len(valid_row) < top_k:
            continue
            
        # Get top K performers
        top_stocks = valid_row.nlargest(top_k).index
        
        # Set signals to 1 for top stocks on this date
        signals.loc[date, top_stocks] = 1
        
    # Since we rebalance periodically, we forward fill the positions from the rebalance dates 
    # to all other days until the next rebalance. 
    # To do this cleanly: keep 0s where we haven't rebalanced yet.
    # At rebalance dates, signals are 1 for longs and 0 for others.
    # We can replace all non-rebalance rows with NaN and forward fill.
    
    # Mask out non-rebalance dates to NaN
    is_rebalance_date = signals.index.isin(valid_rebalance_dates)
    signals_ffill = signals.copy()
    signals_ffill.loc[~is_rebalance_date, :] = np.nan
    
    # Forward fill to hold positions
    signals_ffill = signals_ffill.ffill().fillna(0)
    
    return signals_ffill
