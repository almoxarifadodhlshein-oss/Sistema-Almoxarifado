# Em menus/entrada_estoque.py (VERSÃO FINAL CORRIGIDA)

import streamlit as st
import time
from utils.estoque_db import atualizar_estoque
from utils.itens_db import listar_itens_por_categoria

def carregar():
    st.subheader("📥 Entrada de Estoque")

    # --- Widgets de configuração (fora do formulário) ---
    col1, col2 = st.columns(2)
    with col1:
        tipo_selecionado = st.selectbox(
            "Selecione o Tipo de Item",
            ["EPI", "INSUMO"], # Padronizado para maiúsculas
            key="entrada_tipo_item"
        )
    
    lista_de_itens = listar_itens_por_categoria(tipo_selecionado)

    with col2:
        num_itens = st.number_input(
            "Quantos tipos de itens deseja adicionar?",
            min_value=1, max_value=20, value=1, step=1,
            key="entrada_num_itens"
        )

    st.markdown("---")

    if not lista_de_itens:
        st.warning(f"Nenhum item do tipo '{tipo_selecionado}' encontrado no 'Cadastro de Itens'. Cadastre um item primeiro.")
        return

    # 1. CORREÇÃO: A chave do formulário deve ser única para esta página
    with st.form("entrada_form", clear_on_submit=True):
        
        for i in range(num_itens):
            st.markdown(f"**Item #{i+1}**")
            col_item, col_forn = st.columns(2)
            with col_item:
                st.selectbox(f"Selecione o {tipo_selecionado}", options=[""] + lista_de_itens, key=f"entrada_item_nome_{i}")
            with col_forn:
                st.text_input("Fornecedor", key=f"entrada_item_fornecedor_{i}")

            col_tam, col_status, col_qtd, col_valor_un = st.columns(4)
            with col_tam:
                st.text_input("Tamanho", placeholder="ÚNICO", key=f"entrada_item_tamanho_{i}")
            with col_status:
                st.selectbox("Status", ["NOVO", "HIGIENIZADO"], key=f"entrada_item_status_{i}")
            with col_qtd:
                st.number_input("Quantidade", min_value=1, step=1, key=f"entrada_item_quantidade_{i}")
            with col_valor_un:
                st.number_input("Valor Unitário (R$)", min_value=0.0, format="%.2f", key=f"entrada_item_valor_unitario_{i}")
        
        submitted = st.form_submit_button("Registrar Entradas no Estoque")

    # 2. CORREÇÃO: A lógica de envio deve ficar FORA do 'with st.form'
    if submitted:
        # Pega a quantidade de itens a serem registrados a partir do session_state
        num_itens_registrados = st.session_state.get("entrada_num_itens", 1)
        
        itens_para_adicionar = []
        for i in range(num_itens_registrados):
            # Usamos .get() para evitar erros se a chave não existir
            nome = st.session_state.get(f"entrada_item_nome_{i}")
            if nome:
                fornecedor = st.session_state.get(f"entrada_item_fornecedor_{i}", "")
                tamanho = st.session_state.get(f"entrada_item_tamanho_{i}", "")
                status = st.session_state.get(f"entrada_item_status_{i}", "NOVO")
                quantidade = st.session_state.get(f"entrada_item_quantidade_{i}", 1)
                valor_unitario = st.session_state.get(f"entrada_item_valor_unitario_{i}", 0.0)
                itens_para_adicionar.append((nome, tamanho, status, fornecedor, quantidade, valor_unitario))
        
        if not itens_para_adicionar:
            st.error("Adicione pelo menos um item para registrar a entrada.")
            return

        sucessos = 0
        erros = []
        for nome, tam, stat, forn, qtd, val_un in itens_para_adicionar:
            sucesso, msg = atualizar_estoque(
                item_nome=nome,
                tamanho=tam or "ÚNICO",
                status=stat,
                tipo=tipo_selecionado,
                fornecedor=forn,
                valor_unitario=val_un,
                quantidade_delta=qtd
            )
            if sucesso:
                sucessos += 1
            else:
                erros.append(f"Item '{nome}': {msg}")
        
        if sucessos > 0:
            st.success(f"{sucessos} entrada(s) de item registrada(s) com sucesso!")
        if erros:
            st.error("Algumas entradas falharam:\n" + "\n".join(erros))
        
        time.sleep(2)
        # 3. CORREÇÃO: Não precisamos mais do contador de formulário nem do rerun manual
        st.rerun() # O rerun ainda é útil para recarregar o widget 'num_itens' e a lista, se necessário