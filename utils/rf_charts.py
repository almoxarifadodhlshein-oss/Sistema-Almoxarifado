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

    df = df.copy()

    df["percentual_disponibilidade"] = (
        (df["disponiveis"] / df["total"]) * 100
    ).round(2)

    fig = px.bar(

        df,

        x="area_atual",

        y="percentual_disponibilidade",

        text="disponiveis_%",

        hover_data={
            "total": True,
            "disponiveis": True,
            "quebrados": True,
            "ausentes": True,
            "percentual_disponibilidade": ':.2f'
        },

        title="Disponibilidade de RFs por Área (%)"
    )

    fig.update_traces(

        textposition="outside"
    )

    fig.update_layout(

        yaxis_title="Disponibilidade (%)",

        xaxis_title="Área",

        yaxis=dict(range=[0, 100]),

        uniformtext_minsize=8,

        uniformtext_mode="hide"
    )

    return fig

# ==========================================
# DISPONIBILIDADE POR MARCA
# ==========================================

def grafico_marca(df):

    df = df.copy()

    df["percentual_disponibilidade"] = (
        (df["disponiveis"] / df["total"]) * 100
    ).round(2)

    fig = px.bar(

        df,

        x="marca",

        y="percentual_disponibilidade",

        text="disponiveis_%",

        hover_data={
            "total": True,
            "disponiveis": True,
            "quebrados": True,
            "ausentes": True,
            "percentual_disponibilidade": ':.2f'
        },

        title="Disponibilidade de RFs por Marca (%)"
    )

    fig.update_traces(

        textposition="outside"
    )

    fig.update_layout(

        yaxis_title="Disponibilidade (%)",

        xaxis_title="Marca",

        yaxis=dict(range=[0, 100]),

        uniformtext_minsize=8,

        uniformtext_mode="hide"
    )

    return fig

# ==========================================
# EVOLUÇÃO POR ÁREA
# ==========================================

def grafico_evolucao_area(df):

    fig = px.line(

        df,

        x="semana",

        y="percentual_disponibilidade",

        color="area_atual",

        markers=True,

        title="Evolução Semanal por Área"
    )

    fig.update_layout(

        yaxis_title="% Disponibilidade",

        xaxis_title="Semana",

        hovermode="x unified"
    )

    return fig

# ==========================================
# EVOLUÇÃO POR MARCA
# ==========================================

def grafico_evolucao_marca(df):

    fig = px.line(

        df,

        x="semana",

        y="percentual_disponibilidade",

        color="marca",

        markers=True,

        title="Evolução Semanal por Marca"
    )

    fig.update_layout(

        yaxis_title="% Disponibilidade",

        xaxis_title="Semana",

        hovermode="x unified"
    )

    return fig