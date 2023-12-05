import requests as rq

# packages needed for data fetching from binance API
# this is what actually happens on an import:
#       pd = __import__("pandas")
import pandas as pd

from binance.spot import Spot as Client

# importing to cache
from dataclasses import dataclass
from requests_cache import CachedSession


# this allows to cache the data
session = CachedSession(
    cache_name='cache/cached_btc',
    expire_after=60
)

# class which can save the json crypto data
@dataclass
class CryptoData:
    def __init__(self, meta, values, status):
        self.meta = meta
        self.values = values
        self.status = status


url = "https://api.twelvedata.com/time_series?"

parameters = {
    "end_date": "2023-11-23",
    'outputsize': 20,
    'symbol': "BTC/USD",
    'interval': "1day",
    'apikey': "aa3e44f41ce445f49a5dc838a1ecfd59"
}


def getResponse():
    response = session.get(url, params=parameters)
    json_data = response.json()


    # df = pd.DataFrame(json_data["values"])

    # creating a class instance and assigning the json values to it
    instanceCryptoData = CryptoData(meta=json_data["meta"], values=json_data["values"], status=json_data["status"])

    # print(instanceCryptoData.values)
    df = pd.DataFrame(instanceCryptoData.values)
    return df




def gettingData(coin, candleTimeFrame, limit):

    # keys from binance
    api_key = "LS2FxhfRjqp6TOv3q2QFOGuQzU8KoSGwlcLIOVaxjRjc0UOhncD2ZRMzT4xRGsfu"
    secret_key = "p3AHHm2sq26yV2y92y0XkFkDxNqE3AAPVphtslNzrmLAJOrMN3r5Gm8ohNolfsXn"

    spot_client = Client(api_key, secret_key)
    btcusd_historical = spot_client.klines(coin, candleTimeFrame, limit=limit)


    # columns to structure incoming data
    columns = [
        "Open time",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        "ignore",
    ]

    # creating the df
    df = pd.DataFrame(btcusd_historical, columns=columns)

    df["time"] = pd.to_datetime(df["Open time"], unit="ms")

    # selecting the data
    df = df[["time", "Open", "High", "Low", "Close", "Volume"]]

    # transforming into float values
    df[["Open", "High", "Low", "Close", "Volume"]] = df[
        ["Open", "High", "Low", "Close", "Volume"]
    ].astype(float)


    # df.set_index("time", inplace=False)
    return df

print(getResponse())
# print(gettingData("BTCUSDT", "1d", 10))