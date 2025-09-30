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