# Em menus/devolucao.py (VERSÃO COMPLETA E FUNCIONAL)
import os
import time
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
# 1. NOVAS IMPORTAÇÕES NECESSÁRIAS
from sqlalchemy import text
from utils.db_connection import connect_db

# Importações dos outros módulos de utilidades
from email_utils import enviar_email_devolucao
from utils.estoque_db import atualizar_estoque
from utils.itens_db import listar_itens_por_categoria

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

def registrar_devolucao_avulsa_bd(cpf, coordenador, colaborador, responsavel, turno, centro_de_custo, motivo, status_item, email_coordenador, itens, acao):
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
                    tamanho TEXT, email_coordenador TEXT, emprestimo_id_associado INTEGER
                )"""))
            
            for nome, tam, qtd in itens:
                if not str(nome).strip(): continue
                query = text("""
                    INSERT INTO devolucoes (data, cpf, coordenador, colaborador, responsavel, turno, centro_de_custo, motivo, status_item, acao, item, quantidade, tamanho, email_coordenador)
                    VALUES (:data, :cpf, :coord, :colab, :resp, :turno, :cc, :motivo, :stat_item, :acao, :item, :qtd, :tam, :email)
                """)
                conn.execute(query, {
                    "data": data_str, "cpf": cpf.strip(), "coord": coordenador.strip().upper(),
                    "colab": colaborador.strip().upper(), "resp": responsavel.strip(), "turno": turno.strip(),
                    "cc": centro_de_custo.strip().upper(), "motivo": motivo.strip(), "stat_item": status_item.strip(),
                    "acao": acao.strip(), "item": nome.strip().upper(), "qtd": int(qtd),
                    "tam": tam.strip().upper() if tam else "", "email": email_coordenador.strip()
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
    
    
    form_key = f"devolucao_avulsa_form"
    
    epi_names = listar_itens_por_categoria("EPI")
    coordenadores_emails = _get_coordenadores()
    
    num_itens = st.number_input(
        "Quantidade de tipos de itens para devolução", min_value=1, max_value=10,
        key=f"devolucao_avulsa_num_itens"
    )

    with st.form("devolucao_avulsa_form", clear_on_submit=True):
        cpf = st.text_input("CPF", key=f"devolucao_avulsa_cpf")
        coordenador = st.text_input("Coordenador", key=f"devolucao_avulsa_coordenador")
        colaborador = st.text_input("Colaborador que está devolvendo", key=f"devolucao_avulsa_colaborador")
        email_coordenador = st.selectbox(
            "E-mail do Coordenador", 
            options= [""] + coordenadores_emails,
            key=f"devolucao_avulsa_email_coordenador"
        )
        responsavel = st.selectbox(
            "Responsável",
            ["AMANDA MESSIAS", "ANDREZZA SABINO", "PAMELA SIMEÃO",
             "RAFAEL CRISTOVÃO","SUELI BARBOSA", "ORLANDO ALVES", 
             "JOVEM APRENDIZ"],
            key=f"devolucao_avulsa_responsavel"
        )
        turno = st.selectbox("Turno", ["ADM", "1° TURNO", "2° TURNO", "3° TURNO"], key=f"devolucao_avulsa_turno")
        centro_de_custo = st.selectbox("Centro de Custo", [""] + ["RC", "3P"], key=f"devolucao_avulsa_cc")
        motivo = st.selectbox("Motivo da Devolução", ["AVARIADO", "HIGIENIZAÇÃO", "TROCA DE TAMANHO", "DESLIGAMENTO", "FIM DE CONTRATO", "OUTRO"], key=f"devolucao_avulsa_motivo")
        status_item = st.selectbox("Status do Item Devolvido", ["NOVO", "HIGIENIZADO", "AVARIADO"], key=f"devolucao_avulsa_status")
        
        # --- NOVO CAMPO DE AÇÃO ---
        acao_estoque = st.radio(
            "Ação a ser tomada com os itens:",
            ["Repor no estoque", "Descartar item"],
            horizontal=True,
            key=f"devolucao_avulsa_acao"
        )
        
        st.markdown("---")
        st.markdown("**Itens Devolvidos:**")
        for i in range(num_itens):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.selectbox(f"Item #{i+1}", [""] + epi_names, key=f"devolucao_avulsa_item_nome_{i}", disabled=(not epi_names))
            with col2:
                st.text_input(f"Tamanho #{i+1}", placeholder="ÚNICO", key=f"devolucao_avulsa_item_tam_{i}")
            with col3:
                st.number_input(f"Qtd #{i+1}", min_value=1, value=1, key=f"devolucao_avulsa_item_qtd_{i}")
        
        enviar = st.form_submit_button("Registrar Devolução")

    if enviar:
        # --- LÓGICA DE COLETA CORRIGIDA USANDO O MÉTODO SEGURO .get() ---
        
        colaborador_val = st.session_state.get(f"devolucao_avulsa_colaborador", "")
        cpf_val = st.session_state.get(f"devolucao_avulsa_cpf", "")
        coordenador_val = st.session_state.get(f"devolucao_avulsa_coordenador", "")
        email_val = st.session_state.get(f"devolucao_avulsa_email_coordenador", "")
        responsavel_val = st.session_state.get(f"devolucao_avulsa_responsavel", "")
        turno_val = st.session_state.get(f"devolucao_avulsa_turno", "")
        cc_val = st.session_state.get(f"devolucao_avulsa_cc", "")
        motivo_val = st.session_state.get(f"devolucao_avulsa_motivo", "")
        status_item_val = st.session_state.get(f"devolucao_avulsa_status", "")
        acao_estoque_val = st.session_state.get(f"devolucao_avulsa_acao", "")
        
        itens_final = []
        for i in range(num_itens):
            nome = st.session_state.get(f"devolucao_avulsa_item_nome_{i}", "")
            tam = st.session_state.get(f"devolucao_avulsa_item_tam_{i}", "")
            qtd = st.session_state.get(f"devolucao_avulsa_item_qtd_{i}", 1)
            if nome:
                itens_final.append((nome, tam, qtd))
        
        if not itens_final:
            st.error("Adicione pelo menos um item."); return

        # O resto do código continua como estava...
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
            acao=acao_estoque_val
        )

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

        if not ok_reg:
            st.error(f"Erro ao registrar devolução: {err_reg}"); return
        
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
                st.success("Devolução registrada e estoque atualizado com sucesso!")
        else:
            st.success("Devolução para descarte registrada com sucesso! O estoque não foi alterado.")

        time.sleep(4)
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


