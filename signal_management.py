# signal_management.py

import pandas as pd
import numpy as np
from scipy.stats import pearsonr

class SignalManager:
    """
    Centralized signal management with risk controls and optimization.
    
    This class is responsible for processing raw signals from various strategies,
    removing redundant signals, combining them optimally, and applying
    risk management constraints.
    """

    def __init__(self, max_correlation=0.7, max_position_size=0.15, max_sector_exposure=0.40):
        """
        Initializes the SignalManager with risk parameters.
        
        Args:
            max_correlation (float): The maximum allowed correlation between two
                                     strategy signals before one is removed.
            max_position_size (float): The maximum absolute size for any single position.
            max_sector_exposure (float): The maximum absolute exposure for any sector.
        """
        self.max_correlation = max_correlation
        self.max_position_size = max_position_size
        self.max_sector_exposure = max_sector_exposure
        
    def decorrelate_signals(self, signals_dict):
        """
        Remove highly correlated signals by comparing them only on assets they both trade.
        
        This function identifies pairs of strategies with overlapping asset universes.
        For each pair, it calculates the correlation of their aggregate signals on
        just those shared assets. If two strategies are too highly correlated, the
        one with the lower average absolute signal is removed.
        
        Args:
            signals_dict (dict): A dictionary where keys are strategy names and
                                 values are DataFrames of signals.
        
        Returns:
            dict: A dictionary of cleaned, decorrelated signals.
        """
        cleaned_signals = signals_dict.copy()
        
        # Pre-calculate the list of non-NaN assets for each strategy
        strategy_assets = {}
        for name, signal_df in signals_dict.items():
            # Get assets that have at least one non-NaN signal
            strategy_assets[name] = signal_df.dropna(axis=1, how='all').columns.tolist()

        strategy_names = list(signals_dict.keys())
        
        for i, strat1 in enumerate(strategy_names):
            for j, strat2 in enumerate(strategy_names[i+1:], i+1):
                # Check if strategies are still in our cleaned list
                if strat1 not in cleaned_signals or strat2 not in cleaned_signals:
                    continue

                # Find the common assets between the two strategies
                assets1 = strategy_assets[strat1]
                assets2 = strategy_assets[strat2]
                common_assets = list(set(assets1) & set(assets2))

                # If there are no common assets, they are already decorrelated. Skip.
                if not common_assets:
                    continue

                # --- Comparison Logic for Overlapping Strategies ---
                # Isolate the signals for only the common assets
                sig1_subset = cleaned_signals[strat1][common_assets].dropna()
                sig2_subset = cleaned_signals[strat2][common_assets].dropna()

                if len(sig1_subset) > 10 and len(sig2_subset) > 10:
                    # Align the two dataframes by their index (date)
                    common_idx = sig1_subset.index.intersection(sig2_subset.index)
                    if len(common_idx) > 10:
                        # Calculate the aggregate signal for the overlapping assets only
                        agg_sig1 = sig1_subset.loc[common_idx].mean(axis=1)
                        agg_sig2 = sig2_subset.loc[common_idx].mean(axis=1)
                        
                        # Now calculate the correlation on these comparable series
                        corr, _ = pearsonr(agg_sig1, agg_sig2)
                        
                        if abs(corr) > self.max_correlation:
                            # Keep the signal with higher average absolute value
                            # We compare the mean of the absolute values of the *original* full signal dataframe
                            if abs(cleaned_signals[strat1].values).mean() < abs(cleaned_signals[strat2].values).mean():
                                print(f"Removing {strat1} due to high correlation ({corr:.2f}) with {strat2}")
                                del cleaned_signals[strat1]
                                break
                            else:
                                print(f"Removing {strat2} due to high correlation ({corr:.2f}) with {strat1}")
                                del cleaned_signals[strat2]
        
        return cleaned_signals
    
    def apply_risk_controls(self, combined_signal, sectors=None):
        """
        Apply position sizing and sector exposure limits to the final combined signal.
        
        Args:
            combined_signal (pd.Series): The final combined signal for each asset.
            sectors (dict, optional): A dictionary mapping sector names to lists of assets.
                                       Defaults to a standard set of sectors.
        
        Returns:
            pd.Series: The risk-controlled signal.
        """
        if sectors is None:
            sectors = {
                "equity": ["SPY", "QQQ", "IWM"],
                "crypto": ["BTC-USD", "ETH-USD"],
                "commodity": ["GLD"],
                "fx": ["EURUSD=X"]
            }
        
        # Apply position size limits
        controlled_signal = np.clip(combined_signal, -self.max_position_size, self.max_position_size)
        
        # Calculate sector exposures
        sector_exposure = {}
        for sector, assets in sectors.items():
            sector_assets = [asset for asset in assets if asset in controlled_signal.index]
            if sector_assets:
                sector_exposure[sector] = sum(abs(controlled_signal[asset]) for asset in sector_assets)
        
        # Scale down if sector exposure too high
        for sector, exposure in sector_exposure.items():
            if exposure > self.max_sector_exposure:
                scale_factor = self.max_sector_exposure / exposure
                sector_assets = [asset for asset in sectors[sector] if asset in controlled_signal.index]
                for asset in sector_assets:
                    controlled_signal[asset] *= scale_factor
        
        return controlled_signal
    
    def combine_signals_optimally(self, signals_dict, combination_method="equal_weight"):
        """
        Combine multiple signals using different methodologies.
        
        Args:
            signals_dict (dict): A dictionary of decorrelated signals.
            combination_method (str): The method to use for combining signals.
                                     Options: "equal_weight", "volatility_weighted".
        
        Returns:
            pd.Series: The final combined signal.
        """
        if not signals_dict:
            return pd.Series()
        
        if combination_method == "equal_weight":
            combined = sum(signals_dict.values()) / len(signals_dict)
        elif combination_method == "volatility_weighted":
            # Weight by inverse volatility
            weights = {}
            total_inv_vol = 0
            
            for name, signal in signals_dict.items():
                # Use the mean standard deviation across assets as a proxy for strategy volatility
                vol = signal.std().mean()
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
        
        return combined.fillna(0)
