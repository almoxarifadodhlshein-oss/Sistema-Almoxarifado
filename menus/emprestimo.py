# menus/emprestimo.py
import os
import time
import streamlit as st
import pandas as pd
import pytz
import json
from sqlalchemy import text
from utils.db_connection import connect_db
from datetime import datetime
from email_utils import enviar_email_emprestimo
from utils.estoque_db import atualizar_estoque
from utils.itens_db import listar_itens_por_categoria
from streamlit_drawable_canvas import st_canvas
import base64
from io import BytesIO
from PIL import Image
import numpy as np
# 1. NOVA IMPORTAÇÃO: Traz a lista da base mestre
#from utils.colaboradores_db import get_lista_colaboradores


# Função para ler os e-mails cadastrados
def get_coordenadores():
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


def registrar_emprestimo(cpf, coordenador, colaborador, responsavel, email_coordenador, turno, centro_de_custo, status_item, itens, assinatura_b64):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
            data_atual_obj = datetime.now(fuso_horario_brasilia)
            data_str = data_atual_obj.strftime("%Y-%m-%d %H:%M:%S")

            # Sintaxe do PostgreSQL com SERIAL PRIMARY KEY
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS emprestimos (
                    id SERIAL PRIMARY KEY, 
                    data TEXT, cpf TEXT,
                    coordenador TEXT, 
                    colaborador TEXT,
                    responsavel TEXT, 
                    turno TEXT,
                    centro_de_custo TEXT, 
                    status_item TEXT, 
                    status_emprestimo TEXT, 
                    item TEXT, 
                    quantidade INTEGER, 
                    tamanho TEXT, 
                    email_coordenador TEXT, 
                    assinatura TEXT
                )
            """))
            
            status_emprestimo = "PENDENTE"
            for nome, tam, qtd, status_item in itens:
                if not str(nome).strip(): continue
                
                query = text("""
                    INSERT INTO emprestimos
                    (data, cpf, coordenador, colaborador, responsavel, turno, centro_de_custo, status_item, status_emprestimo, item, quantidade, tamanho, email_coordenador, assinatura)
                    VALUES (:data, :cpf, :coord, :colab, :resp, :turno, :cc, :stat_item, :stat_emp, :item, :qtd, :tam, :email, :ass)
                """)
                conn.execute(query, {
                    "data": data_str, 
                    "cpf": cpf.strip(), 
                    "coord": coordenador.strip().upper(),
                    "colab": colaborador.strip().upper(), 
                    "resp": responsavel.strip().upper(), 
                    "turno": turno.strip(),
                    "cc": centro_de_custo.strip().upper(), 
                    "stat_item": status_item.strip(),
                    "stat_emp": status_emprestimo, 
                    "item": nome.strip().upper(), 
                    "qtd": int(qtd),
                    "tam": tam.strip().upper() if tam else "", 
                    "email": email_coordenador.strip(),
                    "ass": assinatura_b64
                })
            conn.commit()
        return True, None
    except Exception as exc:
        return False, str(exc)

def registrar_emprestimo_pendente(cpf, coordenador, colaborador, responsavel, email_coordenador, turno, centro_de_custo, status_global, itens_saida, assinatura_b64):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
            data_str = datetime.now(fuso_horario_brasilia).strftime("%Y-%m-%d %H:%M:%S")
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pendentes_emprestimos (
                    id SERIAL PRIMARY KEY, 
                    data TEXT, cpf TEXT, 
                    colaborador TEXT,
                    coordenador TEXT, 
                    email_coordenador TEXT, 
                    responsavel TEXT,
                    turno TEXT, 
                    centro_de_custo TEXT, 
                    status_global TEXT, 
                    itens_json TEXT, 
                    assinatura TEXT
                )
            """))
            
            itens_str = json.dumps(itens_saida)
            
            query = text("""
                INSERT INTO pendentes_emprestimos 
                (data, cpf, colaborador, coordenador, email_coordenador, responsavel, turno, centro_de_custo, status_global, itens_json, assinatura)
                VALUES (:data, :cpf, :colab, :coord, :email, :resp, :turno, :cc, :status, :itens, :ass)
            """)
            conn.execute(query, {
                "data": data_str, "cpf": str(cpf).strip(), 
                "colab": colaborador.strip().upper(),
                "coord": coordenador.strip().upper(), 
                "email": email_coordenador.strip(),
                "resp": responsavel.strip().upper(), 
                "turno": turno.strip(),
                "cc": centro_de_custo.strip().upper(), 
                "status": status_global.strip() if status_global else "",
                "itens": itens_str, "ass": assinatura_b64
            })
            conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)


def _safe_rerun():
    st.rerun()


def _safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()


def carregar():
    st.subheader("➡️ Registro de Empréstimo")

    # =======================================================
    # O MOTOR DO RESET MÁGICO
    # =======================================================
    if 'reset_emprestimo' not in st.session_state:
        st.session_state.reset_emprestimo = 0
        
    rs = st.session_state.reset_emprestimo # Atalho para aplicar em todos os campos

    epi_names = listar_itens_por_categoria("EPI")
    coordenadores_emails = get_coordenadores()

    if not epi_names:
        st.warning("Nenhum EPI encontrado no 'Cadastro de Itens'. Por favor, cadastre os itens primeiro.")
        st.stop() # Usamos st.stop() no lugar de return

    num_itens = st.number_input(
        "Quantidade de tipos para empréstimo", min_value=1, max_value=10,
        key=f"emprestimo_num_itens_{rs}"
    )

    # --- Formulário de Empréstimo ---
    with st.form("emprestimo_form", clear_on_submit=False):
        
        st.markdown("**Identificação do Colaborador**")

        col_nome, col_cpf = st.columns(2)
        with col_cpf:
            cpf_value = st.text_input("CPF (Apenas números)", max_chars=11, key=f"emprestimo_cpf_{rs}")
        with col_nome:
            colaborador_value = st.text_input("Nome Completo", key=f"emprestimo_colaborador_{rs}")
        st.markdown("---")

        coordenador = st.text_input("Coordenador", key=f"emprestimo_coordenador_{rs}")
        email_coordenador = st.selectbox("E-mail do Coordenador", options=[""] + coordenadores_emails, key=f"emprestimo_email_coordenador_{rs}")
        responsavel = st.selectbox("Responsável", ["", "ALMOXARIFE", "COORDENADOR", "JOVEM APRENDIZ"], key=f"emprestimo_responsavel_{rs}")
        turno = st.selectbox("Turno", ["", "ADM", "1° TURNO", "2° TURNO"], key=f"emprestimo_turno_{rs}")
        centro_de_custo = st.selectbox("Centro de Custo", ["", "RC", "3P"], key=f"emprestimo_centro_de_custo_{rs}")
        
        # O STATUS GERAL FOI REMOVIDO DAQUI

        st.markdown("---")
        for i in range(num_itens):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1.5]) 
            
            with col1:
                # CORREÇÃO: As chaves agora são 'emprestimo_...' em vez de 'saida_epi_...'
                st.selectbox(f"EPI #{i+1}", [""] + epi_names, key=f"emprestimo_item_nome_{i}_{rs}", disabled=(not epi_names))
            with col2:
                st.text_input(f"Tamanho #{i+1}", placeholder="ÚNICO", key=f"emprestimo_item_tam_{i}_{rs}")
            with col3:
                st.number_input(f"Qtd #{i+1}", min_value=1, value=1, key=f"emprestimo_item_qtd_{i}_{rs}")
            with col4:
                # Status individual devidamente nomeado!
                st.selectbox(f"Status #{i+1}", ["", "NOVO", "HIGIENIZADO"], key=f"emprestimo_item_status_{i}_{rs}")

        st.markdown("### ✍️ Assinatura de Confirmação")
        st.caption("O colaborador deve assinar abaixo para validar a retirada na data de hoje:")
        
        # O Quadro de desenho
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",  
            stroke_width=3,                       
            stroke_color="#000000",               
            background_color="#eeeeee",           
            height=150,                           
            width=400,                            
            drawing_mode="freedraw",
            key=f"canvas_emprestimo_{rs}", 
        )

        enviar = st.form_submit_button("Registrar Empréstimo", type="primary")

    if enviar:
        cpf_value = st.session_state.get(f"emprestimo_cpf_{rs}", "")
        coordenador_value = st.session_state.get(f"emprestimo_coordenador_{rs}", "")
        colaborador_value = st.session_state.get(f"emprestimo_colaborador_{rs}", "")
        responsavel_value = st.session_state.get(f"emprestimo_responsavel_{rs}", "")
        email_value = st.session_state.get(f"emprestimo_email_coordenador_{rs}", "")
        turno_value = st.session_state.get(f"emprestimo_turno_{rs}", "")
        centro_value = st.session_state.get(f"emprestimo_centro_de_custo_{rs}", "")

        # Fallback para o BD/Email
        status_value_global = "MÚLTIPLOS"

        if not cpf_value: 
            st.error("O campo 'CPF' é obrigatório.")
            st.stop()
        elif not cpf_value.isdigit() or len(cpf_value) != 11:
            st.error("⚠️ O CPF deve conter exatamente 11 números (sem pontos ou traços).")
            st.stop()
        if not centro_value: st.error("O campo 'Centro de Custo' é obrigatório."); st.stop()
        if not email_value or email_value == "Nenhum e-mail cadastrado": st.error("Selecione um e-mail válido."); st.stop()
        if not colaborador_value: st.error("O campo 'Colaborador' é obrigatório."); st.stop()
        if not coordenador_value: st.error("O campo 'Coordenador' é obrigatório."); st.stop() 

        # Validação da Assinatura
        if canvas_result.json_data is None or len(canvas_result.json_data.get("objects", [])) == 0:
            st.warning("⚠️ Por favor, colete a assinatura do colaborador antes de salvar.")
            st.stop() 
            
        img_data = canvas_result.image_data
        img = Image.fromarray(img_data.astype('uint8'), 'RGBA')
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        assinatura_final_b64 = f"data:image/png;base64,{img_str}"

        itens_final = []
        num_itens_registrados = st.session_state.get(f"emprestimo_num_itens_{rs}", 1)
        for i in range(num_itens_registrados):
            escolha = st.session_state.get(f"emprestimo_item_nome_{i}_{rs}", "")
            tam = st.session_state.get(f"emprestimo_item_tam_{i}_{rs}", "")
            qtd = st.session_state.get(f"emprestimo_item_qtd_{i}_{rs}", 1)
            status = st.session_state.get(f"emprestimo_item_status_{i}_{rs}", "")
            
            if escolha:
                if not status:
                    st.error(f"Selecione o status para o item: {escolha}")
                    st.stop()
                # Agora anexamos 4 valores na lista
                itens_final.append((escolha, tam, int(qtd), status))

        if not itens_final: st.error("Preencha pelo menos um item."); st.stop()

        perfil_usuario = st.session_state.get("user_role", "visitante")


        if perfil_usuario in ["admin", "almoxarife"]:
            ok, err = registrar_emprestimo(
                cpf=cpf_value, 
                coordenador=coordenador_value, 
                colaborador=colaborador_value,
                responsavel=responsavel_value, 
                email_coordenador=email_value,
                turno=turno_value, 
                centro_de_custo=centro_value, 
                status_item=status_value_global, # Enviando fallback
                itens=itens_final,
                assinatura_b64=assinatura_final_b64
            )

            if not ok: st.error(f"Erro ao salvar no banco: {err}"); st.stop()

            st.success("✅ Empréstimo registrado com sucesso!")

            # Baixa no estoque
            erros_estoque = []
            # CORREÇÃO: Desempacotar 4 variáveis e usar o status INDIVIDUAL (status_item)
            for nome, tam, qtd, status_item in itens_final:
                sucesso_estoque, msg_estoque = atualizar_estoque(
                    item_nome=nome, tamanho=tam, status=status_item,
                    tipo="EPI", quantidade_delta=-int(qtd)
                )
                if not sucesso_estoque:
                    erros_estoque.append(f"Item '{nome}' ({status_item}): {msg_estoque}")
        
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
                    status_item=status_value_global, # Enviando fallback
                    centro_de_custo=centro_value, 
                    itens=itens_final
                )
                if sucesso: st.info(f"📧 {msg}")
                else: st.warning(f"Empréstimo salvo, mas e-mail não enviado: {msg}")
            except Exception as exc:
                st.warning(f"Empréstimo salvo, mas ocorreu um erro ao preparar o e-mail: {exc}")
        else:
            # ---------------------------------------------------
            # ROTA 2: VISITANTE (Vai para Quarentena / Pendentes)
            # ---------------------------------------------------
            ok, err = registrar_emprestimo_pendente(
                colaborador=colaborador_value, 
                cpf=cpf_value, 
                coordenador=coordenador_value,
                email_coordenador=email_value, 
                responsavel=responsavel_value, 
                status_global=status_value_global, 
                turno=turno_value,
                centro_de_custo=centro_value, 
                itens_saida=itens_final,
                assinatura_b64=assinatura_final_b64 
            )

            if not ok: st.error(f"Erro ao enviar solicitação: {err}"); st.stop()

            st.success("⏳ Solicitação de Saída enviada com sucesso! Aguardando aprovação do Almoxarifado.")
            st.info("O estoque e o relatório só serão atualizados após a aprovação.")


        st.session_state.reset_emprestimo += 1
        time.sleep(3)
        st.rerun()




