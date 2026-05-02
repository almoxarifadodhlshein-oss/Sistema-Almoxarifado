# Em menus/devolucao.py (VERSÃO COMPLETA E FUNCIONAL)
import os
import time
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import base64
from io import BytesIO
from PIL import Image
import numpy as np
# 1. NOVAS IMPORTAÇÕES NECESSÁRIAS
from sqlalchemy import text
from utils.db_connection import connect_db
from streamlit_drawable_canvas import st_canvas
# Importações dos outros módulos de utilidades
from email_utils import enviar_email_devolucao
from utils.estoque_db import atualizar_estoque
from utils.itens_db import listar_itens_por_categoria
# 1. NOVA IMPORTAÇÃO: Traz a lista da base mestre
#from utils.colaboradores_db import get_lista_colaboradores

# --- FUNÇÕES DE AJUDA ADAPTADAS PARA POSTGRESQL ---

def _get_coordenadores():
    engine = connect_db()
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text("SELECT email FROM coordenadores ORDER BY email"), conn)
        return df['email'].tolist() if not df.empty else ["Nenhum e-mail cadastrado"]
    except Exception:
        return ["Nenhum e-mail cadastrado"]

def _get_emprestimos_pendentes():
    engine = connect_db()
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text("SELECT * FROM emprestimos WHERE status_emprestimo = 'PENDENTE'"), conn)
        return df
    except Exception:
        return pd.DataFrame()

def _get_emprestimo_by_id(emprestimo_id):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM emprestimos WHERE id = :id_emprestimo")
            result = conn.execute(query, {"id_emprestimo": emprestimo_id}).mappings().first()
        return result # O resultado já vem como um dicionário
    except Exception:
        return None

def _update_status_emprestimo(emprestimo_id, novo_status):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            query = text("UPDATE emprestimos SET status_emprestimo = :novo_status WHERE id = :id_emprestimo")
            conn.execute(query, {"novo_status": novo_status, "id_emprestimo": emprestimo_id})
            conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)

def registrar_devolucao_avulsa_bd(cpf, coordenador, colaborador, responsavel, turno, centro_de_custo, motivo, status_item, email_coordenador, itens, acao, assinatura_b64):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
            data_atual_obj = datetime.now(fuso_horario_brasilia)
            data_str = data_atual_obj.strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS devolucoes (
                    id SERIAL PRIMARY KEY, data TEXT, cpf TEXT, coordenador TEXT, 
                    colaborador TEXT, responsavel TEXT, turno TEXT, centro_de_custo TEXT, 
                    motivo TEXT, status_item TEXT, acao TEXT, item TEXT, quantidade INTEGER, 
                    tamanho TEXT, email_coordenador TEXT, emprestimo_id_associado INTEGER, assinatura TEXT
                )"""))
            
            for nome, tam, qtd in itens:
                if not str(nome).strip(): continue
                query = text("""
                    INSERT INTO devolucoes (data, cpf, coordenador, colaborador, responsavel, turno, centro_de_custo, motivo, status_item, acao, item, quantidade, tamanho, email_coordenador, assinatura)
                    VALUES (:data, :cpf, :coord, :colab, :resp, :turno, :cc, :motivo, :stat_item, :acao, :item, :qtd, :tam, :email, :ass)
                """)
                conn.execute(query, {
                    "data": data_str, 
                    "cpf": cpf.strip(), 
                    "coord": coordenador.strip().upper(),
                    "colab": colaborador.strip().upper(), 
                    "resp": responsavel.strip().upper(), 
                    "turno": turno.strip(),
                    "cc": centro_de_custo.strip().upper(), 
                    "motivo": motivo.strip(), 
                    "stat_item": status_item.strip(),
                    "acao": acao.strip(), 
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

def _safe_rerun():
    st.rerun()

# --- FUNÇÃO PRINCIPAL DA PÁGINA ---

def carregar():
    st.subheader("⬅️ Registro de Devolução")
    st.session_state.setdefault("devolucao_form_count", 0)

    modo = st.radio(
        "Selecione o tipo de devolução:",
        ["Devolução Avulsa (Ex: Desligamento)", "Devolver um Empréstimo Pendente"],
        horizontal=True,
        key=f"devolucao_modo_{st.session_state.devolucao_form_count}"
    )
    st.markdown("---")

    if modo == "Devolução Avulsa (Ex: Desligamento)":
        render_form_devolucao_avulsa()
    else:
        render_form_devolver_emprestimo()

def render_form_devolucao_avulsa():
    st.markdown("##### Registrar Devolução Avulsa")
    
    # =======================================================
    # O MOTOR DO RESET MÁGICO (EXCLUSIVO PARA DEVOLUÇÕES)
    # =======================================================
    if 'reset_devolucao' not in st.session_state:
        st.session_state.reset_devolucao = 0
        
    rd = st.session_state.reset_devolucao # Atalho para aplicar em todos os campos
    
    epi_names = listar_itens_por_categoria("EPI")
    coordenadores_emails = _get_coordenadores()
    
    # O input de quantidade fica fora do form para atualizar a página em tempo real
    num_itens = st.number_input(
        "Quantidade de tipos de itens para devolução", min_value=1, max_value=10,
        key=f"devolucao_avulsa_num_itens_{rd}"
    )

    # --- Formulário de Devolução ---
    with st.form("devolucao_avulsa_form", clear_on_submit=False):

        st.markdown("**Identificação do Colaborador**")

        col_nome, col_cpf = st.columns(2)
        with col_cpf:
            cpf = st.text_input("CPF (Apenas números)", max_chars=11, key=f"devolucao_avulsa_cpf_{rd}")
        with col_nome:
            colaborador = st.text_input("Colaborador que está devolvendo", key=f"devolucao_avulsa_colaborador_{rd}")
        st.markdown("---")

        coordenador = st.text_input("Coordenador", key=f"devolucao_avulsa_coordenador_{rd}")
        email_coordenador = st.selectbox(
            "E-mail do Coordenador", 
            options=[""] + coordenadores_emails,
            key=f"devolucao_avulsa_email_coordenador_{rd}"
        )
        responsavel = st.selectbox("Responsável", ["", "ALMOXARIFE", "COORDENADOR", "JOVEM APRENDIZ"], key=f"devolucao_avulsa_responsavel_{rd}")
        
        turno = st.selectbox("Turno", ["", "ADM", "1° TURNO", "2° TURNO"], key=f"devolucao_avulsa_turno_{rd}")
        centro_de_custo = st.selectbox("Centro de Custo", ["", "RC", "3P"], key=f"devolucao_avulsa_cc_{rd}")
        motivo = st.selectbox("Motivo da Devolução", ["", "AVARIADO", "HIGIENIZAÇÃO", "TROCA DE TAMANHO", "DESLIGAMENTO", "FIM DE CONTRATO", "OUTRO"], key=f"devolucao_avulsa_motivo_{rd}")
        status_item = st.selectbox("Status do Item Devolvido", ["", "NOVO", "HIGIENIZADO", "AVARIADO"], key=f"devolucao_avulsa_status_{rd}")
        
        # --- CAMPO DE AÇÃO ---
        acao_estoque = st.radio(
            "Ação a ser tomada com os itens:",
            ["Repor no estoque", "Descartar item"],
            horizontal=True,
            key=f"devolucao_avulsa_acao_{rd}"
        )
        
        st.markdown("---")
        st.markdown("**Itens Devolvidos:**")
        for i in range(num_itens):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.selectbox(f"Item #{i+1}", [""] + epi_names, key=f"devolucao_avulsa_item_nome_{i}_{rd}", disabled=(not epi_names))
            with col2:
                st.text_input(f"Tamanho #{i+1}", placeholder="ÚNICO", key=f"devolucao_avulsa_item_tam_{i}_{rd}")
            with col3:
                st.number_input(f"Qtd #{i+1}", min_value=1, value=1, key=f"devolucao_avulsa_item_qtd_{i}_{rd}")
        
        st.markdown("### ✍️ Assinatura de Confirmação")
        st.caption("O colaborador deve assinar abaixo para validar a devolução na data de hoje:")
        
        # O Quadro de desenho
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",  
            stroke_width=3,                       
            stroke_color="#000000",               
            background_color="#eeeeee",           
            height=150,                           
            width=400,                            
            drawing_mode="freedraw",
            key=f"canvas_devolucao_{rd}", # Chave isolada para devoluções
        )

        enviar = st.form_submit_button("Registrar Devolução", type="primary")

    if enviar:
        # Coleta de valores usando o ID dinâmico
        if not cpf: 
            st.error("O campo 'CPF' é obrigatório.")
            st.stop()
        elif not cpf.isdigit() or len(cpf) != 11:
            st.error("⚠️ O CPF deve conter exatamente 11 números (sem pontos ou traços).")
            st.stop()
        colaborador_val = st.session_state.get(f"devolucao_avulsa_colaborador_{rd}", "")
        cpf_val = st.session_state.get(f"devolucao_avulsa_cpf_{rd}", "")
        coordenador_val = st.session_state.get(f"devolucao_avulsa_coordenador_{rd}", "")
        email_val = st.session_state.get(f"devolucao_avulsa_email_coordenador_{rd}", "")
        responsavel_val = st.session_state.get(f"devolucao_avulsa_responsavel_{rd}", "")
        turno_val = st.session_state.get(f"devolucao_avulsa_turno_{rd}", "")
        cc_val = st.session_state.get(f"devolucao_avulsa_cc_{rd}", "")
        motivo_val = st.session_state.get(f"devolucao_avulsa_motivo_{rd}", "")
        status_item_val = st.session_state.get(f"devolucao_avulsa_status_{rd}", "")
        acao_estoque_val = st.session_state.get(f"devolucao_avulsa_acao_{rd}", "")
        
        # Validações Rígidas
        if not cpf_val: st.error("O campo 'CPF' é obrigatório."); st.stop()
        if not colaborador_val: st.error("O campo 'Colaborador' é obrigatório."); st.stop()
        if not cc_val: st.error("O campo 'Centro de Custo' é obrigatório."); st.stop()
        if not email_val or email_val == "Nenhum e-mail cadastrado": st.error("Selecione um e-mail válido."); st.stop()
        if not motivo_val: st.error("O campo 'Motivo da Devolução' é obrigatório."); st.stop()
        if not status_item_val: st.error("O campo 'Status do Item Devolvido' é obrigatório."); st.stop()
        if not coordenador_val: st.error("O campo 'Coordenador' é obrigatório."); st.stop()

        itens_final = []
        for i in range(num_itens):
            nome = st.session_state.get(f"devolucao_avulsa_item_nome_{i}_{rd}", "")
            tam = st.session_state.get(f"devolucao_avulsa_item_tam_{i}_{rd}", "")
            qtd = st.session_state.get(f"devolucao_avulsa_item_qtd_{i}_{rd}", 1)
            if nome:
                itens_final.append((nome, tam, int(qtd)))
        
        if not itens_final:
            st.error("Adicione pelo menos um item."); st.stop()

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

        # Registro no Banco de Dados
        ok_reg, err_reg = registrar_devolucao_avulsa_bd(
            cpf=cpf_val, 
            coordenador=coordenador_val, 
            colaborador=colaborador_val,
            responsavel=responsavel_val, 
            turno=turno_val, 
            centro_de_custo=cc_val,
            motivo=motivo_val, 
            status_item=status_item_val, 
            email_coordenador=email_val,
            itens=itens_final, 
            acao=acao_estoque_val,
            assinatura_b64=assinatura_final_b64
        )

        if not ok_reg:
            st.error(f"Erro ao registrar devolução: {err_reg}"); st.stop()

        # Atualização de Estoque
        if acao_estoque_val == "Repor no estoque":
            erros_estoque = []
            for nome, tam, qtd in itens_final:
                sucesso_estoque, msg_estoque = atualizar_estoque(
                    item_nome=nome, tamanho=tam, status=status_item_val,
                    tipo="EPI", quantidade_delta=int(qtd)
                )
                if not sucesso_estoque:
                    erros_estoque.append(f"Item '{nome}': {msg_estoque}")
            
            if erros_estoque:
                st.warning("Devolução registrada, mas com erros na reposição de estoque:\n" + "\n".join(erros_estoque))
            else:
                st.success("✅ Devolução registrada e estoque atualizado com sucesso!")
        else:
            st.success("✅ Devolução para descarte registrada com sucesso! O estoque não foi alterado.")

        # Disparo de Email
        try:
            sucesso_email, msg_email = enviar_email_devolucao(
                cpf=cpf_val,
                coordenador=coordenador_val,
                colaborador=colaborador_val,
                responsavel=responsavel_val,
                email_coordenador=email_val,
                itens=itens_final,
                centro_de_custo=cc_val,
                turno=turno_val,
                motivo=motivo_val,
                status_item=status_item_val
            )
            if sucesso_email:
                st.info(f"📧 {msg_email}")
            else:
                st.warning(f"A devolução foi salva, mas o e-mail não pôde ser enviado: {msg_email}")
        except Exception as e:
            st.warning(f"A devolução foi salva, mas ocorreu um erro inesperado ao preparar o e-mail: {e}")

        # =======================================================
        # SINALIZA SUCESSO E RESETA O FORMULÁRIO DE DEVOLUÇÃO
        # =======================================================
        st.session_state.reset_devolucao += 1
        time.sleep(3)
        st.rerun()
        

# Em menus/devolucao.py

def render_form_devolver_emprestimo():
    st.markdown("##### Devolver um Empréstimo Pendente")
    st.session_state.setdefault('devolucao_emprestimo_id', None)

    # --- ETAPA 1: SELEÇÃO DO EMPRÉSTIMO ---
    if st.session_state.devolucao_emprestimo_id is None:
        df_pendentes = _get_emprestimos_pendentes()

        if df_pendentes.empty:
            st.info("Nenhum empréstimo pendente encontrado para devolução."); return

        st.markdown("###### Empréstimos com Devolução Pendente:")
        
        # Filtros para a tabela
        col1, col2 = st.columns(2)
        with col1:
            filtro_colaborador = st.text_input("Filtrar por Colaborador:")
        with col2:
            filtro_item = st.text_input("Filtrar por Item:")

        if filtro_colaborador:
            df_pendentes = df_pendentes[df_pendentes['colaborador'].str.contains(filtro_colaborador, case=False, na=False)]
        if filtro_item:
            df_pendentes = df_pendentes[df_pendentes['item'].str.contains(filtro_item, case=False, na=False)]
        
        # --- LINHA MODIFICADA AQUI ---
        # Adicionamos 'centro_de_custo' à lista de colunas a serem exibidas
        st.dataframe(df_pendentes[['id', 'colaborador', 'centro_de_custo', 'item', 'quantidade', 'tamanho', 'data']], use_container_width=True)
        # --- FIM DA MODIFICAÇÃO ---
        
        id_para_devolver = st.number_input("Digite o ID do empréstimo que deseja devolver:", min_value=1, step=1)
        
        if st.button("Buscar Empréstimo"):
            emprestimo = _get_emprestimo_by_id(id_para_devolver)
            if emprestimo and emprestimo['status_emprestimo'] == 'PENDENTE':
                st.session_state.devolucao_emprestimo_id = id_para_devolver
                st.rerun()
            elif emprestimo:
                st.error(f"O empréstimo ID {id_para_devolver} já foi devolvido e não está mais pendente.")
            else:
                st.error(f"Nenhum empréstimo pendente encontrado com o ID {id_para_devolver}.")
    
    # --- ETAPA 2: CONFIRMAÇÃO E DEVOLUÇÃO ---
    else:
        emprestimo_id = st.session_state.devolucao_emprestimo_id
        emprestimo_details = _get_emprestimo_by_id(emprestimo_id)

        if not emprestimo_details:
            st.error("Erro: Detalhes do empréstimo não encontrados. Por favor, tente novamente.")
            st.session_state.devolucao_emprestimo_id = None; return

        st.markdown(f"#### Confirmar Devolução do Empréstimo ID: `{emprestimo_id}`")
        
        # Visualização melhorada
        with st.container(border=True):
            # ... (código de visualização continua o mesmo)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.text("Colaborador:"); st.subheader(emprestimo_details['colaborador'])
            with col2:
                st.text("Item:"); st.subheader(emprestimo_details['item'])
            with col3:
                st.text("Quantidade:"); st.subheader(emprestimo_details['quantidade'])
            col4, col5, col6 = st.columns(3)
            with col4:
                st.text("Tamanho:"); st.subheader(emprestimo_details['tamanho'])
            with col5:
                st.text("Status do Item:"); st.subheader(emprestimo_details['status_item'])
            with col6:
                st.text("Data do Empréstimo:"); st.subheader(pd.to_datetime(emprestimo_details['data']).strftime('%d/%m/%Y %H:%M'))

        st.write("") # Espaço

        col1_btn, col2_btn = st.columns(2)
        with col1_btn:
            if st.button("✅ Confirmar Devolução", use_container_width=True, type="primary"):
                
                # --- CHAMADA DA FUNÇÃO CORRIGIDA ---
                # Agora passamos todos os parâmetros necessários, pegando os valores
                # do dicionário 'emprestimo_details'.
                sucesso_estoque, msg_estoque = atualizar_estoque(
                    item_nome=emprestimo_details['item'],
                    tamanho=emprestimo_details['tamanho'],
                    status=emprestimo_details['status_item'],
                    tipo="EPI",  # Assumindo que empréstimos são sempre de EPIs
                    quantidade_delta=int(emprestimo_details['quantidade']) # Positivo para entrada
                )
                # --- FIM DA CORREÇÃO ---

                if not sucesso_estoque:
                    st.error(f"Erro ao devolver item ao estoque: {msg_estoque}"); return
                
                ok_update, err_update = _update_status_emprestimo(emprestimo_id, "DEVOLVIDO")
                if not ok_update:
                    st.error(f"Erro ao atualizar o status do empréstimo: {err_update}"); return
                
                st.success(f"Empréstimo ID {emprestimo_id} devolvido com sucesso e estoque atualizado!")
                st.session_state.devolucao_emprestimo_id = None
                time.sleep(3)
                st.rerun()
        
        with col2_btn:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.devolucao_emprestimo_id = None

                st.rerun()


