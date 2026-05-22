# utils/rf_db.py

from sqlalchemy import text
from utils.db_connection import connect_db
from datetime import datetime
import pandas as pd
import streamlit as st


# =========================
# INICIALIZAÇÃO DAS TABELAS
# =========================

def init_rf_db():

    engine = connect_db()

    with engine.begin() as conn:

        # =========================
        # TABELA RFs
        # =========================

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rfs (

                id SERIAL PRIMARY KEY,

                numero VARCHAR(50),

                codigo_rf VARCHAR(100) UNIQUE NOT NULL,

                modelo TEXT,

                marca TEXT,

                status VARCHAR(30) NOT NULL DEFAULT 'Disponível',

                area_atual VARCHAR(100),

                responsavel_atual VARCHAR(100),

                ativo BOOLEAN DEFAULT TRUE,

                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                ultima_verificacao TIMESTAMP
            );
        """))

        # =========================
        # SESSÕES SEMANAIS
        # =========================

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rf_sessoes_semanais (

                id SERIAL PRIMARY KEY,

                semana VARCHAR(20) UNIQUE,

                iniciada_por VARCHAR(100),

                data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                finalizada BOOLEAN DEFAULT FALSE,

                data_finalizacao TIMESTAMP
            );
        """))

        # =========================
        # VERIFICAÇÕES
        # =========================

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rf_verificacoes (

                id SERIAL PRIMARY KEY,

                rf_id INTEGER REFERENCES rfs(id),

                sessao_id INTEGER REFERENCES rf_sessoes_semanais(id),

                data_verificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                usuario VARCHAR(100),

                presente BOOLEAN DEFAULT TRUE,

                status_operacional VARCHAR(50),

                observacao TEXT
            );
        """))

        # =========================
        # HISTÓRICO
        # =========================

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS rf_historico (

                id SERIAL PRIMARY KEY,

                rf_id INTEGER REFERENCES rfs(id),

                sessao_id INTEGER REFERENCES rf_sessoes_semanais(id),

                acao VARCHAR(100),

                status_anterior VARCHAR(50),

                status_novo VARCHAR(50),

                area_anterior VARCHAR(100),

                area_nova VARCHAR(100),

                responsavel_anterior VARCHAR(100),

                responsavel_novo VARCHAR(100),

                usuario VARCHAR(100),

                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                observacao TEXT
            );
        """))

        conn.execute(text("""
            ALTER TABLE rf_historico
            ADD COLUMN IF NOT EXISTS sessao_id INTEGER
            REFERENCES rf_sessoes_semanais(id);
        """))

        # =========================
        # ÍNDICES PERFORMANCE
        # =========================

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rfs_codigo_rf
            ON rfs(codigo_rf);
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rfs_codigo_rf_upper
            ON rfs(UPPER(codigo_rf));
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rf_verificacoes_sessao
            ON rf_verificacoes(sessao_id);
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rf_verificacoes_rf_id
            ON rf_verificacoes(rf_id);
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rf_historico_rf_id
            ON rf_historico(rf_id);
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rf_historico_sessao
            ON rf_historico(sessao_id);
        """))


# =========================
# CADASTRO RF
# =========================

def cadastrar_rf(
    numero,
    codigo_rf,
    modelo,
    marca,
    area,
    responsavel,
    status="Disponível"
):

    engine = connect_db()

    with engine.begin() as conn:

        conn.execute(text("""
            INSERT INTO rfs (

                numero,
                codigo_rf,
                modelo,
                marca,
                status,
                area_atual,
                responsavel_atual

            )
            VALUES (

                :numero,
                :codigo_rf,
                :modelo,
                :marca,
                :status,
                :area,
                :responsavel
            )
        """), {

            "numero": numero,
            "codigo_rf": codigo_rf.strip().upper(),
            "modelo": modelo,
            "marca": marca,
            "status": status,
            "area": area,
            "responsavel": responsavel

        })




# =========================
# LISTAGEM RF
# =========================


def listar_rfs():

    engine = connect_db()

    query = text("""
        SELECT *
        FROM rfs
        WHERE ativo = TRUE
        ORDER BY codigo_rf
    """)

    return pd.read_sql(query, engine)


# =========================
# BUSCAR RF
# =========================

def buscar_rf_por_codigo(codigo_rf):

    engine = connect_db()

    query = text("""
        SELECT *
        FROM rfs
        WHERE UPPER(codigo_rf) = :codigo_rf
        LIMIT 1
    """)

    with engine.connect() as conn:

        result = conn.execute(query, {
            "codigo_rf": str(codigo_rf).strip().upper()
        }).fetchone()

    if not result:
        return None

    return dict(result._mapping)


# =========================
# REGISTRAR HISTÓRICO
# =========================

def registrar_historico(
    rf_id,
    acao,
    usuario,
    sessao_id=None,
    status_anterior=None,
    status_novo=None,
    area_anterior=None,
    area_nova=None,
    responsavel_anterior=None,
    responsavel_novo=None,
    observacao=None
):

    engine = connect_db()

    with engine.begin() as conn:

        conn.execute(text("""
            INSERT INTO rf_historico (

                rf_id,
                sessao_id,
                acao,
                status_anterior,
                status_novo,
                area_anterior,
                area_nova,
                responsavel_anterior,
                responsavel_novo,
                usuario,
                observacao

            )
            VALUES (

                :rf_id,
                :sessao_id,
                :acao,
                :status_anterior,
                :status_novo,
                :area_anterior,
                :area_nova,
                :responsavel_anterior,
                :responsavel_novo,
                :usuario,
                :observacao
            )
        """), {

            "rf_id": rf_id,
            "sessao_id": sessao_id,
            "acao": acao,
            "status_anterior": status_anterior,
            "status_novo": status_novo,
            "area_anterior": area_anterior,
            "area_nova": area_nova,
            "responsavel_anterior": responsavel_anterior,
            "responsavel_novo": responsavel_novo,
            "usuario": usuario,
            "observacao": observacao
        })



# =========================
# VERIFICAÇÃO SEMANAL
# =========================

def registrar_verificacao(
    rf_id,
    usuario,
    status_operacional,
    observacao=""
):

    engine = connect_db()

    sessao = obter_sessao_ativa()

    if not sessao:
        return False

    sessao_id = sessao["id"]

    with engine.begin() as conn:

        existe = conn.execute(text("""
            SELECT id
            FROM rf_verificacoes
            WHERE rf_id = :rf_id
            AND sessao_id = :sessao_id
        """), {

            "rf_id": rf_id,
            "sessao_id": sessao_id

        }).fetchone()

        if existe:
            return False

        conn.execute(text("""
            INSERT INTO rf_verificacoes (

                rf_id,
                sessao_id,
                usuario,
                status_operacional,
                observacao

            )
            VALUES (

                :rf_id,
                :sessao_id,
                :usuario,
                :status_operacional,
                :observacao
            )
        """), {

            "rf_id": rf_id,
            "sessao_id": sessao_id,
            "usuario": usuario,
            "status_operacional": status_operacional,
            "observacao": observacao
        })

        conn.execute(text("""
            UPDATE rfs
            SET
                ultima_verificacao = CURRENT_TIMESTAMP,
                status = :status
            WHERE id = :rf_id
        """), {

            "status": status_operacional,
            "rf_id": rf_id
        })

    registrar_historico(
        rf_id=rf_id,
        sessao_id=sessao_id,
        acao="Verificação Semanal",
        usuario=usuario,
        status_novo=status_operacional,
        observacao=observacao
    )


    return True


# =========================
# DASHBOARD
# =========================


def obter_dashboard_rf():

    engine = connect_db()

    query = text("""
        SELECT

            COUNT(*) AS total_rfs,

            COUNT(*) FILTER (
                WHERE status = 'Disponível'
            ) AS disponiveis,

            COUNT(*) FILTER (
                WHERE status = 'Quebrado'
            ) AS quebrados,

            COUNT(*) FILTER (
                WHERE status = 'Ausente'
            ) AS ausentes,

            COUNT(*) FILTER (
                WHERE area_atual ILIKE '%RC%'
            ) AS total_rc,

            COUNT(*) FILTER (
                WHERE area_atual ILIKE '%3P%'
            ) AS total_3p

        FROM rfs
        WHERE ativo = TRUE
    """)

    df = pd.read_sql(query, engine)

    return df.iloc[0].to_dict()


# =========================
# HISTÓRICO GERAL
# =========================

def obter_historico():

    engine = connect_db()

    query = text("""
        SELECT

            h.data_hora,
            r.codigo_rf,
            h.acao,
            h.usuario,
            h.status_novo,
            h.observacao

        FROM rf_historico h

        JOIN rfs r
            ON r.id = h.rf_id

        ORDER BY h.data_hora DESC

        LIMIT 200
    """)

    return pd.read_sql(query, engine)


# =========================
# HISTÓRICO DA SESSÃO
# =========================


def obter_historico_sessao():

    engine = connect_db()

    sessao = obter_sessao_ativa()

    if not sessao:
        return pd.DataFrame()

    query = text("""
        SELECT

            r.codigo_rf,
            r.numero,
            h.status_novo,
            h.usuario,
            h.observacao,
            h.data_hora

        FROM rf_historico h

        INNER JOIN rfs r
            ON r.id = h.rf_id

        WHERE h.sessao_id = :sessao_id

        ORDER BY h.data_hora DESC
    """)

    return pd.read_sql(
        query,
        engine,
        params={
            "sessao_id": sessao["id"]
        }
    )


# =========================
# SESSÃO SEMANAL
# =========================

def obter_semana_atual():

    return datetime.now().strftime("%Y-W%U")



def obter_sessao_ativa():

    engine = connect_db()

    semana = obter_semana_atual()

    query = text("""
        SELECT *
        FROM rf_sessoes_semanais
        WHERE semana = :semana
        AND finalizada = FALSE
        LIMIT 1
    """)

    df = pd.read_sql(
        query,
        engine,
        params={
            "semana": semana
        }
    )

    if df.empty:
        return None

    return df.iloc[0].to_dict()


def iniciar_sessao_semana(usuario):

    engine = connect_db()

    semana = obter_semana_atual()

    with engine.begin() as conn:

        existe = conn.execute(text("""
            SELECT id
            FROM rf_sessoes_semanais
            WHERE semana = :semana
        """), {
            "semana": semana
        }).fetchone()

        if existe:
            return False

        conn.execute(text("""
            INSERT INTO rf_sessoes_semanais (

                semana,
                iniciada_por

            )
            VALUES (

                :semana,
                :usuario
            )
        """), {

            "semana": semana,
            "usuario": usuario
        })


    return True


def finalizar_sessao_semana(usuario):

    sessao = obter_sessao_ativa()

    if not sessao:
        return False

    sessao_id = sessao["id"]

    engine = connect_db()

    with engine.begin() as conn:

        nao_verificados = conn.execute(text("""

            SELECT r.id, r.status

            FROM rfs r

            WHERE r.ativo = TRUE

            AND r.id NOT IN (

                SELECT rf_id
                FROM rf_verificacoes
                WHERE sessao_id = :sessao_id
            )

        """), {

            "sessao_id": sessao_id

        }).fetchall()

        for rf in nao_verificados:

            rf_id = rf[0]
            status_atual = rf[1]

            if status_atual == "Quebrado":
                continue

            conn.execute(text("""
                UPDATE rfs
                SET status = 'Ausente'
                WHERE id = :rf_id
            """), {
                "rf_id": rf_id
            })

            conn.execute(text("""
                INSERT INTO rf_historico (

                    rf_id,
                    sessao_id,
                    acao,
                    usuario,
                    status_anterior,
                    status_novo,
                    observacao

                )
                VALUES (

                    :rf_id,
                    :sessao_id,
                    'Ausência Automática',
                    :usuario,
                    :status_anterior,
                    'Ausente',
                    'RF não localizado na verificação semanal'

                )
            """), {

                "rf_id": rf_id,
                "sessao_id": sessao_id,
                "usuario": usuario,
                "status_anterior": status_atual
            })

        conn.execute(text("""
            UPDATE rf_sessoes_semanais
            SET
                finalizada = TRUE,
                data_finalizacao = CURRENT_TIMESTAMP
            WHERE id = :sessao_id
        """), {

            "sessao_id": sessao_id
        })


    return True


# =========================
# BUSCA POR FINAL
# =========================


def buscar_rfs_por_final(final_rf):

    engine = connect_db()

    query = text("""
        SELECT *
        FROM rfs
        WHERE codigo_rf ILIKE :busca
        AND ativo = TRUE
        ORDER BY codigo_rf
    """)

    busca = f"%{final_rf.strip().upper()}"

    return pd.read_sql(
        query,
        engine,
        params={
            "busca": busca
        }
    )


# =========================
# HISTÓRICO DE AUDITORIAS
# =========================


def obter_historico_auditorias():

    engine = connect_db()

    query = text("""
        SELECT

            s.id,
            s.semana,
            s.iniciada_por,
            s.data_inicio,

            COUNT(*) FILTER (
                WHERE v.status_operacional = 'Disponível'
            ) AS disponiveis,

            COUNT(*) FILTER (
                WHERE v.status_operacional = 'Quebrado'
            ) AS quebrados,

            (
                SELECT COUNT(*)

                FROM rfs r

                WHERE r.ativo = TRUE

                AND r.id NOT IN (

                    SELECT rf_id

                    FROM rf_verificacoes

                    WHERE sessao_id = s.id
                )
            ) AS ausentes

        FROM rf_sessoes_semanais s

        LEFT JOIN rf_verificacoes v
            ON v.sessao_id = s.id

        GROUP BY

            s.id,
            s.semana,
            s.iniciada_por,
            s.data_inicio

        ORDER BY s.data_inicio DESC
    """)

    return pd.read_sql(query, engine)