# Em email_utils.py (VERSÃO PARA NUVEM)
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def enviar_email_smtp(assunto, corpo_html, destinatario):
    """
    Função para enviar e-mails usando um servidor SMTP com modo de depuração.
    """
    try:
        remetente = st.secrets["email_remetente"]
        senha = st.secrets["senha_remetente"]

        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo_html, 'html'))

        print("--- INICIANDO ENVIO DE E-MAIL ---")
        print(f"De: {remetente}")
        print(f"Para: {destinatario}")
        print("DEBUG: Conectando ao servidor smtp.gmail.com:465...")

        # --- Bloco de Conexão Corrigido para Office 365 ---
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()  # Inicia a criptografia (TLS)
        server.login(remetente, senha)
        server.send_message(msg)
        server.quit()
        # --- Fim do Bloco Corrigido ---

        return True, "E-mail processado com sucesso (sem erros no Python)."

    except Exception as e:
        print(f"!!!!!!!!!! DEBUG: OCORREU UM ERRO !!!!!!!!!!")
        print(e)
        return False, f"Falha ao enviar e-mail via SMTP: {e}"



def enviar_email_saida_epi(coordenador=None, colaborador=None, responsavel=None,
                           motivo=None, status=None, efetivo=None, centro_de_custo=None, turno=None,
                           itens_saida=None, email_coordenador=None, cpf=None):
    """
    Esta função agora apenas MONTA o conteúdo do e-mail e depois
    chama a função 'enviar_email_smtp' para fazer o envio.
    """
    try:
        if not email_coordenador or "@" not in email_coordenador:
            return False, "E-mail do coordenador inválido."

        # --- 1. Montagem do Conteúdo (Lógica que você já tinha) ---
        itens_saida = itens_saida or []
        data_hora_obj = datetime.now()
        data_hora_str = data_hora_obj.strftime("%d/%m/%Y %H:%M:%S")
        
        endereco_texto = """
        DHL Supply Chain<br>
        GLP Guarulhos II - R. Concretex, 800<br>
        Cumbica, Guarulhos - SP.<br>
        CEP: 07232-050, Brasil
        """
        
        body_rows = ""
        for nome, tam, qtd in itens_saida:
            body_rows += (
                "<tr>"
                f"<td style='padding:3px 6px;border-bottom:1px solid #ccc; width: 160px;text-align:left;'>{nome}</td>"
                f"<td style='padding:6px 6px;border-bottom:1px solid #ccc; width: 80px;text-align:center;'>{tam or '-'}</td>"
                f"<td style='padding:6px 6px;border-bottom:1px solid #ccc; width: 70px;text-align:center;'>{qtd}</td>"
                "</tr>"
            )

        if not body_rows:
            body_rows = "<tr><td colspan='3'>Nenhum item listado.</td></tr>"

        corpo_html = f"""
        <div style="font-family:Calibri, Arial, sans-serif;font-size:11pt;color:#111;">
          <p>Olá <b>{(coordenador or '').upper()}</b>,</p>
          <p>Saída de EPI registrada para <b>{(colaborador or '').upper()}</b>.</p>
          <b>CPF:</b> {cpf or '-'}<br>
          <b>Responsável:</b> {responsavel or '-'}<br>
          <b>Turno:</b> {turno or '-'}<br>
          <b>Centro de Custo:</b> {centro_de_custo or '-'}<br>
          <b>Motivo:</b> {motivo or '-'}<br>
          <b>Status:</b> {status or '-'}<br>
          <b>Efetivo:</b> {efetivo or '-'}<br>
          <b>Data:</b> {data_hora_str}<br><br>

          <table style="border-collapse:collapse;width:auto;font-size:11pt;">
            <thead>
              <tr style="background:#f0f0f0;">
                <th style='text-align:left;padding:4px 6px;border-bottom:1px solid #ccc; width: 160px;'>Item</th>
                <th style='text-align:center;padding:10px 6px;border-bottom:1px solid #ccc; width: 80px;'>Tam</th>
                <th style='text-align:center;padding:10px 6px;border-bottom:1px solid #ccc; width: 70px;'>Qtd</th>
              </tr>
            </thead>
            <tbody>
              {body_rows}
            </tbody>
          </table>
          <p>Atenciosamente,<br>Setor de Almoxarifado.</p>
          <p><b>{endereco_texto}</b></p>
        </div>
        """
        
        assunto = f"Saída de EPI — {(colaborador or '').upper()} — {data_hora_obj.strftime('%d/%m/%Y')}"

        # --- 2. Chamada da Função Universal de Envio ---
        return enviar_email_smtp(assunto, corpo_html, email_coordenador)

    except Exception as exc:
        return False, f"Erro ao preparar o conteúdo do e-mail: {exc}"


def enviar_email_saida_insumos(cpf, coordenador, colaborador, responsavel, email_coordenador, itens, centro_de_custo, turno=None):
    """
    Monta o conteúdo do e-mail de saída de insumos e chama a função de envio SMTP.
    """
    try:
        if not email_coordenador or "@" not in email_coordenador:
            return False, "E-mail do coordenador inválido."

        # --- 1. Montagem do Conteúdo (Lógica que você já tinha) ---
        data_hora_obj = datetime.now()
        data_hora_str = data_hora_obj.strftime("%d/%m/%Y %H:%M")
        
        endereco_texto = """
        DHL Supply Chain<br>
        GLP Guarulhos II - R. Concretex, 800<br>
        Cumbica, Guarulhos - SP.<br>
        CEP: 07232-050, Brasil
        """

        body_rows = ""
        for nome, tam, qtd in itens:
            body_rows += (
                "<tr>"
                f"<td style='padding:4px 8px;border-bottom:1px solid #ccc; width:220px;text-align:left;'>{(nome or '').upper()}</td>"
                f"<td style='padding:4px 8px;border-bottom:1px solid #ccc; width:100px;text-align:center;'>{(tam or '-').upper()}</td>"
                f"<td style='padding:4px 8px;border-bottom:1px solid #ccc; width:80px;text-align:center;'>{qtd}</td>"
                "</tr>"
            )

        if not body_rows:
            body_rows = "<tr><td colspan='3'>Nenhum insumo listado.</td></tr>"

        turno_html = f"<b>Turno:</b> {turno}<br>" if turno else ""

        corpo_html = f"""
        <div style="font-family:Calibri, Arial, sans-serif;font-size:11pt;color:#111;">
          <p>Olá <b>{(coordenador or '').upper()}</b>,</p>
          <p>Foi registrada a saída de insumos para <b>{(colaborador or '').upper()}</b>.</p>
          <b>CPF:</b> {cpf or '-'}<br>
          <b>Responsável:</b> {responsavel or '-'}<br>
          {turno_html}
          <b>Centro de Custo:</b> {centro_de_custo or '-'}<br>
          <b>Data:</b> {data_hora_str}<br><br>

          <table style="border-collapse:collapse;width:auto;font-size:11pt;">
            <thead>
              <tr style="background:#f0f0f0;">
                <th style='text-align:left;padding:6px;border-bottom:1px solid #ccc; width:220px;'>Insumo</th>
                <th style='text-align:center;padding:6px;border-bottom:1px solid #ccc; width:100px;'>Tamanho</th>
                <th style='text-align:center;padding:6px;border-bottom:1px solid #ccc; width:80px;'>Qtd</th>
              </tr>
            </thead>
            <tbody>
              {body_rows}
            </tbody>
          </table>
          <p>Atenciosamente,<br>Setor de Almoxarifado.</p>
          <p><b>{endereco_texto}</b></p>
        </div>
        """

        assunto = f"Saída de Insumos - {(colaborador or '').upper()} - {data_hora_obj.strftime('%d/%m/%Y')}"

        # --- 2. Chamada da Função Universal de Envio ---
        return enviar_email_smtp(assunto, corpo_html, email_coordenador)

    except Exception as exc:
        return False, f"Erro ao preparar o conteúdo do e-mail de saída de insumos: {exc}"


def enviar_email_emprestimo(cpf, coordenador, colaborador, responsavel, email_coordenador, itens, status, centro_de_custo, turno=None):
    try:
        if not email_coordenador or "@" not in email_coordenador:
            return False, "E-mail do coordenador inválido."

        # --- 1. Montagem do Conteúdo (Lógica que você já tinha) ---
        data_hora_obj = datetime.now()
        data_hora_str = data_hora_obj.strftime("%d/%m/%Y %H:%M")

        endereco_texto = """
DHL Supply Chain<br>
GLP Guarulhos II - R. Concretex, 800<br>
Cumbica<br>
Guarulhos - SP.<br>
CEP: 07232-050<br>
Brasil
"""
        body_rows = ""
        for nome, tam, qtd in itens:
            body_rows += (
                "<tr>"
                f"<td style='padding:3px 6px;border-bottom:1px solid #ccc; width: 220px;text-align:left;'>{(nome or '').upper()}</td>"
                f"<td style='padding:6px 6px;border-bottom:1px solid #ccc; width: 100px;text-align:center;'>{(tam or '-').upper()}</td>"
                f"<td style='padding:6px 6px;border-bottom:1px solid #ccc; width: 80px;text-align:center;'>{qtd or '-'}</td>"
                "</tr>"
            )

        if not body_rows:
            body_rows = "<tr><td colspan='3'>Nenhum item listado.</td></tr>"

        turno_html = f"<b>Turno:</b> {turno}<br>" if turno else ""
        corpo_html = f"""
        <div style="font-family:Calibri, Arial, sans-serif;font-size:11pt;color:#111;">
          <p>Olá <b>{(coordenador or '').upper()}</b>,</p>
          <p>Foi registrado um empréstimo para o colaborador <b>{(colaborador or '').upper()}</b>.</p>
          <b>Responsável:</b> {responsavel or '-'}<br>
          {turno_html}
          <b>Status:</b> {status}<br>
          <b>Centro de Custo:</b> {centro_de_custo}<br>
          <b>Data:</b> {data_hora_str}<br><br>

          <table style="border-collapse:collapse;width:auto;font-size:11pt;">
            <thead>
              <tr style="background:#f0f0f0;">
                <th style='text-align:left;padding:4px 6px;border-bottom:1px solid #ccc; width: 220px;'>Item</th>
                <th style='text-align:center;padding:10px 6px;border-bottom:1px solid #ccc; width: 100px;'>Tamanho</th>
                <th style='text-align:center;padding:10px 6px;border-bottom:1px solid #ccc; width: 80px;'>Qtd</th>
              </tr>
            </thead>
            <tbody>
              {body_rows}
            </tbody>
          </table>
          <p>Atenciosamente,<br>
          Setor de Almoxarifado.</p>
          <p><b>{endereco_texto}</b></p>
        </div>
        """
        assunto = f"Empréstimo - {(colaborador or '').upper()} - {data_hora_obj.strftime('%d/%m/%Y')}"

        # --- 2. Chamada da Função Universal de Envio ---
        return enviar_email_smtp(assunto, corpo_html, email_coordenador)

    except Exception as exc:
        return False, f"Erro ao preparar o conteúdo do e-mail de saída de insumos: {exc}"
                
            
def enviar_email_devolucao(cpf, coordenador, colaborador, responsavel, email_coordenador, itens, status, motivo, centro_de_custo, turno=None,):
    try:
        if not email_coordenador or "@" not in email_coordenador:
            return False, "E-mail do coordenador inválido."

        # --- 1. Montagem do Conteúdo (Lógica que você já tinha) ---
        data_hora_obj = datetime.now()
        data_hora_str = data_hora_obj.strftime("%d/%m/%Y %H:%M")

        endereco_texto = """
DHL Supply Chain<br>
GLP Guarulhos II - R. Concretex, 800<br>
Cumbica<br>
Guarulhos - SP.<br>
CEP: 07232-050<br>
Brasil
"""
        body_rows = ""
        for nome, tam, qtd in itens:
            body_rows += (
                "<tr>"
                f"<td style='padding:4px 8px;border-bottom:1px solid #ccc; width:220px;text-align:left;'>{(nome or '').upper()}</td>"
                f"<td style='padding:4px 8px;border-bottom:1px solid #ccc; width:100px;text-align:center;'>{(tam or '-').upper()}</td>"
                f"<td style='padding:4px 8px;border-bottom:1px solid #ccc; width:80px;text-align:center;'>{qtd}</td>"
                "</tr>"
            )

        if not body_rows:
            body_rows = "<tr><td colspan='3'>Nenhum item listado.</td></tr>"

        turno_html = f"<b>Turno:</b> {turno}<br>" if turno else ""

        corpo_html = f"""
        <div style="font-family:Calibri, Arial, sans-serif;font-size:11pt;color:#111;">
          <p>Olá <b>{(coordenador or '').upper()}</b>,</p>
          <p>Foi registrada a devolução para o colaborador <b>{(colaborador or '').upper()}</b>.</p>
          <b>Responsável:</b> {responsavel or '-'}<br>
          {turno_html}
          <b>Status:</b> {status}<br>
          <b>Motivo:</b> {motivo}<br>
          <b>Centro de Custo:</b> {centro_de_custo}<br>
          <b>Data:</b> {data_hora_str}<br><br>

          <table style="border-collapse:collapse;width:auto;font-size:11pt;">
            <thead>
              <tr style="background:#f0f0f0;">
                <th style='text-align:left;padding:6px;border-bottom:1px solid #ccc; width:220px;'>Item</th>
                <th style='text-align:center;padding:6px;border-bottom:1px solid #ccc; width:100px;'>Tamanho</th>
                <th style='text-align:center;padding:6px;border-bottom:1px solid #ccc; width:80px;'>Qtd</th>
              </tr>
            </thead>
            <tbody>
              {body_rows}
            </tbody>
          </table>
          <p>Atenciosamente,<br>
          Setor de Almoxarifado.</p>
          <p><b>{endereco_texto}</b></p>
        </div>
        """

        assunto = f"Devolução - {(colaborador or '').upper()} - {data_hora_obj.strftime('%d/%m/%Y')}"

        # --- 2. Chamada da Função Universal de Envio ---
        return enviar_email_smtp(assunto, corpo_html, email_coordenador)

    except Exception as exc:
        return False, f"Erro ao preparar o conteúdo do e-mail de saída de insumos: {exc}"


def enviar_email_coordenador(coordenador, email):
    """
    Monta o e-mail de confirmação de cadastro de coordenador e chama a função de envio SMTP.
    """
    try:
        # --- 1. Montagem do Conteúdo ---
        data_hora_obj = datetime.now()
        data_hora_str = data_hora_obj.strftime("%d/%m/%Y %H:%M:%S")

        endereco_texto = """
        DHL Supply Chain<br>
        GLP Guarulhos II - R. Concretex, 800<br>
        Cumbica, Guarulhos - SP.<br>
        CEP: 07232-050, Brasil
        """

        corpo_html = f"""
        <div style="font-family:Calibri, Arial, sans-serif;font-size:11pt;color:#111;">
          <p>Prezado(a) <b>{(coordenador or '').upper()}</b>,</p>
          <p>Seu e-mail <b>({email})</b> foi cadastrado com sucesso no Sistema de Almoxarifado.</p>
          <p>A partir de agora, você receberá notificações automáticas sobre empréstimos,
          devoluções e saídas de insumos relacionados à sua área.</p>
          <p>Se você não realizou este cadastro, por favor, entre em contato com o setor
          de Almoxarifado.</p>
          <p><b>Data do Cadastro:</b> {data_hora_str}</p>
          <p>Atenciosamente,<br>Setor de Almoxarifado.</p>
          <p><b>{endereco_texto}</b></p>
        </div>
        """
        
        assunto = f"Confirmação de Cadastro no Sistema de Almoxarifado - {(coordenador or '').upper()}"
        
        destinatario = email

        # --- 2. Chamada da Função Universal de Envio ---
        return enviar_email_smtp(assunto, corpo_html, destinatario)

    except Exception as exc:

        return False, f"Erro ao preparar o e-mail de cadastro do coordenador: {exc}"
