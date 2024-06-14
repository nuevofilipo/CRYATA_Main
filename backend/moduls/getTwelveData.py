import requests as rq
import pandas as pd
from binance.spot import Spot as Client
from datetime import datetime


url = "https://api.twelvedata.com/time_series?"


def getResponse(coin, candleTimeFrame, limit):
    try:
        data = getTwelveData(coin, candleTimeFrame, limit)
    except:
        print("TwelveData API failed, trying CCXT API")
        data = getCCXTData(coin, candleTimeFrame, limit)

    return data


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
        "1day": "1d",
        "1week": "1w",
    }

    timeStampMapping = {
        "1h": 3600000,
        "4h": 14400000,
        "1d": 86400000,
        "1w": 604800000,
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
    data = response.json()
    df = pd.DataFrame(data, columns=columns)
    # dropping volume column
    df.drop(columns=["Volume"], inplace=True)
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    return df


# output = getResponse("BTC/USD", "1day", 100)
# print(output)
