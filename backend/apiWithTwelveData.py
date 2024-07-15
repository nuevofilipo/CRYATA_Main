from flask import Flask, request
from flask_caching import Cache
from flask_cors import CORS

import json, time
from datetime import datetime
import pandas_ta as tan

from scipy.signal import savgol_filter
from scipy.signal import find_peaks

import numpy as np
import pandas as pd

from moduls.getTwelveData import getResponse
from moduls.indicatorFunctions import (
    supplyDemandZonesCalc,
    momentumCalc,
    varvCalc,
    contextBandsCalc,
    imbalanceZonesCalc,
    rangesCalc,
    createQuarterlyCandles,
    create_yearly_candles,
)


app = Flask(__name__)
CORS(app)

#! global variables and small helper functions
mainLimitGlobal = 2000


def intToTime(integer, dataframe):
    timestamp = dataframe.index[integer]
    return timestamp


def transformDf(df):
    df.set_index("time", inplace=True)
    return df


def main_data_fetch(coin, timeframe, limit=mainLimitGlobal):
    return getResponse(coin, timeframe, limit)


#! from here on API FUNCTIONALITY ------------------------------
def make_cache_key(coin, timeframe, limits):
    return f"{coin}_{timeframe}_{limits}"


@app.route("/api/query/", methods=["GET"])
def query_data():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = main_data_fetch(user_query, timeframe_query)
    return df.to_json(orient="records")


@app.route("/api/supplyDemand/", methods=["GET"])
def query_nodbzones():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    indicator_query = str(request.args.get("indicatorTimeframe"))
    df2 = main_data_fetch(user_query, indicator_query)
    df = main_data_fetch(user_query, timeframe_query)
    zones_df = supplyDemandZonesCalc(df2, chartDf=df)

    json_data = zones_df.to_json(orient="records")
    return json_data


@app.route("/api/imbalanceZones/", methods=["GET"])
def query_imbalanceZones():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    indicator_query = str(request.args.get("indicatorTimeframe"))
    df = main_data_fetch(user_query, indicator_query)
    df = transformDf(df)
    zones_df = imbalanceZonesCalc(df)
    json_data = zones_df.to_json(orient="records")
    return json_data


@app.route("/api/momentum/", methods=["GET"])
def query_momentum():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    indicator_query = str(request.args.get("indicatorTimeframe"))

    chart_df = main_data_fetch(user_query, timeframe_query)
    indicator_df = main_data_fetch(user_query, indicator_query)
    df_combined = momentumCalc(indicator_df, chart_df)
    return df_combined.to_json(orient="records")


@app.route("/api/varv/", methods=["GET"])
def query_varv():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    chart_df = main_data_fetch(user_query, timeframe_query)
    df = main_data_fetch(user_query, "1day")
    df2 = varvCalc(df, timeframe_query, chart_df)
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
    df3 = rangesCalc(df, df2)
    return df3.to_json(orient="records")


@app.route("/api/4lines/", methods=["GET"])
def query_4lines():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    chart_df = main_data_fetch(user_query, timeframe_query)

    if timeframe_query != "1week" and timeframe_query != "1day":

        df = main_data_fetch(user_query, "1day")
    else:
        df = chart_df

    df1 = contextBandsCalc(df, timeframe_query, chart_df)
    return df1.to_json(orient="records")


if __name__ == "__main__":
    app.run(debug=True)
