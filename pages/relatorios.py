# Em menus/relatorios.py (VERSÃO FINAL E ROBUSTA)

import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime

# 1. NOVAS IMPORTAÇÕES NECESSÁRIAS
from sqlalchemy import text
from utils.db_connection import connect_db

def _read_postgres_table(table_name):
    """Lê uma tabela específica do banco de dados PostgreSQL de forma segura."""
    engine = connect_db()
    try:
        with engine.connect() as conn:
            # Verifica se a tabela existe no schema 'public'
            query_check = text("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = :table)")
            if not conn.execute(query_check, {"table": table_name}).scalar():
                st.info(f"Nenhum registro encontrado. A tabela '{table_name}' pode estar vazia ou não foi criada.")
                return pd.DataFrame()

            df = pd.read_sql_query(text(f'SELECT * FROM "{table_name}"'), conn) # Aspas duplas para nomes de tabela
            df.columns = [col.lower() for col in df.columns]
            return df
    except Exception as e:
        st.error(f"Erro ao ler a tabela '{table_name}': {e}")
        return pd.DataFrame()

def carregar():
    st.subheader("📊 Relatórios e Histórico de Transações")

    # Mapeamento de nomes de menu para nomes de TABELA no PostgreSQL
    fontes_dados = {
        "Saídas de EPIs": "saida_epis",
        "Saídas de Insumos": "saida_insumos",
        "Empréstimos": "emprestimos",
        "Devoluções": "devolucoes",
    }
    
    fonte_selecionada = st.selectbox("Selecione o relatório que deseja visualizar:", list(fontes_dados.keys()))
    
    # 2. CHAMA A NOVA FUNÇÃO DE LEITURA DO POSTGRESQL
    table_name = fontes_dados[fonte_selecionada]
    df = _read_postgres_table(table_name)

    if df.empty:
        return

    st.markdown("---")
    st.markdown(f"**Visualizando:** {fonte_selecionada}")

    # --- INICIALIZAÇÃO DO SESSION_STATE ---
    keys_a_gerenciar = {
        'rel_data_inicio': None, 'rel_data_fim': None, 'rel_colaborador': "", 'rel_coordenador': "", 
        'rel_item': "", 'rel_responsavel_sel': [], 'rel_turno_sel': [], 'rel_centro_de_custo_sel': [],
        'rel_motivo_sel': [], 'rel_tamanho_sel': [], 'rel_status_item_sel': [], 'rel_status_emprestimo_sel': []
    }
    for key, default_value in keys_a_gerenciar.items():
        st.session_state.setdefault(key, default_value)

    # --- PAINEL DE FILTROS ---
    with st.expander("🔍 Aplicar Filtros", expanded=True):
        
        def clear_filters():
            for key, default_value in keys_a_gerenciar.items():
                st.session_state[key] = default_value
        
        st.button("🧹 Limpar todos os filtros", on_click=clear_filters)
        st.markdown("---")
        
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
            col1, col2 = st.columns(2)
            col1.date_input("Data de Início", key='rel_data_inicio')
            col2.date_input("Data de Fim", key='rel_data_fim')
        
        st.markdown("###### Filtros por Texto (contém)")
        col1, col2, col3 = st.columns(3)
        if 'colaborador' in df.columns: col1.text_input("Filtrar por Colaborador", key='rel_colaborador')
        if 'coordenador' in df.columns: col2.text_input("Filtrar por Coordenador", key='rel_coordenador')
        item_col = next((c for c in ['item', 'insumo'] if c in df.columns), None)
        if item_col: col3.text_input("Filtrar por Item/Insumo", key='rel_item')

        st.markdown("###### Filtros por Categoria")
        col1, col2, col3 = st.columns(3)
        
        def render_multiselect(df, col, title, key, container):
            if col in df.columns and df[col].nunique() > 0:
                opts = sorted(df[col].dropna().unique().tolist())
                container.multiselect(f"Filtrar por {title}", opts, key=key)

        render_multiselect(df, 'responsavel', 'Responsável', 'rel_responsavel_sel', col1)
        render_multiselect(df, 'turno', 'Turno', 'rel_turno_sel', col2)
        render_multiselect(df, 'centro_de_custo', 'Centro de Custo', 'rel_centro_de_custo_sel', col3)
        
        col4, col5, col6 = st.columns(3)
        render_multiselect(df, 'motivo', 'Motivo', 'rel_motivo_sel', col4)
        render_multiselect(df, 'tamanho', 'Tamanho', 'rel_tamanho_sel', col5)

        if fonte_selecionada == "Empréstimos":
            render_multiselect(df, 'status_item', 'Status do Item', 'rel_status_item_sel', col6)
            render_multiselect(df, 'status_emprestimo', 'Status do Empréstimo', 'rel_status_emprestimo_sel', col6)

    # --- LÓGICA DE APLICAÇÃO DOS FILTROS (AGORA COMPLETA) ---
    df_filtrado = df.copy()
    
    # Filtro de data
    if 'data' in df_filtrado.columns and st.session_state.rel_data_inicio and st.session_state.rel_data_fim:
        df_filtrado = df_filtrado[
            (df_filtrado['data'].dt.date >= st.session_state.rel_data_inicio) & 
            (df_filtrado['data'].dt.date <= st.session_state.rel_data_fim)
        ]
    
    # Função auxiliar para filtros de texto
    def apply_text_filter(df, key, col_name):
        if st.session_state[key] and col_name in df.columns:
            return df[df[col_name].str.contains(st.session_state[key], case=False, na=False)]
        return df

    # Função auxiliar para filtros de multiseleção
    def apply_multiselect_filter(df, key, col_name):
        if st.session_state[key] and col_name in df.columns:
            return df[df[col_name].isin(st.session_state[key])]
        return df

    # Aplicando TODOS os filtros
    df_filtrado = apply_text_filter(df_filtrado, 'rel_colaborador', 'colaborador')
    df_filtrado = apply_text_filter(df_filtrado, 'rel_coordenador', 'coordenador')
    df_filtrado = apply_text_filter(df_filtrado, 'rel_item', item_col)
    
    df_filtrado = apply_multiselect_filter(df_filtrado, 'rel_responsavel_sel', 'responsavel')
    df_filtrado = apply_multiselect_filter(df_filtrado, 'rel_turno_sel', 'turno')
    df_filtrado = apply_multiselect_filter(df_filtrado, 'rel_centro_de_custo_sel', 'centro_de_custo')
    df_filtrado = apply_multiselect_filter(df_filtrado, 'rel_motivo_sel', 'motivo')
    df_filtrado = apply_multiselect_filter(df_filtrado, 'rel_tamanho_sel', 'tamanho')

    if fonte_selecionada == "Empréstimos":
        df_filtrado = apply_multiselect_filter(df_filtrado, 'rel_status_item_sel', 'status_item')
        df_filtrado = apply_multiselect_filter(df_filtrado, 'rel_status_emprestimo_sel', 'status_emprestimo')
    
    # --- Exibição dos resultados e botão de exportar ---
    st.markdown(f"**Registros encontrados:** {len(df_filtrado)}")
    st.dataframe(df_filtrado, use_container_width=True)

    # --- Lógica para Exportar para Excel ---
    if not df_filtrado.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name=fonte_selecionada)
        
        processed_data = output.getvalue()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"relatorio_{fonte_selecionada.lower().replace(' ', '_')}_{timestamp}.xlsx"

        col_btn, _ = st.columns([1, 4])
        with col_btn:
            st.download_button(
                label=f"📥 Baixar Relatório",
                data=processed_data,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )