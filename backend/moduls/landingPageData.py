from moduls.getTwelveData import getResponse
from moduls.indicatorFunctions import (
    createVarv,
)
import pandas as pd
import json
import csv


# Input and output file names
csv_file = "BTC-USD.csv"
json_file = "outputData.json"

# Read CSV and convert to list of dictionaries
data = []
with open(csv_file, "r") as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        data.append(
            {
                "time": row["Date"],
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "Close": float(row["Close"]),
            }
        )

# Write to JSON file
# with open(json_file, "w") as file:
#     json.dump(data, file, indent=2)
varvData = []

df = pd.DataFrame(data)

varvDf = createVarv(df, "1day", df)

for index, row in varvDf.iterrows():
    varvData.append(
        {
            "time": row["time"],  # Convert datetime to string
            "out1": row["out1"],
            "out2": row["out2"],
            "out3": row["out3"],
            "out4": row["out4"],
            "out5": row["out5"],
            "out6": row["out6"],
            "out7": row["out7"],
            "out8": row["out8"],
            "out9": row["out9"],
            "out10": row["out10"],
            "out11": row["out11"],
        }
    )

with open("varvData.json", "w") as f:
    json.dump(varvData, f)
