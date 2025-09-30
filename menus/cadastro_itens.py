# Em menus/cadastro_itens.py (VERSÃO CORRIGIDA)
import time
import streamlit as st
# 1. Importamos todas as funções necessárias, incluindo a de listar.
from utils.itens_db import init_items_db, add_item, listar_itens_por_categoria, remove_item_by_name

def carregar():
    st.subheader("⚙️ Cadastro e Gestão de Itens")

    # Garante que o banco de dados e a tabela existam
    init_items_db()

    # --- Formulário para adicionar novos itens ---
    with st.form("form_cadastro_item"):
        st.markdown("##### Adicionar Novo Item")
        # Ajustei as opções para corresponderem ao que o sistema usa
        categoria = st.selectbox("Categoria", ["EPI", "INSUMO"])
        nome = st.text_input("Nome do item", placeholder="Ex.: LUVA DE MALHA PIGMENTADA")

        submitted = st.form_submit_button("Adicionar Item")

        if submitted:
            ok, msg = add_item(categoria, nome)
            if ok:
                st.success("✅ Item adicionado com sucesso!")
                time.sleep(1)
                st.rerun() # Recarrega a página para mostrar o novo item na lista
            else:
                st.error(f"❌ Erro: {msg}")

    st.markdown("---")

    # --- Seção para visualizar os itens já cadastrados ---
    st.subheader("📋 Itens Cadastrados")

    # 2. Loop para buscar e exibir os itens de cada categoria
    for cat in ["EPI", "Insumo"]:
        # Usamos a função para buscar os itens da categoria atual
        itens_cadastrados = listar_itens_por_categoria(cat)
        
        # Cria um expander para cada categoria
        with st.expander(f"Categoria: {cat} ({len(itens_cadastrados)} itens)", expanded=True):
            if not itens_cadastrados:
                st.write("_Nenhum item cadastrado nesta categoria._")
            else:
                # Loop para exibir cada item com um botão de remover
                for item in itens_cadastrados:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(item)
                    with col2:
                        # A chave (key) única garante que cada botão funcione de forma independente
                        if st.button("Remover", key=f"remove_{cat}_{item}"):
                            ok_remove, msg_remove = remove_item_by_name(item)
                            if ok_remove:
                                st.success(f"Item '{item}' removido.")
                                st.rerun() # Recarrega para atualizar a lista
                            else:
                                st.error(f"Erro ao remover: {msg_remove}")