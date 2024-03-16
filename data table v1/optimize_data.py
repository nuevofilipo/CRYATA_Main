import asyncio
import aiohttp
import pandas as pd
import time
import sqlalchemy

from sqlalchemy import create_engine


async def fetch_data(session, url, semaphore, params):
    async with semaphore:
        async with session.get(url, params=params) as response:
            return await response.json()


async def get_data(symbols, time_frames, url, columns):
    realTableNames = []
    results = []
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(50)  # Adjust the value for optimal concurrency
        tasks = []
        for symbol in symbols:
            for time_frame in time_frames:
                params = {"symbol": symbol, "interval": time_frame, "limit": 1000}
                task = fetch_data(session, url, semaphore, params)
                tasks.append(task)
                realTableNames.append(symbol + time_frame)
        responses = await asyncio.gather(*tasks)
        for data in responses:
            df = pd.DataFrame(data, columns=columns)
            results.append(df)
    return realTableNames, results


async def save_to_database(name, df, engine):
    try:
        await asyncio.to_thread(df.to_sql, name, con=engine, if_exists="append")
    except Exception as e:
        print(f"{name}, wasn't able to be added")


time1 = 0
time2 = 0
time3 = 0


async def main(symbols, time_frames, url, columns, engine):
    starttime1 = time.time()
    realTableNames, results = await get_data(symbols, time_frames, url, columns)
    time1 = time.time() - starttime1

    starttime2 = time.time()
    dfs_dictionary = {}
    for i, result in enumerate(results):
        dfs_dictionary[realTableNames[i]] = result
    time2 = time.time() - starttime2

    tasks = [save_to_database(name, df, engine) for name, df in dfs_dictionary.items()]
    starttime3 = time.time()
    await asyncio.gather(*tasks)
    time3 = time.time() - starttime3
    print(f"time1: {time1} seconds, time2: {time2} seconds, time3: {time3} seconds")


# Example usage:

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
timeFrames = ["1h", "1w", "1d"]
url = "https://api.binance.us/api/v3/klines"
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
]  # Adjust columns as per your data
engine = create_engine(
    "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee", echo=True
)

starttime = time.time()
asyncio.run(main(symbols, timeFrames, url, columns, engine))
duration = time.time() - starttime
print(f"duration: {duration} seconds")
