# Em utils/estoque_db.py (VERSÃO FINAL PARA POSTGRESQL)

import streamlit as st
import os
from datetime import datetime
import pandas as pd
from sqlalchemy import text
from utils.db_connection import connect_db

def init_estoque_db():
    """Cria a tabela de estoque no PostgreSQL se ela não existir."""
    engine = connect_db()
    try:
        with engine.connect() as conn:
            # 2. SINTAXE DO CREATE TABLE AJUSTADA PARA POSTGRESQL
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS estoque (
                    id SERIAL PRIMARY KEY,
                    item_nome TEXT NOT NULL,
                    tamanho TEXT NOT NULL,
                    status TEXT NOT NULL, 
                    fornecedor TEXT, 
                    quantidade INTEGER NOT NULL,
                    valor_unitario REAL NOT NULL,
                    tipo TEXT,
                    data_ultima_atualizacao TEXT,
                    UNIQUE(item_nome, tamanho, status)
                )
            """))
            conn.commit()
    except Exception as e:
        st.error(f"ERRO CRÍTICO AO INICIALIZAR A TABELA 'estoque': {e}")
        st.stop()

@st.cache_data
def get_estoque_atual():
    """Retorna o DataFrame completo do estoque atual do PostgreSQL."""
    init_estoque_db() # Garante que a tabela exista antes de ler
    engine = connect_db()
    with engine.connect() as conn:
        df = pd.read_sql_query(
            text("SELECT item_nome, tamanho, status, fornecedor, quantidade, valor_unitario, tipo, data_ultima_atualizacao FROM estoque ORDER BY item_nome, tamanho, status"),
            conn
        )
    return df

def atualizar_estoque(item_nome, tamanho, status, tipo, quantidade_delta, fornecedor=None, valor_unitario=0.0):
    """
    Atualiza o estoque de um item no PostgreSQL.
    'fornecedor' e 'valor_unitario' são usados principalmente em ENTRADAS.
    """
    init_estoque_db() # Garante que a tabela exista
    engine = connect_db()
    
    item_nome = item_nome.strip().upper()
    tamanho = tamanho.strip().upper() if tamanho else "ÚNICO"
    status = status.strip().upper()
    fornecedor_final = fornecedor.strip().upper() if fornecedor else "N/A"
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with engine.connect() as conn:
            # 3. USA A NOVA SINTAXE PARA BUSCAR O ITEM
            query_select = text("SELECT quantidade, valor_unitario, fornecedor FROM estoque WHERE item_nome = :nome AND tamanho = :tam AND status = :stat FOR UPDATE")
            result = conn.execute(query_select, {"nome": item_nome, "tam": tamanho, "stat": status}).first()

            if result:
                nova_quantidade = result.quantidade + quantidade_delta
                valor_final = valor_unitario if quantidade_delta > 0 else result.valor_unitario
                fornecedor_final = fornecedor_final if quantidade_delta > 0 else result.fornecedor
                
                query_update = text("""
                    UPDATE estoque SET quantidade = :qtd, valor_unitario = :val, fornecedor = :forn, data_ultima_atualizacao = :data 
                    WHERE item_nome = :nome AND tamanho = :tam AND status = :stat
                """)
                conn.execute(query_update, {
                    "qtd": nova_quantidade, "val": valor_final, "forn": fornecedor_final, "data": data_atual,
                    "nome": item_nome, "tam": tamanho, "stat": status
                })
            else:
                if quantidade_delta < 0:
                    return False, f"Item '{item_nome}' (Tam: {tamanho}, Status: {status}) não encontrado no estoque para dar baixa."
                
                query_insert = text("""
                    INSERT INTO estoque (item_nome, tamanho, status, fornecedor, quantidade, valor_unitario, tipo, data_ultima_atualizacao) 
                    VALUES (:nome, :tam, :stat, :forn, :qtd, :val, :tipo, :data)
                """)
                conn.execute(query_insert, {
                    "nome": item_nome, "tam": tamanho, "stat": status, "forn": fornecedor_final,
                    "qtd": quantidade_delta, "val": valor_unitario, "tipo": tipo, "data": data_atual
                })
            conn.commit()
        
        get_estoque_atual.clear()
        return True, None
    except Exception as e:
        return False, str(e)