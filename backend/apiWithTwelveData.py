from flask import Flask, request
from flask_caching import Cache

import json, time
from datetime import datetime

from flask_cors import CORS

# needed for calculating zones
import pandas_ta as tan
from scipy.signal import savgol_filter
from scipy.signal import find_peaks

# import talib as ta # luckily we don't need this anymore

import numpy as np

# packages needed to fetch data
import pandas as pd

from moduls.getTwelveData import getResponse
from moduls.indicatorFunctions import (
    supplyDemandZones,
    momentumIndicator,
    createVarv,
    create4Lines,
    imbalanceZones,
)


cache = Cache()

app = Flask(__name__)
CORS(app)

app.config["CACHE_TYPE"] = "simple"
cache.init_app(app)

mainLimit = 2000


# helper functions
def gettingData(coin, candleTimeFrame, limit):
    return getResponse(coin, candleTimeFrame, limit)


def intToTime(integer, dataframe):
    timestamp = dataframe.index[integer]
    return timestamp


def create_yearly_candles(monthly_candles):
    monthly_candles["Time"] = pd.to_datetime(monthly_candles.index)

    # Group the monthly candles by year
    grouped = monthly_candles.groupby(pd.Grouper(key="Time", freq="Y"))
    yearly_candles = []
    # Iterate over the groups and extract the first and last candles of each year
    for year, group in grouped:
        first_candle = group.iloc[0]
        last_candle = group.iloc[-1]

        year_data = {
            "Time": first_candle["Time"],
            "Open": first_candle["Open"],
            "Close": last_candle["Close"],
        }

        yearly_candles.append(year_data)
    columns = ["Time", "Open", "Close"]
    dfYearlyData = pd.DataFrame(yearly_candles, columns=columns)
    dfYearlyData.set_index("Time", inplace=True)
    return dfYearlyData


def createQuarterlyCandles(yearly_df, monthly_df):
    if yearly_df.empty or monthly_df.empty:
        return pd.DataFrame()

    secondLastCandle = yearly_df.iloc[-1]
    quarterIndex = secondLastCandle.name
    quarterly_candles = []
    while quarterIndex <= monthly_df.index[-3]:
        first_candle = monthly_df.loc[quarterIndex]
        last_candle = monthly_df.loc[quarterIndex + pd.DateOffset(months=2)]
        quarter_data = {
            "Time": first_candle.name,
            "Open": first_candle["Open"],
            "Close": last_candle["Close"],
        }
        quarterly_candles.append(quarter_data)
        quarterIndex = quarterIndex + pd.DateOffset(months=3)
    columns = ["Time", "Open", "Close"]
    dfQuarterlyData = pd.DataFrame(quarterly_candles, columns=columns)
    dfQuarterlyData.set_index("Time", inplace=True)
    return dfQuarterlyData


def addRanges(x0, y0, x1, y1):
    rangeLines = []

    rangeLines.append(
        {
            "x0": x0,
            "y0": y0,
            "x1": x1,
            "y1": y0,
        }
    )

    rangeLines.append(
        {
            "x0": x0,
            "y0": y1,
            "x1": x1,
            "y1": y1,
        }
    )
    middle = (y0 + y1) / 2

    rangeLines.append(
        {
            "x0": x0,
            "y0": middle,
            "x1": x1,
            "y1": middle,
        }
    )

    quarter1 = (y0 + middle) / 2
    quarter2 = (y1 + middle) / 2

    rangeLines.append(
        {
            "x0": x0,
            "y0": quarter1,
            "x1": x1,
            "y1": quarter1,
        }
    )

    rangeLines.append(
        {
            "x0": x0,
            "y0": quarter2,
            "x1": x1,
            "y1": quarter2,
        }
    )
    return rangeLines


def createRanges(df, range_df):
    if df.empty or range_df.empty:
        return pd.DataFrame()

    if len(range_df.index) < 2:
        penultimateCandle = range_df.iloc[0]
    else:
        penultimateCandle = range_df.iloc[-2]
    rangeList = addRanges(
        penultimateCandle.name,
        penultimateCandle["Open"],
        df.index[-1],
        penultimateCandle["Close"],
    )

    df_out = pd.DataFrame(rangeList)
    return df_out


def transformDf(df):
    df.set_index("time", inplace=True)
    return df


# from here on API FUNCTIONALITY ------------------------------
def make_cache_key(coin, timeframe, limits):
    return f"{coin}_{timeframe}_{limits}"


# this is the main function for getting data and then caching it
def main_data_fetch(coin, timeframe, limits=mainLimit):
    @cache.cached(
        timeout=60, key_prefix=lambda: make_cache_key(coin, timeframe, limits)
    )
    def fetchDataInside():
        data = gettingData(coin, timeframe, limits)
        return data

    return fetchDataInside()


@app.route("/api/query/", methods=["GET"])  # regular endpoint for simply getting data
def query_nodb():
    user_query = str(request.args.get("coin"))  # /user/?user=USER_NAME
    timeframe_query = str(request.args.get("timeframe"))
    df = main_data_fetch(user_query, timeframe_query)
    return df.to_json(orient="records")


@app.route(
    "/api/supplyDemand/", methods=["GET"]
)  # endpoint for getting suply and demand zones
def query_nodbzones():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    indicator_query = str(request.args.get("indicatorTimeframe"))
    df2 = main_data_fetch(user_query, indicator_query)
    df = main_data_fetch(user_query, timeframe_query)
    zones_df = supplyDemandZones(df2, chartDf=df)

    json_data = zones_df.to_json(orient="records")
    return json_data


@app.route(
    "/api/imbalanceZones/", methods=["GET"]
)  # !endpoint for getting imbalance zones
def query_imbalanceZones():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    indicator_query = str(request.args.get("indicatorTimeframe"))
    df = main_data_fetch(user_query, indicator_query)
    df = transformDf(df)
    zones_df = imbalanceZones(df)
    json_data = zones_df.to_json(orient="records")
    return json_data


@app.route(
    "/api/momentum/", methods=["GET"]
)  # http://127.0.0.1:5000/api/momentum/?coin=BTC/USD&timeframe=1day&indicatorTimeframe=1week
def query_momentum():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    indicator_query = str(request.args.get("indicatorTimeframe"))

    chart_df = main_data_fetch(user_query, timeframe_query)
    indicator_df = main_data_fetch(user_query, indicator_query)
    df_combined = momentumIndicator(indicator_df, chart_df)
    # df_combined = pd.concat([red_boxes, green_boxes])
    return df_combined.to_json(orient="records")


@app.route("/api/varv/", methods=["GET"])
def query_varv():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = main_data_fetch(user_query, "1day")
    df2 = createVarv(df, timeframe_query)
    return df2.to_json(orient="records")


@app.route("/api/ranges/", methods=["GET"])
def query_ranges():
    coin_name = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    ranges_query = str(request.args.get("indicatorTimeframe"))

    if ranges_query == "1y":
        df = transformDf(main_data_fetch(coin_name, "1month", 100))
        df2 = create_yearly_candles(df)
    elif ranges_query == "3m":
        df = transformDf(main_data_fetch(coin_name, "1month", 1000))
        df2 = createQuarterlyCandles(create_yearly_candles(df), df)
    elif ranges_query == "1m":
        df2 = transformDf(main_data_fetch(coin_name, "1month", 1000))
    else:
        df2 = transformDf(main_data_fetch(coin_name, ranges_query, 1000))
    df = transformDf(main_data_fetch(coin_name, timeframe_query, 1000))
    df3 = createRanges(df, df2)
    return df3.to_json(orient="records")


@app.route("/api/4lines/", methods=["GET"])
def query_4lines():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = main_data_fetch(user_query, timeframe_query)

    df1 = create4Lines(df, timeframe_query)
    return df1.to_json(orient="records")


if __name__ == "__main__":
    app.run(debug=True)
