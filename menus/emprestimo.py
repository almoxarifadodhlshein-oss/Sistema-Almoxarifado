# menus/emprestimo.py
import os
import time
import streamlit as st
import pandas as pd
import pytz
from sqlalchemy import text
from utils.db_connection import connect_db
from datetime import datetime
from email_utils import enviar_email_emprestimo
from utils.estoque_db import atualizar_estoque
from utils.itens_db import listar_itens_por_categoria


# Função para ler os e-mails cadastrados
def _get_coordenadores():
    engine = connect_db()
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text("SELECT email FROM coordenadores ORDER BY email"), conn)
        return df['email'].tolist() if not df.empty else ["Nenhum e-mail cadastrado"]
    except Exception:
        return ["Nenhum e-mail cadastrado"]

try:
    from utils.itens_db import init_items_db, listar_itens
    init_items_db()
except Exception:
    def listar_itens(cat): return []

'''DB_DIR = os.path.join(os.getcwd(), "banco de dados")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "emprestimo.db")'''


def registrar_emprestimo(cpf, coordenador, colaborador, responsavel, email_coordenador, turno, centro_de_custo, status_item, itens):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
            data_atual_obj = datetime.now(fuso_horario_brasilia)
            data_str = data_atual_obj.strftime("%Y-%m-%d %H:%M:%S")

            # Sintaxe do PostgreSQL com SERIAL PRIMARY KEY
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS emprestimos (
                    id SERIAL PRIMARY KEY, data TEXT, cpf TEXT,
                    coordenador TEXT, colaborador TEXT, responsavel TEXT, turno TEXT,
                    centro_de_custo TEXT, status_item TEXT, status_emprestimo TEXT, 
                    item TEXT, quantidade INTEGER, tamanho TEXT, email_coordenador TEXT
                )
            """))
            
            status_emprestimo = "PENDENTE"
            for nome, tam, qtd in itens:
                if not str(nome).strip(): continue
                
                query = text("""
                    INSERT INTO emprestimos
                    (data, cpf, coordenador, colaborador, responsavel, turno, centro_de_custo, status_item, status_emprestimo, item, quantidade, tamanho, email_coordenador)
                    VALUES (:data, :cpf, :coord, :colab, :resp, :turno, :cc, :stat_item, :stat_emp, :item, :qtd, :tam, :email)
                """)
                conn.execute(query, {
                    "data": data_str, "cpf": cpf.strip(), "coord": coordenador.strip().upper(),
                    "colab": colaborador.strip().upper(), "resp": responsavel.strip(), "turno": turno.strip(),
                    "cc": centro_de_custo.strip().upper(), "stat_item": status_item.strip(),
                    "stat_emp": status_emprestimo, "item": nome.strip().upper(), "qtd": int(qtd),
                    "tam": tam.strip().upper() if tam else "", "email": email_coordenador.strip()
                })
            conn.commit()
        return True, None
    except Exception as exc:
        return False, str(exc)

def _safe_rerun():
    st.rerun()


def _safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()


def carregar():
    st.subheader("➡️ Registro de Empréstimo")

    # A busca de dados agora fica fora do formulário
    epi_names = listar_itens_por_categoria("EPI")
    coordenadores_emails = _get_coordenadores()

    if not epi_names:
        st.warning("Nenhum EPI encontrado no 'Cadastro de Itens'. Por favor, cadastre os itens primeiro.")

    # O widget para número de itens também fica fora
    num_itens = st.number_input(
        "Quantidade de tipos para empréstimo", min_value=1, max_value=10,
        key="emprestimo_num_itens"
    )

    # Usamos uma chave estática para o formulário
    with st.form("emprestimo_form", clear_on_submit=True):
        # Campos gerais do formulário com chaves estáticas e únicas
        cpf = st.text_input("CPF", key="emprestimo_cpf")
        colaborador = st.text_input("Colaborador", key="emprestimo_colaborador")
        coordenador = st.text_input("Coordenador", key="emprestimo_coordenador")
        email_coordenador = st.selectbox("E-mail do Coordenador", options=[""] + coordenadores_emails, key="emprestimo_email_coordenador")
        responsavel = st.selectbox("Responsável", ["AMANDA MESSIAS", "ANDREZZA SABINO", "PAMELA SIMEÃO", "RAFAEL CRISTOVÃO", "SUELI BARBOSA", "ORLANDO ALVES", "JOVEM APRENDIZ"], key="emprestimo_responsavel")
        turno = st.selectbox("Turno", ["ADM", "1° TURNO", "2° TURNO", "3° TURNO"], key="emprestimo_turno")
        centro_de_custo = st.selectbox("Centro de Custo", ["", "RC", "3P"], key="emprestimo_centro_de_custo")
        status_item = st.selectbox("Status dos Itens Emprestados", ["NOVO", "HIGIENIZADO"], key="emprestimo_status_item")

        st.markdown("---")
        for i in range(num_itens):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.selectbox(f"EPI #{i+1}", [""] + epi_names, key=f"emprestimo_item_nome_{i}", disabled=(not epi_names))
            with col2:
                st.text_input(f"Tamanho #{i+1}", placeholder="ÚNICO", key=f"emprestimo_item_tam_{i}")
            with col3:
                st.number_input(f"Quantidade #{i+1}", min_value=1, value=1, key=f"emprestimo_item_qtd_{i}")

        enviar = st.form_submit_button("Registrar Empréstimo")

    # A lógica de envio fica FORA do 'with st.form'
    if enviar:
        # Coleta de dados do formulário
        cpf_value = st.session_state.get("emprestimo_cpf", "")
        coordenador_value = st.session_state.get("emprestimo_coordenador", "")
        colaborador_value = st.session_state.get("emprestimo_colaborador", "")
        responsavel_value = st.session_state.get("emprestimo_responsavel", "")
        email_value = st.session_state.get("emprestimo_email_coordenador", "")
        turno_value = st.session_state.get("emprestimo_turno", "")
        status_item_value = st.session_state.get("emprestimo_status_item", "")
        centro_value = st.session_state.get("emprestimo_centro_de_custo", "")

        itens_final = []
        num_itens_registrados = st.session_state.get("emprestimo_num_itens", 1)
        for i in range(num_itens_registrados):
            escolha = st.session_state.get(f"emprestimo_item_nome_{i}", "")
            tam = st.session_state.get(f"emprestimo_item_tam_{i}", "")
            qtd = st.session_state.get(f"emprestimo_item_qtd_{i}", 1)
            if escolha:
                itens_final.append((escolha, tam, qtd))
        
        # Validações
        if not centro_value: st.error("O campo 'Centro de Custo' é obrigatório."); return
        if not itens_final: st.error("Preencha pelo menos um item."); return
        if not email_value or email_value == "Nenhum e-mail cadastrado": st.error("Selecione um e-mail válido."); return
        if not cpf_value: st.error("Ocampo 'CPF' é obrigatório."); return
        if not colaborador_value: st.error("O campo 'Colaborador' é obrigatório."); return
        if not status_item_value: st.error("O campo 'Status' é obrigatório."); return
        if not coordenador_value: st.error("O campo 'Coordenador' é obrigatório."); return
        
        # Registro no banco de dados de empréstimos
        ok, err = registrar_emprestimo(
            cpf=cpf_value, 
            coordenador=coordenador_value, 
            colaborador=colaborador_value,
            responsavel=responsavel_value, 
            email_coordenador=email_value,
            turno=turno_value, 
            centro_de_custo=centro_value, 
            status_item=status_item_value, 
            itens=itens_final
        )

        if not ok: st.error(f"Erro ao salvar no banco: {err}"); return
        
        st.success("✅ Empréstimo registrado com sucesso!")

        # Baixa no estoque
        erros_estoque = []
        for nome, tam, qtd in itens_final:
            sucesso_estoque, msg_estoque = atualizar_estoque(
                item_nome=nome, tamanho=tam, status=status_item_value,
                tipo="EPI", quantidade_delta=-int(qtd)
            )
            if not sucesso_estoque:
                erros_estoque.append(f"Item '{nome}' ({status_item_value}): {msg_estoque}")
        
        if erros_estoque:
            st.warning("O empréstimo foi registrado, mas com erros na baixa de estoque:\n" + "\n".join(erros_estoque))

        # Envio de e-mail
        try:
            sucesso, msg = enviar_email_emprestimo(
                cpf=cpf_value, 
                coordenador=coordenador_value, 
                colaborador=colaborador_value,
                responsavel=responsavel_value, 
                email_coordenador=email_value,
                turno=turno_value, 
                status_item=status_item_value,
                centro_de_custo=centro_value, 
                itens=itens_final
            )
            if sucesso: st.info(f"📧 {msg}")
            else: st.warning(f"Empréstimo salvo, mas e-mail não enviado: {msg}")
        except Exception as exc:
            st.warning(f"Empréstimo salvo, mas ocorreu um erro ao preparar o e-mail: {exc}")

        time.sleep(5)

        st.rerun()











