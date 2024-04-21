import ccxt
import pandas as pd

listOfTopCoins = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "TONUSDT",
    "ADAUSDT",
    "SHIBUSDT",
    "AVAXUSDT",
    "DOTUSDT",
    "BCHUSDT",
    "TRXUSDT",
    "LINKSUSDT",
    "MATICUSDT",
    "ICPUSDT",
    "NEARUSDT",
    "LTCUSDT",
    "DAIUSDT",
    "LEOUSDT",
    "UNIUSDT",
    "APTUSDT",
    "STXUSDT",
    "ETCUSDT",

]

ex = ccxt.binance()
markets = ex.fetchMarkets()
btcticker = ex.fetch_ticker("BTC/USDT")


df = pd.DataFrame(markets)
filtered_df = df[df["id"].str.endswith("USDT")]
valuesList = filtered_df["id"].values.tolist()
print(sorted(valuesList))
# btcdf = pd.DataFrame(btcticker)
# print(btcdf.to_string())
