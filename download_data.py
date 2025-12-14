import yfinance as yf
import pandas as pd
import datetime as dt
import time

def load_or_download_data():
    """
    Downloads the latest market data for a given universe of assets.
    Implements a retry mechanism for network issues and validates the
    downloaded data to prevent errors from empty datasets.
    """
    universe = ["SPY", "QQQ", "IWM", "GLD", "BTC-USD", "ETH-USD", "EURUSD=X"]
    today = dt.datetime.utcnow().date()
    # --- CHANGE: Download 90 days of data to satisfy all strategy lookback periods ---
    start = today - dt.timedelta(days=90)

    print("Attempting to download market data...")

    # Retry loop for transient network errors (e.g., connection issues)
    for attempt in range(3):
        try:
            # Download data. `end` is today+1 to ensure we get today's bar if it's already closed.
            df = yf.download(
                universe,
                start=start,
                end=today + dt.timedelta(days=1),
                interval="1d",
                auto_adjust=True,
                progress=False
            )

            # --- Data Validation (This prevents the IndexError) ---
            # 1. Check if the download returned any data at all.
            if df.empty:
                raise ValueError("yfinance returned an empty DataFrame.")

            # 2. Extract the 'Close' prices and drop any rows with missing data.
            close = df["Close"].dropna()

            # 3. Filter to keep only fully completed market days.
            #    This prevents using a partial bar for the current day.
            close = close[close.index.date < today]

            # 4. Final check: ensure we still have data after filtering.
            if close.empty:
                raise ValueError("No complete data bars found for the specified period.")

            print(f"Successfully downloaded and validated data. Found {len(close)} days of data.")
            return close

        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt == 2:  # If this was the last attempt, re-raise the error
                raise RuntimeError("Failed to download data after 3 retries.") from e
            print("Waiting 5 seconds before retrying...")
            time.sleep(5)
