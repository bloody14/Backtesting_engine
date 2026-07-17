import os
import yfinance as yf
import pandas as pd
from typing import List, Optional
import datetime

DEFAULT_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "JPM", "XOM", "JNJ", "PG", "KO",
    "META", "BRK-B", "UNH", "V", "HD",
    "MA", "CVX", "ABBV", "PEP", "SPY"
]

def get_historical_data(
    tickers: List[str] = DEFAULT_UNIVERSE,
    start_date: str = "2018-01-01",
    end_date: Optional[str] = None,
    cache_dir: str = "data"
) -> pd.DataFrame:
    """
    Downloads historical daily OHLCV data from yfinance and caches it locally.
    
    Why this exists: To ensure backtests run quickly by using locally cached CSV data 
    instead of repeatedly hitting the yfinance API, and to standardize the data format.
    
    Args:
        tickers: List of ticker symbols to download.
        start_date: The start date in YYYY-MM-DD format.
        end_date: The end date in YYYY-MM-DD format (defaults to today).
        cache_dir: The directory to store the cached CSV files.
        
    Returns:
        A multi-index DataFrame or a combined DataFrame with prices for all tickers.
        We return adjusted close prices combined into a single DataFrame where 
        columns are tickers and index is Date.
    """
    if end_date is None:
        end_date = datetime.date.today().strftime("%Y-%m-%d")
        
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"cached_prices_{start_date}_{end_date}.csv")
    
    if os.path.exists(cache_path):
        print(f"Loading cached data from {cache_path}")
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return df
        
    print(f"Downloading data from yfinance for {len(tickers)} tickers...")
    # download returns a MultiIndex DataFrame if multiple tickers are passed.
    # group_by='ticker' or default. By default, it's a MultiIndex (Price, Ticker)
    data = yf.download(tickers, start=start_date, end=end_date)
    
    # We primarily need 'Adj Close' for daily return strategies. 
    # If Adj Close is not available (yfinance changes), fallback to Close.
    if 'Adj Close' in data.columns:
        adj_close = data['Adj Close']
    elif 'Close' in data.columns:
        adj_close = data['Close']
    else:
        raise ValueError("yfinance data did not contain 'Adj Close' or 'Close'.")
        
    # Drop columns that are completely NA (e.g. invalid tickers)
    adj_close = adj_close.dropna(axis=1, how='all')
    
    # Save to cache
    adj_close.to_csv(cache_path)
    
    return adj_close
