# menus/rf_controle.py

import streamlit as st
import pandas as pd

from utils.rf_db import (
    init_rf_db,
    cadastrar_rf,
    listar_rfs,
    buscar_rf_por_codigo,
    registrar_verificacao,
    registrar_historico,
    obter_dashboard_rf,
    obter_historico,
    obter_sessao_ativa,
    iniciar_sessao_semana,
    finalizar_sessao_semana,
    buscar_rfs_por_final,
    obter_historico_sessao,
    obter_historico_auditorias

)


def carregar():

    init_rf_db()

    st.title("📡 Controle de RFs")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Dashboard",
        "Cadastrar RF",
        "Auditoria Semanal",
        "Histórico"
    ])

    # =========================
    # DASHBOARD
    # =========================

    with tab1:

        dashboard = obter_dashboard_rf()

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric("Total RFs", dashboard["total_rfs"])
        c2.metric("Disponíveis", dashboard["disponiveis"])
        c3.metric("Quebrados", dashboard["quebrados"])
        c4.metric("RC", dashboard["total_rc"])
        c5.metric("3P", dashboard["total_3p"])

        st.divider()

        sessao = obter_sessao_ativa()

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:

            if not sessao:

                if st.button(
                        "▶️ Iniciar Auditoria Semanal",
                        use_container_width=True
                ):

                    sucesso = iniciar_sessao_semana(
                        st.session_state.get(
                            "username",
                            "Sistema"
                        )
                    )

                    if sucesso:

                        st.success(
                            "Auditoria iniciada."
                        )

                        st.rerun()

                    else:

                        st.warning(
                            "Já existe uma auditoria ativa."
                        )

            else:

                st.success(
                    f"Auditoria ativa "
                    f"(Semana {sessao['semana']})"
                )

        st.subheader("RFs Cadastrados")

        df = listar_rfs()

        if not df.empty:

            st.dataframe(
                df[
                    [
                        "numero",
                        "codigo_rf",
                        "modelo",
                        "marca",
                        "status",
                        "area_atual",
                        "responsavel_atual",
                        "ultima_verificacao"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("Nenhum RF cadastrado.")

    # =========================
    # CADASTRO
    # =========================

    with tab2:

        st.subheader("Cadastrar Novo RF")

        with st.form("form_rf"):

            numero = st.text_input("Número")

            codigo_rf = st.text_input("Código RF")

            modelo = st.text_input(
                "Asset specification and model"
            )

            marca = st.text_input("Brand")

            area = st.text_input("Área")

            responsavel = st.text_input(
                "Responsável Atual"
            )

            status = st.selectbox(
                "Status",
                [
                    "Disponível",
                    "Em uso",
                    "Quebrado",
                    "Ausente"
                ]
            )

            salvar = st.form_submit_button(
                "Cadastrar RF"
            )

            if salvar:

                if not codigo_rf:

                    st.warning(
                        "Informe o código do RF."
                    )

                else:

                    try:

                        cadastrar_rf(
                            numero,
                            codigo_rf,
                            modelo,
                            marca,
                            area,
                            responsavel,
                            status
                        )

                        rf = buscar_rf_por_codigo(
                            codigo_rf
                        )

                        registrar_historico(
                            rf_id=rf["id"],
                            acao="Cadastro RF",
                            usuario=st.session_state.get(
                                "username",
                                "Sistema"
                            ),
                            status_novo=status,
                            area_nova=area,
                            responsavel_novo=responsavel
                        )

                        st.success(
                            "RF cadastrado com sucesso."
                        )

                    except Exception as e:

                        st.error(
                            f"Erro ao cadastrar RF: {e}"
                        )

    # =========================
    # Auditoria Semanal
    # =========================

    with tab3:

        st.subheader("Auditoria Semanal")

        usuario = st.session_state.get(
            "username",
            "Sistema"
        )

        sessao = obter_sessao_ativa()


        # =========================
        # FINALIZAR SESSÃO
        # =========================



        if sessao:

            if st.button(
                "✅ Finalizar Verificação",
                      use_container_width=True
            ):
                    finalizar_sessao_semana(
                        usuario
                    )

                    st.success(
                        "Verificação finalizada."
                    )

                    st.rerun()

        st.divider()

        # =========================
        # SEM SESSÃO
        # =========================

        if not sessao:

            st.info(
                "Aguardando início da "
                "auditoria semanal."
            )

        else:

            st.info(
                "Pesquise pelo código completo "
                "ou pelos últimos dígitos."
            )

            busca = st.text_input(
                "Código RF"
            )

            historico_sessao = obter_historico_sessao()

            if busca:

                resultados = buscar_rfs_por_final(
                    busca.strip().upper()
                )

                if resultados.empty:

                    st.error(
                        "Nenhum RF encontrado."
                    )

                else:

                    st.success(
                        f"{len(resultados)} RF(s) encontrado(s)"
                    )

                    for _, rf in resultados.iterrows():

                        with st.container(border=True):

                            c1, c2 = st.columns(2)

                            c1.write(
                                f"### {rf['codigo_rf']}"
                            )

                            c1.write(
                                f"Número: {rf['numero']}"
                            )

                            c1.write(
                                f"Modelo: {rf['modelo']}"
                            )

                            c1.write(
                                f"Marca: {rf['marca']}"
                            )

                            c1.write(
                                f"Área: {rf['area_atual']}"
                            )

                            c2.write(
                                f"Status atual: "
                                f"{rf['status']}"
                            )

                            c2.write(
                                f"Responsável: "
                                f"{rf['responsavel_atual']}"
                            )

                            c2.write(
                                f"Última verificação: "
                                f"{rf['ultima_verificacao']}"
                            )

                            novo_status = st.selectbox(
                                f"Status {rf['id']}",
                                [
                                    "Disponível",
                                    "Em uso",
                                    "Quebrado",
                                    "Ausente"
                                ],
                                key=f"status_{rf['id']}"
                            )

                            observacao = st.text_area(
                                "Observação",
                                key=f"obs_{rf['id']}"
                            )

                            if st.button(
                                    "Confirmar Verificação",
                                    key=f"btn_{rf['id']}"
                            ):

                                sucesso = registrar_verificacao(
                                    rf["id"],
                                    usuario,
                                    novo_status,
                                    observacao
                                )

                                if not sucesso:

                                    st.warning(
                                        "RF já verificado "
                                        "nesta semana."
                                    )

                                else:

                                    st.success(
                                        "Verificação registrada."
                                    )

                                    st.rerun()

                            st.divider()

            # =========================
            # HISTÓRICO DA AUDITORIA
            # =========================

            st.subheader(
                "Histórico da Auditoria Atual"
            )

            if not historico_sessao.empty:

                st.dataframe(
                    historico_sessao,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "Nenhuma verificação "
                    "realizada nesta auditoria."
                )