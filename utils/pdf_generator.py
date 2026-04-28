import os
import base64
from fpdf import FPDF

class ReciboEPI(FPDF):
    def header(self):
        pasta_utils = os.path.dirname(os.path.abspath(__file__)) 
        pasta_raiz = os.path.dirname(pasta_utils) 
        caminho_logo = os.path.join(pasta_raiz, "dhl_logo.png") 
        
        if os.path.exists(caminho_logo):
            self.image(caminho_logo, x=10, y=8, w=35)
        
        self.set_y(25)
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "DHL - AUDITORIA DE ITENS", ln=True, align="C")
        self.ln(5)

def gerar_pdf_assinado(nome, cpf, df_saidas, df_emprestimos, df_devolucoes, df_insumos):
    pdf = ReciboEPI()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, f"Colaborador: {nome}", ln=True)
    pdf.cell(0, 8, f"CPF: {cpf}", ln=True)
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    temp_pdf_path = f"temp_relatorio_{cpf}.pdf"
    imagens_temporarias = []

    # --- FUNÇÃO ÚNICA PARA DESENHAR TODAS AS TABELAS NO MESMO PADRÃO ---
    def desenhar_tabela_padrao(titulo, df, tipo_tabela):
        if df.empty:
            return

        # Previne que o título fique isolado no final da página
        if pdf.get_y() > 250:
            pdf.add_page()

        pdf.ln(2)
        pdf.set_font("Arial", "B", 11)
        # Usamos ln=1 aqui para garantir a quebra de linha do título
        pdf.cell(0, 8, titulo, ln=1) 
        
        nome_coluna_extra = "Motivo" if tipo_tabela == "SAIDA_EPI" else "Status"

        # Cabeçalho da Tabela
        pdf.set_font("Arial", "B", 8)
        pdf.cell(30, 7, "Data", border=1)
        pdf.cell(25, 7, "Tipo", border=1)  
        pdf.cell(60, 7, "Item / Produto", border=1)
        pdf.cell(10, 7, "Qtd", border=1, align="C")
        pdf.cell(30, 7, nome_coluna_extra, border=1) 
        # O ln=1 no final do cabeçalho força a quebra de forma segura
        pdf.cell(35, 7, "Assinatura", border=1, align="C", ln=1) 

        pdf.set_font("Arial", "", 8)
        for idx, (_, row) in enumerate(df.iterrows()):
            tem_assinatura = False
            ass_b64 = row.get('assinatura')
            if tipo_tabela == "SAIDA_EPI" and ass_b64 and isinstance(ass_b64, str) and "," in ass_b64:
                tem_assinatura = True

            altura_linha = 16 if tem_assinatura else 8
            
            # TRAVA DE SEGURANÇA: Se a linha for bater no rodapé, vira a página ANTES de desenhar
            if pdf.get_y() + altura_linha > 275: 
                pdf.add_page()
                
            # Guardamos as coordenadas exatas do momento
            x_start = pdf.get_x()
            y_start = pdf.get_y()

            # Extração Básica
            data_val = str(row.get('data', '-'))[:16]
            produto_val = str(row.get('item', row.get('insumo', '-')))[:32]
            qtd_val = str(row.get('quantidade', '-'))

            # A MÁGICA DOS DADOS
            if tipo_tabela == "SAIDA_EPI":
                extra_val = str(row.get('motivo', '-'))[:15]
            elif tipo_tabela == "EMPRESTIMO" or tipo_tabela == "DEVOLUCAO":
                extra_val = str(row.get('status_item', '-'))[:15]
            else: # INSUMOS
                extra_val = "-"

            # Nome visível na coluna "Tipo"
            if tipo_tabela == "SAIDA_EPI": tipo_nome = "EPI (Saida)"
            elif tipo_tabela == "EMPRESTIMO": tipo_nome = "Emprestimo"
            elif tipo_tabela == "DEVOLUCAO": tipo_nome = "Devolucao"
            else: tipo_nome = "Insumo"

            # Desenhando as células
            pdf.cell(30, altura_linha, data_val, border=1)
            pdf.cell(25, altura_linha, tipo_nome, border=1)
            pdf.cell(60, altura_linha, produto_val, border=1)
            pdf.cell(10, altura_linha, qtd_val, border=1, align="C")
            pdf.cell(30, altura_linha, extra_val, border=1)
            pdf.cell(35, altura_linha, "" if tem_assinatura else "-", border=1, align="C")
            
            if tem_assinatura:
                try:
                    temp_img_path = f"temp_ass_{cpf}_{tipo_tabela}_{idx}.png"
                    imagens_temporarias.append(temp_img_path) 
                    
                    header, encoded = ass_b64.split(",", 1)
                    img_data = base64.b64decode(encoded)
                    with open(temp_img_path, "wb") as f:
                        f.write(img_data)
                    
                    img_x = x_start + 156
                    pdf.image(temp_img_path, x=img_x, y=y_start + 1, w=33, h=14)
                except Exception:
                    pdf.text(x_start + 160, y_start + 9, "[Erro]")
            
            # =======================================================
            # A CURA DA BAGUNÇA: Força o cursor a voltar para o lugar certo
            # X = 10 (margem esquerda absoluta)
            # Y = y_start + altura_linha (exatamente abaixo da última célula)
            # =======================================================
            pdf.set_xy(10, y_start + altura_linha)
    # 1. Manda a máquina desenhar os 4 blocos
    desenhar_tabela_padrao("1. HISTORICO DE SAIDAS DE EPI", df_saidas, "SAIDA_EPI")
    desenhar_tabela_padrao("2. HISTORICO DE EMPRESTIMOS", df_emprestimos, "EMPRESTIMO")
    desenhar_tabela_padrao("3. HISTORICO DE DEVOLUCOES", df_devolucoes, "DEVOLUCAO")
    desenhar_tabela_padrao("4. HISTORICO DE INSUMOS", df_insumos, "INSUMO")

    # 2. Salva o documento fisicamente
    pdf.output(temp_pdf_path) 
    
    # 3. Lê o documento em formato de "bytes" para o Streamlit entender
    with open(temp_pdf_path, "rb") as f:
        pdf_bytes = f.read() 
        
    # 4. Limpa os arquivos temporários para não lotar o computador
    if os.path.exists(temp_pdf_path): 
        os.remove(temp_pdf_path)
        
    for img_path in imagens_temporarias:
        if os.path.exists(img_path): 
            os.remove(img_path)
            
    # 5. ENTREGA O ARQUIVO PARA O BOTÃO! (Acaba com o erro NoneType)
    return pdf_bytes