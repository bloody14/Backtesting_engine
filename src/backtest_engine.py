import pandas as pd
import numpy as np

def run_backtest(
    prices: pd.DataFrame, 
    signals: pd.DataFrame, 
    transaction_cost_bps: float = 5.0
) -> dict:
    """
    Runs a vectorized backtest by applying trading signals to price returns.
    
    Why this exists: To simulate trading performance correctly without look-ahead bias 
    and account for realistic frictions like transaction costs.
    
    Args:
        prices: DataFrame of daily prices (Adj Close).
        signals: DataFrame of target positions (1, 0, -1). Must align with prices.
        transaction_cost_bps: Flat cost per trade in basis points (e.g., 5.0 = 0.05%).
        
    Returns:
        A dictionary containing:
        - 'returns_gross': Series of daily portfolio returns without costs.
        - 'returns_net': Series of daily portfolio returns with costs.
        - 'equity_gross': Series of cumulative portfolio value without costs (starts at 1).
        - 'equity_net': Series of cumulative portfolio value with costs (starts at 1).
        - 'positions': The actual shifted positions dataframe used.
    """
    # Calculate daily asset returns
    asset_returns = prices.pct_change()
    
    # IMPORTANT: LOOK-AHEAD BIAS PREVENTION
    # A signal generated at the end of day T can only be traded at the open/close of day T+1.
    # We shift the signal by 1 so that day T's signal multiplies day T+1's return.
    actual_positions = signals.shift(1).fillna(0)
    
    # POSITION SIZING: Equal weight across active positions on any given day.
    # Count how many absolute positions we have open each day
    active_positions_count = actual_positions.abs().sum(axis=1)
    
    # Avoid division by zero
    active_positions_count = active_positions_count.replace(0, 1)
    
    # Scale positions so the total portfolio exposure is exactly 1 (or 0)
    # E.g., if we are long 4 stocks, each is 25% of the portfolio.
    weights = actual_positions.div(active_positions_count, axis=0)
    
    # Calculate gross daily portfolio return
    gross_daily_return = (weights * asset_returns).sum(axis=1)
    
    # TRANSACTION COSTS
    # A trade occurs when the target weight changes from the previous day.
    # Note: we use weight changes rather than pure signal changes to account for rebalancing.
    weight_changes = weights.diff().abs()
    
    # Total turnover for the day across all assets
    daily_turnover = weight_changes.sum(axis=1).fillna(0)
    
    # Apply transaction cost
    cost_decimal = transaction_cost_bps / 10000.0
    daily_cost = daily_turnover * cost_decimal
    
    # Calculate net daily portfolio return
    net_daily_return = gross_daily_return - daily_cost
    
    # Calculate cumulative equity curves
    equity_gross = (1 + gross_daily_return).cumprod()
    equity_net = (1 + net_daily_return).cumprod()
    
    return {
        'returns_gross': gross_daily_return,
        'returns_net': net_daily_return,
        'equity_gross': equity_gross,
        'equity_net': equity_net,
        'positions': actual_positions,
        'weights': weights,
        'turnover': daily_turnover
    }

def get_benchmark(prices: pd.DataFrame) -> pd.Series:
    """
    Computes a buy-and-hold equal-weight benchmark for the given price universe.
    
    Why this exists: To provide a baseline to compare strategies against.
    """
    asset_returns = prices.pct_change()
    
    # Equal weight across all valid assets each day
    valid_assets_count = asset_returns.notna().sum(axis=1).replace(0, 1)
    equal_weights = asset_returns.notna().astype(int).div(valid_assets_count, axis=0)
    
    benchmark_returns = (equal_weights * asset_returns).sum(axis=1)
    benchmark_equity = (1 + benchmark_returns).cumprod()
    
    return benchmark_equity
