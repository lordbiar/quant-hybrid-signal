import pandas as pd
import numpy as np
from scipy.stats import pearsonr

class SignalManager:
    """Centralized signal management with risk controls and optimization"""
    
    def __init__(self, max_correlation=0.7, max_position_size=0.15, max_sector_exposure=0.40):
        self.max_correlation = max_correlation
        self.max_position_size = max_position_size
        self.max_sector_exposure = max_sector_exposure
        
    def decorrelate_signals(self, signals_dict):
        """Remove highly correlated signals"""
        cleaned_signals = signals_dict.copy()
        strategy_names = list(signals_dict.keys())
        
        for i, strat1 in enumerate(strategy_names):
            for j, strat2 in enumerate(strategy_names[i+1:], i+1):
                if strat1 in cleaned_signals and strat2 in cleaned_signals:
                    sig1 = cleaned_signals[strat1].dropna()
                    sig2 = cleaned_signals[strat2].dropna()
                    
                    if len(sig1) > 10 and len(sig2) > 10:
                        # Align signals
                        common_idx = sig1.index.intersection(sig2.index)
                        if len(common_idx) > 10:
                            corr, _ = pearsonr(sig1[common_idx], sig2[common_idx])
                            
                            if abs(corr) > self.max_correlation:
                                # Keep the signal with higher average absolute value
                                if abs(sig1.mean()) < abs(sig2.mean()):
                                    del cleaned_signals[strat1]
                                    break
                                else:
                                    del cleaned_signals[strat2]
        
        return cleaned_signals
    
    def apply_risk_controls(self, combined_signal, sectors=None):
        """Apply position sizing and sector exposure limits"""
        if sectors is None:
            sectors = {
                "equity": ["SPY", "QQQ", "IWM"],
                "crypto": ["BTC-USD", "ETH-USD"],
                "commodity": ["GLD"],
                "fx": ["EURUSD=X"]
            }
        
        # Apply position size limits
        combined_signal = np.clip(combined_signal, -self.max_position_size, self.max_position_size)
        
        # Calculate sector exposures
        sector_exposure = {}
        for sector, assets in sectors.items():
            sector_assets = [asset for asset in assets if asset in combined_signal.index]
            if sector_assets:
                sector_exposure[sector] = sum(abs(combined_signal[asset]) for asset in sector_assets)
        
        # Scale down if sector exposure too high
        for sector, exposure in sector_exposure.items():
            if exposure > self.max_sector_exposure:
                scale_factor = self.max_sector_exposure / exposure
                sector_assets = [asset for asset in sectors[sector] if asset in combined_signal.index]
                for asset in sector_assets:
                    combined_signal[asset] *= scale_factor
        
        return combined_signal
    
    def combine_signals_optimally(self, signals_dict, combination_method="equal_weight"):
        """Combine multiple signals using different methodologies"""
        if not signals_dict:
            return pd.Series()
        
        if combination_method == "equal_weight":
            combined = sum(signals_dict.values()) / len(signals_dict)
        elif combination_method == "volatility_weighted":
            # Weight by inverse volatility
            weights = {}
            total_inv_vol = 0
            
            for name, signal in signals_dict.items():
                vol = signal.std()
                if vol > 0:
                    inv_vol = 1 / vol
                    weights[name] = inv_vol
                    total_inv_vol += inv_vol
            
            # Normalize weights
            for name in weights:
                weights[name] /= total_inv_vol
            
            combined = sum(weights[name] * signals_dict[name] for name in weights)
        else:
            combined = sum(signals_dict.values()) / len(signals_dict)
        
        return combined