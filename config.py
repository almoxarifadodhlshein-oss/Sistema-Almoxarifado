# config.py
import os

# Diretório do projeto (pasta onde este arquivo está)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Diretório do banco de dados (garante que exista)
DB_DIR = os.path.join(PROJECT_DIR, "banco de dados")
os.makedirs(DB_DIR, exist_ok=True)

# Caminhos para os DBs usados (adeque outros módulos se necessário)
DB_PATH = os.path.join(DB_DIR, "devolucoes.db")
