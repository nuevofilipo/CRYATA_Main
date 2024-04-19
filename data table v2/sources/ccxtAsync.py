import time
import ccxt.async_support as ccxt

# importing for database connection
from sqlalchemy import create_engine

# for data manipulation
import pandas as pd
import talib as ta

# for async requests
import asyncio
import aiohttp

# for multiprocessing
import multiprocessing as mp
import concurrent.futures

# for turning of logging of warnings
import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
pd.options.mode.chained_assignment = None

# importing own functions
from tableDataCalc import createTableRow

url = "https://api.binance.us/api/v3/klines"
columns = ["timestamp", "Open", "High", "Low", "Close", "Volume"]


def transformingDF(df, time_frame):
    try:
        df["time"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df[["time", "Open", "High", "Low", "Close", "Volume"]]
        df[["Open", "High", "Low", "Close", "Volume"]] = df[
            ["Open", "High", "Low", "Close", "Volume"]
        ].astype(float)
        return df
    except Exception as e:
        print(e)


# this function is a helper function for the protection layer
def transformData2(data):
    columns = columns = [
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
    df = df.drop(
        columns=[
            "Close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
            "ignore",
        ]
    )
    return df.values.tolist()


# this is helper function for get_entire_data() function
async def request_data_pair(exchange, semaphore, symbol, time_frame):
    async with semaphore:
        try:
            data = await exchange.fetchOHLCV(symbol, time_frame, limit=1000)
        except Exception as e:
            # protection layer
            try:
                session = aiohttp.ClientSession()
                response = await session.get(
                    url,
                    params={"symbol": symbol, "interval": time_frame, "limit": 1000},
                    ssl=False,
                )
                data = await response.json()
                data = transformData2(data)
                await session.close()
            except Exception as e:
                print(f"exception occured while fetching {symbol, time_frame}")
                print(e)
                data = []
        return data


async def get_entire_data(exchange, timeFrame, symbols):
    exchange = ccxt.binance()
    results = []
    realTableNames = []
    tasks = []
    semaphore = asyncio.Semaphore(50)  # Limit to 10 concurrent requests
    for symbol in symbols:
        realTableNames.append((symbol + timeFrame).lower())
        tasks.append(request_data_pair(exchange, semaphore, symbol, timeFrame))
    responses = await asyncio.gather(*tasks)
    for data in responses:
        df = pd.DataFrame(data, columns=columns)
        results.append(df)
    await exchange.close()
    return results, realTableNames


def asyncio_main(exchange, timeFrame, symbols, retries_left=3):
    out_dfs_dictionary = {}
    results, realTableNames = asyncio.run(get_entire_data(exchange, timeFrame, symbols))

    empty_list_counter = 0
    for i in range(0, len(results)):
        if len(results[i]) == 0:
            empty_list_counter += 1
            continue
        out_dfs_dictionary[realTableNames[i]] = transformingDF(
            results[i], realTableNames[i][-2:]
        )

    # base case data failed
    if empty_list_counter == len(results) and retries_left == 0:
        print(f"Exception, data failed loading!")
    elif empty_list_counter == len(results):
        time.sleep(60)
        return asyncio_main(retries_left - 1)
    else:
        return out_dfs_dictionary


# # using concurrent futures -------------------

if __name__ == "__main__":
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
        # "HNTUSDT",  # very weird, they don't have the official hntusdt pair
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
    timeframes = ["1d", "1h", "4h", "1w"]

    for timeframe in timeframes:
        exchange = ccxt.binance()
        dfs_dictionary = asyncio_main(exchange, timeframe, symbols)

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=mp.cpu_count()
        ) as executor:  # 4 is current best
            futures_results = [
                executor.submit(createTableRow, df, df_name, timeframe)
                for df_name, df in dfs_dictionary.items()
            ]

        out_results = []

        for f in futures_results:
            try:
                out_results.append(f.result())
            except Exception as e:
                print(e)

        df_table = pd.DataFrame(out_results)
        df_table.index = df_table.index + 1
        print(df_table)

        # !inserting into database -------------------
        #! different engine urls for local and remote database
        engine = create_engine(
            "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee", echo=True
        )
        # ? remote, railway database
        # engine = create_engine(
        #     "mysql+mysqlconnector://root:6544Dd5HFeh4acBeDCbg1cde2H4e6CgC@roundhouse.proxy.rlwy.net:34181/railway",
        #     echo=True,
        # )
        df_table.to_sql(
            "table" + timeframe, con=engine, if_exists="replace", chunksize=1000
        )
