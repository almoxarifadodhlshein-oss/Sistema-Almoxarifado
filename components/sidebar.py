import streamlit as st


def render_sidebar():

    st.markdown("""
    <div class="custom-sidebar">

        <div class="sidebar-logo">
            DHL Logistics Hub
        </div>

        <div class="sidebar-section">
            MENU
        </div>

    </div>
    """, unsafe_allow_html=True)

    # =========================
    # HOME
    # =========================

    if st.sidebar.button("🏠  Home", use_container_width=True):
        st.session_state.page = "home"

    # =========================
    # ESTOQUE
    # =========================

    with st.sidebar.expander("Estoque"):

        if st.button("Visualizar Estoque", use_container_width=True):
            st.session_state.page = "visualizar_estoque"

        if st.button("Entrada de Estoque", use_container_width=True):
            st.session_state.page = "entrada_estoque"

        if st.button("Cadastro de Itens", use_container_width=True):
            st.session_state.page = "cadastro_itens"

    # =========================
    # MOVIMENTAÇÕES
    # =========================

    with st.sidebar.expander("Movimentações"):

        if st.button("Saída de EPIs", use_container_width=True):
            st.session_state.page = "saida_epi"

        if st.button("Saída de Insumos", use_container_width=True):
            st.session_state.page = "saida_insumos"

        if st.button("Empréstimos", use_container_width=True):
            st.session_state.page = "emprestimo"

        if st.button("Devoluções", use_container_width=True):
            st.session_state.page = "devolucao"

    # =========================
    # GESTÃO
    # =========================

    with st.sidebar.expander("Gestão"):

        if st.button("Relatórios", use_container_width=True):
            st.session_state.page = "relatorios"

        if st.button("Aprovações", use_container_width=True):
            st.session_state.page = "aprovacoes"

        if st.button("Controle RF", use_container_width=True):
            st.session_state.page = "rf_controle"

    # =========================
    # ADMIN
    # =========================

    with st.sidebar.expander("Administração"):

        if st.button("Emails", use_container_width=True):
            st.session_state.page = "cadastro_coordenadores"

        if st.button("Auditoria", use_container_width=True):
            st.session_state.page = "consulta_colaborador"

    st.divider()

    if st.sidebar.button("Sair", use_container_width=True):

        st.session_state.logged_in = False
        st.rerun()