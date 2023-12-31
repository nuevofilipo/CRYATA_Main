from flask import Flask, request, jsonify

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text

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


app = Flask(__name__)
CORS(app)
# app.config[
#     "SQLALCHEMY_DATABASE_URI"
# ] = "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee"
# db = SQLAlchemy(app)

# engine = create_engine(
#     "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee", echo=True
# )
# conn = engine.connect()


def gettingData(coin, candleTimeFrame, limit):
    # base_url = "https://api.binance.com"
    api_key = "LS2FxhfRjqp6TOv3q2QFOGuQzU8KoSGwlcLIOVaxjRjc0UOhncD2ZRMzT4xRGsfu"
    secret_key = "p3AHHm2sq26yV2y92y0XkFkDxNqE3AAPVphtslNzrmLAJOrMN3r5Gm8ohNolfsXn"
    spot_client = Client(api_key, secret_key)
    # # spot_client = Client(base_url=base_url) if the other should fail
    limit = limit
    btcusd_historical = spot_client.klines(coin, candleTimeFrame, limit=limit)

    # gettign data the other way, via my own api-------------------
    # BASE_URL = "https://nuevofilipo-1st-test.azurewebsites.net/user/"

    # params = {"coin": coin, "timeframe": candleTimeFrame}

    # response = rq.get(BASE_URL, params=params)
    # json_values = response.json()
    # btcusd_historical = json_values["Data"]

    columns = [
        "Open time",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        "ignore",
    ]

    df = pd.DataFrame(btcusd_historical, columns=columns)
    df["time"] = pd.to_datetime(df["Open time"], unit="ms")
    df = df[["time", "Open", "High", "Low", "Close", "Volume"]]
    df[["Open", "High", "Low", "Close", "Volume"]] = df[
        ["Open", "High", "Low", "Close", "Volume"]
    ].astype(float)

    date_range = df.iloc[-200:]
    min_value = round(float(date_range["Close"].min()))
    max_value = round(float(date_range["Close"].max()))

    # df.set_index("time", inplace=False)
    return df


def create4Lines(df, timeFrame):
    if timeFrame == "1w":
        df["MA"] = tan.sma(df["Close"], length=9)
        df["EMA"] = tan.ema(df["Close"], length=12)
    elif timeFrame == "1d":
        # df["MA"] = ta.SMA(df["Close"], timeperiod=63)
        # df["EMA"] = ta.EMA(df["Close"], timeperiod=84) # using talib you have to give timeperiod, and using pandas_ta you have to give length
        df["MA"] = tan.sma(df["Close"], length=63)
        df["EMA"] = tan.ema(df["Close"], length=84)
    return df


def intToTime(integer, dataframe):
    timestamp = dataframe.index[integer]
    return timestamp


def calculatingZones(df):
    df_length = len(df.index)

    df["atr"] = tan.atr(df["High"], df["Low"], df["Close"], length=1)
    df["atr"] = df.atr.rolling(window=30).mean()
    df["close_smooth"] = savgol_filter(df["Close"], 20, 5)

    atr = df["atr"].iloc[-1]

    peaks_idx, _ = find_peaks(df["close_smooth"], distance=15, width=3, prominence=atr)
    troughs_idx, _ = find_peaks(
        -df["close_smooth"], distance=15, width=3, prominence=atr
    )

    # ! defining accurate highs and lows, scanning candles left and right for the high----------------------------------------------

    df["is_peak"] = 0
    df["is_peak"].iloc[peaks_idx] = 1  # peaks are maxima from the savgol filter

    df["is_trough"] = 0
    df["is_trough"].iloc[troughs_idx] = 1  # troughs are minima from the savgol filter

    df["actual_high"] = 0
    for index, row in df.iterrows():
        if row["is_peak"] == 1:
            integer_index = df.index.get_loc(index)
            if integer_index < 8:
                index_integer1 = 0
            else:
                index_integer1 = integer_index - 8
            start = df.index[index_integer1]
            until_end = df_length - integer_index
            if until_end <= 8 and until_end > 0:
                index_integer2 = integer_index + (until_end - 1)
            else:
                index_integer2 = integer_index + 8
            end = df.index[index_integer2]
            max_value = df.loc[start:end, "High"].max()
            max_index = df.loc[start:end, "High"].idxmax()
            df.at[max_index, "actual_high"] = 1

    df["actual_low"] = 0
    for index, row in df.iterrows():
        if row["is_trough"] == 1:
            integer_index = df.index.get_loc(index)
            if integer_index < 8:
                index_integer1 = 0
            else:
                index_integer1 = integer_index - 8
            start = df.index[index_integer1]
            until_end = df_length - integer_index
            if until_end <= 8:
                index_integer2 = integer_index + (until_end - 1)
            else:
                index_integer2 = integer_index + 8
            end = df.index[index_integer2]
            min_value = df.loc[start:end, "Low"].min()
            min_index = df.loc[start:end, "Low"].idxmin()
            df.at[min_index, "actual_low"] = 1

    # defining valid highs, only the ones that haven't been broken----------------------------------------------

    highs_df = df[df["actual_high"] == 1]
    highest_index = highs_df["High"].idxmax()
    highest_df2 = df.loc[highest_index:]
    df["protected_highs_and_lows"] = 0
    # this is basically the same as the valid_high, just that this is in the real df
    # here I am unnecessarily creating a new df, npt sure whether I really need it

    highest_df2["valid_high"] = 0
    last_high = 0
    for index, row in highest_df2[::-1].iterrows():
        if row["actual_high"] == 1:
            if last_high == 0:
                highest_point = df.loc[index:, "High"].idxmax()
                highest_df2.at[highest_point, "valid_high"] = 1
                df.at[
                    highest_point, "protected_highs_and_lows"
                ] = 1  # trying to add to normal df, so to not need the highest_df2
                last_high = df.at[highest_point, "High"]
            elif row["High"] > last_high:
                highest_df2.at[index, "valid_high"] = 1
                df.at[index, "protected_highs_and_lows"] = 1
                last_high = row["High"]
            elif row["High"] < last_high:
                highest_df2.at[index, "valid_high"] = 0
                df.at[index, "protected_highs_and_lows"] = 0

    lows_df = df[df["actual_low"] == 1]
    lowest_index = lows_df["Low"].idxmin()
    lowest_df2 = df.loc[lowest_index:]

    lowest_df2["valid_low"] = 0
    last_low = 0
    for index, row in lowest_df2[::-1].iterrows():
        if row["actual_low"] == 1:
            if last_low == 0:
                lowest_point = df.loc[index:, "Low"].idxmin()
                lowest_df2.at[lowest_point, "valid_low"] = 1
                df.at[lowest_point, "protected_highs_and_lows"] = -1
                last_low = df.at[lowest_point, "Low"]
            elif row["Low"] < last_low:
                lowest_df2.at[index, "valid_low"] = 1
                df.at[index, "protected_highs_and_lows"] = -1
                last_low = row["Low"]
            elif row["Low"] > last_low:
                lowest_df2.at[index, "valid_low"] = 0
                df.at[index, "protected_highs_and_lows"] = 0

    # checking whether the high is protected or not, name = ultra_stationary----------------------------------------------
    # I don't quite understand what the difference is between valid highs and protected
    df["ultra_stationary"] = 0
    valid_high_bool = False
    for index, row in df.iterrows():
        if row["actual_high"] == 1 or row["actual_low"] == 1:
            if (
                row["actual_low"] == 1
                and row["Low"] < last_low
                and valid_high_bool == True
            ):
                df.at[real_index, "ultra_stationary"] = 1
            if row["actual_high"] == 1 and valid_high_bool == True:
                valid_high_bool = True
            else:
                valid_high_bool = False
            if row["protected_highs_and_lows"] == 1:
                valid_high_bool = True
                real_index = index
            if row["actual_low"] == 1:
                last_low = row["Low"]

    valid_low_bool = False
    for index, row in df.iterrows():
        if row["actual_high"] == 1 or row["actual_low"] == 1:
            if (
                row["actual_high"] == 1
                and row["High"] > last_high
                and valid_low_bool == True
            ):
                df.at[real_index, "ultra_stationary"] = -1
            if row["actual_low"] == 1 and valid_low_bool == True:
                valid_low_bool = True
            else:
                valid_low_bool = False
            if row["protected_highs_and_lows"] == -1:
                valid_low_bool = True
                real_index = index
            if row["actual_high"] == 1:
                last_high = row["High"]

    zones = []

    last_high_zone = 0
    last_index_zone = 0
    for index, row in df[::-1].iterrows():
        if row["ultra_stationary"] == 1 and row["Low"] > last_high_zone:
            zones.append(
                {
                    "x0": index,
                    "y0": df.loc[index, "Low"],
                    "x1": df.index[-1],
                    "y1": df.loc[index, "High"],
                }
            )

            last_high_zone = df.loc[index, "High"]
            last_index_zone = index
        elif row["ultra_stationary"] == 1 and row["Low"] <= last_high_zone:
            # df.at[
            #     index, "zones"
            # ] = f"{index}, {df.loc[index, 'Low']},{last_index_zone}, {df.loc[index, 'High']} "

            zones.append(
                {
                    "x0": index,
                    "y0": df.loc[index, "Low"],
                    "x1": last_index_zone,
                    "y1": df.loc[index, "High"],
                }
            )
            last_high_zone = df.loc[index, "High"]
            last_index_zone = index

    last_low_zone = 100000
    last_index_zone1 = 0
    for index, row in df[::-1].iterrows():
        if row["ultra_stationary"] == -1 and row["High"] < last_low_zone:
            zones.append(
                {
                    "x0": index,
                    "y0": df.loc[index, "Low"],
                    "x1": df.index[-1],
                    "y1": df.loc[index, "High"],
                }
            )

            last_low_zone = lowest_df2.loc[index, "Low"]
            last_index_zone1 = index
        elif row["ultra_stationary"] == -1 and row["High"] >= last_low_zone:
            zones.append(
                {
                    "x0": index,
                    "y0": df.loc[index, "Low"],
                    "x1": last_index_zone,
                    "y1": df.loc[index, "High"],
                }
            )
            last_low_zone = lowest_df2.loc[index, "Low"]
            last_index_zone1 = index

    zones_df = pd.DataFrame(zones)
    return zones_df


def calculatingZones2(df):
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


def superTrend(df, atr_period, multiplier):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    # calculate ATR
    price_diffs = [high - low, high - close.shift(), close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    # default ATR calculation in supertrend indicator
    atr = true_range.ewm(alpha=1 / atr_period, min_periods=atr_period).mean()
    # df['atr'] = df['tr'].rolling(atr_period).mean()

    # HL2 is simply the average of high and low prices
    hl2 = (high + low) / 2
    # upperband and lowerband calculation
    # notice that final bands are set to be equal to the respective bands
    final_upperband = upperband = hl2 + (multiplier * atr)
    final_lowerband = lowerband = hl2 - (multiplier * atr)

    # initialize Supertrend column to True
    supertrend = [True] * len(df)

    for i in range(1, len(df.index)):
        curr, prev = i, i - 1

        # if current close price crosses above upperband
        if close[curr] > final_upperband[prev]:
            supertrend[curr] = True
        # if current close price crosses below lowerband
        elif close[curr] < final_lowerband[prev]:
            supertrend[curr] = False
        # else, the trend continues
        else:
            supertrend[curr] = supertrend[prev]

            # adjustment to the final bands
            if (
                supertrend[curr] == True
                and final_lowerband[curr] < final_lowerband[prev]
            ):
                final_lowerband[curr] = final_lowerband[prev]
            if (
                supertrend[curr] == False
                and final_upperband[curr] > final_upperband[prev]
            ):
                final_upperband[curr] = final_upperband[prev]

        # to remove bands according to the trend direction
        if supertrend[curr] == True:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan

    df = pd.DataFrame(
        {
            # "Supertrend": supertrend,
            "Final Lowerband": final_lowerband,
            "Final Upperband": final_upperband,
        },
        index=df.index,
    )
    df["bullishSUP"] = np.nan
    df_length = len(df)

    df["bullishSUP"] = np.where(
        pd.isna(df["Final Lowerband"]) == False,
        1,
        -1,
    )
    return df


def calculateRMI(df):
    len = 4
    length = 1

    df["priceChange"] = df["Close"] - df["Close"].shift(len)
    df["upMove"] = np.where(df["priceChange"] > 0, df["priceChange"], 0)
    df["downMove"] = np.where(df["priceChange"] < 0, abs(df["priceChange"]), 0)

    df["sumUp"] = df["upMove"].rolling(length).sum()
    df["sumDown"] = df["downMove"].rolling(length).sum()

    df["sumUp"] = tan.ema(df["sumUp"], 20)
    df["sumDown"] = tan.ema(df["sumDown"], 20)

    df["Rmi"] = df["sumUp"] * 100 / (df["sumUp"] + df["sumDown"])

    rmiSlope = df["Rmi"] - df["Rmi"].shift(1)
    df["bullishRMI"] = np.where(rmiSlope > 0, 1, -1)
    df = df[["Rmi", "bullishRMI"]]
    return df


def main(df):
    df1 = superTrend(df, 14, 3)
    df2 = calculateRMI(df)
    frames = [df1, df2]
    df = pd.concat(frames, axis=1)
    df["bullishCombined"] = df["bullishSUP"] + df["bullishRMI"]

    red_boxes = []
    green_boxes = []
    red_box_open = False
    green_box_open = False
    for index, row in df.iterrows():
        if row["bullishCombined"] == -2 and red_box_open == False:
            red_box_start = index
            red_box_open = True
        elif row["bullishCombined"] != -2 and red_box_open == True:
            red_box_end = index
            red_boxes.append(
                {"x0": red_box_start, "x1": red_box_end, "color": "#f52a45"}
            )
            red_box_open = False
        elif index == df.index[-1] and red_box_open == True:
            red_box_end = index
            red_boxes.append(
                {"x0": red_box_start, "x1": red_box_end, "color": "#f52a45"}
            )
            red_box_open = False

    for index, row in df.iterrows():
        if row["bullishCombined"] == 2 and green_box_open == False:
            green_box_start = index
            green_box_open = True
        elif row["bullishCombined"] != 2 and green_box_open == True:
            green_box_end = index
            green_boxes.append(
                {"x0": green_box_start, "x1": green_box_end, "color": "#2af5c2"}
            )
            green_box_open = False
        elif index == df.index[-1] and green_box_open == True:
            green_box_end = index
            green_boxes.append(
                {"x0": green_box_start, "x1": green_box_end, "color": "#2af5c2"}
            )
            green_box_open = False

    red_df = pd.DataFrame(red_boxes)
    green_df = pd.DataFrame(green_boxes)

    return red_df, green_df


def createVarv(df):
    df["standard_deviation"] = df["Close"].rolling(window=200).std() * 100
    df["moving_average"] = df["Close"].rolling(window=200).mean()

    df["deviationRatio"] = df["standard_deviation"] / df["moving_average"]

    df["percentageShift"] = (1 + (0.115 * df["deviationRatio"])) ** (0.1)

    df["band1"] = df["Close"] / (1 + (0.115 * df["deviationRatio"])) ** (0.5)

    df["band2"] = df["band1"] * df["percentageShift"]
    df["band3"] = df["band1"] * df["percentageShift"] ** 2
    df["band4"] = df["band1"] * df["percentageShift"] ** 3
    df["band5"] = df["band1"] * df["percentageShift"] ** 4
    df["band6"] = df["band1"] * df["percentageShift"] ** 5
    df["band7"] = df["band1"] * df["percentageShift"] ** 6
    df["band8"] = df["band1"] * df["percentageShift"] ** 7
    df["band9"] = df["band1"] * df["percentageShift"] ** 8
    df["band10"] = df["band1"] * df["percentageShift"] ** 9
    df["band11"] = df["band1"] * df["percentageShift"] ** 10

    lenMa = 200

    df["out1"] = tan.ema(df["band1"], length=lenMa)
    df["out2"] = tan.ema(df["band2"], length=lenMa)
    df["out3"] = tan.ema(df["band3"], length=lenMa)
    df["out4"] = tan.ema(df["band4"], length=lenMa)
    df["out5"] = tan.ema(df["band5"], length=lenMa)
    df["out6"] = tan.ema(df["band6"], length=lenMa)
    df["out7"] = tan.ema(df["band7"], length=lenMa)
    df["out8"] = tan.ema(df["band8"], length=lenMa)
    df["out9"] = tan.ema(df["band9"], length=lenMa)
    df["out10"] = tan.ema(df["band10"], length=lenMa)
    df["out11"] = tan.ema(df["band11"], length=lenMa)

    df = df[
        [
            "time",
            "out1",
            "out2",
            "out3",
            "out4",
            "out5",
            "out6",
            "out7",
            "out8",
            "out9",
            "out10",
            "out11",
        ]
    ]
    df = df.dropna(subset=["out1"])
    return df


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


@app.route("/api/query/", methods=["GET"])
def query_nodb():
    user_query = str(request.args.get("coin"))  # /user/?user=USER_NAME
    timeframe_query = str(request.args.get("timeframe"))
    df = gettingData(user_query, timeframe_query, 1000)
    return df.to_json(orient="records")


@app.route("/api/zones/", methods=["GET"])
def query_nodbzones():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = gettingData(user_query, timeframe_query, 1000)
    df = transformDf(df)
    zones_df = calculatingZones(df)
    json_data = zones_df.to_json(orient="records")
    return json_data


@app.route("/api/zones2/", methods=["GET"])
def query_zones2():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = gettingData(user_query, timeframe_query, 1000)
    df = transformDf(df)
    zones_df = calculatingZones2(df)
    json_data = zones_df.to_json(orient="records")
    return json_data


@app.route("/api/momentum/", methods=["GET"])
def query_momentum():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = gettingData(user_query, timeframe_query, 1000)
    df1 = transformDf(df)
    red_boxes, green_boxes = main(df1)
    df_combined = pd.concat([red_boxes, green_boxes])
    return df_combined.to_json(orient="records")


@app.route("/api/varv/", methods=["GET"])
def query_varv():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = gettingData(user_query, timeframe_query, 1000)
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
        df = transformDf(gettingData(user_query, "1M", 1000))
        df2 = create_yearly_candles(df)
    elif ranges_query == "3m":
        df = transformDf(gettingData(user_query, "1M", 1000))
        df2 = createQuarterlyCandles(create_yearly_candles(df), df)
    elif ranges_query == "1m":
        df2 = transformDf(gettingData(user_query, "1M", 1000))
    else:
        df2 = transformDf(gettingData(user_query, ranges_query, 1000))
    df = transformDf(gettingData(user_query, timeframe_query, 1000))
    df3 = createRanges(df, df2)
    return df3.to_json(orient="records")


@app.route("/api/4lines/", methods=["GET"])
def query_4lines():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = gettingData(user_query, timeframe_query, 1000)
    df1 = create4Lines(df, timeframe_query)
    return df1.to_json(orient="records")


if __name__ == "__main__":
    app.run(debug=True)
