import streamlit as st
import pandas as pd
import json
import time
from sqlalchemy import text
from utils.db_connection import connect_db

from utils.estoque_db import atualizar_estoque

# --- Certifique-se de importar suas funções de envio de email aqui ---
from email_utils import enviar_email_saida_epi, enviar_email_saida_insumos, enviar_email_emprestimo


# =====================================================================
# FUNÇÕES DE BANCO DE DADOS (APROVAÇÕES)
# =====================================================================

def deletar_pendencia(pendencia_id, tabela):
    """Remove a pendência da quarentena após ser aprovada ou rejeitada."""
    engine = connect_db()
    with engine.connect() as conn:
        conn.execute(text(f"DELETE FROM {tabela} WHERE id = :id"), {"id": pendencia_id})
        conn.commit()


def inserir_saida_oficial(dados_aprovados, itens_editados_lista):
    engine = connect_db()
    with engine.connect() as conn:
        for item, tamanho, quantidade, status_item in itens_editados_lista:
            query = text("""
                         INSERT INTO saida_epis
                         (data, colaborador, cpf, coordenador, email_coordenador, responsavel, motivo, status, efetivo,
                          turno, centro_de_custo, item, tamanho, quantidade, assinatura)
                         VALUES (:data, :colab, :cpf, :coord, :email, :resp, :motivo, :status, :efetivo, :turno, :cc,
                                 :item, :tam, :qtd, :ass)
                         """)
            conn.execute(query, {
                "data": dados_aprovados['data'], "colab": dados_aprovados['colaborador'], "cpf": dados_aprovados['cpf'],
                "coord": dados_aprovados['coordenador'], "email": dados_aprovados['email_coordenador'],
                "resp": dados_aprovados['responsavel'], "motivo": dados_aprovados['motivo'], "status": status_item,
                "efetivo": dados_aprovados['efetivo'], "turno": dados_aprovados['turno'],
                "cc": dados_aprovados['centro_de_custo'],
                "item": item, "tam": tamanho, "qtd": int(quantidade), "ass": dados_aprovados['assinatura']
            })
        conn.commit()


def inserir_insumo_oficial(dados_aprovados, itens_editados_lista):
    engine = connect_db()
    with engine.connect() as conn:
        for item, tamanho, quantidade in itens_editados_lista:
            query = text("""
                         INSERT INTO saida_insumos
                         (data, cpf, coordenador, colaborador, item, turno, quantidade, tamanho, responsavel,
                          email_coordenador, centro_de_custo)
                         VALUES (:data, :cpf, :coord, :colab, :item, :turno, :qtd, :tam, :resp, :email, :cc)
                         """)
            conn.execute(query, {
                "data": dados_aprovados['data'], "cpf": dados_aprovados['cpf'], "coord": dados_aprovados['coordenador'],
                "colab": dados_aprovados['colaborador'], "item": item, "turno": dados_aprovados['turno'],
                "qtd": int(quantidade), "tam": tamanho, "resp": dados_aprovados['responsavel'],
                "email": dados_aprovados['email_coordenador'], "cc": dados_aprovados['centro_de_custo']
            })
        conn.commit()


def inserir_emprestimo_oficial(dados_aprovados, itens_editados_lista):
    engine = connect_db()
    with engine.connect() as conn:
        for item, tamanho, quantidade, status_item in itens_editados_lista:
            query = text("""
                         INSERT INTO emprestimos
                         (data, colaborador, cpf, coordenador, email_coordenador, responsavel, status, turno,
                          centro_de_custo, item, tamanho, quantidade, assinatura)
                         VALUES (:data, :colab, :cpf, :coord, :email, :resp, :status, :turno, :cc, :item, :tam, :qtd,
                                 :ass)
                         """)
            conn.execute(query, {
                "data": dados_aprovados['data'], "colab": dados_aprovados['colaborador'], "cpf": dados_aprovados['cpf'],
                "coord": dados_aprovados['coordenador'], "email": dados_aprovados['email_coordenador'],
                "resp": dados_aprovados['responsavel'], "status": status_item, "turno": dados_aprovados['turno'],
                "cc": dados_aprovados['centro_de_custo'], "item": item, "tam": tamanho, "qtd": int(quantidade),
                "ass": dados_aprovados['assinatura']
            })
        conn.commit()


# =====================================================================
# INTERFACE PRINCIPAL
# =====================================================================

def carregar():
    st.subheader("✅ Painel de Aprovações")

    if st.session_state.get("user_role") != "admin":
        st.error("Acesso restrito. Apenas o Almoxarifado pode acessar esta página.")
        st.stop()

    aba1, aba2, aba3 = st.tabs(["🛡️ Saídas de EPI", "📦 Insumos", "🤝 Empréstimos"])

    # -------------------------------------------------------------------------
    # ABA 1: SAÍDA DE EPIs
    # -------------------------------------------------------------------------
    with aba1:
        engine = connect_db()
        try:
            with engine.connect() as conn:
                df_epi = pd.read_sql_query(text("SELECT * FROM pendentes_saida_epis ORDER BY id ASC"), conn)
        except Exception:
            df_epi = pd.DataFrame()

        if df_epi.empty:
            st.success("Tudo limpo! Nenhuma solicitação de Saída de EPI pendente.")
        else:
            st.info(f"Você tem {len(df_epi)} solicitação(ões) pendente(s).")
            for index, row in df_epi.iterrows():
                p_id = row['id']
                with st.expander(f"Solicitação #{p_id} - {row['colaborador']} ({row['data']})", expanded=False):

                    st.markdown("**Informações Gerais:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        n_colab = st.text_input("Colaborador", value=row['colaborador'], key=f"epi_colab_{p_id}")
                        n_cpf = st.text_input("CPF", value=str(row['cpf']), key=f"epi_cpf_{p_id}")
                        n_coord = st.text_input("Coordenador", value=row['coordenador'], key=f"epi_coord_{p_id}")
                    with col2:
                        n_email = st.text_input("E-mail Coordenador", value=row['email_coordenador'],
                                                key=f"epi_email_{p_id}")
                        n_resp = st.text_input("Responsável", value=row['responsavel'], key=f"epi_resp_{p_id}")
                        n_motivo = st.text_input("Motivo", value=row['motivo'], key=f"epi_motivo_{p_id}")
                    with col3:
                        n_cc = st.text_input("Centro de Custo", value=row['centro_de_custo'], key=f"epi_cc_{p_id}")
                        n_turno = st.text_input("Turno", value=row['turno'], key=f"epi_turno_{p_id}")
                        n_efetivo = st.text_input("Efetivo", value=row['efetivo'], key=f"epi_efetivo_{p_id}")

                    st.markdown("**Itens Solicitados:**")
                    df_itens = pd.DataFrame(json.loads(row['itens_json']),
                                            columns=["Item", "Tamanho", "Quantidade", "Status"])
                    df_editado = st.data_editor(df_itens, key=f"epi_editor_{p_id}", use_container_width=True,
                                                hide_index=True)

                    if row.get('assinatura'):
                        st.markdown(
                            f"<img src='{row['assinatura']}' width='250' style='border:1px solid #ccc; border-radius:8px;'>",
                            unsafe_allow_html=True)

                    col_aprov, col_recusa = st.columns(2)
                    with col_aprov:
                        if st.button("✅ Aprovar Saída", key=f"epi_aprov_{p_id}", type="primary",
                                     use_container_width=True):
                            dados_atualizados = {
                                'data': row['data'], 'colaborador': n_colab, 'cpf': n_cpf, 'coordenador': n_coord,
                                'email_coordenador': n_email, 'responsavel': n_resp, 'motivo': n_motivo,
                                'centro_de_custo': n_cc, 'turno': n_turno, 'efetivo': n_efetivo,
                                'assinatura': row.get('assinatura')
                            }
                            itens_finais = list(df_editado.itertuples(index=False, name=None))

                            with st.spinner("Aprovando..."):
                                inserir_saida_oficial(dados_atualizados, itens_finais)
                                for item_nome, tam, qtd, status_item in itens_finais:
                                    atualizar_estoque(item_nome=item_nome, tamanho=tam, status=status_item, tipo="EPI",
                                                      quantidade_delta=-int(qtd))

                                try:
                                    enviar_email_saida_epi(
                                        cpf=n_cpf, coordenador=n_coord, colaborador=n_colab, responsavel=n_resp,
                                        email_coordenador=n_email, turno=n_turno, centro_de_custo=n_cc,
                                        status="MÚLTIPLOS", motivo=n_motivo, efetivo=n_efetivo, itens_saida=itens_finais
                                    )
                                except Exception as e:
                                    st.warning(f"Erro e-mail: {e}")

                                deletar_pendencia(p_id, "pendentes_saida_epis")
                                st.success("Aprovado com sucesso!")
                                time.sleep(4)
                                st.rerun()

                    with col_recusa:
                        if st.button("❌ Rejeitar", key=f"epi_recusa_{p_id}", use_container_width=True):
                            deletar_pendencia(p_id, "pendentes_saida_epis")
                            st.warning("Rejeitado.")
                            time.sleep(4)
                            st.rerun()

    # -------------------------------------------------------------------------
    # ABA 2: INSUMOS
    # -------------------------------------------------------------------------
    with aba2:
        try:
            with engine.connect() as conn:
                df_insumo = pd.read_sql_query(text("SELECT * FROM pendentes_saida_insumos ORDER BY id ASC"), conn)
        except Exception:
            df_insumo = pd.DataFrame()

        if df_insumo.empty:
            st.success("Nenhuma solicitação de Insumos pendente.")
        else:
            st.info(f"Você tem {len(df_insumo)} solicitação(ões) pendente(s).")
            for index, row in df_insumo.iterrows():
                p_id = row['id']
                with st.expander(f"Solicitação #{p_id} - {row['colaborador']} ({row['data']})", expanded=False):

                    st.markdown("**Informações Gerais:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        n_colab = st.text_input("Colaborador", value=row['colaborador'], key=f"ins_colab_{p_id}")
                        n_cpf = st.text_input("CPF", value=str(row['cpf']), key=f"ins_cpf_{p_id}")
                        n_coord = st.text_input("Coordenador", value=row['coordenador'], key=f"ins_coord_{p_id}")
                        n_cc = st.text_input("Centro de Custo", value=row.get('centro_de_custo', ''),
                                             key=f"ins_cc_{p_id}")
                    with col2:
                        n_email = st.text_input("E-mail Coordenador", value=row['email_coordenador'],
                                                key=f"ins_email_{p_id}")
                        n_resp = st.text_input("Responsável", value=row['responsavel'], key=f"ins_resp_{p_id}")
                        n_turno = st.text_input("Turno", value=row['turno'], key=f"ins_turno_{p_id}")

                    st.markdown("**Itens Solicitados:**")
                    df_itens = pd.DataFrame(json.loads(row['itens_json']), columns=["Item", "Tamanho", "Quantidade"])
                    df_editado = st.data_editor(df_itens, key=f"ins_editor_{p_id}", use_container_width=True,
                                                hide_index=True)

                    st.write("")
                    col_aprov, col_recusa = st.columns(2)
                    with col_aprov:
                        if st.button("✅ Aprovar Insumo", key=f"ins_aprov_{p_id}", type="primary",
                                     use_container_width=True):
                            dados_atualizados = {
                                'data': row['data'], 'colaborador': n_colab, 'cpf': n_cpf, 'coordenador': n_coord,
                                'email_coordenador': n_email, 'responsavel': n_resp, 'turno': n_turno,
                                'centro_de_custo': n_cc
                            }
                            itens_finais = list(df_editado.itertuples(index=False, name=None))

                            with st.spinner("Aprovando..."):
                                inserir_insumo_oficial(dados_atualizados, itens_finais)
                                for item_nome, tam, qtd in itens_finais:
                                    atualizar_estoque(item_nome=item_nome, tamanho=tam, status="NOVO", tipo="INSUMO",
                                                      quantidade_delta=-int(qtd))

                                try:
                                    enviar_email_saida_insumos(
                                        cpf=n_cpf, coordenador=n_coord, colaborador=n_colab, responsavel=n_resp,
                                        email_coordenador=n_email, turno=n_turno, centro_de_custo=n_cc,
                                        itens=itens_finais
                                    )
                                except Exception as e:
                                    st.warning(f"Erro e-mail: {e}")

                                deletar_pendencia(p_id, "pendentes_saida_insumos")
                                st.success("Aprovado com sucesso!")
                                time.sleep(4)
                                st.rerun()

                    with col_recusa:
                        if st.button("❌ Rejeitar", key=f"ins_recusa_{p_id}", use_container_width=True):
                            deletar_pendencia(p_id, "pendentes_saida_insumos")
                            st.warning("Rejeitado.")
                            time.sleep(4)
                            st.rerun()

    # -------------------------------------------------------------------------
    # ABA 3: EMPRÉSTIMOS
    # -------------------------------------------------------------------------
    with aba3:
        try:
            with engine.connect() as conn:
                df_emp = pd.read_sql_query(text("SELECT * FROM pendentes_emprestimos ORDER BY id ASC"), conn)
        except Exception:
            df_emp = pd.DataFrame()

        if df_emp.empty:
            st.success("Nenhuma solicitação de Empréstimo pendente.")
        else:
            st.info(f"Você tem {len(df_emp)} solicitação(ões) pendente(s).")
            for index, row in df_emp.iterrows():
                p_id = row['id']
                with st.expander(f"Solicitação #{p_id} - {row['colaborador']} ({row['data']})", expanded=False):

                    st.markdown("**Informações Gerais:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        n_colab = st.text_input("Colaborador", value=row['colaborador'], key=f"emp_colab_{p_id}")
                        n_cpf = st.text_input("CPF", value=str(row['cpf']), key=f"emp_cpf_{p_id}")
                        n_coord = st.text_input("Coordenador", value=row['coordenador'], key=f"emp_coord_{p_id}")
                    with col2:
                        n_email = st.text_input("E-mail Coordenador", value=row['email_coordenador'],
                                                key=f"emp_email_{p_id}")
                        n_resp = st.text_input("Responsável", value=row['responsavel'], key=f"emp_resp_{p_id}")
                        n_turno = st.text_input("Turno", value=row['turno'], key=f"emp_turno_{p_id}")
                        n_cc = st.text_input("Centro de Custo", value=row['centro_de_custo'], key=f"emp_cc_{p_id}")

                    st.markdown("**Itens Solicitados:**")
                    df_itens = pd.DataFrame(json.loads(row['itens_json']),
                                            columns=["Item", "Tamanho", "Quantidade", "Status"])
                    df_editado = st.data_editor(df_itens, key=f"emp_editor_{p_id}", use_container_width=True,
                                                hide_index=True)

                    if row.get('assinatura'):
                        st.markdown(
                            f"<img src='{row['assinatura']}' width='250' style='border:1px solid #ccc; border-radius:8px;'>",
                            unsafe_allow_html=True)

                    col_aprov, col_recusa = st.columns(2)
                    with col_aprov:
                        if st.button("✅ Aprovar Empréstimo", key=f"emp_aprov_{p_id}", type="primary",
                                     use_container_width=True):
                            dados_atualizados = {
                                'data': row['data'], 'colaborador': n_colab, 'cpf': n_cpf, 'coordenador': n_coord,
                                'email_coordenador': n_email, 'responsavel': n_resp, 'turno': n_turno,
                                'centro_de_custo': n_cc,
                                'assinatura': row.get('assinatura')
                            }
                            itens_finais = list(df_editado.itertuples(index=False, name=None))

                            with st.spinner("Aprovando..."):
                                inserir_emprestimo_oficial(dados_atualizados, itens_finais)
                                for item_nome, tam, qtd, status_item in itens_finais:
                                    atualizar_estoque(item_nome=item_nome, tamanho=tam, status=status_item, tipo="EPI",
                                                      quantidade_delta=-int(qtd))

                                try:
                                    enviar_email_emprestimo(
                                        cpf=n_cpf, coordenador=n_coord, colaborador=n_colab, responsavel=n_resp,
                                        email_coordenador=n_email, turno=n_turno, centro_de_custo=n_cc,
                                        status_item="MÚLTIPLOS", itens=itens_finais
                                    )
                                except Exception as e:
                                    st.warning(f"Erro e-mail: {e}")

                                deletar_pendencia(p_id, "pendentes_emprestimos")
                                st.success("Aprovado com sucesso!")
                                time.sleep(4)
                                st.rerun()

                    with col_recusa:
                        if st.button("❌ Rejeitar", key=f"emp_recusa_{p_id}", use_container_width=True):
                            deletar_pendencia(p_id, "pendentes_emprestimos")
                            st.warning("Rejeitado.")
                            time.sleep(4)
                            st.rerun()