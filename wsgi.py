import subprocess
import os
import sys

# Obtém o caminho absoluto do diretório onde este script está
base_dir = os.path.dirname(os.path.abspath(__file__))
# Define o caminho para o app.py relativo a este script
script_path = os.path.join(base_dir, "app.py")

# Verifica se o arquivo existe antes de tentar executar
if not os.path.exists(script_path):
    print(f"Erro: Arquivo não encontrado: {script_path}")
    sys.exit(1)

# Chama o Streamlit via subprocess
# Adiciona 'sys.executable' para garantir que use o mesmo interpretador Python
cmd = [sys.executable, "-m", "streamlit", "run", script_path]
subprocess.run(cmd)