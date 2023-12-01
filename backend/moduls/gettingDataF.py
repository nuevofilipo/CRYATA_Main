# packages needed for data fetching from binance API
import pandas as pd
from binance.spot import Spot as Client


def gettingData(coin, candleTimeFrame, limit):

    # keys from binance
    api_key = "LS2FxhfRjqp6TOv3q2QFOGuQzU8KoSGwlcLIOVaxjRjc0UOhncD2ZRMzT4xRGsfu"
    secret_key = "p3AHHm2sq26yV2y92y0XkFkDxNqE3AAPVphtslNzrmLAJOrMN3r5Gm8ohNolfsXn"

    spot_client = Client(api_key, secret_key)
    btcusd_historical = spot_client.klines(coin, candleTimeFrame, limit=limit)


    # columns to structure incoming data
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

    # creating the df
    df = pd.DataFrame(btcusd_historical, columns=columns)

    df["time"] = pd.to_datetime(df["Open time"], unit="ms")

    # selecting the data
    df = df[["time", "Open", "High", "Low", "Close", "Volume"]]

    # transforming into float values
    df[["Open", "High", "Low", "Close", "Volume"]] = df[
        ["Open", "High", "Low", "Close", "Volume"]
    ].astype(float)


    # df.set_index("time", inplace=False)
    return df