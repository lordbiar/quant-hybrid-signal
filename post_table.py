#!/usr/bin/env python3
import requests
import datetime as dt
import pandas as pd
from tabulate import tabulate

def fetch_and_display_signals():
    """
    Fetches the latest signal data from GitHub and displays it in a formatted table.
    Includes error handling for cases where the data is not yet available.
    Enhanced with visual indicators, sector grouping, and better formatting.
    """
    # Use a consistent date format for the URL and print statements
    today_str = dt.date.today().strftime('%Y-%m-%d')
    url = f"https://raw.githubusercontent.com/lordbiar/quant-hybrid-signal/main/signals/{today_str}.json"

    print(f"📡 Fetching signal data for: {today_str}\n")

    try:
        # Attempt to get the data from the URL
        response = requests.get(url, timeout=10)

        # This will raise an error for bad responses (like 404 Not Found)
        response.raise_for_status()

        # If the request was successful, parse the JSON
        sig = response.json()
        
        # --- Enhanced Table Formatting ---
        # Define asset categories for grouping
        asset_categories = {
            "Equity": ["SPY", "QQQ", "IWM"],
            "Crypto": ["BTC-USD", "ETH-USD"],
            "Commodity": ["GLD"],
            "FX": ["EURUSD=X"]
        }
        
        # Create a mapping from asset to category
        asset_to_category = {}
        for category, assets in asset_categories.items():
            for asset in assets:
                asset_to_category[asset] = category
        
        # Create the DataFrame with additional columns
        df = pd.DataFrame({
            "Asset": sig["universe"],
            "Signal": sig["signal"],
            "Weight %": [round(w*100,1) for w in sig["weight"]],
            "Side": ["Long" if s > 0 else "Short" for s in sig["signal"]],
            "Category": [asset_to_category.get(asset, "Other") for asset in sig["universe"]]
        })
        
        # Add visual signal strength indicators
        df["Strength"] = df["Signal"].apply(lambda x: "█" * int(abs(x) * 5) + "░" * (5 - int(abs(x) * 5)))
        
        # Sort by category and signal strength
        df = df.sort_values(["Category", "Signal"], ascending=[True, False])
        
        # Add color coding for long/short (will be shown in terminal)
        df["Colored_Side"] = df["Side"].apply(lambda x: f"\033[92m{x}\033[0m" if x == "Long" else f"\033[91m{x}\033[0m")
        
        # Create a more detailed table
        detailed_table = tabulate(
            df[["Asset", "Category", "Signal", "Strength", "Weight %", "Colored_Side"]],
            headers=["Asset", "Category", "Signal", "Strength", "Weight %", "Position"],
            tablefmt="grid",
            floatfmt=".4f",
            showindex=False
        )
        
        # Create a summary table by category
        category_summary = df.groupby("Category").agg({
            "Weight %": lambda x: sum(abs(w) for w in x),
            "Asset": "count"
        }).rename(columns={"Asset": "Count"})
        category_summary["Net Exposure"] = df.groupby("Category")["Weight %"].sum()
        
        summary_table = tabulate(
            category_summary,
            headers=["Category", "Total Exposure %", "Count", "Net Exposure %"],
            tablefmt="grid",
            floatfmt=".1f"
        )
        
        # Display the enhanced output
        print(f"📊 HYBRID SIGNAL DASHBOARD – {sig['date']}")
        print("="*80)
        print(f"Model Version: {sig.get('model_version', 'Unknown')}")
        print(f"Generation Time (UTC): {sig.get('generation_time_utc', 'Unknown')}")
        print(f"Target Volatility: {sig.get('target_vol', 'Unknown')}")
        print("="*80)
        
        print("\n📈 PORTFOLIO BREAKDOWN BY CATEGORY")
        print(summary_table)
        
        print("\n📊 DETAILED SIGNALS")
        print(detailed_table)
        
        # Add risk metrics if available
        if "risk_metrics" in sig:
            risk_metrics = sig["risk_metrics"]
            print("\n⚠️  RISK METRICS")
            print(f"Max Position Size: {risk_metrics.get('max_position_size', 0):.1%}")
            
            if "sector_exposure" in risk_metrics:
                print("\nSector Exposure:")
                for sector, exposure in risk_metrics["sector_exposure"].items():
                    print(f"  {sector.title()}: {exposure:.1%}")
        
        print("="*80)
        print("Note: Signal strength bars represent the magnitude of the signal (0-5 bars)")
        print("      Green indicates Long positions, Red indicates Short positions")

    except requests.exceptions.HTTPError as e:
        # Handle cases where the file is not found (404) or other server errors
        if e.response.status_code == 404:
            print(f"❌ Signal file for {today_str} not found.")
            print("   It may not have been generated yet. Please check back later.")
        else:
            print(f"❌ Could not fetch data. Server responded with: {e.response.status_code}")

    except requests.exceptions.JSONDecodeError:
        # Handle cases where the file exists but is not valid JSON
        print(f"❌ Error: The file at the URL is not valid JSON.")
        print(f"   URL: {url}")

    except requests.exceptions.RequestException as e:
        # Handle other network-level errors (e.g., no internet connection)
        print(f"❌ A network error occurred: {e}")

    except KeyError:
        # Handle cases where the JSON is valid but missing expected keys
        print(f"❌ Error: The signal data is missing expected keys (e.g., 'universe', 'signal').")
        print("   The data format may have changed.")


if __name__ == "__main__":
    fetch_and_display_signals()