import ccxt.async_support as ccxt
import pandas as pd
import asyncio


async def fetchData(ex, symbol, timeframe, limit):
    data = await ex.fetchOHLCV(symbol, timeframe, limit=limit)
    return data


symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]


async def main():
    ex = ccxt.binance()
    tasks = []
    for sym in symbols:
        tasks.append(fetchData(ex, sym, "1m", 12))

    responses = await asyncio.gather(*tasks)
    await ex.close()
    return responses


output = asyncio.run(main())
print(output)
