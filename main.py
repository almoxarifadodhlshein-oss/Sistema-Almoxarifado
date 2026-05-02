# Em main.py (VERSÃO FINAL CORRIGIDA)

import streamlit as st
import hashlib
from PIL import Image
import base64
from pathlib import Path

# --- FUNÇÕES DE AJUDA ---
@st.cache_data
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
USERS = {
    "admin": {
        "password_hash": "da921b8550242f14805d7c292de25578573dfbd5cbd9cfceb9ffb24e05c40341",
        "role": "admin",
        "label": "Admin Geral",
    },
    "visitante": {
        "password_hash": "44bd2deb7718dfd3a4ed3c426b29e329d19f1b985b9c41610634ddb0eebf5ed4",
        "role": "visitante",
        "label": "Visitante",
    },
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_role = ""

if "username" not in st.session_state:
    st.session_state.username = ""

if "user_role" not in st.session_state:
    st.session_state.user_role = ""


def show_login_page():
    # Injeta CSS específico apenas para a tela de login
    st.markdown("""
    <style>
    /* Esconde a barra superior padrão do Streamlit e o menu lateral na tela de login */
    [data-testid="stHeader"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}

    /* Reduz a margem gigante do topo do Streamlit para a página ficar mais centralizada */
    .block-container {
        padding-top: 3rem !important;
    }

    /* Fundo da página (replicando o bg-surface e os efeitos blur do Stitch) */
    .stApp {
        background-color: #fcf9f8;
        background-image: radial-gradient(circle at 5% 5%, rgba(254, 203, 0, 0.05) 0%, transparent 40%),
                          radial-gradient(circle at 95% 95%, rgba(212, 5, 17, 0.05) 0%, transparent 40%);
    }

    /* Estilo do Card Central de Login */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 12px 32px -4px rgba(27,28,28,0.06);
        border: 1px solid rgba(232, 189, 183, 0.3);
        padding: 2rem 1rem;
    }

    /* Estilizando os campos de texto do Streamlit para parecerem os do Tailwind */
    div[data-baseweb="input"] {
        background-color: #f0eded;
        border-radius: 6px;
        border: none;
    }
    
    /* Remove a borda azul padrão do Streamlit ao clicar no input */
    div[data-baseweb="base-input"] {
        background-color: transparent !important;
        border: none !important;
    }

    /* Estilizando o Botão de Entrar (Gradiente) */
    .stButton > button {
        background: linear-gradient(135deg, #a70009 0%, #d40511 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.75rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px 0 rgba(167, 0, 9, 0.2);
    }
    .stButton > button:hover {
        transform: scale(0.98);
        box-shadow: 0 6px 20px rgba(167, 0, 9, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

    # Top Bar (DHL Logistics Hub) - Mudamos para 'fixed' para colar bem lá em cima
    st.markdown("""
    <div style="position: fixed; top: 25px; left: 40px; z-index: 999999;">
        <span style="font-size: 24px; font-weight: 800; color: #d40511; font-family: 'Inter', sans-serif; letter-spacing: -1px;">
            DHL Logistics Hub
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Reduzi o número de quebras de linha para o card não ficar tão esmagado para baixo
    st.write("") 
    st.write("")
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        # Usamos o container com borda do Streamlit que estilizamos no CSS acima
        with st.container(border=True):
            
            # Cabeçalho do Card
            st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="font-size: 24px; font-weight: 700; color: #1b1c1c; margin-bottom: 8px; font-family: 'Inter', sans-serif;">Controle de Almoxarifado</h1>
                <p style="color: #5e3f3b; font-size: 14px; margin: 0;">Acesse o sistema de gerenciamento de precisão.</p>
            </div>
            """, unsafe_allow_html=True)

            # Labels arrumadas (margens positivas e espaçamento correto)
            st.markdown('<p style="font-size: 12px; font-weight: 600; color: #5e3f3b; margin-bottom: 5px;">USUÁRIO</p>', unsafe_allow_html=True)
            username = st.text_input("Usuário", key="login_username", placeholder="Insira seu login", label_visibility="collapsed")
            
            st.markdown('<p style="font-size: 12px; font-weight: 600; color: #5e3f3b; margin-bottom: 5px; margin-top: 15px;">SENHA</p>', unsafe_allow_html=True)
            password = st.text_input("Senha", type="password", key="login_password", placeholder="••••••••", label_visibility="collapsed")

            if password:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
            else:
                password_hash = ""

            st.write("") # Espaçamento
            
            # Botão Nativo de tela cheia
            if st.button("Entrar", use_container_width=True):
                if username in USERS and password_hash == USERS[username]["password_hash"]:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_role = USERS[username]["role"]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

            # Indicador de Operação
            st.markdown("""
            <div style="text-align: center; margin-top: 25px; font-size: 12px; font-weight: 500; color: #5e3f3b; display: flex; justify-content: center; align-items: center; gap: 8px;">
                <span style="width: 8px; height: 8px; background-color: #fecb00; border-radius: 50%;"></span>
                Operação de DHL
                <span style="width: 8px; height: 8px; background-color: #fecb00; border-radius: 50%;"></span>
            </div>
            """, unsafe_allow_html=True)

    # Rodapé
    st.markdown("""
    <div style="text-align: center; margin-top: 40px; color: #5e3f3b; font-size: 12px; opacity: 0.7;">
        Acesso restrito a colaboradores autorizados.
    </div>
    """, unsafe_allow_html=True)

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
                <div class="header-divider"></div>
                <h1 class="app-title">Controle de Almoxarifado</h1>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- MENU LATERAL (SIDEBAR) ---
    user_label = USERS.get(st.session_state.username, {}).get("label", "Usuário")
    st.sidebar.header(f"Bem-vindo(a), {user_label}!")
    st.sidebar.subheader(f"Perfil: {st.session_state.user_role.capitalize()}")

    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_role = ""
        st.rerun()

    # Mapeamento de nomes de menu para nomes de módulo
    PAGES = {
        "🏠 Home": "home",
        "📧 Cadastro de Emails": "cadastro_coordenadores",
        "📝 Cadastro de Itens": "cadastro_itens",
        "➕ Entrada de Estoque": "entrada_estoque",
        "📤 Saída de EPIs": "saida_epi",
        "📦 Saída de Insumos": "saida_insumos",
        "🤝 Empréstimos": "emprestimo",
        "🔄 Devoluções": "devolucao",
        "🔍 Visualizar Estoque": "visualizar_estoque",
        "📈 Relatórios": "relatorios",
        "📑 Auditoria de Colaboradores": "consulta_colaborador",
    }

    if st.session_state.user_role in ["visitante"]:
        allowed = {"📤 Saída de EPIs", "📦 Saída de Insumos", "🤝 Empréstimos"}
        PAGES = {k: v for k, v in PAGES.items() if k in allowed}

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