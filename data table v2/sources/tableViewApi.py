from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
import pandas as pd
import json, time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ? creating connection to remote database
# engine = create_engine(
#     "mysql+mysqlconnector://root:6544Dd5HFeh4acBeDCbg1cde2H4e6CgC@roundhouse.proxy.rlwy.net:34181/railway",
#     echo=True,
#     isolation_level="READ COMMITTED",
# )

#! creating connection to local database
engine = create_engine(
    "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee", echo=False
)


def getTableViewData(name):
    conn = engine.connect()
    try:

        df = pd.read_sql(name, conn)
        return df
    except Exception as e:
        print(e)
    finally:
        conn.close()


@app.route("/", methods=["GET"])
def index():
    name = str(request.args.get("name"))
    dataOut = getTableViewData(name)
    return dataOut.to_json(orient="records")


if __name__ == "__main__":
    app.run()
