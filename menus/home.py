# Em menus/home.py (VERSÃO PARA POSTGRESQL)

import streamlit as st
import pandas as pd
from sqlalchemy import text

# Importa nossas funções de ajuda centralizadas
from utils.db_connection import connect_db
from utils.estoque_db import get_estoque_atual # Para o valor do estoque

def _read_table_postgres(table_name):
    """Função de ajuda para ler uma tabela específica do PostgreSQL."""
    engine = connect_db()
    try:
        with engine.connect() as conn:
            # Padroniza nomes de colunas para minúsculas para facilitar o acesso
            df = pd.read_sql_query(text(f"SELECT * FROM {table_name}"), conn)
            df.columns = [col.lower() for col in df.columns]
        return df
    except Exception as e:
        # Se a tabela não existir ainda, não é um erro crítico na home.
        # Apenas retorna um DataFrame vazio.
        # print(f"Aviso ao ler '{table_name}': {e}") # descomente para depurar
        return pd.DataFrame()

def carregar():
    st.title("🏠 Página Inicial")
    st.markdown("Bem-vindo(a) ao painel do Sistema de Almoxarifado.")
    st.markdown("---")

    # --- MÉTRICAS PRINCIPAIS ---
    col1, col2 = st.columns(2)
    
    # Métrica 1: Valor Total do Estoque
    with col1:
        try:
            df_estoque = get_estoque_atual()
            if not df_estoque.empty:
                df_estoque['valor_total'] = df_estoque['quantidade'] * df_estoque['valor_unitario']
                valor_total_estoque = df_estoque['valor_total'].sum()
                st.metric("Valor Total do Estoque", f"R$ {valor_total_estoque:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            else:
                st.metric("Valor Total do Estoque", "R$ 0,00")
        except Exception:
            st.metric("Valor Total do Estoque", "Erro ao calcular")

    # Métrica 2: Total de Saídas de EPIs
    with col2:
        df_saidas_epis = _read_table_postgres("saida_epis")
        if not df_saidas_epis.empty and 'quantidade' in df_saidas_epis.columns:
            total_saidas_epis = df_saidas_epis['quantidade'].sum()
            st.metric(label="Total de EPIs Saídos (Todos os Tempos)", value=int(total_saidas_epis))
        else:
            st.metric(label="Total de EPIs Saídos (Todos os Tempos)", value=0)

    st.markdown("---")

    # --- DASHBOARD DE ITENS E EMPRÉSTIMOS ---
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("📊 Itens Mais Utilizados (Saídas de EPI)")
        if not df_saidas_epis.empty and 'item' in df_saidas_epis.columns:
            df_frequencia = df_saidas_epis.groupby('item').agg(
                total_retirado=('quantidade', 'sum'),
                numero_retiradas=('item', 'count')
            ).sort_values(by='total_retirado', ascending=False).reset_index()
            
            st.dataframe(df_frequencia.head(5).rename(columns={
                'item': 'Item',
                'total_retirado': 'Total Retirado',
                'numero_retiradas': 'Nº de Retiradas'
            }), use_container_width=True)
        else:
            st.info("Nenhum dado de saída de EPIs encontrado.")

    with col4:
        st.subheader("⏳ Últimos Empréstimos Pendentes")
        df_emprestimos = _read_table_postgres("emprestimos")
        
        if not df_emprestimos.empty and 'status_emprestimo' in df_emprestimos.columns:
            df_pendentes = df_emprestimos[df_emprestimos['status_emprestimo'] == 'PENDENTE'].copy()
            
            if not df_pendentes.empty:
                df_pendentes['data'] = pd.to_datetime(df_pendentes['data'], errors='coerce')
                df_pendentes.sort_values(by='data', ascending=False, inplace=True)
                
                colunas_desejadas = ['colaborador', 'item', 'quantidade', 'data']
                # Garante que as colunas existem antes de tentar acessá-las
                colunas_existentes = [col for col in colunas_desejadas if col in df_pendentes.columns]
                
                ultimos_emprestimos = df_pendentes[colunas_existentes].head(5)
                ultimos_emprestimos['data'] = ultimos_emprestimos['data'].dt.strftime('%d/%m/%Y %H:%M')
                
                st.dataframe(ultimos_emprestimos, use_container_width=True)
            else:
                st.info("Nenhum empréstimo com status 'Pendente'.")
        else:
            st.info("Nenhum registro de empréstimo encontrado.")