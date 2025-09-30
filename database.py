import sqlite3
from datetime import datetime
import pandas as pd

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

