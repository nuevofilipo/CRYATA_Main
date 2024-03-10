from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
import pandas as pd
import json, time
from datetime import datetime

from flask_cors import CORS

# needed for calculating zones
import pandas_ta as tan
from scipy.signal import savgol_filter
from scipy.signal import find_peaks

# import talib as ta # luckily we don't need this anymore

import numpy as np


app = Flask(__name__)
CORS(app)
# app.config["SQLALCHEMY_DATABASE_URI"] = (
#     "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee"
# )
# db = SQLAlchemy(app)

engine = create_engine(
    "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee", echo=True
)
conn = engine.connect()

columns = [
    "time",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "MA",
    "EMA",
]


def transformDf(df):
    df.set_index("time", inplace=True)
    return df


def gettingData(symbol, timeFrame):
    try:
        df = pd.read_sql(symbol.lower() + timeFrame, conn)
        return transformDf(df)
    except Exception as e:
        print(e)


@app.route("/", methods=["GET"])
def index():
    df = gettingData("BTCUSDT", "1d")
    return df.to_json(orient="records")


if __name__ == "__main__":
    app.run()
