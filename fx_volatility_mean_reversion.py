# strategies/fx_volatility_mean_reversion.py
import pandas as pd
import numpy as np

def generate_fx_signals(price_data, lookback=50, volatility_period=14):
    """
    Generates a volatility-adjusted mean reversion signal for FX pairs.
    
    This strategy identifies when an asset is overbought or oversold
    relative to its recent average, scaled by its recent volatility.
    
    Args:
        price_data (pd.DataFrame): DataFrame with price data for the assets.
        lookback (int): The period for the simple moving average (the "mean").
        volatility_period (int): The period to calculate volatility (standard deviation).

    Returns:
        pd.DataFrame: A DataFrame of signals, indexed by date.
    """
    signals = pd.DataFrame(0.0, index=price_data.index, columns=price_data.columns)
    
    for asset in price_data.columns:
        prices = price_data[asset].dropna()
        
        if len(prices) < lookback:
            continue # Not enough data to calculate the signal
            
        # 1. Calculate the Simple Moving Average (the mean)
        sma = prices.rolling(window=lookback).mean()
        
        # 2. Calculate the deviation from the mean
        deviation = prices - sma
        
        # 3. Calculate recent volatility (standard deviation of returns)
        # We add a small epsilon to prevent division by zero
        returns = prices.pct_change()
        volatility = returns.rolling(window=volatility_period).std()
        
        # 4. Calculate the normalized signal
        # This is our core edge: distance from mean / volatility
        raw_signal = -deviation / (volatility + 1e-8) # Negate to signal mean reversion
        
        # 5. Clip the signal to a reasonable range [-1.5, 1.5] and then scale to [-1, 1]
        # This prevents extreme signals during low-volatility periods
        clipped_signal = np.clip(raw_signal, -1.5, 1.5) / 1.5
        
        signals[asset] = clipped_signal
        
    return signals.fillna(0)