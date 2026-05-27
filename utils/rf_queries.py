from sqlalchemy import text
import pandas as pd

from utils.db_connection import connect_db
import streamlit as st


# EVOLUÇÃO SEMANAL


@st.cache_data(ttl=30)
def obter_evolucao_semanal(
    data_inicio=None,
    data_fim=None
):

    engine = connect_db()

    query = text("""
        SELECT

            s.semana,

            COUNT(v.id) FILTER (
                WHERE v.status_operacional = 'Disponível'
            ) AS disponiveis,

            COUNT(v.id) FILTER (
                WHERE v.status_operacional = 'Quebrado'
            ) AS quebrados,

            COUNT(v.id) FILTER (
                WHERE v.status_operacional = 'Ausente'
            ) AS ausentes,

            COUNT(v.id) AS total

        FROM rf_sessoes_semanais s

        LEFT JOIN rf_verificacoes v
            ON v.sessao_id = s.id

        WHERE s.data_inicio::date
        BETWEEN :data_inicio
        AND :data_fim

        GROUP BY s.semana

        ORDER BY s.semana
    """)

    return pd.read_sql(

        query,

        engine,

        params={

            "data_inicio": data_inicio,
            "data_fim": data_fim
        }
    )



# DISPONIBILIDADE POR ÁREA


@st.cache_data(ttl=30)
def obter_disponibilidade_por_area(
    data_inicio=None,
    data_fim=None
):

    engine = connect_db()

    query = text("""
        SELECT

            r.area_atual,

            COUNT(*) AS total,

            COUNT(*) FILTER (
                WHERE v.status_operacional = 'Disponível'
            ) AS disponiveis,

            COUNT(*) FILTER (
                WHERE v.status_operacional = 'Quebrado'
            ) AS quebrados,

            COUNT(*) FILTER (
                WHERE v.status_operacional = 'Ausente'
            ) AS ausentes

        FROM rf_verificacoes v

        INNER JOIN rfs r
            ON r.id = v.rf_id

        INNER JOIN rf_sessoes_semanais s
            ON s.id = v.sessao_id

        WHERE s.data_inicio::date
        BETWEEN :data_inicio
        AND :data_fim

        GROUP BY r.area_atual

        ORDER BY disponiveis DESC
    """)

    return pd.read_sql(

        query,

        engine,

        params={

            "data_inicio": data_inicio,
            "data_fim": data_fim
        }
    )



# DISPONIBILIDADE POR MARCA

@st.cache_data(ttl=30)
def obter_disponibilidade_por_marca(
    data_inicio=None,
    data_fim=None
):

    engine = connect_db()

    query = text("""
        SELECT

            r.marca,

            COUNT(*) AS total,

            COUNT(*) FILTER (
                WHERE v.status_operacional = 'Disponível'
            ) AS disponiveis,

            COUNT(*) FILTER (
                WHERE v.status_operacional = 'Quebrado'
            ) AS quebrados,

            COUNT(*) FILTER (
                WHERE v.status_operacional = 'Ausente'
            ) AS ausentes

        FROM rf_verificacoes v

        INNER JOIN rfs r
            ON r.id = v.rf_id

        INNER JOIN rf_sessoes_semanais s
            ON s.id = v.sessao_id

        WHERE s.data_inicio::date
        BETWEEN :data_inicio
        AND :data_fim

        GROUP BY r.marca

        ORDER BY disponiveis DESC
    """)

    return pd.read_sql(

        query,

        engine,

        params={

            "data_inicio": data_inicio,
            "data_fim": data_fim
        }
    )