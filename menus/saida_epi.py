# Em menus/saida_epi.py

import time
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

# FUNÇÃO AJUSTADA: Agora recebe e salva a assinatura_b64
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
                    assinatura TEXT -- NOVA COLUNA ADICIONADA
                )
            """))
            
            for item, tamanho, quantidade, status in itens_saida:
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
                    "status": status.strip(),
                    "efetivo": efetivo.strip(), 
                    "turno": turno.strip(), 
                    "cc": centro_de_custo.strip().upper(),
                    "item": item.strip().upper(), 
                    "tam": tamanho.strip().upper() if tamanho else "", 
                    "qtd": int(quantidade),
                    "ass": assinatura_b64 # SALVANDO A ASSINATURA DA HORA
                })
            conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)

# --- FUNÇÃO PRINCIPAL DA PÁGINA ---

def carregar():
    st.subheader("📦 Registro de Saída de EPI")

    # =======================================================
    # O MOTOR DO RESET MÁGICO
    # =======================================================
    if 'reset_saida' not in st.session_state:
        st.session_state.reset_saida = 0
        
    rs = st.session_state.reset_saida # Atalho para aplicar em todos os campos

    epi_names = listar_itens_por_categoria("EPI")
    coordenadores_emails = get_coordenadores()

    if not epi_names:
        st.warning("Nenhum EPI encontrado no 'Cadastro de Itens'. Por favor, cadastre os itens primeiro.")
        return

    num_itens = st.number_input(
        "Quantidade de tipos de EPIs para saída", min_value=1, max_value=10,
        key=f"saida_epi_num_itens_{rs}"
    )

    # --- Formulário de Saída ---
    with st.form("saida_epi_form", clear_on_submit=False):
        
        st.markdown("**Identificação do Colaborador**")
        col_nome, col_cpf = st.columns(2)
        with col_cpf:
            cpf_value = st.text_input("CPF (Apenas números)", max_chars=11, key=f"saida_epi_cpf_{rs}")
        with col_nome:
            colaborador_value = st.text_input("Nome Completo", key=f"saida_epi_colab_{rs}")
        st.markdown("---")
        
        coordenador = st.text_input("Coordenador", key=f"saida_epi_coordenador_{rs}")
        email_coordenador = st.selectbox("E-mail do Coordenador", options=[""] + coordenadores_emails, key=f"saida_epi_email_coordenador_{rs}")
        responsavel = st.selectbox("Responsável", ["", "ALMOXARIFE", "COORDENADOR", "JOVEM APRENDIZ"], key=f"saida_epi_responsavel_{rs}")
        turno = st.selectbox("Turno", ["", "ADM", "1° TURNO", "2° TURNO",], key=f"saida_epi_turno_{rs}")
        centro_de_custo = st.selectbox("Centro de Custo", ["", "RC", "3P"], key=f"saida_epi_centro_de_custo_{rs}")
        motivo = st.selectbox("Motivo da Saída", ["", "PERDA", "1° RETIRADA", "AVARIADO", "ESQUECEU O EPI", "DEVOLUÇÃO", "TROCA DE TAMANHO", "PERÍODO VENCIDO", "MANCHA"], key=f"saida_epi_motivo_{rs}")
        efetivo = st.selectbox("Efetivo", ["", "DHL", "AGÊNCIA"], key=f"saida_epi_efetivo_{rs}")

        st.markdown("---")
        for i in range(num_itens):
            # Mudamos para 4 colunas (Ajustei as larguras para caber tudo bem formatado)
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1.5]) 
            
            with col1:
                st.selectbox(f"EPI #{i+1}", [""] + epi_names, key=f"saida_epi_item_nome_{i}_{rs}", disabled=(not epi_names))
            with col2:
                st.text_input(f"Tamanho #{i+1}", placeholder="ÚNICO", key=f"saida_epi_item_tam_{i}_{rs}")
            with col3:
                st.number_input(f"Qtd #{i+1}", min_value=1, value=1, key=f"saida_epi_item_qtd_{i}_{rs}")
            with col4:
                # O novo campo de Status individual para CADA item!
                st.selectbox(f"Status #{i+1}", ["", "NOVO", "HIGIENIZADO"], key=f"saida_epi_item_status_{i}_{rs}")
        
        st.markdown("---")
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

        # O status geral foi removido, então usamos "MÚLTIPLOS" como fallback global 
        # (caso o seu banco/email ainda exija esse campo).
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

        # Validação da Assinatura
        if canvas_result.json_data is None or len(canvas_result.json_data.get("objects", [])) == 0:
            st.warning("⚠️ Por favor, colete a assinatura do colaborador antes de salvar.")
            st.stop() # Para a execução, mas preserva os campos!
            
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
        
        # Salvando no banco 
        ok, err = registrar_saida_epi(
            colaborador=colaborador_value, 
            cpf=cpf_value, 
            coordenador=coordenador_value,
            email_coordenador=email_value, 
            responsavel=responsavel_value, 
            motivo=motivo_value,
            status=status_value_global, # Enviando o fallback
            efetivo=efetivo_value, 
            turno=turno_value,
            centro_de_custo=centro_value, 
            itens_saida=itens_final,
            assinatura_b64=assinatura_final_b64 
        )

        if not ok: st.error(f"Erro ao salvar no banco de saídas: {err}"); st.stop()

        st.success("✅ Saída de EPI registrada com sucesso!")

        erros_estoque = []
        # ATUALIZADO: Agora desempacota 4 valores e usa o status específico do item
        for nome, tam, qtd, status_item in itens_final:
            sucesso_estoque, msg_estoque = atualizar_estoque(
                item_nome=nome, tamanho=tam, status=status_item,
                tipo="EPI", quantidade_delta=-int(qtd)
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
                status=status_value_global, # Enviando o fallback
                motivo=motivo_value,
                efetivo=efetivo_value,
                itens_saida=itens_final
            )
            if sucesso: st.info(f"📧 {msg}")
            else: st.warning(f"Saída salva, mas e-mail não enviado: {msg}")
        except Exception as exc:
            st.warning(f"Saída salva, mas ocorreu um erro ao preparar o e-mail: {exc}")

        # =======================================================
        # SINALIZA SUCESSO E RESETA TODO O FORMULÁRIO DE UMA VEZ
        # =======================================================
        st.session_state.reset_saida += 1
        time.sleep(3)
        st.rerun()