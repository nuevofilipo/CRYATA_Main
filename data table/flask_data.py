from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from dataHandling4 import loadData
from dataHandling2 import removeData

app = Flask(__name__)


def dbdataLoading():
    loadData()
    print("loading fresh data")


scheduler = BackgroundScheduler()
scheduler.add_job(dbdataLoading, "interval", seconds=30)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)
