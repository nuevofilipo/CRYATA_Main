import pandas as pd
import sys

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

    marketCondition = "neutral"  # default value

    if dfLastRow["Close"] > upperMA:
        marketCondition = "extremely overvalued"
    elif dfLastRow["Close"] <= upperMA and dfLastRow["Close"] > upperEMA:
        marketCondition = "overvalued"
    elif dfLastRow["Close"] <= upperEMA and dfLastRow["Close"] > lowerEMA:
        marketCondition = "neutral"
    elif dfLastRow["Close"] <= lowerEMA and dfLastRow["Close"] > lowerMA:
        marketCondition = "undervalued"
    elif dfLastRow["Close"] <= lowerMA:
        marketCondition = "extremely undervalued"

    return marketCondition  # return a string from 5 possible values


def varvIndicatorMetric(df):
    price = df.iloc[-1]["Close"]
    dfVarv = createVarv(df)
    dfLastRow = dfVarv.iloc[-1]

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
    combinedDf = pd.concat(dataframes).sort_values(by="x0")
    dfLastRow = combinedDf.iloc[-1]
    if dfLastRow["color"] == "#2af5c2":
        return 1
    elif dfLastRow["color"] == "#f52a45":
        return -1


def volatilityIndicatorMetric(df):
    last100Df = df.iloc[-100:]

    standardDeviation = last100Df["Close"].rolling(100).std()
    mean = last100Df["Close"].rolling(100).mean()
    volatility = standardDeviation / mean
    return volatility.iloc[-1] * 100


def createTableRow(df, coin):
    lastRow = df.iloc[-1]
    price = lastRow["Close"]

    dict_entry = {
        "coin": coin,
        "price": price,
        "fourLineIndicator": fourLineIndicatorMetric(df),
        "varvIndicator": varvIndicatorMetric(df),
        "momentumIndicator": momentumIndicatorMetric(df),
        "volatilityIndicator": volatilityIndicatorMetric(df),
    }

    return dict_entry


def createEntireTable():
    allEntries = []
    coins = ["BTC/USD", "ETH/USD", "ADA/USD", "XRP/USD", "DOGE/USD"]
    for coin in coins:
        df = getResponse(
            coin,
            "1day",
            1000,
        )
        entry = createTableRow(df, coin)
        allEntries.append(entry)

    return allEntries


def main():
    df = getResponse(
        "BTC/USD",
        "1day",
        1000,
    )

    result = createTableRow(df, "BTC/USD")
    print(result)


main()
