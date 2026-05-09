import sqlite3
from datetime import datetime
import pandas as pd
from sqlalchemy import text
from utils.db_connection import connect_db
import json
import pytz
from datetime import datetime
from sqlalchemy import text
# (Mantenha os seus imports do engine / connect_db)

def registrar_saida_epi_pendente(colaborador, cpf, coordenador, email_coordenador, responsavel, motivo, status, efetivo, turno, centro_de_custo, itens_saida, assinatura_b64):
    engine = connect_db()
    try:
        with engine.connect() as conn:
            fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
            data_atual_obj = datetime.now(fuso_horario_brasilia)
            data_str = data_atual_obj.strftime("%Y-%m-%d %H:%M:%S")
            
            # Cria a tabela de PENDENTES (estrutura adaptada para agrupar o pedido)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pendentes_saida_epis (
                    id SERIAL PRIMARY KEY,
                    data TEXT,
                    colaborador TEXT,
                    cpf TEXT,
                    coordenador TEXT,
                    email_coordenador TEXT,
                    responsavel TEXT,
                    motivo TEXT,
                    status_global TEXT,
                    efetivo TEXT,
                    turno TEXT,
                    centro_de_custo TEXT,
                    itens_json TEXT, -- Guardamos a lista completa de itens aqui
                    assinatura TEXT
                )
            """))
            
            # Converte a lista de itens [(nome, tam, qtd, status), ...] em texto JSON
            itens_str = json.dumps(itens_saida)
            
            query = text("""
                INSERT INTO pendentes_saida_epis 
                (data, colaborador, cpf, coordenador, email_coordenador, responsavel, motivo, status_global, efetivo, turno, centro_de_custo, itens_json, assinatura)
                VALUES (:data, :colab, :cpf, :coord, :email, :resp, :motivo, :status, :efetivo, :turno, :cc, :itens, :ass)
            """)
            
            conn.execute(query, {
                "data": data_str, 
                "colab": colaborador.strip().upper(), 
                "cpf": str(cpf).strip(),
                "coord": coordenador.strip().upper(), 
                "email": email_coordenador.strip(),
                "resp": responsavel.strip().upper(), 
                "motivo": motivo.strip(), 
                "status": status.strip() if status else "",
                "efetivo": efetivo.strip(), 
                "turno": turno.strip(), 
                "cc": centro_de_custo.strip().upper(),
                "itens": itens_str, 
                "ass": assinatura_b64
            })
            
            conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)

# ----------------- SAÍDA DE EPIs --------------------
def registrar_saida_epi(cpf, coordenador, colaborador, item, turno, quantidade, tamanho,
                        responsavel, email_coordenador, motivo, status, efetivo):
    conn = sqlite3.connect('banco de dados/saidadeepis.db')
    c = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO saida_epis (
            cpf, coordenador, colaborador, item, turno, quantidade, tamanho,
            responsavel, email_coordenador, motivo, status, efetivo, data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (cpf, coordenador, colaborador, item, turno, quantidade, tamanho,
          responsavel, email_coordenador, motivo, status, efetivo, data))
    conn.commit()
    conn.close()

# ----------------- SAÍDA DE INSUMOS --------------------
def registrar_saida_insumos(cpf, coordenador, colaborador, item, turno, quantidade, tamanho,
                            responsavel, email_coordenador, data):
    conn = sqlite3.connect('banco de dados/insumos.db')
    c = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO saida_insumos (
              cpf, coordenador, colaborador, item, turno, quantidade,
              tamanho, responsavel, email_coordenador, data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cpf, coordenador, colaborador, item, turno, quantidade,
              tamanho, responsavel, email_coordenador, data))
    conn.commit()
    conn.close()

# ----------------- EMPRÉSTIMO --------------------
def registrar_emprestimo(cpf, coordenador, colaborador, item, turno, quantidade,
                         tamanho, responsavel, email_coordenador, data):
    conn = sqlite3.connect('banco de dados/emprestimo.db')
    c = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO emprestimos (
              cpf, coordenador, colaborador, item, turno, quantidade,
                tamanho, responsavel, email_coordenador, data
            ) VALUES (?, ?, ?, ?)
    ''', (cpf, coordenador, colaborador, item, turno, quantidade,
            tamanho, responsavel, email_coordenador, data))
    conn.commit()
    conn.close()

# ----------------- DEVOLUÇÃO --------------------
def registrar_devolucao(cpf, coordenador, colaborador, item, turno, quantidade,
                         tamanho, responsavel, email_coordenador, data):
    conn = sqlite3.connect('banco de dados/devolucoes.db')
    c = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO devolucoes (
            cpf, coordenador, colaborador, item, turno, quantidade,
            tamanho, responsavel, email_coordenador, data
        ) VALUES (?, ?, ?, ?)
    ''', (cpf, coordenador, colaborador, item, turno, quantidade,
         tamanho, responsavel, email_coordenador, data))
    conn.commit()
    conn.close()

