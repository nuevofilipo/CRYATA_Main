import pandas as pd
import sys
import time
import ccxt


sys.path.append("../../")

from backend.moduls.getTwelveData import getResponse
from backend.moduls.indicatorFunctions import (
    create4Lines,
    createVarv,
    momentumIndicator,
)


def fourLineIndicatorMetric(df):
    df4Lines = create4Lines(df, "1day")
    dfLastRow = df4Lines.iloc[-1]
    upperMA = dfLastRow["MA"] * 1.62
    lowerMA = dfLastRow["MA"] * 0.62
    upperEMA = dfLastRow["EMA"] * 1.21
    lowerEMA = dfLastRow["EMA"] * 0.79

    marketCondition = 0  # default value

    if dfLastRow["Close"] > upperMA:
        marketCondition = 2
    elif dfLastRow["Close"] <= upperMA and dfLastRow["Close"] > upperEMA:
        marketCondition = 1
    elif dfLastRow["Close"] <= upperEMA and dfLastRow["Close"] > lowerEMA:
        marketCondition = 0
    elif dfLastRow["Close"] <= lowerEMA and dfLastRow["Close"] > lowerMA:
        marketCondition = -1
    elif dfLastRow["Close"] <= lowerMA:
        marketCondition = -2

    return marketCondition  # return a string from 5 possible values


def varvIndicatorMetric(df):
    price = df.iloc[-1]["Close"]
    dfVarv = createVarv(df)

    try:
        dfLastRow = dfVarv.iloc[-1]
    except:
        return "not sufficient data"

    zone = 1

    for i in range(1, 12):
        if price < dfLastRow[f"out{i}"]:
            break
        else:
            zone += 1
    return zone  # return an integer from 1 to 12


def momentumIndicatorMetric(df):
    redDf = momentumIndicator(df)[0]
    greenDf = momentumIndicator(df)[1]
    dataframes = [redDf, greenDf]

    # case when there is not enough data
    if redDf.empty or greenDf.empty:
        return 0

    combinedDf = pd.concat(dataframes).sort_values(by="x0")
    dfLastRow = combinedDf.iloc[-1]
    if dfLastRow["color"] == "#2af5c2":
        return 1
    elif dfLastRow["color"] == "#f52a45":
        return -1


def volatilityIndicatorMetric(df):
    last100Df = df.iloc[-100:]

    standardDeviation = (
        last100Df["Close"].rolling(100).std()
    )  # change from std to mad, check whether it works
    mean = last100Df["Close"].rolling(100).mean()
    volatility = standardDeviation / mean
    return volatility.iloc[-1] * 100


# def meanAbsoluteDeviation(df):  # helper function
#     mean = df["Close"].mean()
#     deviation = abs(df["Close"] - mean).mean()
#     return deviation


# def volatilityMeanAbsolute(df):
#     last100Df = df.iloc[-100:]

#     meanAbsoluteDev = meanAbsoluteDeviation(last100Df)

#     mean = last100Df["Close"].mean()
#     volatility = meanAbsoluteDev / mean
#     return round(volatility * 100, 1)  # rounding to one number after comma


# def volatilityMedianAbsolute(df):
#     last100Df = df.iloc[-100:]

#     medianAbsoluteDev = abs(last100Df["Close"] - last100Df["Close"].mean()).median()

#     mean = last100Df["Close"].mean()
#     volatility = medianAbsoluteDev / mean
#     return round(volatility * 100, 1)  # rounding to one number after comma


def volatilities(df):
    last100Df = df.iloc[-100:]

    mean = last100Df["Close"].mean()
    deviation = abs(last100Df["Close"] - mean)
    meanAbsoluteDeviation = round((deviation.mean() / mean) * 100, 1)
    medianAbsoluteDeviation = round((deviation.median() / mean) * 100, 1)
    return meanAbsoluteDeviation, medianAbsoluteDeviation


def priceChangePercent(df):
    oneDayAgo = df.iloc[-24]
    priceChangePercent = df.iloc[-1]["Close"] / oneDayAgo["Open"]
    return round((priceChangePercent - 1) * 100, 1)


def createTableRow(df, coin, timeframe="1d"):
    # print(f"Creating table row for {coin}")
    lastRow = df.iloc[-1]
    price = lastRow["Close"]

    coin = coin[: len(coin) - 6].upper()

    priceChange = "no data"
    if timeframe == "1h":
        priceChange = priceChangePercent(df)

    dict_entry = {
        "coin": coin,
        "price": price,
        "priceChange": priceChange,
        "fourLineIndicator": fourLineIndicatorMetric(df),
        "varvIndicator": varvIndicatorMetric(df),
        "momentumIndicator": momentumIndicatorMetric(df),
        "volatilityMeanAbsolute": str(volatilities(df)[0]) + " %",
        "volatilityMedianAbsolute": str(volatilities(df)[1]) + " %",
    }

    return dict_entry


def createEntireTable():
    allEntries = []
    coins = ["BTC/USD", "ETH/USD", "ADA/USD", "XRP/USD", "DOGE/USD"]
    totalTime = 0

    for coin in coins:
        df = getResponse(
            coin,
            "1day",
            1000,
        )
        start = time.time()
        entry = createTableRow(df, coin)
        end = time.time()
        print(f"Time for {coin}: {end - start} sec")
        totalTime += end - start
        allEntries.append(entry)

    print(f"Total time: {totalTime}")
    return allEntries


def transformingDF(df):
    try:
        df["time"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df[["time", "open", "high", "low", "close", "volume"]]
        df[["open", "high", "low", "close", "volume"]] = df[
            ["open", "high", "low", "close", "volume"]
        ].astype(float)
        return df
    except Exception as e:
        print(e)


def main():
    df = getResponse("BTC/USD", "1day", 1000)

    print(createTableRow(df, "BTC/USD"))


# main()
