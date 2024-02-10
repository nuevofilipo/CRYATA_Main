import requests as rq

# packages needed for data fetching from binance API
import pandas as pd

from binance.spot import Spot as Client

# importing to cache
from dataclasses import dataclass
from requests_cache import CachedSession

from datetime import datetime


# this allows to cache the data
session = CachedSession(cache_name="cache/cached_btc", expire_after=60)  # seconds


# class which can save the json crypto data
@dataclass
class CryptoData:
    def __init__(self, meta, values, status):
        self.meta = meta
        self.values = values
        self.status = status


url = "https://api.twelvedata.com/time_series?"


def getResponse(coin, candleTimeFrame, limit):

    now = datetime.now()

    parameters = {
        "end_date": now,
        "outputsize": limit,
        "symbol": coin,
        "interval": candleTimeFrame,
        "exchange": "Binance",
        "apikey": "aa3e44f41ce445f49a5dc838a1ecfd59",
    }

    response = rq.get(url, params=parameters)
    json_data = response.json()

    # creating a class instance and assigning the json values to it this is used for caching

    # instanceCryptoData = CryptoData(
    #     meta=json_data["meta"], values=json_data["values"], status=json_data["status"]
    # )

    df = pd.DataFrame(json_data["values"])

    # renaming columns to match exactly those from binance
    column_mapping = {
        "datetime": "time",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
    }

    # "inplace" means, that it applies it directly to the object, and you don't need to assign it again to another variable
    df.rename(columns=column_mapping, inplace=True)

    # reversing df
    df = df.iloc[::-1].reset_index(drop=True)

    # have to make floats out of it, as it is initialized as string
    df[
        [
            "Open",
            "High",
            "Low",
            "Close",
        ]
    ] = df[
        [
            "Open",
            "High",
            "Low",
            "Close",
        ]
    ].astype(float)

    df["time"] = pd.to_datetime(df["time"])

    df = fixingData(df)
    return df


def fixingData(df):
    prev_low = 0

    for index, row in df.iterrows():
        if index == 0:
            prev_low = row["Low"]
        elif (row["Low"] / prev_low) < 0.1:
            df.at[index, "Low"] = prev_low
        else:
            prev_low = row["Low"]

    prev_high = 0

    for index, row in df.iterrows():
        if index == 0:
            prev_high = row["High"]
        elif (row["High"] / prev_high) > 10:
            df.at[index, "High"] = prev_high
        else:
            prev_high = row["High"]

    return df


# print(getResponse("BTC/USD", "1month", 200).to_string())
