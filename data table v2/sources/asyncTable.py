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

import multiprocessing as mp
import concurrent.futures

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

timeFrames = ["1d", "1w", "4h"]

# timeFrames = ["1d", "1w", "1M", "1h", "4h"]


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

symbols = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "ADAUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "DOTUSDT",
    "UNIUSDT",
    "BCHUSDT",
    "LTCUSDT",
    "LINKUSDT",
    "SOLUSDT",
    "MATICUSDT",
    "XLMUSDT",
    "ETCUSDT",
    "THETAUSDT",
    "ICPUSDT",
    "VETUSDT",
    "FILUSDT",
    "TRXUSDT",
    "EOSUSDT",
    "XMRUSDT",
    "AAVEUSDT",
    "NEOUSDT",
    "XTZUSDT",
    "MKRUSDT",
    "ALGOUSDT",
    "ATOMUSDT",
    "KSMUSDT",
    "BTTUSDT",
    "CAKEUSDT",
    "AVAXUSDT",
    "LUNAUSDT",
    "COMPUSDT",
    "HBARUSDT",
    "GRTUSDT",
    "EGLDUSDT",
    "CHZUSDT",
    "WAVESUSDT",
    "RUNEUSDT",
    "NEARUSDT",
    "HNTUSDT",
    "DASHUSDT",
    "ZECUSDT",
    "MANAUSDT",
    "ENJUSDT",
    "ZILUSDT",
    "SNXUSDT",
    "BATUSDT",
    "QTUMUSDT",
    "ONTUSDT",
    "FTTUSDT",
    "YFIUSDT",
    "ZRXUSDT",
    "SUSHIUSDT",
    "ICXUSDT",
    "BTGUSDT",
    "IOSTUSDT",
    "DGBUSDT",
    "STXUSDT",
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


for i in range(0, len(results)):
    if len(results[i]) == 0:
        continue

    dfs_dictionary[realTableNames[i]] = transformingDF(
        results[i], realTableNames[i][-2:]
    )


# until here everything scales very well


# async def createRowAsync(df, name):

#     startRow = time.time()
#     output =  createTableRow(df, name)
#     endRow = time.time()
#     print(f"time for {name}: {endRow - startRow} sec")
#     return output


# async def create_tasks_for_dataframes(dfs_dictionary):
#     tasks = []
#     for table_name, df in dfs_dictionary.items():
#         task = asyncio.create_task(createRowAsync(df, table_name))
#         tasks.append(task)
#     task_results = await asyncio.gather(*tasks)
#     return task_results


# def main():
#     start = time.time()
#     task_results = asyncio.run(create_tasks_for_dataframes(dfs_dictionary))
#     end = time.time()
#     print(end - start)


# main()

# # using concurrent futures -------------------

if __name__ == "__main__":
    start = time.time()

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=4
    ) as executor:  # 4 is current best
        results = [
            executor.submit(createTableRow, df, df_name)
            for df_name, df in dfs_dictionary.items()
        ]

    # for f in concurrent.futures.as_completed(results):
    #     print(f.result())

    end = time.time()
    print(f"Finished in: {end-start} sec")
    print(f"length of results: {len(results)}")


# # single process option for comparing -------------------

# if __name__ == "__main__":
#     start = time.time()
#     results = []
#     for df_name, df in dfs_dictionary.items():
#         result = createTableRow(df, df_name)
#         results.append(result)
#     end = time.time()
#     print(f"Finished in: {end-start} sec")
#     print(f"length of results: {len(results)}")


# # using multiprocessing -------------------

# if __name__ == "__main__":
#     start = time.time()

#     processes = []

#     for df_name, df in dfs_dictionary.items():
#         p = mp.Process(target=createTableRow, args=(df, df_name))
#         p.start()
#         processes.append(p)

#     for process in processes:
#         process.join()

#     end = time.time()
#     print(f"Finished in: {end-start} sec")
