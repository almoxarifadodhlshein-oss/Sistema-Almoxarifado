# Em menus/visualizar_estoque.py (VERSÃO FINAL PARA POSTGRESQL)

import streamlit as st
import pandas as pd
import io
from datetime import datetime
# A única função de DB que esta tela precisa é a que busca o estoque
from utils.estoque_db import get_estoque_atual

def carregar():
    st.subheader("📦 Visualização e Filtro de Estoque Atual")

    try:
        df_estoque = get_estoque_atual()
    except Exception as e:
        st.error(f"Erro ao carregar o estoque: {e}")
        return

    if df_estoque.empty:
        st.info("Nenhum item cadastrado no estoque ainda.")
        return

    # --- Cálculos dos valores ---
    # Garante que as colunas existem antes de calcular
    if 'quantidade' in df_estoque.columns and 'valor_unitario' in df_estoque.columns:
        df_estoque['valor_total'] = df_estoque['quantidade'] * df_estoque['valor_unitario']
        valor_total_estoque = df_estoque['valor_total'].sum()
        
        # Filtra por tipo antes de somar para evitar erros se uma categoria não existir
        valor_total_epi = df_estoque[df_estoque['tipo'] == 'EPI']['valor_total'].sum()
        valor_total_insumo = df_estoque[df_estoque['tipo'] == 'INSUMO']['valor_total'].sum()
    else:
        df_estoque['valor_total'] = 0
        valor_total_estoque = valor_total_epi = valor_total_insumo = 0

    # --- Exibição das métricas ---
    col1, col2, col3 = st.columns(3)
    def format_currency(value):
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    with col1:
        st.metric("Valor Total do Estoque", format_currency(valor_total_estoque))
    with col2:
        st.metric("Valor Total em EPIs", format_currency(valor_total_epi))
    with col3:
        st.metric("Valor Total em Insumos", format_currency(valor_total_insumo))
    st.markdown("---")

    # --- Lógica de Filtros com o novo campo 'Fornecedor' ---
    st.session_state.setdefault("est_item_nome", "")
    st.session_state.setdefault("est_tipo_sel", [])
    st.session_state.setdefault("est_tamanho_sel", [])
    st.session_state.setdefault("est_status_sel", [])
    st.session_state.setdefault("est_fornecedor_sel", []) # <-- NOVO FILTRO

    with st.expander("🔍 Filtros Avançados (clique para abrir)", expanded=True):
        def clear_filters():
            st.session_state.est_item_nome = ""
            st.session_state.est_tipo_sel = []
            st.session_state.est_tamanho_sel = []
            st.session_state.est_status_sel = []
            st.session_state.est_fornecedor_sel = [] # <-- LIMPA O NOVO FILTRO

        st.button("🧹 Limpar filtros", on_click=clear_filters)
        st.text_input("Buscar por nome do item (contém)", key="est_item_nome")
        
        f_col1, f_col2, f_col3, f_col4 = st.columns(4) # Adicionamos uma coluna para o novo filtro
        with f_col1:
            if 'tipo' in df_estoque.columns:
                st.multiselect("Filtrar por Tipo", sorted(df_estoque['tipo'].dropna().unique()), key="est_tipo_sel")
        with f_col2:
            if 'tamanho' in df_estoque.columns:
                st.multiselect("Filtrar por Tamanho", sorted(df_estoque['tamanho'].dropna().unique()), key="est_tamanho_sel")
        with f_col3:
            if 'status' in df_estoque.columns:
                st.multiselect("Filtrar por Status", sorted(df_estoque['status'].dropna().unique()), key="est_status_sel")
        with f_col4:
            # <-- NOVO FILTRO SENDO ADICIONADO NA TELA
            if 'fornecedor' in df_estoque.columns:
                st.multiselect("Filtrar por Fornecedor", sorted(df_estoque['fornecedor'].dropna().unique()), key="est_fornecedor_sel")


    # --- Aplicação dos filtros ---
    df_filtrado = df_estoque.copy()
    
    # ... (lógica de aplicação dos filtros antigos continua igual) ...
    item_nome_filter = st.session_state.get("est_item_nome", "")
    tipo_sel_filter = st.session_state.get("est_tipo_sel", [])
    tamanho_sel_filter = st.session_state.get("est_tamanho_sel", [])
    status_sel_filter = st.session_state.get("est_status_sel", [])
    fornecedor_sel_filter = st.session_state.get("est_fornecedor_sel", []) # <-- Pega o valor do novo filtro
    
    if item_nome_filter: df_filtrado = df_filtrado[df_filtrado['item_nome'].str.contains(item_nome_filter, case=False, na=False)]
    if tipo_sel_filter: df_filtrado = df_filtrado[df_filtrado['tipo'].isin(tipo_sel_filter)]
    if tamanho_sel_filter: df_filtrado = df_filtrado[df_filtrado['tamanho'].isin(tamanho_sel_filter)]
    if status_sel_filter: df_filtrado = df_filtrado[df_filtrado['status'].isin(status_sel_filter)]
    if fornecedor_sel_filter: df_filtrado = df_filtrado[df_filtrado['fornecedor'].isin(fornecedor_sel_filter)] # <-- APLICA O NOVO FILTRO

    # --- Exibição dos resultados e Exportação (continua igual) ---
    st.markdown(f"**Itens encontrados:** {len(df_filtrado)}")
    st.dataframe(df_filtrado, use_container_width=True,
                 column_config={
                     "valor_unitario": st.column_config.NumberColumn("Valor Unitário (R$)", format="R$ %.2f"),
                     "valor_total": st.column_config.NumberColumn("Valor Total (R$)", format="R$ %.2f")
                 })
    
    st.write("")
    if not df_filtrado.empty:
        col_btn, _ = st.columns([1, 4]) 
        with col_btn:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Renomeia colunas para o Excel ficar mais bonito
                df_to_export = df_filtrado.rename(columns=lambda c: c.replace('_', ' ').title())
                df_to_export.to_excel(writer, index=False, sheet_name='Estoque_Atual')
            
            processed_data = output.getvalue()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"relatorio_estoque_{timestamp}.xlsx"
            st.download_button(
                label="📥 Baixar Excel", data=processed_data, file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )