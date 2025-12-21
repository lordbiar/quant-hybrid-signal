import pandas as pd
import numpy as np

def compute_momentum_signal(price_series, lookback=21, min_periods=None):
    """
    Enhanced momentum calculation with validation.
    
    Args:
        price_series (pd.Series): Price data
        lookback (int): Momentum lookback period
        min_periods (int): Minimum periods required (defaults to lookback // 2)
    
    Returns:
        float: Momentum signal value
    """
    if min_periods is None:
        min_periods = max(lookback // 2, 10)
    
    if len(price_series.dropna()) < min_periods + 1:
        return 0.0
    
    # Calculate momentum with validation
    momentum = price_series.pct_change(lookback).iloc[-1]
    
    # Clip extreme values
    return np.clip(momentum, -0.5, 0.5)

def generate_momentum_signals(price_data, lookback=21, clip_range=(-1, 1)):
    """
    Enhanced momentum signal generation with standardized output.
    
    Args:
        price_data (pd.DataFrame): Price data
        lookback (int): Momentum lookback period
        clip_range (tuple): Signal clipping range
    
    Returns:
        pd.DataFrame: Standardized momentum signals
    """
    signals = pd.DataFrame(0.0, index=price_data.index, columns=price_data.columns)
    
    for col in price_data.columns:
        # Calculate momentum for each time step
        for i in range(lookback, len(price_data)):
            momentum = compute_momentum_signal(price_data[col].iloc[:i+1], lookback)
            signals.iloc[i, signals.columns.get_loc(col)] = momentum
    
    # Standardize signals and add shift to prevent lookahead bias
    signals = np.clip(signals, clip_range[0], clip_range[1])
    return signals.shift(1).fillna(0)