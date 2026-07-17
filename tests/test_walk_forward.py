import pytest
import pandas as pd
from src.walk_forward import generate_walk_forward_splits

def test_walk_forward_splits_validity():
    """
    Tests that walk-forward train and test windows do not overlap, 
    and that the test window is always strictly after the train window.
    """
    dates = pd.date_range("2010-01-01", "2020-01-01", freq="B") # 10 years of business days
    
    splits = generate_walk_forward_splits(dates, train_years=3, test_years=1)
    
    assert len(splits) > 0, "Should generate at least one split"
    
    for train_idx, test_idx in splits:
        # Assert they are not empty
        assert len(train_idx) > 0
        assert len(test_idx) > 0
        
        # Assert no overlap
        overlap = train_idx.intersection(test_idx)
        assert len(overlap) == 0, f"Found overlapping dates: {overlap}"
        
        # Assert test window is strictly after train window
        max_train_date = train_idx.max()
        min_test_date = test_idx.min()
        
        assert min_test_date > max_train_date, \
            f"Test window starts at {min_test_date} but train window ends at {max_train_date}"
            
        # Optional: check if train is roughly train_years and test is test_years
        train_duration_days = (max_train_date - train_idx.min()).days
        assert train_duration_days > 365 * 2 # At least > 2 years for a 3 year window
