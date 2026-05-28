import streamlit as st


def carregar():

    st.subheader("📦 Estoque")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("➕ Entrada de Estoque", use_container_width=True):
            st.session_state.pagina = "entrada_estoque"
            st.rerun()

    with col2:
        if st.button("📋 Visualizar Estoque", use_container_width=True):
            st.session_state.pagina = "visualizar_estoque"
            st.rerun()