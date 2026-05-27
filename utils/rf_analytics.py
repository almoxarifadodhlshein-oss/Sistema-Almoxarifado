import pandas as pd


# ==========================================
# CALCULAR PERCENTUAIS
# ==========================================

def calcular_percentuais(df):

    df = df.copy()

    # EVITAR DIVISÃO POR ZERO
    df["total"] = df["total"].replace(0, 1)

    df["percentual_disponiveis"] = (
        (df["disponiveis"] / df["total"]) * 100
    ).round(2)

    df["percentual_quebrados"] = (
        (df["quebrados"] / df["total"]) * 100
    ).round(2)

    df["percentual_ausentes"] = (
        (df["ausentes"] / df["total"]) * 100
    ).round(2)

    df["disponiveis_%"] = (
        df["percentual_disponiveis"]
        .map(lambda x: f"{x:.2f}%")
    )

    df["quebrados_%"] = (
        df["percentual_quebrados"]
        .map(lambda x: f"{x:.2f}%")
    )

    df["ausentes_%"] = (
        df["percentual_ausentes"]
        .map(lambda x: f"{x:.2f}%")
    )

    return df