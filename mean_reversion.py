import pandas as pd
import numpy as np

def generate_mean_reversion_signals(prices, lookback=5):
    returns = prices.pct_change()
    rolling_mean = returns.rolling(lookback).mean()
    rolling_std = returns.rolling(lookback).std()
    zscore = (returns - rolling_mean) / rolling_std
    signal = -np.clip(zscore, -1, 1)
    return signal.shift(1).fillna(0)