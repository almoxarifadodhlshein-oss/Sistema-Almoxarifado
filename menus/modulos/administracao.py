import streamlit as st


def carregar():

    st.subheader("⚙ Administração")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📦 Cadastro de Itens", use_container_width=True):
            st.session_state.pagina = "cadastro_itens"
            st.rerun()

    with col2:
        if st.button("👥 Coordenadores", use_container_width=True):
            st.session_state.pagina = "cadastro_coordenadores"
            st.rerun()