import streamlit as st


def carregar():

    st.subheader("👷 Movimentações")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🦺 Saída EPI", use_container_width=True):
            st.session_state.pagina = "saida_epi"
            st.rerun()

    with col2:
        if st.button("🧴 Saída Insumos", use_container_width=True):
            st.session_state.pagina = "saida_insumos"
            st.rerun()

    col3, col4 = st.columns(2)

    with col3:
        if st.button("🤝 Empréstimos", use_container_width=True):
            st.session_state.pagina = "emprestimo"
            st.rerun()

    with col4:
        if st.button("🔄 Devoluções", use_container_width=True):
            st.session_state.pagina = "devolucao"
            st.rerun()