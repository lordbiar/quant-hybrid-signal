import yfinance as yf, pandas as pd, datetime as dt, time

def load_or_download_data():
    universe = ["SPY", "QQQ", "IWM", "GLD", "BTC-USD", "ETH-USD", "EURUSD=X"]
    today = dt.datetime.utcnow().date()
    start = today - dt.timedelta(days=7)   # wider buffer

    # retry loop for yfinance lock
    for attempt in range(3):
        try:
            df = yf.download(universe, start=start, end=today + dt.timedelta(days=1),
                             interval="1d", auto_adjust=True, progress=False)
            if df.empty:
                raise ValueError("empty download")
            close = df["Close"].dropna()
            # keep only COMPLETED market days
            close = close[close.index.date < today]
            if close.empty:
                raise ValueError("no complete bars")
            return close
        except Exception as e:
            if attempt == 2:
                raise RuntimeError("yfinance failed after 3 retries") from e
            time.sleep(5)