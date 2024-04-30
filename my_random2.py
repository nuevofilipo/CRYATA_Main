import ccxt
import pandas as pd

ex = ccxt.binance()
ms = ex.milliseconds()
msOneHour = ms - 60 * 60 * 1000


data = ex.fetchOHLCV("TRX/USDT", "1m", limit=100, since=msOneHour)

df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])

print(df)
