import pandas as pd
import numpy as np

def generate_stat_arb_signals(price_data, lookback=20, zscore_threshold=2.0, clip_range=(-1, 1)):
    """
    Enhanced statistical arbitrage with improved pair selection and risk controls.
    
    Args:
        price_data (pd.DataFrame): Price data
        lookback (int): Lookback period for mean reversion
        zscore_threshold (float): Z-score threshold for signal generation
        clip_range (tuple): Signal clipping range
    
    Returns:
        pd.DataFrame: Standardized stat arb signals
    """
    signals = pd.DataFrame(0.0, index=price_data.index, columns=price_data.columns)
    
    # Enhanced pair selection with correlation validation
    pairs = []
    
    # BTC-ETH pair
    if 'BTC-USD' in price_data.columns and 'ETH-USD' in price_data.columns:
        btc_eth_corr = price_data['BTC-USD'].corr(price_data['ETH-USD'])
        if btc_eth_corr > 0.5:  # Minimum correlation threshold
            pairs.append(('BTC-USD', 'ETH-USD'))
    
    # SPY-QQQ pair
    if 'SPY' in price_data.columns and 'QQQ' in price_data.columns:
        spy_qqq_corr = price_data['SPY'].corr(price_data['QQQ'])
        if spy_qqq_corr > 0.7:  # Minimum correlation threshold
            pairs.append(('SPY', 'QQQ'))
    
    for asset1, asset2 in pairs:
        # Calculate price ratio
        ratio = price_data[asset1] / price_data[asset2]
        
        # Calculate rolling statistics with minimum periods
        min_periods = max(lookback // 2, 10)
        rolling_mean = ratio.rolling(lookback, min_periods=min_periods).mean()
        rolling_std = ratio.rolling(lookback, min_periods=min_periods).std()
        
        # Calculate z-score
        zscore = (ratio - rolling_mean) / (rolling_std + 1e-8)
        
        # Generate signal with threshold
        pair_signal = -np.clip(zscore / zscore_threshold, -2, 2) / 2.0
        
        # Apply final clipping and assign signals
        final_signal = np.clip(pair_signal, clip_range[0], clip_range[1])
        signals[asset1] = final_signal
        signals[asset2] = -final_signal
    
    # Add shift to prevent lookahead bias
    return signals.shift(1).fillna(0)