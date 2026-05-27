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
from utils.rf_queries import (
    obter_evolucao_semanal,
    obter_disponibilidade_por_area,
    obter_disponibilidade_por_marca,
    obter_evolucao_por_area,
    obter_evolucao_por_marca
)

from utils.rf_analytics import (
    calcular_percentuais
)

from utils.rf_charts import (
    grafico_evolucao,
    grafico_area,
    grafico_marca,
    grafico_evolucao_area,
    grafico_evolucao_marca
)

def carregar():



    st.title("📡 Controle de RFs")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "RFs",
        "Cadastrar RF",
        "Auditoria Semanal",
        "Histórico",
        "Dashboard"
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
# =========================
# HISTÓRICO
# =========================

    with tab4:

        st.subheader("Histórico de Auditorias")

        auditorias = obter_historico_auditorias()

        if auditorias.empty:

            st.info(
                "Nenhuma auditoria encontrada."
            )

        else:

            st.dataframe(
                auditorias,
                use_container_width=True,
                hide_index=True
            )
    with tab5:

        st.subheader("Analytics RF")
        
        # FILTROS

        with st.container(border=True):
            st.markdown("### Filtros")

            col1, col2 = st.columns(2)

            with col1:
                data_inicio = st.date_input(
                    "Data inicial"
                )

            with col2:
                data_fim = st.date_input(
                    "Data final"
                )

        st.divider()

        # ======================================
        # VISÃO GERAL
        # ======================================

        st.header("Visão Geral")

        st.subheader(
            "Evolução Geral das Auditorias"
        )

        df_evolucao = obter_evolucao_semanal(
            data_inicio,
            data_fim
        )

        fig = grafico_evolucao(
            df_evolucao
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.dataframe(
            df_evolucao,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # ======================================
        # STATUS ATUAL
        # ======================================

        st.header("Status Atual dos RFs")

        col_area, col_marca = st.columns(2)

        # ======================================
        # ÁREA
        # ======================================

        with col_area:
            st.subheader(
                "Disponibilidade Atual por Área"
            )

            df_area = obter_disponibilidade_por_area()

            df_area = calcular_percentuais(
                df_area
            )

            fig_area = grafico_area(
                df_area
            )

            st.plotly_chart(
                fig_area,
                use_container_width=True
            )

            st.dataframe(

                df_area[
                    [
                        "area_atual",
                        "total",
                        "disponiveis",
                        "disponiveis_%",
                        "quebrados",
                        "quebrados_%",
                        "ausentes",
                        "ausentes_%"
                    ]
                ],

                use_container_width=True,
                hide_index=True
            )

        # ======================================
        # MARCA
        # ======================================

        with col_marca:
            st.subheader(
                "Disponibilidade Atual por Marca"
            )

            df_marca = obter_disponibilidade_por_marca()

            df_marca = calcular_percentuais(
                df_marca
            )

            fig_marca = grafico_marca(
                df_marca
            )

            st.plotly_chart(
                fig_marca,
                use_container_width=True
            )

            st.dataframe(

                df_marca[
                    [
                        "marca",
                        "total",
                        "disponiveis",
                        "disponiveis_%",
                        "quebrados",
                        "quebrados_%",
                        "ausentes",
                        "ausentes_%"
                    ]
                ],

                use_container_width=True,
                hide_index=True
            )

        st.divider()

        # ======================================
        # ACOMPANHAMENTO EVOLUTIVO
        # ======================================

        st.header("Acompanhamento Evolutivo")

        # ======================================
        # EVOLUÇÃO POR ÁREA
        # ======================================

        st.subheader(
            "Evolução Semanal por Área"
        )

        df_evolucao_area = obter_evolucao_por_area(
            data_inicio,
            data_fim
        )

        fig_evolucao_area = grafico_evolucao_area(
            df_evolucao_area
        )

        st.plotly_chart(
            fig_evolucao_area,
            use_container_width=True
        )

        st.dataframe(

            df_evolucao_area[
                [
                    "semana",
                    "area_atual",
                    "total",
                    "disponiveis",
                    "percentual_disponibilidade"
                ]
            ],

            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # ======================================
        # EVOLUÇÃO POR MARCA
        # ======================================

        st.subheader(
            "Evolução Semanal por Marca"
        )

        df_evolucao_marca = obter_evolucao_por_marca(
            data_inicio,
            data_fim
        )

        fig_evolucao_marca = grafico_evolucao_marca(
            df_evolucao_marca
        )

        st.plotly_chart(
            fig_evolucao_marca,
            use_container_width=True
        )

        st.dataframe(

            df_evolucao_marca[
                [
                    "semana",
                    "marca",
                    "total",
                    "disponiveis",
                    "percentual_disponibilidade"
                ]
            ],

            use_container_width=True,
            hide_index=True
        )