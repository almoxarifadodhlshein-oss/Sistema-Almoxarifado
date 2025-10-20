# Em utils/coordenadores_db.py
import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils.db_connection import connect_db

@st.cache_data
def get_coordenadores():
    """Busca e retorna uma lista de e-mails de coordenadores do PostgreSQL."""
    engine = connect_db()
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text("SELECT email FROM coordenadores ORDER BY email"), conn)
        return df['email'].tolist() if not df.empty else ["Nenhum e-mail cadastrado"]
    except Exception:
        return ["Nenhum e-mail cadastrado"]
    
def remove_coordenador_by_email(email):
    """Remove um coordenador do banco de dados pelo e-mail."""
    engine = connect_db()
    try:
        with engine.connect() as conn:
            query = text("DELETE FROM coordenadores WHERE email = :email_para_remover")
            conn.execute(query, {"email_para_remover": email})
            conn.commit()

        # Limpa o cache da função de listagem
        get_coordenadores.clear()
        return True, None
    except Exception as e:
        return False, str(e)