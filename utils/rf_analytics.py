import pandas as pd



# CALCULAR PERCENTUAIS


def calcular_percentuais(df):

    df = df.copy()

    df["percentual_disponiveis"] = (
        df["disponiveis"] / df["total"] * 100
    ).round(2)

    df["percentual_quebrados"] = (
        df["quebrados"] / df["total"] * 100
    ).round(2)

    df["percentual_ausentes"] = (
        df["ausentes"] / df["total"] * 100
    ).round(2)

    return df