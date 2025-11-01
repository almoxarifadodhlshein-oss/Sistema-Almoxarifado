# Em menus/saida_epi.py (VERSÃO CORRIGIDA E FINAL)

import time
import streamlit as st
from datetime import datetime
import pytz
# 1. NOVAS IMPORTAÇÕES NECESSÁRIAS
from sqlalchemy import text
from utils.db_connection import connect_db

# Importações dos outros módulos de utilidades
from email_utils import enviar_email_saida_epi
from utils.estoque_db import atualizar_estoque
from utils.itens_db import listar_itens_por_categoria
from utils.coordenadores_db import get_coordenadores

def registrar_saida_epi(colaborador, cpf, coordenador, email_coordenador, responsavel, motivo, status, efetivo, turno, centro_de_custo, itens_saida):
    """Registra a saída de um ou mais EPIs no banco de dados PostgreSQL."""
    engine = connect_db()
    try:
        with engine.connect() as conn:
            fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
            data_atual_obj = datetime.now(fuso_horario_brasilia)
            data_str = data_atual_obj.strftime("%Y-%m-%d %H:%M:%S")
            # 2. SINTAXE DO CREATE TABLE AJUSTADA PARA POSTGRESQL
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS saida_epis (
                    id SERIAL PRIMARY KEY,
                    data TEXT,
                    colaborador TEXT,
                    cpf TEXT,
                    coordenador TEXT,
                    email_coordenador TEXT,
                    responsavel TEXT,
                    motivo TEXT,
                    status TEXT,
                    efetivo TEXT,
                    turno TEXT,
                    centro_de_custo TEXT,
                    item TEXT,
                    tamanho TEXT,
                    quantidade INTEGER
                )
            """))
            
            for item, tamanho, quantidade in itens_saida:
                if not str(item).strip(): continue
                
                query = text("""
                    INSERT INTO saida_epis 
                    (data, colaborador, cpf, coordenador, email_coordenador, responsavel, motivo, status, efetivo, turno, centro_de_custo, item, tamanho, quantidade)
                    VALUES (:data, :colab, :cpf, :coord, :email, :resp, :motivo, :status, :efetivo, :turno, :cc, :item, :tam, :qtd)
                """)
                conn.execute(query, {
                    "data": data_str, "colab": colaborador.strip().upper(), "cpf": cpf.strip(),
                    "coord": coordenador.strip().upper(), "email": email_coordenador.strip(),
                    "resp": responsavel.strip(), "motivo": motivo.strip(), "status": status.strip(),
                    "efetivo": efetivo.strip(), "turno": turno.strip(), "cc": centro_de_custo.strip().upper(),
                    "item": item.strip().upper(), "tam": tamanho.strip().upper() if tamanho else "", "qtd": int(quantidade)
                })
            conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)

def _safe_rerun():
    st.rerun()
# --- FUNÇÃO PRINCIPAL DA PÁGINA ---

def carregar():
    st.subheader("📦 Registro de Saída de EPI")

    # --- Widgets de configuração (fora do formulário) ---
    epi_names = listar_itens_por_categoria("EPI")
    coordenadores_emails = get_coordenadores()

    if not epi_names:
        st.warning("Nenhum EPI encontrado no 'Cadastro de Itens'. Por favor, cadastre os itens primeiro.")
        # Retornamos para não tentar renderizar o formulário sem itens
        return

    # A chave do number_input agora é estática
    num_itens = st.number_input(
        "Quantidade de tipos de EPIs para saída", min_value=1, max_value=10,
        key="saida_epi_num_itens"
    )

    # --- Formulário de Saída ---
    with st.form("saida_epi_form", clear_on_submit=True):
        # Campos gerais do formulário
        cpf = st.text_input("CPF", key="saida_epi_cpf")
        coordenador = st.text_input("Coordenador", key="saida_epi_coordenador")
        colaborador = st.text_input("Colaborador", key="saida_epi_colaborador")
        email_coordenador = st.selectbox("E-mail do Coordenador", options=[""] + coordenadores_emails, key="saida_epi_email_coordenador")
        responsavel = st.selectbox("Responsável", ["AMANDA MESSIAS", "ANDREZZA SABINO", "PAMELA SIMEÃO", "RAFAEL CRISTOVÃO", "SUELI BARBOSA", "ORLANDO ALVES", "JOVEM APRENDIZ"], key="saida_epi_responsavel")
        turno = st.selectbox("Turno", ["ADM", "1° TURNO", "2° TURNO", "3° TURNO"], key="saida_epi_turno")
        centro_de_custo = st.selectbox("Centro de Custo", ["", "RC", "3P"], key="saida_epi_centro_de_custo")
        motivo = st.selectbox("Motivo da Saída", ["PERDA", "1° RETIRADA", "AVARIADO", "ESQUECEU O EPI", "DEVOLUÇÃO", "TROCA DE TAMANHO", "PERÍODO VENCIDO", "MANCHA"], key="saida_epi_motivo")
        efetivo = st.selectbox("Efetivo", ["DHL", "AGÊNCIA"], key="saida_epi_efetivo")
        status_geral = st.selectbox("Status dos Itens Retirados", ["NOVO", "HIGIENIZADO"], key="saida_epi_status_geral")

        st.markdown("---")
        for i in range(num_itens):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.selectbox(f"EPI #{i+1}", [""] + epi_names, key=f"saida_epi_item_nome_{i}", disabled=(not epi_names))
            with col2:
                st.text_input(f"Tamanho #{i+1}", placeholder="ÚNICO", key=f"saida_epi_item_tam_{i}")
            with col3:
                st.number_input(f"Qtd #{i+1}", min_value=1, value=1, key=f"saida_epi_item_qtd_{i}")
        
        enviar = st.form_submit_button("Registrar Saída de EPI")

    # A lógica de envio fica FORA do 'with st.form'
    if enviar:
        # Pega os valores gerais do formulário usando .get() para segurança
        cpf_value = st.session_state.get("saida_epi_cpf", "")
        coordenador_value = st.session_state.get("saida_epi_coordenador", "")
        colaborador_value = st.session_state.get("saida_epi_colaborador", "")
        email_value = st.session_state.get("saida_epi_email_coordenador", "")
        responsavel_value = st.session_state.get("saida_epi_responsavel", "")
        motivo_value = st.session_state.get("saida_epi_motivo", "")
        status_value = st.session_state.get("saida_epi_status_geral", "")
        efetivo_value = st.session_state.get("saida_epi_efetivo", "")
        turno_value = st.session_state.get("saida_epi_turno", "")
        centro_value = st.session_state.get("saida_epi_centro_de_custo", "")

        # Monta a lista de itens a partir do loop do formulário
        itens_final = []
        num_itens_registrados = st.session_state.get("saida_epi_num_itens", 1)
        for i in range(num_itens_registrados):
            escolha = st.session_state.get(f"saida_epi_item_nome_{i}", "")
            tam = st.session_state.get(f"saida_epi_item_tam_{i}", "")
            qtd = st.session_state.get(f"saida_epi_item_qtd_{i}", 1)
            if escolha:
                itens_final.append((escolha, tam, int(qtd)))

        # Validações
        if not centro_value: st.error("O campo 'Centro de Custo' é obrigatório."); return
        if not itens_final: st.error("Preencha pelo menos um EPI."); return
        if not email_value or email_value == "Nenhum e-mail cadastrado": st.error("Selecione um e-mail válido."); return
        if not cpf_value: st.error("Ocampo 'CPF' é obrigatório."); return
        if not colaborador_value: st.error("O campo 'Colaborador' é obrigatório."); return
        if not efetivo_value: st.error("O campo 'Efetivo' é obrigatório."); return
        if not status_value: st.error("O campo 'Status' é obrigatório."); return
        if not coordenador_value: st.error("O campo 'Coordenador' é obrigatório."); return
        
        # Registro no banco de dados de saída
        ok, err = registrar_saida_epi(
            colaborador=colaborador_value, 
            cpf=cpf_value, 
            coordenador=coordenador_value,
            email_coordenador=email_value, 
            responsavel=responsavel_value, 
            motivo=motivo_value,
            status=status_value, 
            efetivo=efetivo_value, 
            turno=turno_value,
            centro_de_custo=centro_value, 
            itens_saida=itens_final
        )

        if not ok: st.error(f"Erro ao salvar no banco de saídas: {err}"); return

        st.success("✅ Saída de EPI registrada com sucesso!")

        # Baixa no banco de estoque
        erros_estoque = []
        for nome, tam, qtd in itens_final:
            sucesso_estoque, msg_estoque = atualizar_estoque(
                item_nome=nome, tamanho=tam, status=status_value,
                tipo="EPI", quantidade_delta=-int(qtd)
            )
            if not sucesso_estoque:
                erros_estoque.append(f"Item '{nome}' ({status_value}): {msg_estoque}")
        
        if erros_estoque:
            st.warning("Saída registrada, mas com erros na baixa de estoque:\n" + "\n".join(erros_estoque))

        # Envio de e-mail
        try:
            sucesso, msg = enviar_email_saida_epi(
                cpf=cpf_value, 
                coordenador=coordenador_value, 
                colaborador=colaborador_value,
                responsavel=responsavel_value, 
                email_coordenador=email_value,
                turno=turno_value, 
                centro_de_custo=centro_value, 
                status=status_value,
                motivo=motivo_value,
                efetivo=efetivo_value,
                itens_saida=itens_final
            )
            if sucesso: st.info(f"📧 {msg}")
            else: st.warning(f"Saída salva, mas e-mail não enviado: {msg}")
        except Exception as exc:
            st.warning(f"Saída salva, mas ocorreu um erro ao preparar o e-mail: {exc}")

        time.sleep(4)

        st.rerun()




