# strategies/stat_arb.py
import pandas as pd
import numpy as np

# Define the lookback period here instead of a separate config file
STAT_ARB_LOOKBACK = 20

def generate_stat_arb_signals(price_data, lookback=STAT_ARB_LOOKBACK):
    """
    Generates statistical arbitrage signals based on mean reversion of asset pairs.
    """
    # Initialize a DataFrame for signals with the same index and columns as price_data
    signals = pd.DataFrame(0.0, index=price_data.index, columns=price_data.columns)
    
    # Define the pairs to trade. Use the correct tickers from your universe.
    pairs = []
    if 'BTC-USD' in price_data.columns and 'ETH-USD' in price_data.columns:
        pairs.append(('BTC-USD', 'ETH-USD'))
    
    if 'SPY' in price_data.columns and 'QQQ' in price_data.columns:
        pairs.append(('SPY', 'QQQ'))
    
    for asset1, asset2 in pairs:
        # Calculate the price ratio
        ratio = price_data[asset1] / price_data[asset2]
        
        # Calculate rolling mean and standard deviation of the ratio
        rolling_mean = ratio.rolling(lookback).mean()
        rolling_std = ratio.rolling(lookback).std()
        
        # Calculate the z-score of the current ratio
        zscore = (ratio - rolling_mean) / rolling_std
        
        # Generate a signal: when the ratio is high (zscore > 1), short asset1 and long asset2.
        # When the ratio is low (zscore < -1), long asset1 and short asset2.
        # We clip the signal to be between -1 and 1 to limit position size.
        pair_signal = -np.clip(zscore, -2, 2) / 2.0 # Scale the signal
        
        # Assign the signal to the assets
        signals[asset1] = pair_signal
        signals[asset2] = -pair_signal
    
    return signals.fillna(0)