# Análise de Oportunidades Aftermarket (Reposição)

> Ferramenta corporativa de *Business Intelligence* desenvolvida para identificar lacunas de vendas em grandes clientes industriais e gerar oportunidades para o mercado de reposição.

![Status do Projeto](https://img.shields.io/badge/Status-Em_Produção-brightgreen)
![Python Version](https://img.shields.io/badge/Python-3.9+-blue)
![Stack](https://img.shields.io/badge/Backend-SQL_Server-lightgrey)

---

## 🎯 Objetivo do Negócio
Em indústrias de manufatura, é comum que clientes do tipo "Planta" (OEM - montadoras) deixem de comprar certos componentes após o fim do ciclo de vida de um produto. No entanto, existe uma oportunidade contínua de vender esses mesmos componentes para o mercado de **Aftermarket** (Reposição).

O objetivo desta aplicação é automatizar a identificação desses "gaps": produtos que não têm pedidos recentes ou previsões futuras para as Plantas, sinalizando-os para que o time de Vendas possa reavaliar preços e ofertá-los ativamente ao mercado de reposição.

---

## ⚙️ Arquitetura e Destaques Técnicos

Este projeto não é apenas um dashboard simples; ele envolveu desafios interessantes de integração em um ambiente corporativo legado.

### 1. Integração Python/Streamlit com IIS (Internet Information Services)
Um dos maiores desafios foi realizar o deploy de uma aplicação Python moderna dentro de uma infraestrutura Windows Server tradicional.
- **Solução:** Utilização do **IIS** como Proxy Reverso.
- O arquivo `web.config` foi configurado para gerenciar a autenticação via Windows (SSO - Single Sign-On) e redirecionar o tráfego internamente para a porta onde o serviço Streamlit está rodando.
- Um script `bootstrap.aspx` intermediário captura as credenciais do usuário Windows e as repassa para a sessão do Streamlit, garantindo que os logs de auditoria registrem o usuário correto sem necessidade de login manual.

### 2. SQL Complexo com PIVOT Dinâmico
O banco de dados (ERP Protheus/SQL Server) possui um número variável de "Lojas" para cada cliente "Planta". Uma consulta estática não seria suficiente.
- **Solução:** Implementação de uma query com **PIVOT Dinâmico** em Python (`consultaBD.py`).
- O script primeiro identifica todas as lojas ativas para a planta solicitada e, em seguida, constrói a query SQL programaticamente para transformar linhas (lojas) em colunas. Isso permite que a interface se adapte automaticamente quer o cliente tenha 2 ou 20 lojas.

### 3. Automação e Notificações
- **Relatórios Automáticos:** Geração de planilhas Excel formatadas (via `XlsxWriter`) com os resultados da análise.
- **E-mail Integrado:** Envio proativo dos relatórios para os gestores responsáveis utilizando servidor SMTP interno (relay).
- **Logs de Auditoria:** Registro detalhado de quem usou a ferramenta e quais itens foram selecionados para ação, salvos tanto em CSV local quanto em uma planilha Excel compartilhada na rede para controle gerencial.

---

## 🚀 Funcionalidades Principais

* **Filtros Inteligentes:**
    * Busca por Planta e Loja principal.
    * Filtro de "inatividade": permite encontrar produtos sem vendas há X dias em lojas secundárias.
    * Inclusão/Exclusão de previsões de vendas retroativas.
* **Interface Interativa (Streamlit):**
    * Visualização de dados em tabela dinâmica.
    * Seleção múltipla de itens para tomada de ação em lote.
* **Exportação de Dados:**
    * Download dos dados completos (brutos) para análise exploratória.
    * Download apenas dos itens selecionados para trabalho focado do time de vendas.

---

## 🛠️ Tecnologias Utilizadas

* **Frontend:** [Streamlit](https://streamlit.io/) (Interface Web rápida e responsiva).
* **Backend Language:** Python 3.x.
* **Database:** SQL Server (integrado via `pyodbc`).
* **Web Server:** IIS (Internet Information Services) com URL Rewrite module.
* **Bibliotecas Chave:**
    * `pandas`: Manipulação pesada de dados e DataFrames.
    * `xlsxwriter` & `openpyxl`: Geração e manipulação avançada de arquivos Excel.
    * `smtplib`: Automação de envio de e-mails corporativos.
    * `python-dotenv`: Gerenciamento seguro de variáveis de ambiente.

---

## 📂 Estrutura do Projeto

```bash
.
├── app.py                # Aplicação principal (Lógica de UI e Fluxo)
├── consultaBD.py         # Camada de Dados (Query Builder e Pivot Dinâmico)
├── settings.py           # Gerenciamento de configurações (carrega o .env)
├── web.config            # Configuração do IIS (Reverse Proxy e Auth)
├── wsgi.py               # Entry point para execução via serviços Windows
├── .env                  # Variáveis de ambiente (excluído do repo por segurança)
└── requirements.txt      # Dependências do projeto
```

## 🔧 Configuração (Exemplo)
Para rodar este projeto localmente (em modo de desenvolvimento), é necessário configurar um arquivo .env na raiz com as credenciais adequadas:

```.env example

# Banco de Dados ERP
DB_SERVER=seu_servidor_sql
DB_DATABASE=seu_DB
DB_USER=usuario_leitura
DB_PASSWORD=senha_segura

# Caminhos de Rede para Logs
FOLDER_PATH=./logs_locais/
FOLDER_PATH_LOCAL=\\servidor_arquivos\Compartilhado\Vendas\Logs_Aftermarket.xlsx

# Configurações de E-mail (SMTP Interno)
SMTP_SERVER=smtp.empresa.interno
SMTP_PORT=25
SMTP_USER=bot.notificacoes@empresa.com
SMTP_PASSWORD=
```

## Executando
```
# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação Streamlit
streamlit run app.py
```
