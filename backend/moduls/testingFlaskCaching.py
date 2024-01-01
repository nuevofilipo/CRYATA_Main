from getTwelveData import getResponse

from flask import Flask, request
from flask_caching import Cache 
from random import randint



cache = Cache()

app = Flask(__name__)

app.config['CACHE_TYPE'] = "simple"

cache.init_app(app)

def make_cache_key(*args, **kwargs): 
    return request.url


#  this is how you can cache a route
#@app.route('/', methods = ["GET"])
@cache.cached(timeout=60, key_prefix=make_cache_key)
def get_data(coin, timeframe):
    data = getResponse(coin, timeframe, 10) # BTC/USD, 1day
    return data.to_json(orient="records")

@app.route('/number')
def return_number():
    num = getNumber()
    user_query = str(request.args.get("coin"))
    timeframe_query = str(request.args.get("timeframe"))
    cached_data = get_data(user_query, timeframe_query)



    return cached_data



#  this below is how you can cache a funtion value
@cache.cached(timeout=5, key_prefix='calculate')
def getNumber():
    number = randint(5,100)
    return number

if __name__ == "__main__":
    app.run(debug=True)