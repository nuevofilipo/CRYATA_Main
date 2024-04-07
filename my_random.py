import pandas as pd

data = {"code": -1121, "msg": "Invalid symbol."}
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

df = pd.DataFrame(data, columns=columns)

print(df)
