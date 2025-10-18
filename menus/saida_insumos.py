# menus/saida_insumos.py
import time
import streamlit as st
from datetime import datetime

# 1. NOVAS IMPORTAÇÕES NECESSÁRIAS
from sqlalchemy import text
from utils.db_connection import connect_db

# Importações dos outros módulos de utilidades
from email_utils import enviar_email_saida_insumos
from utils.estoque_db import atualizar_estoque
from utils.itens_db import listar_itens_por_categoria
from utils.coordenadores_db import get_coordenadores # Usando a função centralizada

# tentativa de importar utilitário de itens (fallback para listas vazias)
try:
    from utils.itens_db import init_items_db, listar_itens
    init_items_db()
except Exception:
    def listar_itens(cat): return []


def registrar_saida_insumos(cpf, coordenador, colaborador, responsavel, email_coordenador, turno, centro_de_custo, itens_saida):
    """Registra a saída de um ou mais insumos no banco de dados PostgreSQL."""
    engine = connect_db()
    try:
        with engine.connect() as conn:
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 2. SINTAXE DO CREATE TABLE AJUSTADA PARA POSTGRESQL
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS saida_insumos (
                    id SERIAL PRIMARY KEY,
                    data TEXT,
                    cpf TEXT,
                    coordenador TEXT,
                    colaborador TEXT,
                    responsavel TEXT,
                    turno TEXT,
                    centro_de_custo TEXT,
                    insumo TEXT,
                    quantidade INTEGER,
                    tamanho TEXT,
                    email_coordenador TEXT
                )
            """))
            
            for item, tamanho, quantidade in itens_saida:
                if not str(item).strip(): continue
                
                query = text("""
                    INSERT INTO saida_insumos
                    (data, cpf, coordenador, colaborador, responsavel, turno, centro_de_custo, insumo, quantidade, tamanho, email_coordenador)
                    VALUES (:data, :cpf, :coord, :colab, :resp, :turno, :cc, :insumo, :qtd, :tam, :email)
                """)
                conn.execute(query, {
                    "data": data_hora, "cpf": cpf.strip(), "coord": coordenador.strip().upper(),
                    "colab": colaborador.strip().upper(), "resp": responsavel.strip(), "turno": turno.strip(),
                    "cc": centro_de_custo.strip().upper(), "insumo": item.strip().upper(),
                    "qtd": int(quantidade), "tam": tamanho.strip().upper() if tamanho else "",
                    "email": email_coordenador.strip()
                })
            conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)

def _safe_rerun():
    st.rerun()


def carregar():
    st.subheader("📤 Registro de Saída de Insumos")

    # --- Widgets de configuração (fora do formulário) ---
    insumo_names = listar_itens_por_categoria("INSUMO")
    coordenadores_emails = get_coordenadores()

    if not insumo_names:
        st.warning("Nenhum Insumo encontrado no 'Cadastro de Itens'. Por favor, cadastre os itens primeiro.")
        return

    num_itens = st.number_input(
        "Quantidade de tipos de Insumo para saída", min_value=1, max_value=10,
        key="saida_insumos_num_itens"
    )

    # --- Formulário de Saída ---
    with st.form("saida_insumos_form", clear_on_submit=True):
        # Campos gerais do formulário
        cpf = st.text_input("CPF", key="saida_insumos_cpf")
        colaborador = st.text_input("Colaborador", key="saida_insumos_colaborador")
        coordenador = st.text_input("Coordenador", key="saida_insumos_coordenador")
        email_coordenador = st.selectbox("E-mail do Coordenador", options=[""] + coordenadores_emails, key="saida_insumos_email_coordenador")
        responsavel = st.selectbox("Responsável", ["AMANDA MESSIAS", "ANDREZZA SABINO", "PAMELA SIMEÃO", "SUELI BARBOSA", "ORLANDO ALVES", "JOVEM APRENDIZ"], key="saida_insumos_responsavel")
        turno = st.selectbox("Turno", ["ADM", "1° TURNO", "2° TURNO", "3° TURNO"], key="saida_insumos_turno")
        centro_de_custo = st.selectbox("Centro de Custo", ["", "RC", "3P"], key="saida_insumos_centro_de_custo")

        st.markdown("---")
        for i in range(num_itens):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.selectbox(f"Insumo #{i+1}", [""] + insumo_names, key=f"saida_insumos_item_nome_{i}", disabled=(not insumo_names))
            with col2:
                st.text_input(f"Tamanho #{i+1}", placeholder="ÚNICO", key=f"saida_insumos_item_tam_{i}")
            with col3:
                st.number_input(f"Qtd #{i+1}", min_value=1, value=1, key=f"saida_insumos_item_qtd_{i}")
        
        enviar = st.form_submit_button("Registrar Saída de Insumos")

    # A lógica de envio fica FORA do 'with st.form'
    if enviar:
        # Coleta de dados do formulário
        cpf_value = st.session_state.get("saida_insumos_cpf", "")
        coordenador_value = st.session_state.get("saida_insumos_coordenador", "")
        colaborador_value = st.session_state.get("saida_insumos_colaborador", "")
        responsavel_value = st.session_state.get("saida_insumos_responsavel", "")
        email_value = st.session_state.get("saida_insumos_email_coordenador", "")
        turno_value = st.session_state.get("saida_insumos_turno", "")
        centro_value = st.session_state.get("saida_insumos_centro_de_custo", "")

        itens_final = []
        num_itens_registrados = st.session_state.get("saida_insumos_num_itens", 1)
        for i in range(num_itens_registrados):
            escolha = st.session_state.get(f"saida_insumos_item_nome_{i}", "")
            tam = st.session_state.get(f"saida_insumos_item_tam_{i}", "")
            qtd = st.session_state.get(f"saida_insumos_item_qtd_{i}", 1)
            if escolha:
                itens_final.append((escolha, tam, int(qtd)))

        # Validações
        if not centro_value: st.error("O campo 'Centro de Custo' é obrigatório."); return
        if not itens_final: st.error("Preencha pelo menos um insumo."); return
        if not email_value or email_value == "Nenhum e-mail cadastrado": st.error("Selecione um e-mail válido."); return

        # Registro no banco de dados de saída
        ok, err = registrar_saida_insumos(
            cpf=cpf_value, coordenador=coordenador_value, colaborador=colaborador_value,
            responsavel=responsavel_value, email_coordenador=email_value,
            turno=turno_value, centro_de_custo=centro_value, itens_saida=itens_final
        )

        if not ok: st.error(f"Erro ao salvar no banco: {err}"); return

        st.success("✅ Saída de insumos registrada com sucesso!")

        # Baixa no estoque
        erros_estoque = []
        for nome, tam, qtd in itens_final:
            sucesso_estoque, msg_estoque = atualizar_estoque(
                item_nome=nome, tamanho=tam, status="N/A", tipo="INSUMO",
                quantidade_delta=-int(qtd)
            )
            if not sucesso_estoque:
                erros_estoque.append(f"Item '{nome}': {msg_estoque}")
        
        if erros_estoque:
            st.warning("A saída foi registrada, mas com erros na baixa de estoque:\n" + "\n".join(erros_estoque))

        # Envio de e-mail
        try:
            sucesso, msg = enviar_email_saida_insumos(
                cpf=cpf_value, 
                coordenador=coordenador_value, 
                colaborador=colaborador_value,
                responsavel=responsavel_value, 
                email_coordenador=email_value,
                turno=turno_value, 
                centro_de_custo=centro_value, 
                itens=itens_final
            )
            if sucesso: st.info(f"📧 {msg}")
            else: st.warning(f"Saída salva, mas e-mail não enviado: {msg}")
        except Exception as exc:
            st.warning(f"Saída salva, mas ocorreu um erro ao preparar o e-mail: {exc}")

        time.sleep(5)

        st.rerun()