import pandas as pd

pd.options.mode.chained_assignment = None
import numpy as np
import time

import pandas_ta as tan


from scipy.signal import savgol_filter
from scipy.signal import find_peaks


def intToTime(integer, dataframe):
    if integer > 0:
        timestamp = dataframe.loc[integer, "time"]
    else:
        timestamp = dataframe.loc[0, "time"]
    return timestamp


def intToTime1(integer, dataframe):
    timestamp = dataframe.index[integer]
    return timestamp


# this two are helper functions for the supplyDemandZones function
def findLastGreenCandle(intIndex, df):
    for index, row in df[intIndex::-1].iterrows():
        if row["Close"] > row["Open"]:
            return index
    return 0


def findLastRedCandle(intIndex, df):
    for index, row in df[intIndex::-1].iterrows():
        if row["Close"] < row["Open"]:
            return index
    return 0


def supplyDemandZones(df, chartDf):
    lowest_df2 = highsForSupplyZones(df)[1]
    df = highsForSupplyZones(df)[0]

    zones = []

    # finding high zones
    # explanation: given a high that wasn't broken, we go back until we find a green candle
    # from that green candle we take the open and plot a zone from there to the high
    # vice versa for the low zones

    last_high_zone = 0
    last_index_zone = 0
    for index, row in df[::-1].iterrows():

        if row["ultra_stationary"] == 1 and row["Low"] > last_high_zone:
            start_index = findLastGreenCandle(index, df)
            zones.append(
                {
                    "x0": intToTime(start_index, df),
                    "y0": df.loc[start_index, "Open"],
                    "x1": intToTime(df.index[-1], df),
                    "y1": df.loc[index, "High"],
                }
            )

            last_high_zone = df.loc[index, "High"]
            last_index_zone = index
        elif row["ultra_stationary"] == 1 and row["Low"] <= last_high_zone:
            start_index = findLastGreenCandle(index, df)

            zones.append(
                {
                    "x0": intToTime(start_index, df),
                    "y0": df.loc[start_index, "Open"],
                    "x1": intToTime(last_index_zone, df),
                    "y1": df.loc[index, "High"],
                }
            )
            last_high_zone = df.loc[index, "High"]
            last_index_zone = index

    # finding low zones
    last_low_zone = 1000000
    last_index_zone1 = 0
    for index, row in df[::-1].iterrows():
        if row["ultra_stationary"] == -1 and row["High"] < last_low_zone:
            start_index = findLastRedCandle(index, df)
            zones.append(
                {
                    "x0": intToTime(start_index, df),
                    "y0": df.loc[start_index, "Open"],
                    "x1": intToTime(df.index[-1], df),
                    "y1": df.loc[index, "Low"],
                }
            )

            last_low_zone = lowest_df2.loc[index, "Low"]
            last_index_zone1 = index
        elif row["ultra_stationary"] == -1 and row["High"] >= last_low_zone:
            start_index = findLastRedCandle(index, df)
            zones.append(
                {
                    "x0": intToTime(start_index, df),
                    "y0": df.loc[start_index, "Open"],
                    "x1": intToTime(last_index_zone1, df),
                    "y1": df.loc[index, "Low"],
                }
            )
            last_low_zone = lowest_df2.loc[index, "Low"]
            last_index_zone1 = index

    # checking if zones go beyond the chart and adjusting accordingly
    earliest_time = chartDf["time"].iloc[0]
    for zone in zones:
        if zone["x0"] < earliest_time:
            zone["x0"] = earliest_time

    zones_df = pd.DataFrame(zones)
    return zones_df


def highsForSupplyZones(df):
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

    df["actual_high"] = (
        0  # actual highs are the real highs surrounding the approximate high
    )
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

    ##! working on
    try:
        highest_index = highs_df["High"].idxmax()
    except Exception as e:
        print(e)
        return pd.DataFrame(), pd.DataFrame()  # no idea what's happening here

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
                df.at[highest_point, "protected_highs_and_lows"] = (
                    1  # trying to add to normal df, so to not need the highest_df2
                )
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
    # there is no difference between valid highs and protected, however ones are in another
    # based on the ultra stationary we will define the zones
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

    return df, lowest_df2


def momentumIndicatorPrep(df):
    currState = "neutral"
    last_high = None
    last_low = None

    df["momentum"] = "neutral"

    for index, row in df.iterrows():
        if row["actual_high"] == 1:
            last_high = row["High"]
        if row["actual_low"] == 1:
            last_low = row["Low"]

        if last_high != None and last_low != None:
            if row["Close"] > last_high and currState != "bullish":
                currState = "bullish"
            elif row["Close"] < last_low and currState != "bearish":
                currState = "bearish"

        df.at[index, "momentum"] = currState

    return df


def momentumIndicator(df, chart_df):  # takes df with integer indices
    df = momentumIndicatorPrep(highsForSupplyZones(df)[0])
    timeNow = chart_df["time"].iloc[-1]

    red_boxes = []
    green_boxes = []
    red_box_open = False
    green_box_open = False

    if df.empty:
        print("Dataframe is empty")
        return pd.DataFrame()

    high_y = df["High"].max()
    low_y = df["Low"].min()

    for index, row in df.iterrows():
        if row["momentum"] == "bearish" and red_box_open == False:
            red_box_start = index
            red_box_open = True
        elif row["momentum"] != "bearish" and red_box_open == True:
            red_box_end = index
            red_boxes.append(
                {
                    "x0": intToTime(red_box_start, df),
                    "y0": low_y,
                    "x1": intToTime(red_box_end, df),
                    "y1": high_y,
                    "color": "#f52a45",
                }
            )
            red_box_open = False
        elif index == df.index[-1] and red_box_open == True:
            red_box_end = index
            red_boxes.append(
                {
                    "x0": intToTime(red_box_start, df),
                    "y0": low_y,
                    "x1": timeNow,
                    "y1": high_y,
                    "color": "#f52a45",
                }
            )
            red_box_open = False

        if row["momentum"] == "bullish" and green_box_open == False:
            green_box_start = index
            green_box_open = True
        elif row["momentum"] != "bullish" and green_box_open == True:
            green_box_end = index
            green_boxes.append(
                {
                    "x0": intToTime(green_box_start, df),
                    "y0": low_y,
                    "x1": intToTime(green_box_end, df),
                    "y1": high_y,
                    "color": "#2af5c2",
                }
            )
            green_box_open = False
        elif index == df.index[-1] and green_box_open == True:
            green_box_end = index
            green_boxes.append(
                {
                    "x0": intToTime(green_box_start, df),
                    "y0": low_y,
                    "x1": timeNow,
                    "y1": high_y,
                    "color": "#2af5c2",
                }
            )
            green_box_open = False

    combined_zones = red_boxes + green_boxes
    combined_df = pd.DataFrame(combined_zones)

    return combined_df


def createVarv(df, timeframe, chart_df):
    if len(df.index) < 650:
        return pd.DataFrame()

    length = 500
    df["standard_deviation"] = df["Close"].rolling(window=length).std() * 100
    df["moving_average"] = df["Close"].rolling(window=length).mean()

    df["deviationRatio"] = df["standard_deviation"] / df["moving_average"]

    df["percentageShift"] = (1 + (0.115 * df["deviationRatio"])) ** (0.1)

    df["band1"] = df["Close"] / (1 + (0.115 * df["deviationRatio"])) ** (0.5)

    # print(df)

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

    lenMa = 150

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
    if timeframe == "1week":
        df.set_index("time", inplace=True)
        df = df.resample("W-MON").last().dropna().reset_index()

    cutoff_timestamp = chart_df["time"].iloc[0]
    df = df[df["time"] > cutoff_timestamp]
    return df


def createContextBands(df, timeFrame, chart_df):
    if timeFrame == "1week":
        df["MA"] = tan.sma(df["Close"], length=9)
        df["EMA"] = tan.ema(df["Close"], length=12)
    else:
        # df["MA"] = ta.SMA(df["Close"], timeperiod=63)
        # df["EMA"] = ta.EMA(df["Close"], timeperiod=84) # using talib you have to give timeperiod, and using pandas_ta you have to give length
        df["MA"] = tan.sma(df["Close"], length=63)
        df["EMA"] = tan.ema(df["Close"], length=84)

    cutoff_timestamp = chart_df["time"].iloc[0]
    df = df[df["time"] > cutoff_timestamp]
    return df


def imbalanceZones(df):
    df_length = len(df.index)
    zonesRed = []
    updated_zonesRed = []
    for index, row in df.iterrows():
        if row["Open"] > row["Close"]:  # this means this is a red candle
            integer_idx = df.index.get_loc(index)
            if integer_idx > 4 and integer_idx < df_length - 4:
                high_boundary = df.loc[
                    intToTime1(integer_idx - 4, df) : intToTime1(integer_idx - 1, df),
                    "Low",
                ].min()
                low_boundary = df.loc[
                    intToTime1(integer_idx + 1, df) : intToTime1(integer_idx + 4, df),
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
                    intToTime1(integer_idx - 4, df) : intToTime1(integer_idx - 1, df),
                    "High",
                ].max()
                high_boundary = df.loc[
                    intToTime1(integer_idx + 1, df) : intToTime1(integer_idx + 4, df),
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
