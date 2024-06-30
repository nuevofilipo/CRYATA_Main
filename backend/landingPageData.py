from moduls.getTwelveData import getResponse
from moduls.indicatorFunctions import (
    createVarv,
)
import pandas as pd
import json

data = getResponse("BTC/USD", "1day", 3000)
df = pd.DataFrame(data)

cdata = []

for index, row in df.iterrows():
    cdata.append(
        {
            "time": row["time"].strftime("%Y-%m-%d"),  # Convert datetime to string
            "open": row["Open"],
            "high": row["High"],
            "low": row["Low"],
            "close": row["Close"],
        }
    )

# print(cdata)

with open("cdata.json", "w") as f:
    json.dump(cdata, f)
# varvData = []

# varvDf = createVarv(df, "1day", df)

# for index, row in varvDf.iterrows():
#     varvData.append(
#         {
#             "time": row["time"].strftime("%Y-%m-%d"),  # Convert datetime to string
#             "out1": row["out1"],
#             "out2": row["out2"],
#             "out3": row["out3"],
#             "out4": row["out4"],
#             "out5": row["out5"],
#             "out6": row["out6"],
#             "out7": row["out7"],
#             "out8": row["out8"],
#             "out9": row["out9"],
#             "out10": row["out10"],
#             "out11": row["out11"],
#         }
#     )

# with open("varvData.json", "w") as f:
#     json.dump(varvData, f)
