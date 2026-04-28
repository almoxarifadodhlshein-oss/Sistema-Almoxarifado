# Em menus/home.py

import streamlit as st
import pandas as pd
from sqlalchemy import text
import streamlit.components.v1 as components
from string import Template # <-- Importação necessária

from utils.db_connection import connect_db
from utils.estoque_db import get_estoque_atual

@st.cache_data(ttl=60)
def _read_table_postgres(table_name):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(f"SELECT * FROM {table_name}"), conn)
            df.columns = [col.lower() for col in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

def carregar():
    # --- 1. BUSCA E PREPARAÇÃO DOS DADOS ---
    valor_total_estoque = 0
    itens_baixo_estoque = 0
    df_estoque = get_estoque_atual()
    
    if not df_estoque.empty:
        df_estoque['valor_total'] = df_estoque['quantidade'] * df_estoque['valor_unitario']
        valor_total_estoque = df_estoque['valor_total'].sum()
        itens_baixo_estoque = len(df_estoque[df_estoque['quantidade'] < 10])

    valor_formatado = f"R$ {valor_total_estoque:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    total_saidas_epis = 0
    linhas_tabela_html = ""
    df_saidas_epis = _read_table_postgres("saida_epis")
    
    if not df_saidas_epis.empty and 'quantidade' in df_saidas_epis.columns:
        total_saidas_epis = int(df_saidas_epis['quantidade'].sum())
        
        df_frequencia = df_saidas_epis.groupby('item').agg(
            total_retirado=('quantidade', 'sum'),
            numero_retiradas=('item', 'count')
        ).sort_values(by='total_retirado', ascending=False).reset_index()
        
        for index, row in df_frequencia.head(4).iterrows():
            linhas_tabela_html += f"""
            <tr class="hover:bg-stone-50 transition-colors border-b border-stone-50">
                <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded bg-stone-100 flex items-center justify-center">
                            <span class="material-symbols-outlined text-stone-500 text-sm">inventory_2</span>
                        </div>
                        <span class="text-sm font-semibold text-stone-800">{row['item']}</span>
                    </div>
                </td>
                <td class="px-6 py-4 text-sm text-stone-600 text-right font-medium">{row['total_retirado']} und</td>
                <td class="px-6 py-4 text-sm text-stone-600 text-right">{row['numero_retiradas']}</td>
                <td class="px-6 py-4 text-center">
                    <span class="inline-block w-2 h-2 rounded-full bg-green-500"></span>
                </td>
            </tr>
            """
    else:
        linhas_tabela_html = """<tr><td colspan="4" class="px-6 py-4 text-center text-sm text-stone-500">Nenhum dado de EPI encontrado.</td></tr>"""

    cards_emprestimos_html = ""
    df_emprestimos = _read_table_postgres("emprestimos")
    
    if not df_emprestimos.empty and 'status_emprestimo' in df_emprestimos.columns:
        df_pendentes = df_emprestimos[df_emprestimos['status_emprestimo'] == 'PENDENTE'].copy()
        if not df_pendentes.empty:
            df_pendentes['data'] = pd.to_datetime(df_pendentes['data'], errors='coerce')
            df_pendentes.sort_values(by='data', ascending=False, inplace=True)
            
            for index, row in df_pendentes.head(4).iterrows():
                data_formatada = row['data'].strftime('%d/%m') if pd.notnull(row['data']) else 'N/A'
                
                cards_emprestimos_html += f"""
                <div class="flex items-start gap-4 p-4 rounded-lg hover:bg-stone-50 transition-all border border-stone-100 group">
                    <div class="flex-1">
                        <div class="flex justify-between">
                            <h3 class="text-xs font-bold text-stone-900">{row.get('colaborador', 'Desconhecido')}</h3>
                            <span class="text-[10px] text-stone-400 font-medium">{data_formatada}</span>
                        </div>
                        <div class="text-xs text-stone-600 mt-1">{row.get('item', 'Item Indefinido')}</div>
                        <div class="flex items-center gap-2 mt-2">
                            <span class="text-[10px] font-bold text-stone-500 bg-stone-100 px-2 py-0.5 rounded">Qtd: {row.get('quantidade', 0)}</span>
                            <span class="text-[10px] font-bold text-yellow-600 bg-yellow-50 px-2 py-0.5 rounded">Pendente</span>
                        </div>
                    </div>
                </div>
                """
        else:
            cards_emprestimos_html = "<div class='text-xs text-stone-500 text-center p-4'>Nenhum empréstimo pendente.</div>"
    else:
         cards_emprestimos_html = "<div class='text-xs text-stone-500 text-center p-4'>Nenhum registro de empréstimo.</div>"


    # --- 2. LEITURA E INJEÇÃO DE DADOS NO HTML ---
    nome_usuario = st.session_state.get("username", "Usuário").capitalize()
    
    try:
        # Lê o arquivo HTML externo
        with open("templates/home.html", "r", encoding="utf-8") as file:
            template_html = file.read()
            
        # Injeta as variáveis Python no lugar dos identificadores com $
        html_final = Template(template_html).safe_substitute(
            nome_usuario=nome_usuario,
            valor_formatado=valor_formatado,
            total_saidas_epis=total_saidas_epis,
            itens_baixo_estoque=itens_baixo_estoque,
            linhas_tabela_html=linhas_tabela_html,
            cards_emprestimos_html=cards_emprestimos_html
        )
        # --- A CORREÇÃO MÁGICA DA LARGURA DA TELA ---
        st.markdown(
            """
            <style>
            /* 1. Alarga a área principal do Streamlit ao máximo */
            .block-container {
                max-width: 98% !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }
            /* 2. Força o componente HTML a esticar 100% da área */
            div[data-testid="stHtml"] {
                width: 100% !important;
                min-width: 100% !important;
            }
            /* 3. Estica o próprio iframe por dentro */
            iframe[title="streamlit_components.components.html"] {
                width: 100% !important;
                min-width: 100% !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Renderiza na tela (Apague o st.markdown com CSS que estava antes disso)
        components.html(html_final, height=850, scrolling=True)
        
    except FileNotFoundError:
        st.error("Arquivo templates/home.html não encontrado.")