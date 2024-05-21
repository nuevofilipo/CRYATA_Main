import requests

url = "https://vercel-proxy-api-cyan.vercel.app"


params = {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "limit": 100,
    "since": 1651846814000,
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print("Error:", response.status_code)
