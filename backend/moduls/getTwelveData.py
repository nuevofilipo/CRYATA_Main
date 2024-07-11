import requests as rq
import pandas as pd
from datetime import datetime
import numpy as np

# needed for caching
import redis
import json
from functools import lru_cache

redis_client = redis.Redis(host="localhost", port=6379, db=0)

CACHE_EXPIRATION = 60  # one minute


def cache_key(coin, candleTimeFrame, limit):
    return f"{coin}-{candleTimeFrame}-{limit}"


@lru_cache(maxsize=128)
def getResponse(coin, candleTimeFrame, limit):
    key = cache_key(coin, candleTimeFrame, limit)
    cached_data = redis_client.get(key)
    if cached_data:
        cached_data_str = cached_data.decode("utf-8")
        return pd.read_json(cached_data_str)

    result = None
    if coin.endswith("BTC"):
        coin_df = getResponse(coin[:-3] + "USD", candleTimeFrame, limit)
        btc_df = getResponse("BTC/USD", candleTimeFrame, limit)
        result = create_result_df(coin_df, btc_df)
    else:
        try:
            data = getTwelveData(coin, candleTimeFrame, limit)
        except:
            print("TwelveData API failed, trying CCXT API")
            data = getCCXTData(coin, candleTimeFrame, limit)
        result = data

    redis_client.setex(key, CACHE_EXPIRATION, result.to_json())
    return result


def create_result_df(coin_df, btc_df):
    # Find common time values
    common_times = np.intersect1d(coin_df["time"], btc_df["time"])

    coin_df = coin_df[coin_df["time"].isin(common_times)]
    btc_df = btc_df[btc_df["time"].isin(common_times)]

    coin_df = coin_df.sort_values("time")
    btc_df = btc_df.sort_values("time")

    result_df = pd.DataFrame()

    result_df["time"] = common_times

    columns = ["Open", "High", "Low", "Close"]
    result_df[columns] = coin_df[columns].values / btc_df[columns].values

    return result_df


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


def getTwelveData(coin, candleTimeFrame, limit):
    url = "https://api.twelvedata.com/time_series?"

    now = datetime.now()

    parameters = {
        "end_date": now,
        "outputsize": limit,
        "symbol": coin,  # "BTC/USD",
        "interval": candleTimeFrame,  # "1day",
        "exchange": "Binance",
        "apikey": "aa3e44f41ce445f49a5dc838a1ecfd59",
    }

    response = rq.get(url, params=parameters)
    json_data = response.json()

    df = pd.DataFrame(json_data["values"])

    # renaming columns to match exactly those from binance
    column_mapping = {
        "datetime": "time",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
    }

    # "inplace" means, that it applies it directly to the object, and you don't need to assign it again to another df1 variable or so
    df.rename(columns=column_mapping, inplace=True)

    # reversing df
    df = df.iloc[::-1].reset_index(drop=True)

    # making floats out of it, as it is initialized as string
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


def getCCXTData(coin, candleTimeFrame, limit):
    proxyUrl = "https://vercel-proxy-api-cyan.vercel.app"

    # coin needs to be in this format BTCUSDT but is currently in BTC/USD
    coin = coin.replace("/", "")
    coin += "T"

    columns = [
        "time",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    # timeframe mapping
    timeFrameMapping = {
        "1h": "1h",
        "4h": "4h",
        "1day": "1d",
        "1week": "1w",
        "1month": "1M",
    }

    timeStampMapping = {
        "1h": 3600000,
        "4h": 14400000,
        "1d": 86400000,
        "1w": 604800000,
        "1M": 2592000000,
    }

    candleTimeFrame = timeFrameMapping[candleTimeFrame]

    timeframe_ms = timeStampMapping[candleTimeFrame]
    now_ms = int(datetime.now().timestamp() * 1000)
    since_ms = now_ms - (limit * timeframe_ms)

    response = rq.get(
        proxyUrl,
        params={
            "symbol": coin,
            "timeframe": candleTimeFrame,
            "limit": limit,
            "since": since_ms,
        },
    )

    try:
        data = response.json()
        df = pd.DataFrame(data, columns=columns)
        # dropping volume column
        df.drop(columns=["Volume"], inplace=True)
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        return df
    except:
        return pd.DataFrame(columns=columns)


# output = getResponse("ETH/BTC", "1day", 100)
# print(output)
