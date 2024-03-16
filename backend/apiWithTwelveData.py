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
from binance.spot import Spot as Client

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

mainLimit = 1000


# helper functions
def gettingData(coin, candleTimeFrame, limit):
    return getResponse(coin, candleTimeFrame, limit)


def intToTime(integer, dataframe):
    timestamp = dataframe.index[integer]
    return timestamp


def imbalanceZones(df):
    df_length = len(df.index)
    zonesRed = []
    updated_zonesRed = []
    for index, row in df.iterrows():
        if row["Open"] > row["Close"]:  # this means this is a red candle
            integer_idx = df.index.get_loc(index)
            if integer_idx > 4 and integer_idx < df_length - 4:
                high_boundary = df.loc[
                    intToTime(integer_idx - 4, df) : intToTime(integer_idx - 1, df),
                    "Low",
                ].min()
                low_boundary = df.loc[
                    intToTime(integer_idx + 1, df) : intToTime(integer_idx + 4, df),
                    "High",
                ].max()
                end_plot = df.index[-1]
                # print(high_boundary)
                # print(low_boundary)
                # print("-------------------")
                # i += 1
                if high_boundary - low_boundary > 0:
                    zone = {
                        "x0": index,
                        "y0": low_boundary,
                        "x1": end_plot,
                        "y1": high_boundary,
                    }
                    zonesRed.append(zone)
        for zone in zonesRed:
            if row["High"] > (zone["y1"] + zone["y0"]) / 2 and zone["x0"] != index:
                zone["x1"] = index
                updated_zonesRed.append(zone)
                zonesRed.remove(zone)

    zonesGreen = []
    updated_zonesGreen = []
    for index, row in df.iterrows():
        if row["Open"] < row["Close"]:
            integer_idx = df.index.get_loc(index)
            if integer_idx > 4 and integer_idx < df_length - 4:
                low_boundary = df.loc[
                    intToTime(integer_idx - 4, df) : intToTime(integer_idx - 1, df),
                    "High",
                ].max()
                high_boundary = df.loc[
                    intToTime(integer_idx + 1, df) : intToTime(integer_idx + 4, df),
                    "Low",
                ].min()
                end_plot = df.index[-1]
                # print(high_boundary)
                # print(low_boundary)
                # print("-------------------")
                # i += 1
                if high_boundary - low_boundary > 0:
                    zone = {
                        "x0": index,
                        "y0": low_boundary,
                        "x1": end_plot,
                        "y1": high_boundary,
                    }
                    zonesGreen.append(zone)

        for zone in zonesGreen:
            if row["Low"] < (zone["y1"] + zone["y0"]) / 2 and zone["x0"] != index:
                zone["x1"] = index
                updated_zonesGreen.append(zone)
                zonesGreen.remove(zone)

    all_zones = updated_zonesRed + updated_zonesGreen + zonesGreen + zonesRed

    zones_df = pd.DataFrame(all_zones)
    return zones_df


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
    penultimateCandle = range_df.iloc[-2]
    if penultimateCandle.name < df.index[0]:
        penultimateCandle.name = df.index[0]
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


# this is a function used for making keys for caching
def make_cache_key(*args, **kwargs):
    return request.url


# this is the main function for getting data and then caching it
@cache.cached(timeout=60, key_prefix=make_cache_key)
def main_data_fetch(coin, timeframe, limits=mainLimit):
    data = gettingData(coin, timeframe, limits)
    return data


@app.route("/api/query/", methods=["GET"])  # regular endpoint for simply getting data
def query_nodb():
    user_query = str(request.args.get("coin"))  # /user/?user=USER_NAME
    timeframe_query = str(request.args.get("timeframe"))
    df = main_data_fetch(user_query, timeframe_query)
    return df.to_json(orient="records")


@app.route(
    "/api/zones/", methods=["GET"]
)  # endpoint for getting suply and demand zones
def query_nodbzones():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = main_data_fetch(user_query, timeframe_query)
    zones_df = supplyDemandZones(df)  # working on
    json_data = zones_df.to_json(orient="records")
    return json_data


@app.route("/api/zones2/", methods=["GET"])  # endpoint for getting imbalance zones
def query_zones2():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = main_data_fetch(user_query, timeframe_query)
    df = transformDf(df)
    zones_df = imbalanceZones(df)
    json_data = zones_df.to_json(orient="records")
    return json_data


@app.route(
    "/api/momentum/", methods=["GET"]
)  # http://127.0.0.1:5000/api/momentum/?coin=BTC/USD&timeframe=1day
def query_momentum():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = main_data_fetch(user_query, timeframe_query)
    red_boxes, green_boxes = momentumIndicator(df)
    df_combined = pd.concat([red_boxes, green_boxes])
    return df_combined.to_json(orient="records")


@app.route("/api/varv/", methods=["GET"])
def query_varv():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = main_data_fetch(user_query, timeframe_query)
    df2 = createVarv(df)
    return df2.to_json(orient="records")


@app.route("/api/ranges/", methods=["GET"])
def query_ranges():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    ranges_query = str(
        request.args.get("ranges")
    )  # here we get which range we want to see
    if ranges_query == "1y":
        df = transformDf(
            main_data_fetch(user_query, "1month", 100)
        )  # I need to change the syntax here, however don't know exactly what it is
        df2 = create_yearly_candles(df)
    elif ranges_query == "3m":
        df = transformDf(main_data_fetch(user_query, "1month", 1000))
        df2 = createQuarterlyCandles(create_yearly_candles(df), df)
    elif ranges_query == "1m":
        df2 = transformDf(main_data_fetch(user_query, "1month", 1000))
    else:
        df2 = transformDf(main_data_fetch(user_query, ranges_query, 1000))
    df = transformDf(main_data_fetch(user_query, timeframe_query, 1000))
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
