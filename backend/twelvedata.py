import requests as rq

# packages needed for data fetching from binance API
# this is what actually happens on an import:
#       pd = __import__("pandas")
import pandas as pd

from binance.spot import Spot as Client

# importing gettingData function
from moduls.gettingDataF import gettingData

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


url = "https://api.twelvedata.com/time_series?end_date=2023-11-23&outputsize=20&symbol=BTC/USD&interval=1day&apikey=aa3e44f41ce445f49a5dc838a1ecfd59"




def getResponse():
    response = session.get(url)
    json_data = response.json()


    # df = pd.DataFrame(json_data["values"])

    # creating a class instance and assigning the json values to it
    instanceCryptoData = CryptoData(meta=json_data["meta"], values=json_data["values"], status=json_data["status"])

    # print(instanceCryptoData.values)
    df = pd.DataFrame(instanceCryptoData.values)
    print(df)


if __name__ == "__main__":
    getResponse()
