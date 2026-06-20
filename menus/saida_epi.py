import time
import json # <-- NOVO IMPORT ADICIONADO PARA OS PENDENTES
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from sqlalchemy import text
from utils.db_connection import connect_db

# Importações para a Assinatura
from streamlit_drawable_canvas import st_canvas
import base64
from io import BytesIO
from PIL import Image
import numpy as np

# Importações dos outros módulos de utilidades
from email_utils import enviar_email_saida_epi
from utils.estoque_db import atualizar_estoque
from utils.itens_db import listar_itens_por_categoria
from utils.coordenadores_db import get_coordenadores

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

# ====================================================================
# FUNÇÃO 1: SALVA DIRETO NA TABELA OFICIAL (Para Almoxarife / Admin)
# ====================================================================
def registrar_saida_epi(colaborador, cpf, coordenador, email_coordenador, responsavel, motivo, status, efetivo, turno, centro_de_custo, itens_saida, assinatura_b64):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
            data_atual_obj = datetime.now(fuso_horario_brasilia)
            data_str = data_atual_obj.strftime("%Y-%m-%d %H:%M:%S")
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS saida_epis (
                    id SERIAL PRIMARY KEY,
                    data TEXT,
                    colaborador TEXT,
                    cpf INTEGER,
                    coordenador TEXT,
                    email_coordenador TEXT,
                    responsavel TEXT,
                    motivo TEXT,
                    status TEXT,
                    efetivo TEXT,
                    turno TEXT,
                    centro_de_custo TEXT,
                    item TEXT,
                    tamanho TEXT,
                    quantidade INTEGER,
                    assinatura TEXT
                )
            """))
            
            for item, tamanho, quantidade, status_item in itens_saida:
                if not str(item).strip(): continue
                
                query = text("""
                    INSERT INTO saida_epis 
                    (data, colaborador, cpf, coordenador, email_coordenador, responsavel, motivo, status, efetivo, turno, centro_de_custo, item, tamanho, quantidade, assinatura)
                    VALUES (:data, :colab, :cpf, :coord, :email, :resp, :motivo, :status, :efetivo, :turno, :cc, :item, :tam, :qtd, :ass)
                """)
                conn.execute(query, {
                    "data": data_str, 
                    "colab": colaborador.strip().upper(), 
                    "cpf": cpf.strip(),
                    "coord": coordenador.strip().upper(), 
                    "email": email_coordenador.strip(),
                    "resp": responsavel.strip().upper(), 
                    "motivo": motivo.strip(), 
                    "status": status_item.strip(), # Ajustado para o status individual
                    "efetivo": efetivo.strip(), 
                    "turno": turno.strip(), 
                    "cc": centro_de_custo.strip().upper(),
                    "item": item.strip().upper(), 
                    "tam": tamanho.strip().upper() if tamanho else "", 
                    "qtd": int(quantidade),
                    "ass": assinatura_b64
                })
            conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)


# ====================================================================
# FUNÇÃO 2: SALVA NA QUARENTENA (Para Visitantes)
# ====================================================================
def registrar_saida_epi_pendente(colaborador, cpf, coordenador, email_coordenador, responsavel, motivo, status_global, efetivo, turno, centro_de_custo, itens_saida, assinatura_b64):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
            data_atual_obj = datetime.now(fuso_horario_brasilia)
            data_str = data_atual_obj.strftime("%Y-%m-%d %H:%M:%S")
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pendentes_saida_epis (
                    id SERIAL PRIMARY KEY,
                    data TEXT,
                    colaborador TEXT,
                    cpf TEXT,
                    coordenador TEXT,
                    email_coordenador TEXT,
                    responsavel TEXT,
                    motivo TEXT,
                    status_global TEXT,
                    efetivo TEXT,
                    turno TEXT,
                    centro_de_custo TEXT,
                    itens_json TEXT, 
                    assinatura TEXT
                )
            """))
            
            itens_str = json.dumps(itens_saida)
            
            query = text("""
                INSERT INTO pendentes_saida_epis 
                (data, colaborador, cpf, coordenador, email_coordenador, responsavel, motivo, status_global, efetivo, turno, centro_de_custo, itens_json, assinatura)
                VALUES (:data, :colab, :cpf, :coord, :email, :resp, :motivo, :status, :efetivo, :turno, :cc, :itens, :ass)
            """)
            
            conn.execute(query, {
                "data": data_str, 
                "colab": colaborador.strip().upper(), 
                "cpf": str(cpf).strip(),
                "coord": coordenador.strip().upper(), 
                "email": email_coordenador.strip(),
                "resp": responsavel.strip().upper(), 
                "motivo": motivo.strip(), 
                "status": status_global.strip() if status_global else "",
                "efetivo": efetivo.strip(), 
                "turno": turno.strip(), 
                "cc": centro_de_custo.strip().upper(),
                "itens": itens_str, 
                "ass": assinatura_b64
            })
            conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)


# --- FUNÇÃO PRINCIPAL DA PÁGINA ---

def carregar():
    st.subheader("📦 Registro de Saída de EPI")

    if 'reset_saida' not in st.session_state:
        st.session_state.reset_saida = 0
        
    rs = st.session_state.reset_saida

    epi_names = listar_itens_por_categoria("EPI")
    coordenadores_emails = get_coordenadores()

    if not epi_names:
        st.warning("Nenhum EPI encontrado no 'Cadastro de Itens'. Por favor, cadastre os itens primeiro.")
        return

    num_itens = st.number_input(
        "Quantidade de tipos de EPIs para saída", min_value=1, max_value=10,
        key=f"saida_epi_num_itens_{rs}"
    )

    with st.form("saida_epi_form", clear_on_submit=False):
        perfil_usuario = st.session_state.get("user_role", "visitante")
        
        st.markdown("**Identificação do Colaborador**")
        col_nome, col_cpf = st.columns(2)
        with col_cpf:
            cpf_value = st.text_input("CPF (Apenas números)", max_chars=11, key=f"saida_epi_cpf_{rs}")
        with col_nome:
            colaborador_value = st.text_input("Nome Completo", key=f"saida_epi_colab_{rs}")
        st.markdown("---")
        
        coordenador = st.text_input("Coordenador", key=f"saida_epi_coordenador_{rs}")
        email_coordenador = st.selectbox("E-mail do Coordenador", options=[""] + coordenadores_emails, key=f"saida_epi_email_coordenador_{rs}")

        # 2. Define a lista de opções com base no perfil
        if perfil_usuario == "visitante":
            opcoes_responsavel = ["COORDENADOR"] # Bloqueia apenas em Coordenador
        else:
            opcoes_responsavel = ["", "ALMOXARIFE", "COORDENADOR", "JOVEM APRENDIZ"]
        responsavel = st.selectbox("Responsável", opcoes_responsavel, key=f"saida_epi_responsavel_{rs}")

        if perfil_usuario == "visitante":
            opcoes_turno = ["", "1° TURNO", "2° TURNO"] # Bloqueia apenas em ADM
        else:
            opcoes_turno = ["", "ADM", "1° TURNO", "2° TURNO"]
        turno = st.selectbox("Turno", opcoes_turno, key=f"saida_epi_turno_{rs}")

        centro_de_custo = st.selectbox("Centro de Custo", ["", "RC", "3P"], key=f"saida_epi_centro_de_custo_{rs}")

        if perfil_usuario == "visitante":
            opcoes_motivo = ["", "PERDA", "AVARIADO"] # Bloqueia apenas em 1° RETIRADA
        else:
            opcoes_motivo = ["", "PERDA", "1° RETIRADA", "AVARIADO", "ESQUECEU O EPI", "DEVOLUÇÃO", "TROCA DE TAMANHO", "PERÍODO VENCIDO", "MANCHA"]
        motivo = st.selectbox("Motivo da Saída", opcoes_motivo, key=f"saida_epi_motivo_{rs}")

        efetivo = st.selectbox("Efetivo", ["", "DHL", "AGÊNCIA"], key=f"saida_epi_efetivo_{rs}")


        # 1. Define as listas de EPIs e Status com base no perfil
        if perfil_usuario == "visitante":
            opcoes_epi = ["LUVA SOFT PRO 540 - CA 28793"] # Trava no EPI específico
            opcoes_status = ["NOVO"]                      # Trava o status
        else:
            opcoes_epi = [""] + epi_names                 # Lista completa
            opcoes_status = ["", "NOVO", "HIGIENIZADO"]   # Status completos

        st.markdown("---")
        for i in range(num_itens):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1.5]) 
            with col1:
                st.selectbox(f"EPI #{i+1}", opcoes_epi, key=f"saida_epi_item_nome_{i}_{rs}", disabled=(not opcoes_epi))
            with col2:
                st.text_input(f"Tamanho #{i+1}", placeholder="ÚNICO", key=f"saida_epi_item_tam_{i}_{rs}")
            with col3:
                st.number_input(f"Qtd #{i+1}", min_value=1, value=1, key=f"saida_epi_item_qtd_{i}_{rs}")
            with col4:
                st.selectbox(f"Status #{i+1}", opcoes_status, key=f"saida_epi_item_status_{i}_{rs}")
        
        st.markdown("---")
        st.markdown("### ✍️ Assinatura de Confirmação")
        st.caption("O colaborador deve assinar abaixo para validar a retirada na data de hoje:")
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",  
            stroke_width=3,                       
            stroke_color="#000000",               
            background_color="#eeeeee",           
            height=150,                           
            width=400,                            
            drawing_mode="freedraw",
            key=f"canvas_saida_{rs}", 
        )
        
        enviar = st.form_submit_button("Registrar Saída de EPI", type="primary")

    if enviar:
        cpf_value = st.session_state.get(f"saida_epi_cpf_{rs}", "")
        colaborador_value = st.session_state.get(f"saida_epi_colab_{rs}", "")
        coordenador_value = st.session_state.get(f"saida_epi_coordenador_{rs}", "")
        email_value = st.session_state.get(f"saida_epi_email_coordenador_{rs}", "")
        responsavel_value = st.session_state.get(f"saida_epi_responsavel_{rs}", "").strip().upper()
        motivo_value = st.session_state.get(f"saida_epi_motivo_{rs}", "")
        efetivo_value = st.session_state.get(f"saida_epi_efetivo_{rs}", "")
        turno_value = st.session_state.get(f"saida_epi_turno_{rs}", "")
        centro_value = st.session_state.get(f"saida_epi_centro_de_custo_{rs}", "")

        status_value_global = "MÚLTIPLOS" 
        
        if not cpf_value: 
            st.error("O campo 'CPF' é obrigatório.")
            st.stop()
        elif not cpf_value.isdigit() or len(cpf_value) != 11:
            st.error("⚠️ O CPF deve conter exatamente 11 números (sem pontos ou traços).")
            st.stop()
        if not responsavel_value: st.error("O campo 'Responsável' é obrigatório."); st.stop()
        if not centro_value: st.error("O campo 'Centro de Custo' é obrigatório."); st.stop()
        if not email_value or email_value == "Nenhum e-mail cadastrado": st.error("Selecione um e-mail válido."); st.stop()
        if not efetivo_value: st.error("O campo 'Efetivo' é obrigatório."); st.stop()
        if not coordenador_value: st.error("O campo 'Coordenador' é obrigatório."); st.stop()
        if not colaborador_value: st.error("O campo 'Nome Completo' é obrigatório."); st.stop()

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
        num_itens_registrados = st.session_state.get(f"saida_epi_num_itens_{rs}", 1)
        for i in range(num_itens_registrados):
            escolha = st.session_state.get(f"saida_epi_item_nome_{i}_{rs}", "")
            tam = st.session_state.get(f"saida_epi_item_tam_{i}_{rs}", "")
            qtd = st.session_state.get(f"saida_epi_item_qtd_{i}_{rs}", 1)
            status_item = st.session_state.get(f"saida_epi_item_status_{i}_{rs}", "")
            
            if escolha:
                if not status_item:
                    st.error(f"Selecione o status para o item: {escolha}")
                    st.stop()
                itens_final.append((escolha, tam, int(qtd), status_item))

        if not itens_final: st.error("Preencha pelo menos um EPI."); st.stop()
        
        # =======================================================
        # A MÁGICA ACONTECE AQUI: BIFURCAÇÃO POR PERFIL
        # =======================================================
        
        # Recupera o perfil do utilizador (se não existir, assume 'visitante' por segurança)
        perfil_usuario = st.session_state.get("user_role", "visitante") 

        if perfil_usuario in ["admin", "almoxarife"]:
            # ---------------------------------------------------
            # ROTA 1: ALMOXARIFE / ADMIN (Salva direto e dá baixa)
            # ---------------------------------------------------
            ok, err = registrar_saida_epi(
                colaborador=colaborador_value, 
                cpf=cpf_value, 
                coordenador=coordenador_value,
                email_coordenador=email_value, 
                responsavel=responsavel_value, 
                motivo=motivo_value,
                status=status_value_global, 
                efetivo=efetivo_value, 
                turno=turno_value,
                centro_de_custo=centro_value, 
                itens_saida=itens_final,
                assinatura_b64=assinatura_final_b64 
            )

            if not ok: st.error(f"Erro ao salvar no banco de saídas: {err}"); st.stop()

            st.success("✅ Saída de EPI registrada com sucesso!")

            erros_estoque = []
            for nome, tam, qtd, status_item in itens_final:
                sucesso_estoque, msg_estoque = atualizar_estoque(
                    item_nome=nome, 
                    tamanho=tam, 
                    status=status_item,
                    tipo="EPI", 
                    quantidade_delta=-int(qtd)
                )
                if not sucesso_estoque:
                    erros_estoque.append(f"Item '{nome}' ({status_item}): {msg_estoque}")
            
            if erros_estoque:
                st.warning("Saída registrada, mas com erros na baixa de estoque:\n" + "\n".join(erros_estoque))

            try:
                sucesso, msg = enviar_email_saida_epi(
                    cpf=cpf_value, 
                    coordenador=coordenador_value, 
                    colaborador=colaborador_value,
                    responsavel=responsavel_value, 
                    email_coordenador=email_value, 
                    turno=turno_value, 
                    centro_de_custo=centro_value, 
                    status=status_value_global, 
                    motivo=motivo_value,
                    efetivo=efetivo_value, 
                    itens_saida=itens_final
                )
                if sucesso: st.info(f"📧 {msg}")
                else: st.warning(f"Saída salva, mas e-mail não enviado: {msg}")
            except Exception as exc:
                st.warning(f"Saída salva, mas ocorreu um erro ao preparar o e-mail: {exc}")

        else:
            # ---------------------------------------------------
            # ROTA 2: VISITANTE (Vai para Quarentena / Pendentes)
            # ---------------------------------------------------
            ok, err = registrar_saida_epi_pendente(
                colaborador=colaborador_value, 
                cpf=cpf_value, 
                coordenador=coordenador_value,
                email_coordenador=email_value, 
                responsavel=responsavel_value, 
                motivo=motivo_value,
                status_global=status_value_global, 
                efetivo=efetivo_value, 
                turno=turno_value,
                centro_de_custo=centro_value, 
                itens_saida=itens_final,
                assinatura_b64=assinatura_final_b64 
            )

            if not ok: st.error(f"Erro ao enviar solicitação: {err}"); st.stop()

            st.success("⏳ Solicitação de Saída enviada com sucesso! Aguardando aprovação do Almoxarifado.")
            st.info("O estoque e o relatório só serão atualizados após a aprovação.")

        # =======================================================
        # SINALIZA SUCESSO E RESETA TODO O FORMULÁRIO DE UMA VEZ
        # =======================================================
        st.session_state.reset_saida += 1
        time.sleep(4)
        st.rerun()