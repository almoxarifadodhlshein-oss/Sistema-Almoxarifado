# utils/db_connection.py

import streamlit as st
from sqlalchemy import create_engine


@st.cache_resource
def connect_db():

    connection_uri = st.secrets["postgres_uri"]

    engine = create_engine(

        connection_uri,

        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300

    )

    return engine