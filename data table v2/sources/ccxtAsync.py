import time
import ccxt.async_support as ccxt

# importing for database connection
from sqlalchemy import create_engine

# for data manipulation
import pandas as pd

# for async requests
import asyncio
import aiohttp

# for multiprocessing
import multiprocessing as mp
import concurrent.futures

# for turning of logging of warnings
import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)
pd.options.mode.chained_assignment = None

# importing own functions
from tableDataCalc import createTableRow, createTableRow2

backupUrl = "https://api.binance.us/api/v3/klines"
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
        print(f"exception while transformingDF function: {e}")


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
async def request_data_pair(
    session, exchange, semaphore, symbol, time_frame, limit, since
):
    async with semaphore:
        try:
            if time_frame == "1m":
                proxyUrl = "https://vercel-proxy-api-cyan.vercel.app"
                response = await session.get(
                    proxyUrl,
                    params={
                        "symbol": symbol,
                        "timeframe": time_frame,
                        "limit": limit,
                        "since": since,
                    },
                    ssl=False,
                )
                data = await response.json()
            else:
                data = await exchange.fetchOHLCV(
                    symbol, time_frame, limit=limit
                )  # removed since=since
        except Exception as e:
            # protection layer
            try:
                response = await session.get(
                    backupUrl,
                    params={
                        "symbol": symbol,
                        "interval": time_frame,
                        "limit": limit,
                        "startTime": since,
                    },
                    ssl=False,
                )
                data = await response.json()
                data = transformData2(data)
            except Exception as e:
                print(f"exception occured while fetching {symbol, time_frame}")
                print(e)
                data = []
        return data


async def get_entire_data(exchange, timeFrame, symbols, limit, since):
    exchange = (
        ccxt.binance()
    )  # ! why do I provide it prior, if the ex instance is created here
    results = []
    realTableNames = []
    tasks = []
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(50)  # Limit to 10 concurrent requests
        for symbol in symbols:
            realTableNames.append((symbol + timeFrame).lower())
            tasks.append(
                request_data_pair(
                    session, exchange, semaphore, symbol, timeFrame, limit, since
                )
            )
        responses = await asyncio.gather(*tasks)
        for data in responses:
            df = pd.DataFrame(data, columns=columns)
            results.append(df)
    await exchange.close()
    return results, realTableNames


def asyncio_main(exchange, timeFrame, symbols, retries_left=3, limit=1000, since=None):
    out_dfs_dictionary = {}
    results, realTableNames = asyncio.run(
        get_entire_data(exchange, timeFrame, symbols, limit, since)
    )

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


# !using concurrent futures -------------------
sinceTimestampMapping = {
    "1d": 1000 * 60 * 60 * 24,
    "1w": 1000 * 60 * 60 * 24 * 7,
    "1h": 1000 * 60 * 60,
    "4h": 1000 * 60 * 60 * 4,
}


if __name__ == "__main__":
    logging.info("logger: before data loading")
    symbols = [
        "BTCUSDT",
        "ETHUSDT",
        "BNBUSDT",
        "SOLUSDT",
        "XRPUSDT",
        "DOGEUSDT",
        "TONUSDT",
        "ADAUSDT",
        "SHIBUSDT",
        "AVAXUSDT",
        "DOTUSDT",
        "BCHUSDT",
        "TRXUSDT",
        "LINKSUSDT",
        "MATICUSDT",
        "ICPUSDT",
        "NEARUSDT",
        "LTCUSDT",
        "DAIUSDT",
        "LEOUSDT",
        "UNIUSDT",
        "APTUSDT",
        "STXUSDT",
        "ETCUSDT",
        "MNTUSDT",
        "FILUSDT",
        "CROUSDT",
        "RNDRUSDT",
        "ATOMUSDT",
        "XLMUSDT",
        "OKBUSDT",
        "HBARUSDT",
        "ARBUSDT",
        "IMXUSDT",
        "TAOUSDT",
        "VETUSDT",
        "WIFUSDT",
        "MKRUSDT",
        "KASUSDT",
        "GRTUSDT",
        "GRTUSDT",
        "INJUSDT",
        "OPUSDT",
        "PEPEUSDT",
        "THETAUSDT",
        "RUNEUSDT",
        "FTMUSDT",
        "FETUSDT",
        "TIAUSDT",
        "LDOUSDT",
        "FLOKIUSDT",
        "BGBUSDT",
        "ALGOUSDT",
        "COREUSDT",
        "BONKUSDT",
        "SEIUSDT",
        "JUPUSDT",
        "FLOWUSDT",
        "ENAUSDT",
        "GALAUSDT",
        "AAVEUSDT",
        "BSVUSDT",
        "BEAMUSDT",
        "DYDXUSDT",
        "QNTUSDT",
        "AKTUSDT",
        "BTTUSDT",
        "AGIXUSDT",
        "SXPUSDT",
        "WLDUSDT",
        "FLRUSDT",
        "WUSDT",
        "CHZUSDT",
        "PENDLEUSDT",
        "ONDOUSDT",
        "EGLDUSDT",
        "NEOUSDT",
        "AXSUSDT",
        "KCSUSDT",
        "SANDUSDT",
        "XECUSDT",
        "AIOZUSDT",
        "EOSUSDT",
        "XTZUSDT",
        "STRKUSDT",
        "JASMYUSDT",
        "MINAUSDT",
        "RONUSDT",
        "CFXUSDT",
        "SNXUSDT",
        "MANAUSDT",
        "ORDIUSDT",
        "GNOUSDT",
        "GTUSDT",
        "CKBUSDT",
        "APEUSDT",
        "BOMEUSDT",
        "DEXEUSDT",
        "BLURUSDT",
        "FRONTUSDT",
        "FXSUSDT",
        "DOGUSDT",
        "ROSEUSDT",
        "SAFEUSDT",
        "LPTUSDT",
        "KLAYUSDT",
        "CAKEUSDT",
        "USDDUSDT",
        "AXLUSDT",
        "HNTUSDT",
        "BTGUSDT",
        "WOOUSDT",
        "1INCHUSDT",
        "MANTAUSDT",
        "CRVUSDT",
        "IOTXUSDT",
        "ASTRUSDT",
        "PRIMEUSDT",
        "FTTUSDT",
        "BICOUSDT",
        "TWTUSDT",
        "MEMEUSDT",
        "OSMOUSDT",
        "ARKMUSDT",
        "BNXUSDT",
        "WEMIXUSDT",
        "DYMUSDT",
        "COMPUSDT",
        "SUPERUSDT",
        "GLM/USDT",
        "NFTUSDT",
        "RAYUSDT",
        "LUNAUSDT",
        "GMTUSDT",
        "OCEANUSDT",
        "PAXGUSDT",
        "RPLUSDT",
        "XRDUSDT",
        "POLYXUSDT",
        "ANTUSDT",
        "JTOUSDT",
        "ZILUSDT",
        "MXUSDT",
        "PYUSDUSDT",
        "ANKRUSDT",
        "HOTUSDT",
        "CELOUSDT",
        "ZRXUSDT",
        "ZECUSDT",
        "SSVUSDT",
        "METISUSDT",
        "ENJUSDT",
        "GMXUSDT",
        "ILVUSDT",
        "GALUSDT",
        "IDUSDT",
        "TRACUSDT",
        "RVNUSDT",
        "RSRUSDT",
        "SFPUSDT",
        "SKLUSDT",
        "ABTUSDT",
        "ETHWUSDT",
        "SCUSDT",
        "ELFUSDT",
        "QTUMUSDT",
        "ALTUSDT",
        "BATUSDT",
        "YGGUSDT",
        "CSPRUSDT",
        "PEOPLEUSDT",
        "LUNCUSDT",
        "SATSUSDT",
        "XAUTUSDT",
    ]
    timeframes = ["1d", "1h", "4h", "1w"]

    for timeframe in timeframes:
        exchange = ccxt.binance()
        sinceTimestamp = None
        currentTimeInMs = exchange.milliseconds()
        sinceTimestamp = currentTimeInMs - sinceTimestampMapping[timeframe]

        priceChange_dictionary = asyncio_main(
            exchange,
            "1m",
            symbols,
            limit=1,
            since=sinceTimestamp,
        )
        logging.info(f"logger: fetched priceChangeDictionary {timeframe}")

        dfs_dictionary = asyncio_main(exchange, timeframe, symbols)
        btc_df = dfs_dictionary[
            "btcusdt" + timeframe
        ]  #! need this to calculate table with alt/btc data

        logging.info(f"logger: fetched data for {timeframe}")

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=mp.cpu_count()
        ) as executor:  # 4 is current best
            futures_results = [
                executor.submit(
                    createTableRow2,
                    df,
                    df_name,
                    timeframe,
                    priceChange_dictionary,
                    btc_df,
                )
                for df_name, df in dfs_dictionary.items()
            ]

        usd_results = []
        btc_results = []

        for f in futures_results:
            try:
                result = f.result()
                usd_results.append(result["usd"])
                btc_results.append(result["btc"])
            except Exception as e:
                print(e)

        df_usd_table = pd.DataFrame(usd_results)
        df_usd_table.index = df_usd_table.index + 1

        df_btc_table = pd.DataFrame(btc_results)
        df_btc_table.index = df_btc_table.index + 1
        logging.info(f"logger: calculated table for {timeframe}")

        # !inserting into database -------------------
        #! different engine urls for local and remote database
        # engine = create_engine(
        #     "mysql+mysqlconnector://root:Hallo123@localhost/nc_coffee", echo=True
        # )
        # # ? remote, railway database
        engine = create_engine(
            "mysql+mysqlconnector://root:zNnZbBPAcbSpNkoliyQForRNuuZLDyMW@roundhouse.proxy.rlwy.net:29401/railway",
            echo=False,
            isolation_level="READ COMMITTED",
        )
        df_usd_table.to_sql(
            "table" + timeframe, con=engine, if_exists="replace", chunksize=1000
        )
        df_btc_table.to_sql(
            "table" + timeframe + "_btc",
            con=engine,
            if_exists="replace",
            chunksize=1000,
        )
        logging.info(f"logger: inserted data for {timeframe}")
