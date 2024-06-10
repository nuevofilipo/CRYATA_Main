import pandas as pd
import sys
import time
import ccxt
import logging


sys.path.append("../../")

from backend.moduls.getTwelveData import getResponse
from backend.moduls.indicatorFunctions import (
    create4Lines,
    createVarv,
    momentumIndicator,
)


def contextBandsCalculation(df):
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

    return marketCondition  # return a int from 5 possible values


def varvIndicatorMetric(df, timeframe):
    if timeframe != "1d":
        return -1

    price = df.iloc[-1]["Close"]
    dfVarv = createVarv(df, timeframe)

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
    return zone - 1  # return an integer from 1 to 12


def momentumIndicatorMetric(df):
    combinedDf = momentumIndicator(df, df)

    # case when there is not enough data
    if combinedDf.empty:
        return 0

    combinedDf = combinedDf.sort_values(by="x0")
    dfLastRow = combinedDf.iloc[-1]
    if dfLastRow["color"] == "#2af5c2":
        return 1
    elif dfLastRow["color"] == "#f52a45":
        return -1


def meanAbsoluteDeviation(df):  # helper function

    mean = df["Close"].mean()
    deviation = abs(df["Close"] - mean).mean()
    return deviation


def volatilityMeanAbsolute(df, pastCandles=100):
    last100Df = df.iloc[-pastCandles:]

    meanAbsoluteDev = meanAbsoluteDeviation(last100Df)

    mean = last100Df["Close"].rolling(pastCandles).mean()
    volatility = meanAbsoluteDev / mean
    return round(volatility.iloc[-1] * 100, 1)  # rounding to one number after comma


# Performances --------------------------------------------
def meanPerformance(df):
    last100Df = df.iloc[-100:]
    mean = ((last100Df["Close"] - last100Df["Open"]) / last100Df["Open"]).mean()
    return round(mean * 100, 3)


def medianPerformance(df):
    last100Df = df.iloc[-100:]
    median = ((last100Df["Close"] - last100Df["Open"]) / last100Df["Open"]).median()
    return round(median * 100, 3)


def createTableRow(df, coin, timeframe, priceChangeDict={}):
    pastCoinName = coin[: len(coin) - 2] + "1m"  # btcusdt1m, for every timeframe

    lastRow = df.iloc[-1]
    price = lastRow["Close"]

    pastDataValue = price
    priceChange = "no data"
    if pastCoinName in priceChangeDict:
        pastDataValue = priceChangeDict[pastCoinName].iloc[0]["Open"]
        priceChange = round((price - pastDataValue) / pastDataValue * 100, 1)

    coin = coin[: len(coin) - 6].upper()

    dict_entry = {}
    if timeframe == "1d":
        dict_entry = {
            "coin": coin,
            "price": price,
            "priceChange": priceChange,
            "contextBands": contextBandsCalculation(df),
            "varvIndicator": varvIndicatorMetric(df, timeframe),
            "momentumIndicator": momentumIndicatorMetric(df),
            "volatilityMean1d": str(volatilityMeanAbsolute(df, 200)) + " %",
            "volatilityMean4h": str(volatilityMeanAbsolute(df, 100)) + " %",
            "volatilityMean1h": str(volatilityMeanAbsolute(df, 22)) + " %",
            "volatilityMean1w": str(volatilityMeanAbsolute(df, 400)) + " %",
            "meanPerformance": str(meanPerformance(df)) + " %",
            "medianPerformance": str(medianPerformance(df)) + " %",
        }
    else:
        dict_entry = {
            "coin": coin,
            "price": price,
            "priceChange": priceChange,
            # "fourLineIndicator": contextBandsCalculation(df),
            "varvIndicator": varvIndicatorMetric(df, timeframe),
            "momentumIndicator": momentumIndicatorMetric(df),
            "meanPerformance": str(meanPerformance(df)) + " %",
            "medianPerformance": str(medianPerformance(df)) + " %",
        }
    return dict_entry


def createEntireTable():  # for experimenting -- not used for any calculations
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


def main():  # for experimenting -- not used for any calculations
    df = getResponse("BTC/USD", "1day", 1000)
    # print(createTableRow(df, "BTC/USD", "1d"))
    print(meanPerformance(df))
