# menus/saida_insumos.py
import time
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import json
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

def get_coordenadores():
    engine = connect_db()
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text("SELECT email FROM coordenadores ORDER BY email"), conn)
        return df['email'].tolist() if not df.empty else ["Nenhum e-mail cadastrado"]
    except Exception:
        return ["Nenhum e-mail cadastrado"]

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
            fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
            data_atual_obj = datetime.now(fuso_horario_brasilia)
            data_str = data_atual_obj.strftime("%Y-%m-%d %H:%M:%S")
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
                    "data": data_str, "cpf": cpf.strip(), "coord": coordenador.strip().upper(),
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

def registrar_saida_insumos_pendente(cpf, coordenador, colaborador, responsavel, email_coordenador, turno, centro_de_custo, itens_saida):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
            data_str = datetime.now(fuso_horario_brasilia).strftime("%Y-%m-%d %H:%M:%S")
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pendentes_saida_insumos (
                    id SERIAL PRIMARY KEY, data TEXT, cpf TEXT, colaborador TEXT,
                    coordenador TEXT, email_coordenador TEXT, responsavel TEXT,
                    turno TEXT, centro_de_custo TEXT, itens_json TEXT
                )
            """))
            
            itens_str = json.dumps(itens_saida)
            
            query = text("""
                INSERT INTO pendentes_saida_insumos 
                (data, cpf, colaborador, coordenador, email_coordenador, responsavel, turno, centro_de_custo, itens_json)
                VALUES (:data, :cpf, :colab, :coord, :email, :resp, :turno, :cc, :itens)
            """)
            conn.execute(query, {
                "data": data_str, "cpf": str(cpf).strip(), "colab": colaborador.strip().upper(),
                "coord": coordenador.strip().upper(), "email": email_coordenador.strip(),
                "resp": responsavel.strip().upper(), "turno": turno.strip(),
                "cc": centro_de_custo.strip().upper(), "itens": itens_str
            })
            conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)


def carregar():
    st.subheader("📤 Registro de Saída de Insumos")

    # =======================================================
    # O MOTOR DO RESET MÁGICO (EXCLUSIVO PARA INSUMOS)
    # =======================================================
    if 'reset_insumo' not in st.session_state:
        st.session_state.reset_insumo = 0
        
    ri = st.session_state.reset_insumo # Atalho para aplicar em todos os campos

    # --- Widgets de configuração (fora do formulário) ---
    insumo_names = listar_itens_por_categoria("INSUMO")
    coordenadores_emails = get_coordenadores()

    if not insumo_names:
        st.warning("Nenhum Insumo encontrado no 'Cadastro de Itens'. Por favor, cadastre os itens primeiro.")
        st.stop() # Alterado de return para st.stop()

    num_itens = st.number_input(
        "Quantidade de tipos de Insumo para saída", min_value=1, max_value=10,
        key=f"saida_insumos_num_itens_{ri}"
    )

    # --- Formulário de Saída ---
    with st.form("saida_insumos_form", clear_on_submit=False): # Mudar para False
        perfil_usuario = st.session_state.get("user_role", "visitante")
        
        st.markdown("**Identificação do Colaborador**")
        col_nome, col_cpf = st.columns(2)
        with col_cpf:
            cpf_value = st.text_input("CPF (Apenas números)", max_chars=11, key=f"saida_insumos_cpf_{ri}")
        with col_nome:
            colaborador_value = st.text_input("Nome Completo", key=f"saida_insumos_colaborador_{ri}")
        st.markdown("---")
        coordenador = st.text_input("Coordenador", key=f"saida_insumos_coordenador_{ri}")
        email_coordenador = st.selectbox("E-mail do Coordenador", options=[""] + coordenadores_emails, key=f"saida_insumos_email_coordenador_{ri}")
        
        # 2. Define a lista de opções com base no perfil
        if perfil_usuario == "visitante":
            opcoes_responsavel = ["COORDENADOR"] # Bloqueia apenas em Coordenador
        else:
            opcoes_responsavel = ["", "ALMOXARIFE", "COORDENADOR", "JOVEM APRENDIZ"]
            
        # 3. Desenha o campo com a lista correta
        responsavel = st.selectbox("Responsável", opcoes_responsavel, key=f"saida_insumos_responsavel_{ri}")
        
        if perfil_usuario == "visitante":
            opcoes_turno = ["", "1° TURNO", "2° TURNO"] # Bloqueia apenas em ADM
        else:
            opcoes_turno = ["", "ADM", "1° TURNO", "2° TURNO"]
        turno = st.selectbox("Turno", opcoes_turno, key=f"saida_insumos_turno_{ri}")

        centro_de_custo = st.selectbox("Centro de Custo", ["", "RC", "3P"], key=f"saida_insumos_centro_de_custo_{ri}")

        if perfil_usuario == "visitante":
            opcoes_insumo = ["BICO DE PATO", "REFIL DO BICO DE PATO" "RIBBON CERA EASY WAX 110X450",
                            "FOLHA SULFITE A4", "FITA DUREX 45MMX100M","ETIQUETA TERMICA 100X150", 
                            "EMBALAGEM PP 320X400", "EMBALAGEM P 380X450", "EMBALAGEM M 380X470", 
                            "EMABALAGEM G 500X600", "EMBALAGEM EXG 1000X600"] # Bloqueia a seleção de insumos para visitantes
        else:
            opcoes_insumo = insumo_names

        st.markdown("---")
        for i in range(num_itens):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.selectbox(f"Insumo #{i+1}", [""] + opcoes_insumo, key=f"saida_insumos_item_nome_{i}_{ri}", disabled=(not opcoes_insumo))
            with col2:
                st.text_input(f"Tamanho #{i+1}", placeholder="ÚNICO", key=f"saida_insumos_item_tam_{i}_{ri}")
            with col3:
                st.number_input(f"Qtd #{i+1}", min_value=1, value=1, key=f"saida_insumos_item_qtd_{i}_{ri}")
        

        enviar = st.form_submit_button("Registrar Saída de Insumos", type="primary")

    # A lógica de envio fica FORA do 'with st.form'
    if enviar:
        # Coleta de dados do formulário
        cpf_value = st.session_state.get(f"saida_insumos_cpf_{ri}", "")
        coordenador_value = st.session_state.get(f"saida_insumos_coordenador_{ri}", "")
        colaborador_value = st.session_state.get(f"saida_insumos_colaborador_{ri}", "")
        responsavel_value = st.session_state.get(f"saida_insumos_responsavel_{ri}", "")
        email_value = st.session_state.get(f"saida_insumos_email_coordenador_{ri}", "")
        turno_value = st.session_state.get(f"saida_insumos_turno_{ri}", "")
        centro_value = st.session_state.get(f"saida_insumos_centro_de_custo_{ri}", "")

        itens_final = []
        num_itens_registrados = st.session_state.get(f"saida_insumos_num_itens_{ri}", 1)
        for i in range(num_itens_registrados):
            escolha = st.session_state.get(f"saida_insumos_item_nome_{i}_{ri}", "")
            tam = st.session_state.get(f"saida_insumos_item_tam_{i}_{ri}", "")
            qtd = st.session_state.get(f"saida_insumos_item_qtd_{i}_{ri}", 1)
            if escolha:
                itens_final.append((escolha, tam, int(qtd)))

        # Validações com st.stop()
        if not cpf_value: 
            st.error("O campo 'CPF' é obrigatório.")
            st.stop()
        elif not cpf_value.isdigit() or len(cpf_value) != 11:
            st.error("⚠️ O CPF deve conter exatamente 11 números (sem pontos ou traços).")
            st.stop()
        if not centro_value: st.error("O campo 'Centro de Custo' é obrigatório."); st.stop()
        if not itens_final: st.error("Preencha pelo menos um insumo."); st.stop()
        if not email_value or email_value == "Nenhum e-mail cadastrado": st.error("Selecione um e-mail válido."); st.stop()
        if not colaborador_value: st.error("O campo 'Colaborador' é obrigatório."); st.stop()
        # if not coordenador_value: st.error("O campo 'Coordenador' é obrigatório."); st.stop()
        
        perfil_usuario = st.session_state.get("user_role", "visitante")
        if perfil_usuario in ["admin", "almoxarife"]:
            ok, err = registrar_saida_insumos(
                cpf=cpf_value, 
                coordenador=coordenador_value, 
                colaborador=colaborador_value,
                responsavel=responsavel_value, 
                email_coordenador=email_value,
                turno=turno_value, 
                centro_de_custo=centro_value, 
                itens_saida=itens_final
            )

            if not ok: st.error(f"Erro ao salvar no banco: {err}"); st.stop()

            st.success("✅ Saída de insumos registrada com sucesso!")

            # Baixa no estoque
            erros_estoque = []
            for nome, tam, qtd in itens_final:
                sucesso_estoque, msg_estoque = atualizar_estoque(
                    item_nome=nome, 
                    tamanho=tam, 
                    status="NOVO", 
                    tipo="INSUMO",
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
        else:
            # ---------------------------------------------------
            # ROTA 2: VISITANTE (Vai para Quarentena / Pendentes)
            # ---------------------------------------------------
            ok, err = registrar_saida_insumos_pendente(
                colaborador=colaborador_value, 
                cpf=cpf_value, 
                coordenador=coordenador_value,
                email_coordenador=email_value, 
                responsavel=responsavel_value, 
                turno=turno_value,
                centro_de_custo=centro_value, 
                itens_saida=itens_final,
            )

            if not ok: st.error(f"Erro ao enviar solicitação: {err}"); st.stop()

            st.success("⏳ Solicitação de Saída enviada com sucesso! Aguardando aprovação do Almoxarifado.")
            st.info("O estoque e o relatório só serão atualizados após a aprovação.")


        # =======================================================
        # SINALIZA SUCESSO E RESETA TODO O FORMULÁRIO
        # =======================================================
        st.session_state.reset_insumo += 1
        time.sleep(4)
        st.rerun()






