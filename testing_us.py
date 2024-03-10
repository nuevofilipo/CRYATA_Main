import requests as rq
from flask import Flask, request
from flask_cors import CORS

import pandas as pd

url = "https://api.binance.us/api/v3/klines"


def gettingData(symbol, timeframe):
    response = rq.get(
        url,
        params={"symbol": symbol, "interval": timeframe, "limit": 1000},
    )

    data = response.json()

    columns = [
        "Open time",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Close time",
        "Quote asset volume",
        "Number of trades",
        "Taker buy base asset volume",
        "Taker buy quote asset volume",
        "Ignore",
    ]

    df = pd.DataFrame(data, columns=columns)

    df = df[
        [
            "Open time",
            "Open",
            "High",
            "Low",
            "Close",
        ]
    ]

    return df


print(gettingData("BTCUSDT", "1h"))

app = Flask(__name__)


@app.route("/", methods=["GET"])  # http://127.0.0.1:5000/?coin=BTCUSDT&timeframe=1d
def query_nodb():
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    df = gettingData(user_query, timeframe_query)
    return df.to_json(orient="records")


if __name__ == "__main__":
    app.run(debug=True)
