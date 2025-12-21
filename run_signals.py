#!/usr/bin/env python3
import json
import hashlib
import datetime as dt
import pandas as pd
import numpy as np

# Import enhanced strategy functions
from download_data import load_or_download_data
from mean_reversion import generate_mean_reversion_signals
from momentum import generate_momentum_signals
from stat_arb import generate_stat_arb_signals
from fx_volatility_mean_reversion import generate_fx_signals
from signal_management import SignalManager

def generate_hybrid_signals():
    """Enhanced multi-strategy signal generation with risk management"""
    
    # --- 1. Load Data ---
    print("Loading market data...")
    prices = load_or_download_data()
    universe = prices.columns.tolist()
    
    # --- 2. Define Strategy Universes ---
    MOMENTUM_UNIVERSE = ["SPY", "QQQ", "BTC-USD", "ETH-USD"]
    MEAN_REV_UNIVERSE = ["IWM", "GLD"]
    FX_UNIVERSE = ["EURUSD=X"]
    STAT_ARB_PAIRS = [("BTC-USD", "ETH-USD"), ("SPY", "QQQ")]
    
    # --- 3. Generate Individual Strategy Signals ---
    print("Generating enhanced signals from individual strategies...")
    
    # Initialize signal manager
    signal_manager = SignalManager(max_correlation=0.7, max_position_size=0.15, max_sector_exposure=0.40)
    
    # Dictionary to store all signals
    all_signals = {}
    
    # Generate Mean Reversion signals
    print("  - Calculating enhanced Mean Reversion signals...")
    mean_rev_signal = generate_mean_reversion_signals(
        prices[MEAN_REV_UNIVERSE], 
        lookback=15,
        clip_range=(-1, 1)
    )
    all_signals['mean_reversion'] = mean_rev_signal
    
    # Generate Momentum signals
    print("  - Calculating enhanced Momentum signals...")
    momentum_signal = generate_momentum_signals(
        prices[MOMENTUM_UNIVERSE],
        lookback=21,
        clip_range=(-1, 1)
    )
    all_signals['momentum'] = momentum_signal
    
    # Generate Statistical Arbitrage signals
    print("  - Calculating enhanced Statistical Arbitrage signals...")
    stat_arb_signal = generate_stat_arb_signals(
        prices,
        lookback=20,
        zscore_threshold=2.0,
        clip_range=(-1, 1)
    )
    all_signals['stat_arb'] = stat_arb_signal
    
    # Generate FX Volatility-Adjusted Mean Reversion signals
    print("  - Calculating enhanced FX Volatility-Adjusted Mean Reversion signals...")
    fx_signal = generate_fx_signals(
        prices[FX_UNIVERSE],
        lookback=50,
        volatility_period=14,
        clip_range=(-1, 1)
    )
    all_signals['fx_vol'] = fx_signal
    
    # --- 4. Signal Processing and Risk Management ---
    print("Processing and optimizing signals...")
    
    # Decorrelate signals
    cleaned_signals = signal_manager.decorrelate_signals(all_signals)
    
    # Combine signals optimally
    combined_signal_raw = signal_manager.combine_signals_optimally(
        cleaned_signals, 
        combination_method="volatility_weighted"
    )
    
    # Apply risk controls
    final_signal = signal_manager.apply_risk_controls(combined_signal_raw)
    
    # --- 5. Generate Final Portfolio Weights ---
    print("Generating final portfolio weights...")
    
    # Get the latest signal values
    today_signal = final_signal.iloc[-1] if len(final_signal) > 0 else final_signal
    
    # Select top 3 and bottom 3 signals
    top3 = today_signal.nlargest(3).index
    bot3 = today_signal.nsmallest(3).index
    
    # Create weights
    weight = pd.Series(0.0, index=universe)
    weight[top3] = 1.0
    weight[bot3] = -1.0
    
    # Ensure market neutral and scale
    if weight.abs().sum() > 0:
        weight = weight / weight.abs().sum()
    
    # --- 6. Build Enhanced Output ---
    out = {
        "date": dt.datetime.now(dt.UTC).date().isoformat(),
        "generation_time_utc": dt.datetime.now(dt.UTC).isoformat(),
        "model_version": "v4.0-enhanced-risk-managed",
        "universe": universe,
        "signal": today_signal.round(4).tolist(),
        "weight": weight.round(4).tolist(),
        "signal_breakdown": {
            strategy: sig.iloc[-1].round(4).tolist() 
            for strategy, sig in cleaned_signals.items()
        },
        "risk_metrics": {
            "max_position_size": weight.abs().max(),
            "sector_exposure": {
                "equity": sum(abs(weight[asset]) for asset in ["SPY", "QQQ", "IWM"] if asset in weight),
                "crypto": sum(abs(weight[asset]) for asset in ["BTC-USD", "ETH-USD"] if asset in weight),
                "commodity": abs(weight.get("GLD", 0)),
                "fx": abs(weight.get("EURUSD=X", 0))
            }
        },
        "target_vol": "0.10"
    }
    
    # --- 7. Save Files ---
    import os
    import pathlib
    pathlib.Path("signals").mkdir(exist_ok=True)
    
    fname = f"signals/{out['date']}.json"
    with open(fname, "w") as f:
        json.dump(out, f, indent=2)
    
    # Generate MD5 hash
    md5 = hashlib.md5(open(fname, "rb").read()).hexdigest()
    with open(fname.replace(".json", ".md5"), "w") as f:
        f.write(md5)
    
    # --- 8. Display Results ---
    print("\n" + "="*60)
    print("ENHANCED MULTI-STRATEGY SIGNAL GENERATION COMPLETE")
    print("="*60)
    
    print(f"\nFinal Signal Values:")
    print(today_signal.sort_values(ascending=False))
    
    print(f"\nFinal Portfolio Weights:")
    print(weight.sort_values(ascending=False))
    
    print(f"\nRisk Metrics:")
    print(f"Max Position Size: {weight.abs().max():.1%}")
    for sector, exposure in out['risk_metrics']['sector_exposure'].items():
        print(f"{sector.title()} Exposure: {exposure:.1%}")
    
    print(f"\nSignal file: {fname}")
    print(f"MD5: {md5}")
    
    return out

if __name__ == "__main__":
    generate_hybrid_signals()