#!/usr/bin/env python3
import requests
import datetime as dt
import pandas as pd

def fetch_and_display_signals():
    """
    Fetches the latest signal data from GitHub and displays it in a formatted table.
    Includes error handling for cases where the data is not yet available.
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

        # --- This is your original, excellent formatting logic ---
        df = pd.DataFrame({
            "Asset": sig["universe"],
            "Signal": sig["signal"],
            "Weight %": [round(w*100,1) for w in sig["weight"]],
            "Side": ["Long" if s > 0 else "Short" for s in sig["signal"]]
        })

        table = df.to_string(index=False)
        print(f"📊 Hybrid Signal – {sig['date']}")
        print("="*len(table.splitlines()[0]))
        print(table)
        print("="*len(table.splitlines()[0]))

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