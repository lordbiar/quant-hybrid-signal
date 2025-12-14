# strategies/momentum.py
import pandas as pd
import numpy as np

def compute_momentum_signal(price_series, lookback=21):
    """
    Calculates a simple momentum signal based on N-day return.
    A positive value indicates positive momentum.
    """
    if len(price_series) < lookback + 1:
        return 0.0
    return price_series.pct_change(lookback).iloc[-1]

def generate_momentum_signals(price_data):
    """
    Generates a momentum signal for each asset in the DataFrame.
    """
    signals = {}
    for col in price_data.columns:
        # Use a 21-day lookback (approx. 1 trading month) for momentum
        signals[col] = compute_momentum_signal(price_data[col], lookback=21)
    
    # Return as a DataFrame to be consistent with other strategies
    return pd.DataFrame([signals], index=price_data.index[-1:])
