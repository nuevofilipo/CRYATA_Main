from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from dH4_railway import loadData

app = Flask(__name__)

loadData()  # first time loading data upon start


def dbdataLoading():
    loadData()
    print("loading fresh data")


scheduler = BackgroundScheduler()
scheduler.add_job(dbdataLoading, "interval", seconds=30)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)
