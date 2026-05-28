import streamlit as st


def carregar():

    st.subheader("📊 Gestão")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Aprovações Pendentes", use_container_width=True):
            st.session_state.pagina = "aprovacoes"
            st.rerun()

    with col2:
        if st.button("📋 Relatórios", use_container_width=True):
            st.session_state.pagina = "relatorios"
            st.rerun()

    col3, col4 = st.columns(2)

    with col3:
        if st.button("👤 Auditoria", use_container_width=True):
            st.session_state.pagina = "consulta_colaborador"
            st.rerun()

    with col4:
        if st.button("📡 RF Controle", use_container_width=True):
            st.session_state.pagina = "rf_controle"
            st.rerun()