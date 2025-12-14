#!/usr/bin/env python3
import json
import hashlib
import datetime as dt
import pandas as pd
import numpy as np

# Import your strategy functions
from download_data import load_or_download_data
from mean_reversion import generate_mean_reversion_signals
from momentum import generate_momentum_signals
from stat_arb import generate_stat_arb_signals
from fx_volatility_mean_reversion import generate_fx_signals # <-- NEW IMPORT

# --- 1. Load Data ---
print("Loading market data...")
prices = load_or_download_data()
universe = prices.columns.tolist()

# --- 2. Define Strategy Universes ---
# Define which assets each strategy will be applied to.
MOMENTUM_UNIVERSE = ["SPY", "QQQ", "BTC-USD", "ETH-USD"]
MEAN_REV_UNIVERSE = ["IWM", "GLD"] # <-- REMOVED EURUSD=X
FX_UNIVERSE = ["EURUSD=X"]          # <-- NEW FX UNIVERSE
STAT_ARB_PAIRS = [("BTC-USD", "ETH-USD"), ("SPY", "QQQ")]

# --- 3. Generate Individual Strategy Signals on Targeted Assets ---
print("Generating signals from individual strategies...")

# Initialize a final signal DataFrame with zeros
final_signal = pd.DataFrame(0.0, index=prices.index, columns=universe)

# Generate and add Mean Reversion signals
print("  - Calculating Mean Reversion signals...")
mean_rev_signal = generate_mean_reversion_signals(prices[MEAN_REV_UNIVERSE], lookback=5)
final_signal[MEAN_REV_UNIVERSE] += mean_rev_signal[MEAN_REV_UNIVERSE]

# Generate and add Momentum signals
print("  - Calculating Momentum signals...")
momentum_signal = generate_momentum_signals(prices[MOMENTUM_UNIVERSE])
final_signal[MOMENTUM_UNIVERSE] += momentum_signal[MOMENTUM_UNIVERSE]

# Generate and add Statistical Arbitrage signals
print("  - Calculating Statistical Arbitrage signals...")
stat_arb_signal = generate_stat_arb_signals(prices, lookback=20)
final_signal += stat_arb_signal

# Generate and add the new FX Volatility-Adjusted Mean Reversion signal
print("  - Calculating FX Volatility-Adjusted Mean Reversion signals...")
fx_signal = generate_fx_signals(prices[FX_UNIVERSE], lookback=50, volatility_period=14)
final_signal[FX_UNIVERSE] += fx_signal[FX_UNIVERSE]


# --- 4. Combine the Signals into a Final Hybrid Signal ---
print("Combining signals into a final hybrid signal...")
# Get the last row of the combined signal DataFrame
today_signal = final_signal.iloc[-1]

# --- 5. Calculate Weights from the Final Signal ---
# Let's go long the top 3 and short the bottom 3 of the final hybrid signal.
top3 = today_signal.nlargest(3).index
bot3 = today_signal.nsmallest(3).index

weight = pd.Series(0.0, index=universe)
weight[top3] = 1.0
weight[bot3] = -1.0

# Ensure the weights sum to zero (market neutral) and scale them
if weight.abs().sum() > 0:
    weight = weight / weight.abs().sum()

# --- 6. Build Output and Save File ---
out = {
    "date": dt.datetime.now(dt.UTC).date().isoformat(),
    "generation_time_utc": dt.datetime.now(dt.UTC).isoformat(),
    "model_version": "v3.1.0-multi-strategy", # Updated version name
    "universe": universe,
    "signal": today_signal.round(4).tolist(),
    "weight": weight.round(4).tolist(),
    "target_vol": "0.10"
}

# --- 7. Write file + md5 ---
import os
import pathlib
pathlib.Path("signals").mkdir(exist_ok=True)
fname = f"signals/{out['date']}.json"
with open(fname, "w") as f:
    json.dump(out, f, indent=2)

md5 = hashlib.md5(open(fname, "rb").read()).hexdigest()
with open(fname.replace(".json", ".md5"), "w") as f:
    f.write(md5)

print("\nMulti-strategy signal generation complete.")
print("Final Signal Values:")
print(today_signal.sort_values())
print("\nFinal Weights:")
print(weight.sort_values())
print("\nSignal file:", fname, "MD5:", md5)