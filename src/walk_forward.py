import pandas as pd
from typing import List, Tuple

def generate_walk_forward_splits(
    index: pd.DatetimeIndex, 
    train_years: int = 3, 
    test_years: int = 1
) -> List[Tuple[pd.DatetimeIndex, pd.DatetimeIndex]]:
    """
    Generates train and test date indices for walk-forward validation.
    
    Why this exists: To prevent overfitting. By evaluating the strategy on out-of-sample 
    data (test window) that strictly follows the in-sample data (train window), we can 
    simulate real-world performance more accurately.
    
    Args:
        index: The full DatetimeIndex of the dataset.
        train_years: Number of years for the in-sample training window.
        test_years: Number of years for the out-of-sample testing window.
        
    Returns:
        A list of tuples: (train_indices, test_indices).
    """
    if len(index) == 0:
        return []
        
    start_date = index.min()
    end_date = index.max()
    
    splits = []
    
    current_train_start = start_date
    
    while True:
        # Calculate window ends
        current_train_end = current_train_start + pd.DateOffset(years=train_years)
        current_test_end = current_train_end + pd.DateOffset(years=test_years)
        
        # If the test window goes beyond our data, we stop
        if current_train_end >= end_date or current_test_end > end_date + pd.Timedelta(days=30):
            # Allow slight overflow for the last window (up to a month) but fundamentally break if out of bounds
            if current_train_end >= end_date:
                break
        
        # Get actual available dates in these theoretical windows
        # Train: [start, end)
        # Test: [end, test_end)
        train_mask = (index >= current_train_start) & (index < current_train_end)
        test_mask = (index >= current_train_end) & (index < current_test_end)
        
        train_idx = index[train_mask]
        test_idx = index[test_mask]
        
        if len(train_idx) > 0 and len(test_idx) > 0:
            splits.append((train_idx, test_idx))
            
        # Roll forward by the test window size
        current_train_start = current_train_start + pd.DateOffset(years=test_years)
        
    return splits
