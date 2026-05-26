from sqlalchemy import text
import pandas as pd

from utils.db_connection import connect_db



# EVOLUÇÃO SEMANAL


def obter_evolucao_semanal():

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

            COUNT(v.id) AS total_verificados

        FROM rf_sessoes_semanais s

        LEFT JOIN rf_verificacoes v
            ON v.sessao_id = s.id

        GROUP BY s.semana

        ORDER BY s.semana

    """)

    return pd.read_sql(query, engine)



# DISPONIBILIDADE POR ÁREA


def obter_disponibilidade_por_area():

    engine = connect_db()

    query = text("""

        SELECT

            area_atual,

            COUNT(*) AS total,

            COUNT(*) FILTER (
                WHERE status = 'Disponível'
            ) AS disponiveis,

            COUNT(*) FILTER (
                WHERE status = 'Quebrado'
            ) AS quebrados,

            COUNT(*) FILTER (
                WHERE status = 'Ausente'
            ) AS ausentes

        FROM rfs

        WHERE ativo = TRUE

        GROUP BY area_atual

        ORDER BY disponiveis DESC

    """)

    return pd.read_sql(query, engine)



# DISPONIBILIDADE POR MARCA

def obter_disponibilidade_por_marca():

    engine = connect_db()

    query = text("""

        SELECT

            marca,

            COUNT(*) AS total,

            COUNT(*) FILTER (
                WHERE status = 'Disponível'
            ) AS disponiveis,

            COUNT(*) FILTER (
                WHERE status = 'Quebrado'
            ) AS quebrados,

            COUNT(*) FILTER (
                WHERE status = 'Ausente'
            ) AS ausentes

        FROM rfs

        WHERE ativo = TRUE

        GROUP BY marca

        ORDER BY disponiveis DESC

    """)

    return pd.read_sql(query, engine)