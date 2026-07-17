import pandas as pd
import numpy as np
from typing import Dict, Any

TRADING_DAYS_PER_YEAR = 252

def calculate_metrics(
    daily_returns: pd.Series, 
    daily_turnover: pd.Series = None,
    risk_free_rate: float = 0.0
) -> Dict[str, Any]:
    """
    Computes standard performance metrics for a backtested strategy.
    
    Why this exists: To evaluate and compare strategy performance using standardized 
    quant metrics like Sharpe, CAGR, and Drawdown.
    
    Args:
        daily_returns: Series of daily portfolio returns.
        daily_turnover: Series of daily portfolio turnover (optional).
        risk_free_rate: Annualized risk-free rate (e.g., 0.02 for 2%).
        
    Returns:
        Dictionary of computed metrics.
    """
    # Drop NaNs
    rets = daily_returns.dropna()
    
    if len(rets) == 0:
        return {}
        
    # Cumulative Return
    cum_returns = (1 + rets).cumprod()
    total_return = cum_returns.iloc[-1] - 1.0
    
    # CAGR
    years = len(rets) / TRADING_DAYS_PER_YEAR
    cagr = (1 + total_return) ** (1 / years) - 1.0 if years > 0 else 0.0
    
    # Annualized Volatility
    ann_vol = rets.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    # Sharpe Ratio
    daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR
    excess_returns = rets - daily_rf
    if ann_vol > 1e-6:
        sharpe = (excess_returns.mean() / rets.std()) * np.sqrt(TRADING_DAYS_PER_YEAR)
    else:
        sharpe = 0.0
        
    # Max Drawdown
    rolling_max = cum_returns.cummax()
    drawdown = (cum_returns - rolling_max) / rolling_max
    max_dd = drawdown.min()
    
    # Win Rate (% of positive days)
    win_rate = len(rets[rets > 0]) / len(rets[rets != 0]) if len(rets[rets != 0]) > 0 else 0.0
    
    # Average Daily Turnover
    avg_turnover = daily_turnover.mean() if daily_turnover is not None else 0.0
    
    return {
        "Total Return": float(total_return),
        "CAGR": float(cagr),
        "Annualized Volatility": float(ann_vol),
        "Sharpe Ratio": float(sharpe),
        "Max Drawdown": float(max_dd),
        "Win Rate": float(win_rate),
        "Average Daily Turnover": float(avg_turnover)
    }
