# Em utils/db_connection.py
import streamlit as st
import sqlalchemy

# Usa o cache de recursos do Streamlit para criar a conexão apenas uma vez
@st.cache_resource
def connect_db():
    """Conecta-se ao banco de dados PostgreSQL usando a connection string."""
    # A forma segura de guardar a senha é usando os "Secrets" do Streamlit.
    # Por enquanto, podemos colocar direto, mas vamos mudar isso na hora de hospedar.
    connection_uri = st.secrets["postgres_uri"]
    engine = sqlalchemy.create_engine(connection_uri)
    return engine