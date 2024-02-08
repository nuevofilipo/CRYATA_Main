import pandas as pd

pd.options.mode.chained_assignment = None
import numpy as np

import pandas_ta as tan
import plotly.graph_objects as go


from scipy.signal import savgol_filter
from scipy.signal import find_peaks

from getTwelveData import (
    getResponse,
)  # so stupid needs to be changed to moduls. whne calling from other file

df = getResponse("BTC/USD", "1day", 300)


def intToTime(integer, dataframe):
    if integer > 0:
        timestamp = dataframe.loc[integer, "time"]
    else:
        timestamp = dataframe.loc[0, "time"]
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


def supplyDemandZones(df):
    df = highsForSupplyZones(df)[0]
    lowest_df2 = highsForSupplyZones(df)[1]

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


def momentumIndicator(df):
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


df = getResponse("BTC/USD", "1day", 1000)
df = highsForSupplyZones(df)[0]

df = momentumIndicator(df)

# print(df.to_string())

# plotting chart in plotly
fig = go.Figure(
    data=[
        go.Candlestick(
            x=df["time"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
        )
    ]
)

highs = go.Scatter(
    x=df[df["actual_high"] == 1]["time"],
    y=df[df["actual_high"] == 1]["High"],
    mode="markers",
    marker=dict(color="red", size=8),
    name="Highs",
)

lows = go.Scatter(
    x=df[df["actual_low"] == 1]["time"],
    y=df[df["actual_low"] == 1]["Low"],
    mode="markers",
    marker=dict(color="blue", size=8),
    name="Lows",
)

visualizeBullish = go.Scatter(
    x=df[df["momentum"] == "bullish"]["time"],
    y=[20000] * len(df),
    mode="markers",
    marker=dict(color="green", size=8),
    name="Bullish",
)

visualizeBearish = go.Scatter(
    x=df[df["momentum"] == "bearish"]["time"],
    y=[20000] * len(df),
    mode="markers",
    marker=dict(color="red", size=8),
    name="Bearish",
)

fig.add_trace(visualizeBullish)
fig.add_trace(visualizeBearish)


fig.add_trace(highs)
fig.add_trace(lows)


fig.show()
