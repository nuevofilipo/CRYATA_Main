from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
import pandas as pd
import json, time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

#! creating connection to database
engine = create_engine(
    "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee", echo=False
)
conn = engine.connect()


def getTableViewData(name):
    try:
        df = pd.read_sql(name, conn)
        return df
    except Exception as e:
        print(e)


@app.route("/", methods=["GET"])
def index():
    name = str(request.args.get("name"))
    dataOut = getTableViewData(name)
    return dataOut.to_json(orient="records")


if __name__ == "__main__":
    app.run()
