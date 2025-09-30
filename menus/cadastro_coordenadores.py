# menus/cadastro_coordenadores.py
import os
import time
import streamlit as st
from sqlalchemy import text
from utils.db_connection import connect_db
import pandas as pd
from datetime import datetime
from email_utils import enviar_email_coordenador

DB_DIR = os.path.join(os.getcwd(), "banco de dados")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "coordenadores.db")


def _get_coordenadores():
    """
    Função robusta para ler e-mails cadastrados do PostgreSQL.
    """
    engine = connect_db() # Usa a nova conexão
    try:
        with engine.connect() as conn:
            # Envolve a query com text()
            df = pd.read_sql_query(text("SELECT email FROM coordenadores ORDER BY email"), conn)
        return df['email'].tolist()
    except Exception as e:
        # Se a tabela ainda não existe, não é um erro crítico.
        # O 'str(e)' vai mostrar o erro no console se algo mais sério acontecer.
        # st.warning(f"Ainda não há coordenadores cadastrados. {str(e)}")
        return []

def registrar_coordenador(coordenador, email, data_cadastro):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            # 2. NÃO USAMOS MAIS O 'cursor'. A conexão executa diretamente.
            
            # 3. MUDAMOS a sintaxe para SERIAL PRIMARY KEY do PostgreSQL
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS coordenadores (
                    id SERIAL PRIMARY KEY,
                    coordenador TEXT,
                    email TEXT UNIQUE,
                    data_cadastro TEXT
                )
            """))
            
            # 4. USAMOS parâmetros nomeados (ex: :coord) para mais clareza e segurança
            query = text("""
                INSERT INTO coordenadores (coordenador, email, data_cadastro)
                VALUES (:coord, :email, :data)
            """)
            conn.execute(query, {
                "coord": coordenador.strip().upper(),
                "email": email.strip(),
                "data": data_cadastro
            })
            conn.commit() # Commit para salvar as alterações
        return True, None
    except Exception as exc:
        if "duplicate key value violates unique constraint" in str(exc):
            return False, f"O e-mail '{email}' já está cadastrado."
        return False, str(exc)


def _safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()


def carregar():
    st.subheader("📝 Cadastro de Emails")

    form_key = f"coordenadores_form"

    with st.form(key=form_key, clear_on_submit=True):
        coordenador = st.text_input("Nome do Coordenador", key=f"coordenador")
        email = st.text_input("E-mail do Coordenador", key=f"email")
        
        enviar = st.form_submit_button("Cadastrar Coordenador")

    if enviar:
        coordenador_value = st.session_state.get(f"coordenador", "")
        email_value = st.session_state.get(f"email", "")

        if not coordenador_value or not email_value:
            st.error("Por favor, preencha o nome do coordenador e o e-mail.")
            return

        if "@" not in email_value:
            st.error("Por favor, insira um e-mail válido.")
            return

        data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ok, err = registrar_coordenador(coordenador_value, email_value, data_cadastro)

        if not ok:
            st.error(f"Erro ao salvar no banco de dados: {err}")
            return

        try:
            sucesso, msg = enviar_email_coordenador(coordenador_value, email_value)
            if not sucesso:
                st.warning(f"E-mail não pôde ser preparado: {msg}")
            else:
                st.info("📧 E-mail preparado (janela do Outlook aberta).")
        except Exception as exc:
            st.warning(f"Erro ao preparar e-mail: {exc}")

        st.success("✅ Coordenador cadastrado com sucesso!")
        time.sleep(3)
        st.rerun()

    st.markdown("---")
    
    st.subheader("📧 Coordenadores Cadastrados")
    coordenadores = _get_coordenadores()
    
    if not coordenadores:
        st.info("Nenhum e-mail de coordenador cadastrado ainda.")
    else:
        st.write(pd.DataFrame({"E-mail": coordenadores}))
