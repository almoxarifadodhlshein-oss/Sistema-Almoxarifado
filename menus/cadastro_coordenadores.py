# Em menus/cadastro_coordenadores.py (VERSÃO FINAL)

import time
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.coordenadores_db import get_coordenadores, remove_coordenador_by_email

# Importações necessárias para o novo padrão
from sqlalchemy import text
from utils.db_connection import connect_db
from email_utils import enviar_email_coordenador

# --- FUNÇÕES DE ACESSO AO BANCO DE DADOS (JÁ CORRIGIDAS PARA POSTGRESQL) ---

'''def _get_coordenadores():
    """Lê e-mails cadastrados do PostgreSQL."""
    engine = connect_db()
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text("SELECT email FROM coordenadores ORDER BY email"), conn)
        return df['email'].tolist()
    except Exception:
        return []'''

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
    st.subheader("📝 Cadastro e Gestão de Coordenadores")

    # --- Formulário de Cadastro (O SEU CÓDIGO, ESTÁ CORRETO) ---
    with st.form("coordenador_form", clear_on_submit=True):
        coordenador = st.text_input("Nome do Coordenador", key="coord_nome")
        email = st.text_input("E-mail do Coordenador", key="coord_email")
        enviar = st.form_submit_button("Cadastrar Coordenador")

    # Lógica de envio (fora do with)
    if enviar:
        coordenador_value = st.session_state.get("coord_nome", "")
        email_value = st.session_state.get("coord_email", "")

        if not coordenador_value or not email_value or "@" not in email_value:
            st.error("Por favor, preencha um nome e um e-mail válidos.")
            return

        data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ok, err = registrar_coordenador(coordenador_value, email_value, data_cadastro)

        if not ok:
            st.error(f"Erro ao salvar: {err}"); return

        st.success("✅ Coordenador cadastrado com sucesso!")
        get_coordenadores.clear()

        try:
            sucesso_email, msg_email = enviar_email_coordenador(coordenador_value, email_value)
            if sucesso_email: st.info(f"📧 {msg_email}")
            else: st.warning(f"Coordenador salvo, mas e-mail não enviado: {msg_email}")
        except Exception as e:
            st.warning(f"Coordenador salvo, mas ocorreu um erro ao preparar o e-mail: {e}")

        time.sleep(4)
        st.rerun()

    st.markdown("---")

    # --- SEÇÃO DE VISUALIZAÇÃO E EXCLUSÃO (ATUALIZADA) ---
    st.subheader("📧 Coordenadores Cadastrados")
    coordenadores_cadastrados = get_coordenadores()

    if not coordenadores_cadastrados:
        st.info("Nenhum e-mail de coordenador cadastrado ainda.")
    else:
        # Transforma a lista em um DataFrame para exibir o nome e o email
        engine = connect_db()
        try:
            engine = connect_db()
            with engine.connect() as conn:
                df_coords = pd.read_sql_query(text("SELECT coordenador, email FROM coordenadores ORDER BY coordenador"), conn)

            # Exibe cada coordenador com um botão de remover
            for index, row in df_coords.iterrows():
                col1, col2 = st.columns([4, 1])
                with col1:
                    # Mostra o nome e o e-mail
                    st.write(f"**{row['coordenador']}** ({row['email']})")
                with col2:
                    # Chave única para cada botão
                    if st.button("Remover", key=f"remove_coord_{row['email']}"):
                        ok_remove, msg_remove = remove_coordenador_by_email(row['email'])
                        if ok_remove:
                            st.success(f"Coordenador '{row['coordenador']}' removido.")
                            get_coordenadores.clear()
                            st.rerun() # Recarrega para atualizar a lista
                        else:
                            st.error(f"Erro ao remover: {msg_remove}")
        except Exception as e:

            st.error(f"Erro ao carregar lista de coordenadores: {e}")





