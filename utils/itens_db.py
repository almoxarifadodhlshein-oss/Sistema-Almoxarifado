# Em utils/itens_db.py (VERSÃO FINAL E ROBUSTA)

import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils.db_connection import connect_db

def init_items_db():
    """
    Cria a tabela de itens no PostgreSQL se ela não existir.
    Esta função agora será nossa principal 'verificadora'.
    """
    try:
        engine = connect_db()
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS itens (
                    id SERIAL PRIMARY KEY,
                    nome TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    UNIQUE(nome, categoria)
                )
            """))
            conn.commit()
    except Exception as e:
        st.error(f"ERRO CRÍTICO AO INICIALIZAR A TABELA 'itens': {e}")
        st.stop()

def add_item(categoria, nome):
    """Adiciona um novo item ao banco de dados."""
    # 1. GARANTE que a tabela exista antes de tentar inserir.
    init_items_db()
    
    if not categoria or not nome or not nome.strip():
        return False, "Categoria e nome são obrigatórios."
    
    engine = connect_db()
    try:
        with engine.connect() as conn:
            query = text("INSERT INTO itens (categoria, nome) VALUES (:cat, :nom)")
            conn.execute(query, {"cat": categoria.strip().upper(), "nom": nome.strip().upper()})
            conn.commit()
        # Limpa o cache da função de listagem para que o novo item apareça
        listar_itens_por_categoria.clear()
        return True, None
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e):
            return False, f"O item '{nome.upper()}' já existe na categoria '{categoria.upper()}'."
        return False, str(e)

def remove_item_by_name(nome):
    """Remove um item do banco de dados pelo nome."""
    init_items_db() # Garante que a tabela exista
    engine = connect_db()
    try:
        with engine.connect() as conn:
            query = text("DELETE FROM itens WHERE nome = :nom")
            conn.execute(query, {"nom": nome})
            conn.commit()
        # Limpa o cache da função de listagem para que o item removido desapareça
        listar_itens_por_categoria.clear()
        return True, None
    except Exception as e:
        return False, str(e)

@st.cache_data
def listar_itens_por_categoria(categoria):
    """Busca e retorna uma lista de nomes de itens filtrados por categoria."""
    # 2. GARANTE que a tabela exista antes de tentar ler.
    init_items_db()
    
    engine = connect_db()
    try:
        with engine.connect() as conn:
            query = text("SELECT nome FROM itens WHERE UPPER(categoria) = :cat ORDER BY nome")
            df = pd.read_sql_query(query, conn, params={"cat": categoria.upper()})
        return df['nome'].tolist() if not df.empty else []
    except Exception as e:
        # Não mostra erro aqui, pois a tabela pode simplesmente não existir ainda.
        # A função init_items_db() já lidaria com erros críticos de conexão.
        return []

def listar_itens(cat):
    """Alias para manter compatibilidade."""
    return listar_itens_por_categoria(cat)