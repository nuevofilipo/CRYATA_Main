import time

# importing for database connection
from sqlalchemy import create_engine

# for data manipulation
import pandas as pd
import talib as ta

# for async requests
import aiohttp
import asyncio

# for multiprocessing
import multiprocessing as mp
import concurrent.futures

# for turning of logging of warnings
import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
pd.options.mode.chained_assignment = None

# importing own functions
from tableDataCalc import createTableRow

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


## ! different urls-------------------
url = "https://api.binance.us/api/v3/klines"
# url = "https://api.binance.com/api/v3/klines"
# urlfull = "https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000"
# url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000"
# url2 =" https://api.binance.us/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000"


##! parameters -------------------
# timeFrames = ["1d", "1w", "1M", "1h", "4h"]
timeFrames = ["1d"]
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


def transformingDF(df, timeFrame):
    try:
        df["time"] = pd.to_datetime(df["Open time"], unit="ms")
        df = df[["time", "Open", "High", "Low", "Close", "Volume"]]
        df[["Open", "High", "Low", "Close", "Volume"]] = df[
            ["Open", "High", "Low", "Close", "Volume"]
        ].astype(float)
        return df
    except Exception as e:
        print(e)


# this is helper function for get_data() function
async def request_data_pair(session, semaphore, symbol, time_frame):
    async with semaphore:
        response = await session.get(
            url,
            params={"symbol": symbol, "interval": time_frame, "limit": 1000},
            ssl=False,
        )
        data = await response.json()
        return data


async def get_entire_data():
    results = []
    realTableNames = []

    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(50)  # Limit to 10 concurrent requests
        tasks = []
        for symbol in symbols:
            for time_frame in timeFrames:
                realTableNames.append((symbol + time_frame).lower())
                tasks.append(request_data_pair(session, semaphore, symbol, time_frame))
        responses = await asyncio.gather(*tasks)
        for data in responses:
            df = pd.DataFrame(data, columns=columns)
            results.append(df)

    return results, realTableNames


def asyncio_main():
    out_dfs_dictionary = {}
    results, realTableNames = asyncio.run(get_entire_data())

    for i in range(0, len(results)):
        if len(results[i]) == 0:
            continue
        out_dfs_dictionary[realTableNames[i]] = transformingDF(
            results[i], realTableNames[i][-2:]
        )

    return out_dfs_dictionary


# # using concurrent futures -------------------

if __name__ == "__main__":
    dfs_dictionary = asyncio_main()
    start = time.time()

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=mp.cpu_count()
    ) as executor:  # 4 is current best
        futures_results = [
            executor.submit(createTableRow, df, df_name)
            for df_name, df in dfs_dictionary.items()
        ]

    end = time.time()
    print(f"Finished in: {end-start} sec")
    print(f"length of results: {len(futures_results)}")
    out_results = []

    for f in futures_results:
        try:
            out_results.append(f.result())
        except Exception as e:
            print(e)

    df_table = pd.DataFrame(out_results)
    print(df_table)

    # !inserting into database -------------------
    
    engine = create_engine(
    "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee", echo=True
    )  

    df_table.to_sql("dailytable", con=engine, if_exists="replace", chunksize=1000)

    # for using with my external railway db

    # engine = create_engine(
    #     "mysql+mysqlconnector://root:6544Dd5HFeh4acBeDCbg1cde2H4e6CgC@roundhouse.proxy.rlwy.net:34181/railway",
    #     echo=True,
    # )



