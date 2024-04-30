import ccxt
import pandas as pd

ex = ccxt.binance()

data = ex.fetchOHLCV("BTC/USDT", "1d", limit=1500, params={"paginate": True})

df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])

print(df)
