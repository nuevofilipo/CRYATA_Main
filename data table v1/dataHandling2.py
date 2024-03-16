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


timeFrames = [
    "1h",
    "4h",
    "1w",
    "1d",
    "1M",
]


engine = create_engine(
    "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee", echo=True
)


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

# columns = [
#     "Open time",
#     "Open",
#     "High",
#     "Low",
#     "Close",
#     "Volume",
#     "Close_time",
#     "quote_asset_volume",
#     "number_of_trades",
#     "taker_buy_base_asset_volume",
#     "taker_buy_quote_asset_volume",
#     "ignore",
# ]

# results = []
# realTableNames = []

# starttime = time.time()


# def get_tasks(session):
#     tasks = []
#     for (
#         symbol
#     ) in (
#         symbols
#     ):  # replace tableNames with symbols(tableNames just used for easier testing)
#         for time_frame in timeFrames:
#             realTableNames.append(symbol + time_frame)
#             tasks.append(
#                 session.get(
#                     url,
#                     params={"symbol": symbol, "interval": time_frame, "limit": 100},
#                     ssl=False,
#                 )
#             )
#     return tasks


# async def get_data():
#     async with aiohttp.ClientSession() as session:
#         tasks = get_tasks(session)
#         responses = await asyncio.gather(*tasks)
#         for response in responses:
#             # results.append(await response.json())
#             data = await response.json()
#             df = pd.DataFrame(data, columns=columns)
#             results.append(df)


def removeData():
    for symbol in symbols:
        for time_frame in timeFrames:
            real_name = symbol + time_frame
            sql = text(f"DROP TABLE {real_name}")
            with engine.connect() as conn:
                try:
                    conn.execute(sql)
                except Exception as e:
                    print(f"{real_name}, wasn't able to be deleted! -----------------")


removeData()
