#!/usr/bin/env python3
import json, hashlib, datetime as dt, pandas as pd
from download_data import load_or_download_data

# 1. grab live prices
prices = load_or_download_data()

# 2. simple equal-weight signal for today (we'll improve later)
universe = prices.columns.tolist()
last_price = prices.iloc[-1]
signal   = pd.Series(0.0, index=universe)
weight   = pd.Series(0.0, index=universe)

# dummy logic: long 3 highest-price assets, short 3 lowest
top3 = last_price.nlargest(3).index
bot3 = last_price.nsmallest(3).index
signal[top3] =  1.0
signal[bot3] = -1.0
weight = signal / 6.0   # gross 50 %, net 0 %

# 3. build output
out = {
    "date": prices.index[-1].date().isoformat(),
    "generation_time_utc": dt.datetime.utcnow().isoformat(),
    "model_version": "v1.0.0",
    "universe": universe,
    "signal": signal.round(2).tolist(),
    "weight": weight.round(2).tolist(),
    "target_vol": "0.10"
}

# 4. write file + md5
import os, pathlib
pathlib.Path("signals").mkdir(exist_ok=True)
fname = f"signals/{out['date']}.json"
with open(fname, "w") as f:
    json.dump(out, f, indent=2)

md5 = hashlib.md5(open(fname, "rb").read()).hexdigest()
open(fname.replace(".json", ".md5"), "w").write(md5)

print("Signal file:", fname, "MD5:", md5)