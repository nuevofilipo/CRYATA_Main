import pandas as pd
import sys

sys.path.append("../../")

from backend.moduls.getTwelveData import getResponse


def createDictionaryEntry(df):
    # perform heavy calculations with some functions to be created

    dict_entry = df.iloc[-1].to_dict()
    return dict_entry


def main():
    df = getResponse(
        "BTC/USD",
        "1day",
        200,
    )

    print(createDictionaryEntry(df))


main()
