import streamlit.components.v1 as components

def render_navbar():

    html = """
    <!DOCTYPE html>
    <html>

    <head>

    <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
    >

    <style>

    body {
        margin: 0;
        overflow: hidden;
        font-family: Arial, sans-serif;
    }

    .navbar {

        width: 100%;
        height: 72px;

        background: #ffcc00;

        display: flex;
        align-items: center;
        justify-content: space-between;

        padding: 0 40px;

        box-sizing: border-box;
    }

    .left {

        display: flex;
        align-items: center;

        gap: 50px;
    }

    .logo {

        height: 36px;
    }

    .menu {

        display: flex;
        align-items: center;

        gap: 35px;
    }

    .menu-link {
        text-decoration: none;
        color: inherit;
    }

    .item {

        position: relative;

        height: 72px;

        display: flex;
        align-items: center;

        gap: 10px;

        cursor: pointer;

        font-size: 16px;
        font-weight: 600;

        color: #1b1c1c;

        transition: 0.2s;
    }

    .item:hover {
        color: #d40511;
    }

    .dropdown {

        position: absolute;

        top: 72px;
        left: 0;

        width: 260px;

        background: white;

        box-shadow:
            0 12px 24px rgba(0,0,0,0.12);

        display: none;

        flex-direction: column;

        z-index: 999999;
    }

    .item:hover .dropdown {
        display: flex;
    }

    .dropdown a {

        text-decoration: none;

        color: black;

        padding: 15px 18px;

        font-size: 14px;

        transition: 0.2s;

        cursor: pointer;

        display: block;
    }

    .dropdown a:hover {

        background: #f5f5f5;

        color: #d40511;
    }

    </style>

    </head>

    <body>

        <div class="navbar">

            <div class="left">

                <img
                    class="logo"
                    src="https://upload.wikimedia.org/wikipedia/commons/a/ac/DHL_Logo.svg"
                >

                <div class="menu">

                    <!-- HOME -->
                    <a onclick="window.open('/?page=home', '_self')" class="menu-link">

                        <div class="item">
                            <i class="fa-solid fa-house"></i>
                            Home
                        </div>

                    </a>

                    <!-- ESTOQUE -->
                    <div class="item">

                        <i class="fa-solid fa-boxes-stacked"></i>
                        Estoque

                        <div class="dropdown">

                            <a onclick="window.open('/?page=entrada_estoque.py', '_self')">
                                Entrada Estoque
                            </a>

                            <a onclick="window.open('/?page=visualizar_estoque', '_self')">
                                Visualizar Estoque
                            </a>

                            <a onclick="window.open('/?page=cadastro_itens', '_self')">
                                Cadastro Itens
                            </a>

                        </div>

                    </div>

                    <!-- MOVIMENTAÇÕES -->
                    <div class="item">

                        <i class="fa-solid fa-arrow-right-arrow-left"></i>
                        Movimentações

                        <div class="dropdown">

                            <a onclick="window.open('/?page=saida_epi', '_self')">
                                Saída EPI
                            </a>

                            <a onclick="window.open('/?page=saida_insumos', '_self')">
                                Saída Insumos
                            </a>

                            <a onclick="window.open('/?page=emprestimo', '_self')">
                                Empréstimos
                            </a>

                            <a onclick="window.open('/?page=devolucao', '_self')">
                                Devoluções
                            </a>

                        </div>

                    </div>

                    <!-- GESTÃO -->
                    <div class="item">

                        <i class="fa-solid fa-chart-column"></i>
                        Gestão

                        <div class="dropdown">

                            <a onclick="window.open('/?page=relatorios', '_self')">
                                Relatórios
                            </a>

                            <a onclick="window.open('/?page=rf_controle', '_self')">
                                Controle RF
                            </a>

                        </div>

                    </div>

                    <!-- ADMIN -->
                    <div class="item">

                        <i class="fa-solid fa-gear"></i>
                        Administração

                        <div class="dropdown">

                            <a onclick="window.open('/?page=aprovacoes', '_self')">
                                Aprovações
                            </a>

                            <a onclick="window.open('/?page=cadastro_coordenadores', '_self')">
                                Coordenadores
                            </a>

                            <a onclick="window.open('/?page=consulta_colaborador', '_self')">
                                Auditoria
                            </a>

                        </div>

                    </div>

                </div>

            </div>

            <div>
                <i class="fa-solid fa-user"></i>
            </div>

        </div>

    </body>

    </html>
    """

    components.html(
        html,
        height=72,
        scrolling=False
    )