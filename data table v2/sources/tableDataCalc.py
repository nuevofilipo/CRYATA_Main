import pandas as pd
import sys

sys.path.append("../../")

from backend.moduls.getTwelveData import getResponse
from backend.moduls.indicatorFunctions import create4Lines, createVarv


def createTableRow(df):
    # perform heavy calculations with some functions to be created

    dict_entry = df.iloc[-1].to_dict()
    return dict_entry


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
    price = 20000
    dfVarv = createVarv(df)
    dfLastRow = dfVarv.iloc[-1]

    zone = 1

    for i in range(1, 12):
        if price < dfLastRow[f"out{i}"]:
            break
        else:
            zone += 1
    return zone  # return an integer from 1 to 12


def main():
    df = getResponse(
        "BTC/USD",
        "1day",
        1000,
    )

    varvIndicatorMetric(df)


main()
