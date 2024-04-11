import pandas as pd
import sys
import time


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


def meanAbsoluteDeviation(df):  # helper function

    mean = df["Close"].mean()
    deviation = abs(df["Close"] - mean).mean()
    return deviation


def volatilityMeanAbsolute(df):
    last100Df = df.iloc[-100:]

    meanAbsoluteDev = meanAbsoluteDeviation(last100Df)

    mean = last100Df["Close"].rolling(100).mean()
    volatility = meanAbsoluteDev / mean
    return volatility.iloc[-1] * 100


def volatilityMedianAbsolute(df):
    last100Df = df.iloc[-100:]

    medianAbsoluteDev = abs(df["Close"] - df["Close"].median()).median()

    mean = last100Df["Close"].rolling(100).mean()
    volatility = medianAbsoluteDev / mean
    return volatility.iloc[-1] * 100


def createTableRow(df, coin):
    # print(f"Creating table row for {coin}")
    lastRow = df.iloc[-1]
    price = lastRow["Close"]

    coin = coin[: len(coin) - 6].upper()

    dict_entry = {
        "coin": coin,
        "price": price,
        "fourLineIndicator": fourLineIndicatorMetric(df),
        "varvIndicator": varvIndicatorMetric(df),
        "momentumIndicator": momentumIndicatorMetric(df),
        "volatilityMeanAbsolute": volatilityMeanAbsolute(df),
        "volatilityMedianAbsolute": volatilityMedianAbsolute(df),
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


def main():
    df = getResponse("BTC/USD", "1day", 1000)
    volatility = volatilityIndicatorMetric(df)
    print(f" standard deviation Volatility: {volatility}")
    medianAbs = volatilityMedianAbsolute(df)
    print(f"Median absolute volatility: {medianAbs}")
    meanAbs = volatilityMeanAbsolute(df)
    print(f"Mean absolute volatility: {meanAbs}")


# main()
