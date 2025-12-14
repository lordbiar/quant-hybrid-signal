import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def load_or_download_data():
    """Return yesterday’s close for the configured universe."""
    universe = ["SPY", "QQQ", "IWM", "GLD", "BTC-USD", "ETH-USD", "EURUSD=X"]
    today   = datetime.utcnow().date()
    start   = today - timedelta(days=5)
    df = yf.download(universe, start=start, end=today, interval="1d", auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError("YFinance download failed")
    close = df["Close"].dropna()
    # make sure we use the last COMPLETE day only
    if close.index[-1].date() >= today:
        close = close.iloc[:-1]
    return close