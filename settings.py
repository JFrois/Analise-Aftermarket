# settings.py
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

# --- Credenciais do Banco de Dados ---
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# --- Caminhos de Pastas ---
# Defaults ajustados para pastas locais relativas ao projeto
FOLDER_LOG_PATH = os.getenv("FOLDER_PATH", "./logs/")
FOLDER_LOG_PATH_LOCAL = os.getenv("FOLDER_PATH_LOCAL", "./logs/AfterMarket_Base.xlsx")

# --- Informações SMTP ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")