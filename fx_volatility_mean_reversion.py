import pandas as pd
import numpy as np

def generate_fx_signals(price_data, lookback=50, volatility_period=14, clip_range=(-1, 1)):
    """
    Enhanced FX volatility-adjusted mean reversion with standardized output.
    
    Args:
        price_data (pd.DataFrame): Price data
        lookback (int): Period for moving average
        volatility_period (int): Period for volatility calculation
        clip_range (tuple): Signal clipping range
    
    Returns:
        pd.DataFrame: Standardized FX signals
    """
    signals = pd.DataFrame(0.0, index=price_data.index, columns=price_data.columns)
    
    for asset in price_data.columns:
        prices = price_data[asset].dropna()
        
        if len(prices) < max(lookback, volatility_period):
            continue
            
        # Calculate moving average
        sma = prices.rolling(window=lookback).mean()
        
        # Calculate deviation from mean
        deviation = prices - sma
        
        # Calculate volatility with minimum periods
        returns = prices.pct_change()
        volatility = returns.rolling(window=volatility_period, min_periods=volatility_period//2).std()
        
        # Calculate normalized signal
        raw_signal = -deviation / (volatility + 1e-8)
        
        # Clip and scale signal
        clipped_signal = np.clip(raw_signal, -1.5, 1.5) / 1.5
        
        # Apply final clipping range and store
        signals[asset] = np.clip(clipped_signal, clip_range[0], clip_range[1])
    
    # Add shift to prevent lookahead bias
    return signals.shift(1).fillna(0)