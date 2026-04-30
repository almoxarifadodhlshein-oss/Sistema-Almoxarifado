import os
import base64
from fpdf import FPDF

def gerar_pdf_assinado(nome, cpf, df_saidas, df_emprestimos, df_devolucoes, df_insumos):
    # Removemos a classe antiga para termos controle total da 1ª página
    pdf = FPDF()
    pdf.add_page()
    
    pasta_utils = os.path.dirname(os.path.abspath(__file__)) 
    pasta_raiz = os.path.dirname(pasta_utils) 
    
    # Tenta puxar o logo (usando "dhl_logo.png" que apareceu num erro seu, ou "logo.png")
    caminho_logo_dhl = os.path.join(pasta_raiz, "dhl_logo.png") 
    caminho_logo_normal = os.path.join(pasta_raiz, "logo.png")
    caminho_logo = caminho_logo_dhl if os.path.exists(caminho_logo_dhl) else caminho_logo_normal

    # =======================================================
    # NOVO CABEÇALHO CORPORATIVO (TERMO DE RESPONSABILIDADE)
    # =======================================================
    x_start = pdf.get_x() # 10
    y_start = pdf.get_y() # 10
    
    # --- Linha 1: Títulos e Logo ---
    pdf.set_font("Arial", "B", 13)
    pdf.rect(10, y_start, 145, 16) # Caixa do Título
    pdf.set_xy(10, y_start + 2)
    pdf.cell(145, 6, "REGISTRO DE DEVOLUCAO DE EPI - EQUIPAMENTO DE", border=0, align="C", ln=1)
    pdf.set_xy(10, y_start + 8)
    pdf.cell(145, 6, "PROTECAO INDIVIDUAL", border=0, align="C")
    
    pdf.rect(155, y_start, 45, 16) # Caixa do Logo
    if os.path.exists(caminho_logo):
        # Injeta o logo perfeitamente centralizado na caixa da direita
        pdf.image(caminho_logo, x=158.5, y=y_start - 4.0, w=38)
        
    pdf.set_xy(10, y_start + 16)
    
    # --- Linha 2: ANEXO A ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(190, 6, "ANEXO: A", border=1, align="C", fill=True, ln=1)
    
    # --- Linha 3: Colaborador e Registro ---
    y_linha3 = pdf.get_y()
    pdf.rect(10, y_linha3, 145, 12)
    pdf.rect(155, y_linha3, 45, 12)
    
    pdf.set_xy(10, y_linha3 + 1)
    pdf.cell(145, 5, f"COLABORADOR: {nome}", border=0, align="L")
    
    pdf.set_xy(155, y_linha3 + 1)
    pdf.cell(45, 5, f"CPF: {cpf}", border=0, align="L")
    
    pdf.set_xy(10, y_linha3 + 12)
    
    # --- Linha 4: Função, Admissão, Demissão ---
    y_linha4 = pdf.get_y()
    pdf.rect(10, y_linha4, 95, 12)
    pdf.rect(105, y_linha4, 47, 12)
    pdf.rect(152, y_linha4, 48, 12)
    
    pdf.set_xy(10, y_linha4 + 1)
    pdf.cell(95, 5, "FUNCAO:", border=0, align="L")
    
    pdf.set_xy(105, y_linha4 + 1)
    pdf.cell(47, 5, "DATA DE ADMISSAO:", border=0, align="L")
    
    pdf.set_xy(152, y_linha4 + 1)
    pdf.cell(48, 5, "DATA DE DEMISSAO:", border=0, align="L")
    
    pdf.set_xy(10, y_linha4 + 12)
    
    # --- Linha 5: TERMO DE RESPONSABILIDADE ---
    pdf.set_font("Arial", "B", 10)
    pdf.cell(190, 7, "TERMO DE RESPONSABILIDADE", border=1, align="C", ln=1)
    
    # --- Linha 6: Texto Legal e Obrigatório ---
    texto_termo = (
        "Pelo presente declaro ter recebido os EPI's abaixo relacionados, comprometendo-me a utilizá-los de acordo com a finalidade a que se "
        "destinam, responsabilizando-me pela sua guarda e conservação, comunicando à empresa qualquer alteração que torne impróprio o seu "
        "uso. Declaro ainda ter sido treinado quanto ao uso correto dos EPI's abaixo relacionados, bem como, cientificado da obrigatoriedade do "
        "uso deles, comprometendo-me ainda a devolvê-los quando danificado ou ao término do contrato de trabalho, em cumprimento ao "
        "disposto nas letras \"A\" e \"B\", do item 1.8 e item 1.8.1 da NR 01 e item 6.7 e 6.7.1 letras \"A\", \"B\", \"C\" da NR 06 da Portaria 3214 de 08/06/78 "
        "do MTE bem como disposto na CLT Arts 157, 158, 166 e 167. Declaro ainda que concordo expressamente com minha responsabilidade "
        "única e pessoal em sua(s) conservação(ões) mantendo-o(s) em perfeito estado de uso. Fui comunicado ainda sobre minha obrigação na "
        "respectiva reposição do(s) EPI(s) quando por negligência ou propositalmente ocorrer a perda ou danificação dele(s)."
    )
    pdf.set_font("Arial", "", 8)

    # Proteção de conversão de caracteres para evitar crash na nuvem (latin-1)
    texto_seguro = texto_termo.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(190, 4, texto_seguro, border="LTR", align="J")
    
    y_ass = pdf.get_y()

    # MODIFICAÇÃO 2: Cria um bloco vazio de 22mm de altura e fecha com "LBR" (Left, Bottom, Right)
    pdf.cell(190, 22, "", border="LBR", ln=1)
    
    # --- Linha de Assinatura ---
    pdf.line(35, y_ass + 14, 115, y_ass + 14) # Desenha a linha física com o "lápis" do PDF
    pdf.set_xy(35, y_ass + 15)
    pdf.set_font("Arial", "", 8)
    # Já colocamos o nome do colaborador debaixo da linha para ficar ainda mais oficial
    pdf.cell(80, 4, f"Assinatura do Colaborador: {nome}", align="C")
    
    # --- Linha de Data ---
    pdf.line(145, y_ass + 14, 175, y_ass + 14)
    pdf.set_xy(145, y_ass + 15)
    pdf.cell(30, 4, "Data", align="C")
    
    # Devolve o cursor para o lugar certo para as tabelas começarem
    pdf.set_xy(10, y_ass + 22)
    pdf.ln(5)

    # =======================================================
    # FIM DO CABEÇALHO. DAQUI PARA BAIXO O CÓDIGO É O MESMO
    # =======================================================

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
        pdf.cell(0, 8, titulo, ln=1) 
        
        nome_coluna_extra = "Motivo" if tipo_tabela == "SAIDA_EPI" else "Status"

        # Cabeçalho da Tabela
        pdf.set_font("Arial", "B", 8)
        pdf.cell(30, 7, "Data", border=1)
        pdf.cell(25, 7, "Tipo", border=1)  
        pdf.cell(60, 7, "Item / Produto", border=1)
        pdf.cell(10, 7, "Qtd", border=1, align="C")
        pdf.cell(30, 7, nome_coluna_extra, border=1) 
        pdf.cell(35, 7, "Assinatura", border=1, align="C", ln=1) 

        pdf.set_font("Arial", "", 8)
        for idx, (_, row) in enumerate(df.iterrows()):
            tem_assinatura = False
            ass_b64 = row.get('assinatura')
            if tipo_tabela == "SAIDA_EPI" and ass_b64 and isinstance(ass_b64, str) and "," in ass_b64:
                tem_assinatura = True

            altura_linha = 16 if tem_assinatura else 8
            
            # TRAVA DE SEGURANÇA: Vira a página antes de desenhar se for bater no rodapé
            if pdf.get_y() + altura_linha > 275: 
                pdf.add_page()
                
            x_start_cell = pdf.get_x()
            y_start_cell = pdf.get_y()

            # Extração Básica
            data_val = str(row.get('data', '-'))[:16]
            produto_val = str(row.get('item', row.get('insumo', '-')))[:32]
            qtd_val = str(row.get('quantidade', '-'))

            # A MÁGICA DOS DADOS
            if tipo_tabela == "SAIDA_EPI":
                extra_val = str(row.get('motivo', '-'))[:15]
            elif tipo_tabela == "EMPRESTIMO" or tipo_tabela == "DEVOLUCAO":
                extra_val = str(row.get('status_item', '-'))[:15]
            else: 
                extra_val = "-"

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
                    
                    img_x = x_start_cell + 156
                    pdf.image(temp_img_path, x=img_x, y=y_start_cell + 1, w=33, h=14)
                except Exception:
                    pdf.text(x_start_cell + 160, y_start_cell + 9, "[Erro]")
            
            # Força o cursor a voltar para o lugar certo matematicamente
            pdf.set_xy(10, y_start_cell + altura_linha)

    # 1. Manda a máquina desenhar os 4 blocos
    desenhar_tabela_padrao("1. HISTORICO DE SAIDAS DEFINITIVAS (EPI)", df_saidas, "SAIDA_EPI")
    desenhar_tabela_padrao("2. HISTORICO DE EMPRESTIMOS", df_emprestimos, "EMPRESTIMO")
    desenhar_tabela_padrao("3. HISTORICO DE DEVOLUCOES", df_devolucoes, "DEVOLUCAO")
    #desenhar_tabela_padrao("4. HISTORICO DE INSUMOS", df_insumos, "INSUMO")

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
            
    # 5. ENTREGA O ARQUIVO
    return pdf_bytes