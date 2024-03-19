from sqlalchemy import (
    create_engine,
    ForeignKey,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    BigInteger,
    CHAR,
    Table,
    update,
    insert,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from sqlalchemy import text
import pandas as pd
from binance.spot import Spot as Client

import time
import aiohttp
import asyncio

import talib as ta

import logging

# logging.basicConfig(level=logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

pd.options.mode.chained_assignment = None

from tableDataCalc import createTableRow


# api_key = "LS2FxhfRjqp6TOv3q2QFOGuQzU8KoSGwlcLIOVaxjRjc0UOhncD2ZRMzT4xRGsfu"
# secret_key = "p3AHHm2sq26yV2y92y0XkFkDxNqE3AAPVphtslNzrmLAJOrMN3r5Gm8ohNolfsXn"
# spot_client = Client(api_key, secret_key)


def transformingDF(df, timeFrame):
    try:
        df["time"] = pd.to_datetime(df["Open time"], unit="ms")
        df = df[["time", "Open", "High", "Low", "Close", "Volume"]]
        df[["Open", "High", "Low", "Close", "Volume"]] = df[
            ["Open", "High", "Low", "Close", "Volume"]
        ].astype(float)

        return df

        # print(df)
    except Exception as e:
        print(e)


tableNames = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "ADAUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "TRXUSDT",
]
# tableNames = ["BTCUSDT"]

timeFrames = ["1h", "4h", "1w", "1d", "1M"]


engine = create_engine(
    "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee", echo=True
)  # set echo to True to see the logs in the console

# for using with my external railway db

# engine = create_engine(
#     "mysql+mysqlconnector://root:6544Dd5HFeh4acBeDCbg1cde2H4e6CgC@roundhouse.proxy.rlwy.net:34181/railway",
#     echo=True,
# )


# conn = engine.connect()  # needed to perform stuff like direct sql queries

# Session = sessionmaker(bind=engine)  # this is the class

# this is the instance

# getting data asynchronously from api

# url = "https://api.binance.com/api/v3/klines"
url = "https://api.binance.us/api/v3/klines"

# url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000"
# url2 =" https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000"


symbols = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "ADAUSDT",
    # "XRPUSDT",
    # "DOGEUSDT",
    # "DOTUSDT",
    # "UNIUSDT",
    # "BCHUSDT",
    # "LTCUSDT",
    # "LINKUSDT",
    # "SOLUSDT",
    # "MATICUSDT",
    # "XLMUSDT",
    # "ETCUSDT",
    # "THETAUSDT",
    # "ICPUSDT",
    # "VETUSDT",
    # "FILUSDT",
    # "TRXUSDT",
    # "EOSUSDT",
    # "XMRUSDT",
    # "AAVEUSDT",
    # "NEOUSDT",
    # "XTZUSDT",
    # "MKRUSDT",
    # "ALGOUSDT",
    # "ATOMUSDT",
    # "KSMUSDT",
    # "BTTUSDT",
    # "CAKEUSDT",
    # "AVAXUSDT",
    # "LUNAUSDT",
    # "COMPUSDT",
    # "HBARUSDT",
    # "GRTUSDT",
    # "EGLDUSDT",
    # "CHZUSDT",
    # "WAVESUSDT",
    # "RUNEUSDT",
    # "NEARUSDT",
    # "HNTUSDT",
    # "DASHUSDT",
    # "ZECUSDT",
    # "MANAUSDT",
    # "ENJUSDT",
    # "ZILUSDT",
    # "SNXUSDT",
    # "BATUSDT",
    # "QTUMUSDT",
    # "ONTUSDT",
    # "FTTUSDT",
    # "YFIUSDT",
    # "ZRXUSDT",
    # "SUSHIUSDT",
    # "ICXUSDT",
    # "BTGUSDT",
    # "IOSTUSDT",
    # "DGBUSDT",
    # "STXUSDT",
]

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

results = []
realTableNames = []


async def fetch_data(session, semaphore, symbol, time_frame):
    realTableNames.append((symbol + time_frame).lower())
    async with semaphore:
        response = await session.get(
            url,
            params={"symbol": symbol, "interval": time_frame, "limit": 1000},
            ssl=False,
        )
        data = await response.json()
        return data


async def get_data():
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(50)  # Limit to 10 concurrent requests
        tasks = [
            fetch_data(session, semaphore, symbol, time_frame)
            for symbol in symbols
            for time_frame in timeFrames
        ]
        responses = await asyncio.gather(*tasks)
        for data in responses:
            df = pd.DataFrame(data, columns=columns)
            results.append(df)


asyncio.run(get_data())


# I need this below-----------------
dfs_dictionary = {}

for i in range(0, len(results) - 1):
    dfs_dictionary[realTableNames[i]] = transformingDF(
        results[i], realTableNames[i][-2:]
    )


async def create_tasks_for_dataframes(dfs_dictionary):
    tasks = []
    for table_name, df in dfs_dictionary.items():
        task = asyncio.create_task(createTableRow(df, table_name))
        tasks.append(task)
    task_results = await asyncio.gather(*tasks)
    for table_name, result in zip(dfs_dictionary.keys(), task_results):
        results[table_name] = result
    return results


asyncio.run(create_tasks_for_dataframes(dfs_dictionary))
