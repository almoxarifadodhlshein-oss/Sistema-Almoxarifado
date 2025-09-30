# Em menus/cadastro_itens.py (VERSÃO FINAL)
import time
import streamlit as st
from utils.itens_db import init_items_db, add_item, listar_itens_por_categoria, remove_item_by_name

def carregar():
    st.subheader("⚙️ Cadastro e Gestão de Itens")

    # Garante que o banco de dados e a tabela existam
    init_items_db()

    # --- Formulário para adicionar novos itens ---
    with st.form("form_cadastro_item", clear_on_submit=True):
        st.markdown("##### Adicionar Novo Item")
        categoria = st.selectbox("Categoria", ["EPI", "INSUMO"], key="item_categoria")
        nome = st.text_input("Nome do item", placeholder="Ex.: LUVA DE MALHA PIGMENTADA", key="item_nome")
        submitted = st.form_submit_button("Adicionar Item")

    # A lógica de processamento agora fica FORA do 'with st.form'
    if submitted:
        # Lemos os valores a partir do st.session_state com as chaves estáticas
        categoria_val = st.session_state.get("item_categoria")
        nome_val = st.session_state.get("item_nome")

        ok, msg = add_item(categoria_val, nome_val)
        if ok:
            st.success("✅ Item adicionado com sucesso!")
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"❌ Erro: {msg}")

    st.markdown("---")

    # --- Seção para visualizar os itens já cadastrados ---
    st.subheader("📋 Itens Cadastrados")

    for cat in ["EPI", "INSUMO"]:
        itens_cadastrados = listar_itens_por_categoria(cat)
        
        with st.expander(f"Categoria: {cat} ({len(itens_cadastrados)} itens)", expanded=True):
            if not itens_cadastrados:
                st.write("_Nenhum item cadastrado nesta categoria._")
            else:
                for item in itens_cadastrados:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(item)
                    with col2:
                        # A lógica de remoção aqui está correta e não precisa de mudança
                        if st.button("Remover", key=f"remove_{cat}_{item}"):
                            ok_remove, msg_remove = remove_item_by_name(item)
                            if ok_remove:
                                st.success(f"Item '{item}' removido.")
                                st.rerun()
                            else:
                                st.error(f"Erro ao remover: {msg_remove}")