import pandas as pd
import numpy as np

def generate_mean_reversion_signals(prices, lookback=15, clip_range=(-1, 1)):
    """
    Enhanced mean reversion strategy with standardized signal generation.
    
    Args:
        prices (pd.DataFrame): Price data
        lookback (int): Lookback period (increased from 5 to 15 for reliability)
        clip_range (tuple): Signal clipping range
    
    Returns:
        pd.DataFrame: Standardized signals
    """
    returns = prices.pct_change()
    rolling_mean = returns.rolling(lookback).mean()
    rolling_std = returns.rolling(lookback).std()
    
    # Calculate z-score with minimum observations requirement
    min_periods = max(lookback // 2, 5)
    zscore = (returns - rolling_mean) / (rolling_std + 1e-8)
    
    # Generate mean reversion signal (negative z-score = buy signal)
    signal = -np.clip(zscore, clip_range[0], clip_range[1])
    
    # Add shift to prevent lookahead bias and fill NaN
    return signal.shift(1).fillna(0)