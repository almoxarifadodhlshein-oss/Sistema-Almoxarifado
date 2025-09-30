# Em menus/cadastro_coordenadores.py (VERSÃO FINAL)

import time
import streamlit as st
import pandas as pd
from datetime import datetime

# Importações necessárias para o novo padrão
from sqlalchemy import text
from utils.db_connection import connect_db
from email_utils import enviar_email_coordenador

# --- FUNÇÕES DE ACESSO AO BANCO DE DADOS (JÁ CORRIGIDAS PARA POSTGRESQL) ---

def _get_coordenadores():
    """Lê e-mails cadastrados do PostgreSQL."""
    engine = connect_db()
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text("SELECT email FROM coordenadores ORDER BY email"), conn)
        return df['email'].tolist()
    except Exception:
        return []

def registrar_coordenador(coordenador, email, data_cadastro):
    """Registra um novo coordenador no PostgreSQL."""
    engine = connect_db()
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS coordenadores (
                    id SERIAL PRIMARY KEY,
                    coordenador TEXT,
                    email TEXT UNIQUE,
                    data_cadastro TEXT
                )
            """))
            query = text("INSERT INTO coordenadores (coordenador, email, data_cadastro) VALUES (:coord, :email, :data)")
            conn.execute(query, {"coord": coordenador.strip().upper(), "email": email.strip(), "data": data_cadastro})
            conn.commit()
        return True, None
    except Exception as exc:
        if "duplicate key value violates unique constraint" in str(exc):
            return False, f"O e-mail '{email}' já está cadastrado."
        return False, str(exc)

# --- FUNÇÃO PRINCIPAL DA PÁGINA ---

def carregar():
    st.subheader("📝 Cadastro de Coordenadores")

    # 1. O formulário agora tem uma chave estática e 'clear_on_submit=True'
    with st.form("coordenador_form", clear_on_submit=True):
        coordenador = st.text_input("Nome do Coordenador", key="coord_nome")
        email = st.text_input("E-mail do Coordenador", key="coord_email")
        enviar = st.form_submit_button("Cadastrar Coordenador")

    # 2. A lógica de processamento fica FORA do 'with st.form'
    if enviar:
        coordenador_value = st.session_state.get("coord_nome", "")
        email_value = st.session_state.get("coord_email", "")

        if not coordenador_value or not email_value or "@" not in email_value:
            st.error("Por favor, preencha um nome e um e-mail válidos.")
            return

        data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ok, err = registrar_coordenador(coordenador_value, email_value, data_cadastro)

        if not ok:
            st.error(f"Erro ao salvar: {err}")
            return
        
        st.success("✅ Coordenador cadastrado com sucesso!")

        try:
            sucesso_email, msg_email = enviar_email_coordenador(coordenador_value, email_value)
            if sucesso_email:
                st.info(f"📧 {msg_email}")
            else:
                st.warning(f"Coordenador salvo, mas o e-mail não pôde ser enviado: {msg_email}")
        except Exception as e:
            st.warning(f"Coordenador salvo, mas ocorreu um erro ao preparar o e-mail: {e}")
        
        time.sleep(2)
        # 3. 'st.rerun()' é usado para recarregar a lista de coordenadores abaixo
        st.rerun()

    st.markdown("---")
    
    st.subheader("📧 Coordenadores Cadastrados")
    coordenadores_cadastrados = _get_coordenadores()
    
    if not coordenadores_cadastrados:
        st.info("Nenhum e-mail de coordenador cadastrado ainda.")
    else:
        # Usamos st.dataframe para uma melhor visualização
        st.dataframe(pd.DataFrame({"E-mails Cadastrados": coordenadores_cadastrados}), use_container_width=True)