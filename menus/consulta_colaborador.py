import streamlit as st
from datetime import datetime, timedelta
import pytz
from utils.colaboradores_db import get_lista_pessoas_com_movimentacao, get_historico_por_cpf
from utils.pdf_generator import gerar_pdf_assinado

def carregar():
    st.subheader("🔍 Central de Auditoria e Histórico Completo")
    
    df_lista = get_lista_pessoas_com_movimentacao()
    if df_lista.empty:
        st.warning("Nenhuma movimentação registrada no sistema ainda.")
        return

    lista_formatada = [f"{row['nome']} - CPF: {row['cpf']}" for _, row in df_lista.iterrows()]
    
    # Criamos as colunas
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selecao = st.selectbox("Selecione o colaborador", [""] + lista_formatada)
        
    with col2:
        fuso = pytz.timezone('America/Sao_Paulo')
        hoje = datetime.now(fuso).date()
        
        # Calendário limpo, sem o limitador de max_value
        datas = st.date_input(
            "Filtrar período",
            value=(hoje, hoje), 
            format="DD/MM/YYYY"
        )
    
    # -------------------------------------------------------------
    # Toda a lógica abaixo precisa estar ALINHADA À ESQUERDA
    # e dentro do 'if selecao:' para só rodar se alguém for escolhido
    # -------------------------------------------------------------
    if selecao:
        if len(datas) != 2:
            st.info("⚠️ Por favor, clique na data de início e depois na data de fim no calendário para completar o filtro.")
            return
            
        data_inicio, data_fim = datas
        nome_selecionado, parte_cpf = selecao.split(" - CPF: ")
        cpf_selecionado = parte_cpf.strip()
        
        # Agora recebe as 4 tabelas
        df_sai, df_emp, df_dev, df_ins = get_historico_por_cpf(cpf_selecionado, data_inicio, data_fim)
        
        st.markdown(f"### Histórico de: **{nome_selecionado}**")
        
        if df_sai.empty and df_emp.empty and df_dev.empty and df_ins.empty:
            st.info(f"Nenhuma movimentação registrada entre {data_inicio.strftime('%d/%m')} e {data_fim.strftime('%d/%m')}.")
            return

        # Trazendo as Abas de volta
        tab1, tab2, tab3, tab4 = st.tabs([
            f"EPI'S ({len(df_sai)})", 
            f"Empréstimos ({len(df_emp)})", 
            f"Devoluções ({len(df_dev)})", 
            f"Insumos ({len(df_ins)})"
        ])
        
        with tab1:
            st.dataframe(df_sai.drop(columns=['assinatura'], errors='ignore'), use_container_width=True) if not df_sai.empty else st.write("Nenhuma saída.")
        with tab2:
            st.dataframe(df_emp, use_container_width=True) if not df_emp.empty else st.write("Nenhum empréstimo.")
        with tab3:
            st.dataframe(df_dev, use_container_width=True) if not df_dev.empty else st.write("Nenhuma devolução.")
        with tab4:
            st.dataframe(df_ins, use_container_width=True) if not df_ins.empty else st.write("Nenhuma saída de insumos.")
            
        st.markdown("---")
        
        # Mandamos as 4 tabelas para o PDF
        pdf_bytes = gerar_pdf_assinado(nome_selecionado, cpf_selecionado, df_sai, df_emp, df_dev, df_ins)
        
        st.download_button(
            label="📥 Exportar Relatório de Auditoria",
            data=pdf_bytes,
            file_name=f"Auditoria_{cpf_selecionado}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            type="primary"
        )