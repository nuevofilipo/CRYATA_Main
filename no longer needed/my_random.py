import ccxt.async_support as ccxt

# import ccxt
import pandas as pd
import asyncio


symbols = [
    "BTCUSDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "DOGE/USDT",
    "TON/USDT",
    "ADA/USDT",
    "SHIB/USDT",
    "AVAX/USDT",
    "DOT/USDT",
    "BCH/USDT",
    "TRX/USDT",
    "LINK/SUSDT",
    "MATIC/USDT",
    "ICP/USDT",
    "NEAR/USDT",
    "LTC/USDT",
    "DAI/USDT",
    "LEO/USDT",
    "UNI/USDT",
    "APT/USDT",
    "STX/USDT",
    "ETC/USDT",
    "MNT/USDT",
    "FIL/USDT",
    "CRO/USDT",
    "RNDR/USDT",
    "ATOM/USDT",
    "XLM/USDT",
    "OKB/USDT",
    "HBAR/USDT",
    "ARB/USDT",
    "IMX/USDT",
    "TAO/USDT",
    "VET/USDT",
    "WIF/USDT",
    "MKR/USDT",
    "KAS/USDT",
    "GRT/USDT",
    "GRT/USDT",
    "INJ/USDT",
    "OP/USDT",
    "PEPE/USDT",
    "THETA/USDT",
]


async def fetchData(exchanges, symbol, timeframe, limit):
    for ex in exchanges:
        try:
            data = await ex.fetchOHLCV(symbol, timeframe, limit=limit)
            print(f"data fetching success for {ex} for {symbol}")
            break
        except Exception as e:
            print(f"failed, exception: {e}")
            data = []
    return data


async def main():
    exchanges = [ccxt.binance()]
    tasks = []
    for sym in symbols:
        tasks.append(fetchData(exchanges, sym, "1d", 1000))

    responses = await asyncio.gather(*tasks)
    for ex in exchanges:
        await ex.close()
    return responses


output = asyncio.run(main())
print(f"length of output: {len(output)}")

amount_smaller_1000 = 0

for result in output:
    print(len(result))
    if len(result) < 1000:
        amount_smaller_1000 += 1

print(f"amount of data smaller than 1000: {amount_smaller_1000}")

# ex = ccxt.bybit()
# tickers = ex.fetchTickers()
# pairs = tickers.keys()

# usdt_pairs = {pair for pair in pairs if "USD" in pair}

# print(usdt_pairs)
