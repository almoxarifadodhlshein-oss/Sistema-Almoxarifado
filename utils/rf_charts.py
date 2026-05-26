import plotly.express as px



# EVOLUÇÃO SEMANAL


def grafico_evolucao(df):

    fig = px.line(

        df,

        x="semana",

        y=[
            "disponiveis",
            "quebrados",
            "ausentes"
        ],

        markers=True,

        title="Evolução Semanal RFs"
    )

    return fig


# ==========================================
# DISPONIBILIDADE POR ÁREA
# ==========================================

def grafico_area(df):

    fig = px.bar(

        df,

        x="percentual_disponiveis",

        y="area_atual",

        orientation="h",

        title="Disponibilidade por Site",

        hover_data=[
            "total",
            "disponiveis",
            "quebrados",
            "ausentes"
        ]
    )

    return fig


# ==========================================
# DISPONIBILIDADE POR MARCA
# ==========================================

def grafico_marca(df):

    fig = px.bar(

        df,

        x="percentual_disponiveis",

        y="marca",

        orientation="h",

        title="Disponibilidade por Marca",

        hover_data=[
            "total",
            "disponiveis",
            "quebrados",
            "ausentes"
        ]
    )

    return fig