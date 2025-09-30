# Em main.py (VERSÃO FINAL CORRIGIDA)

import streamlit as st
import hashlib
from PIL import Image
import base64
from pathlib import Path

# --- FUNÇÕES DE AJUDA ---
def img_to_bytes(img_path):
    try:
        img_bytes = Path(img_path).read_bytes()
        encoded = base64.b64encode(img_bytes).decode()
        return encoded
    except FileNotFoundError:
        st.error(f"Arquivo de logo não encontrado: {img_path}")
        return None

def carregar_css(nome_arquivo):
    try:
        with open(nome_arquivo, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo CSS '{nome_arquivo}' não encontrado.")

# --- CONFIGURAÇÕES DA PÁGINA ---
# Esta deve ser a PRIMEIRA chamada Streamlit no seu script
st.set_page_config(
    page_title="Controle de Almoxarifado DHL",
    page_icon="https://www.dhl.com/etc/clientlibs/dhl/clientlib-all/assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carrega o CSS a partir do arquivo externo
carregar_css("modelo.css")

# --- GERENCIAMENTO DE SESSÃO E LOGIN ---
USUARIO_CORRETO = "admin"
SENHA_HASH_CORRETA = "da921b8550242f14805d7c292de25578573dfbd5cbd9cfceb9ffb24e05c40341"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def show_login_page():
    # ... (a função de login permanece a mesma)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image(Image.open("dhl_logo.png"), width=200)
        except FileNotFoundError:
            st.warning("dhl_logo.png não encontrada.")
        
        st.subheader("Login do Sistema de Almoxarifado")
        username = st.text_input("Usuário", key="login_username")
        password = st.text_input("Senha", type="password", key="login_password")
        
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
        else:
            password_hash = ""
        
        if st.button("Entrar"):
            if username == USUARIO_CORRETO and password_hash == SENHA_HASH_CORRETA:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

# --- ESTRUTURA PRINCIPAL DA APLICAÇÃO ---
if not st.session_state.logged_in:
    show_login_page()
else:
    # --- CABEÇALHO ---
    logo_base64 = img_to_bytes("dhl_logo.png")
    if logo_base64:
        logo_html = f"<img src='data:image/png;base64,{logo_base64}' class='logo-img'>"
        st.markdown(
            f"""
            <div class="app-header">
                {logo_html}
                <h1 class="app-title">Controle de Almoxarifado</h1>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- MENU LATERAL (SIDEBAR) ---
    st.sidebar.header("Bem-vindo(a), Admin Geral!")
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    # Mapeamento de nomes de menu para nomes de módulo
    PAGES = {
        "🏠 Home": "home",
        "📧 Cadastro de Emails": "cadastro_coordenadores",
        "📝 Cadastro de Itens": "cadastro_itens",
        "➕ Entrada de Estoque": "entrada_estoque",
        "📦 Saída de EPIs": "saida_epi",
        "📤 Saída de Insumos": "saida_insumos",
        "➡️ Empréstimos": "emprestimo",
        "⬅️ Devoluções": "devolucao",
        "🗳️ Visualizar Estoque": "visualizar_estoque",
        "📊 Relatórios": "relatorios",
    }
    
    selection = st.sidebar.radio("Navegar", list(PAGES.keys()), label_visibility="collapsed")

    # --- LÓGICA DE CARREGAMENTO DE PÁGINA (A CORREÇÃO PRINCIPAL) ---
    # Importamos o módulo APENAS quando ele é selecionado.
    # Isso evita a importação de todos os arquivos de uma vez e quebra o ciclo.
    try:
        page_module_name = PAGES[selection]
        # Constrói o caminho completo para a importação: menus.nome_do_arquivo
        module_path = f"menus.{page_module_name}"
        # Importa o módulo dinamicamente
        page_module = __import__(module_path, fromlist=[page_module_name])
        # Chama a função 'carregar()' dentro do módulo importado
        page_module.carregar()
    except ImportError as e:
        st.error(f"Erro ao carregar a página '{selection}': {e}. Verifique o nome do arquivo e as importações.")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")