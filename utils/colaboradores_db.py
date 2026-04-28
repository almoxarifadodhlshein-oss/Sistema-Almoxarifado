# Em utils/colaboradores_db.py

import pandas as pd
from sqlalchemy import text
from utils.db_connection import connect_db
import streamlit as st

def get_lista_pessoas_com_movimentacao():
    engine = connect_db()
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT DISTINCT cpf, colaborador AS nome 
                FROM saida_epis 
                WHERE cpf IS NOT NULL AND cpf != ''
                ORDER BY colaborador
            """)
            df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        return pd.DataFrame()

def get_historico_por_cpf(cpf, data_inicio, data_fim):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            params = {
                "cpf": cpf,
                "data_inicio": f"{data_inicio} 00:00:00",
                "data_fim": f"{data_fim} 23:59:59"
            }
            
            # 1. Saídas de EPI
            query_saidas = text("""
                SELECT data, item, tamanho, quantidade, motivo, assinatura 
                FROM saida_epis 
                WHERE cpf = :cpf AND data >= :data_inicio AND data <= :data_fim 
                ORDER BY data DESC
            """)
            df_saidas = pd.read_sql_query(query_saidas, conn, params=params)
            
            # 2. Empréstimos
            try:
                query_emp = text("""
                    SELECT data, item, quantidade, status_item, assinatura
                    FROM emprestimos 
                    WHERE cpf = :cpf AND data >= :data_inicio AND data <= :data_fim 
                    ORDER BY data DESC
                """)
                df_emprestimos = pd.read_sql_query(query_emp, conn, params=params)
            except:
                df_emprestimos = pd.DataFrame()
                
            # 3. Devoluções
            try:
                query_dev = text("""
                    SELECT data, item, quantidade, status_item, assinatura
                    FROM devolucoes 
                    WHERE cpf = :cpf AND data >= :data_inicio AND data <= :data_fim 
                    ORDER BY data DESC
                """)
                df_devolucoes = pd.read_sql_query(query_dev, conn, params=params)
            except:
                df_devolucoes = pd.DataFrame()

            # 4. Saídas de Insumos (NOVO)
            try:
                query_ins = text("""
                    SELECT data, insumo as item, quantidade
                    FROM saida_insumos 
                    WHERE cpf = :cpf AND data >= :data_inicio AND data <= :data_fim 
                    ORDER BY data DESC
                """)
                df_insumos = pd.read_sql_query(query_ins, conn, params=params)
            except Exception as e:
                # LIGANDO O MODO DETETIVE: Vai mostrar o erro real na tela do Streamlit!
                st.warning(f"Atenção, erro na tabela de Insumos: {e}")
                df_insumos = pd.DataFrame()
            
            # Agora retornamos 4 tabelas!
            return df_saidas, df_emprestimos, df_devolucoes, df_insumos
    except Exception as e:
        st.error(f"Erro na busca: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()