# consultaBD.py
import pyodbc
import traceback
import logging
from settings import (
    DB_SERVER,
    DB_DATABASE,
    DB_USER,
    DB_PASSWORD,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class RepositorioPrincipal:
    def __init__(self):
        # A string de conexão usa as variáveis importadas do settings.py
        # Certifique-se de que o driver ODBC correspondente esteja instalado no ambiente de destino.
        self.connection_string = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_DATABASE};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD}"
        )
        logging.info(f"Repositório Principal inicializado para DB: {DB_DATABASE}")

    def _conectar(self):
        return pyodbc.connect(self.connection_string, timeout=15)

    def _obter_lojas_da_planta(self, planta: str, connection) -> list[str]:
        query_lojas = f"""
            SELECT DISTINCT TRIM(A1_LOJA)
            FROM [dbo].[SA1010]
            WHERE A1_COD = ? AND D_E_L_E_T_ <> '*'
            ORDER BY 1
        """
        cursor = connection.cursor()
        cursor.execute(query_lojas, (planta,))
        return [row[0].strip() for row in cursor.fetchall()]

    def buscar_dados(self, filtros: dict) -> list:
        planta_filtrada = filtros.get("planta")
        loja_principal = filtros.get("loja")
        cliente_filtrado = filtros.get("cliente")
        pn_cliente_filtrado = filtros.get("pn_cliente")
        pn_voss_filtrado = filtros.get("pn_voss")

        logging.info(f"Iniciando buscar_dados com filtros: {filtros}")

        if not planta_filtrada or not loja_principal:
            logging.error("Filtros obrigatórios (Planta, Loja) não fornecidos.")
            return []

        # --- Parâmetros de filtro para a CTE 'ProdutosFiltrados' ---
        where_conditions_cte = []
        parameters_cte = []

        if pn_voss_filtrado:
            where_conditions_cte.append(f"A7.A7_PRODUTO LIKE ?")
            parameters_cte.append(f"%{pn_voss_filtrado}%")

        if pn_cliente_filtrado:
            where_conditions_cte.append(f"REPLACE(TRIM(A7.A7_CODCLI), ' ', '') LIKE ?")
            parameters_cte.append(f"%{pn_cliente_filtrado}%")

        if cliente_filtrado:
            cliente_like_param = f"%{cliente_filtrado}%"
            where_conditions_cte.append(
                f"(TRIM(A1.A1_NOME) LIKE ? OR TRIM(A1.A1_NREDUZ) LIKE ?)"
            )
            parameters_cte.extend([cliente_like_param, cliente_like_param])

        where_clause_cte = ""
        if where_conditions_cte:
            where_clause_cte = " AND " + " AND ".join(where_conditions_cte)
        # --- Fim Parâmetros CTE ---

        try:
            with self._conectar() as connection:
                todas_as_lojas = self._obter_lojas_da_planta(
                    planta_filtrada, connection
                )

                if not todas_as_lojas:
                    logging.warning(
                        f"Nenhuma loja encontrada para a planta: {planta_filtrada}"
                    )
                    return []

                if loja_principal in todas_as_lojas:
                    todas_as_lojas.remove(loja_principal)
                    todas_as_lojas.insert(0, loja_principal)

                # --- PIVOT Dinâmico ---
                pivot_columns_select = ""
                pivot_parameters = []

                for loja in todas_as_lojas:
                    # Aliases são seguros pois vêm de um replace para evitar SQL Injection via nome de loja
                    loja_alias_safe = loja.replace("]", "]]")

                    alias_nome_red = f"[Nome Reduzido {loja_alias_safe}]"
                    alias_data_primeira = f"[Primeira NF {loja_alias_safe}]"
                    alias_data_ultima = f"[Última NF {loja_alias_safe}]"
                    alias_previsao = f"[Previsão Vendas {loja_alias_safe}]"
                    alias_qtd_previsao = f"[Qtd Previsão Futura {loja_alias_safe}]"
                    alias_dias = f"[Dias {loja_alias_safe}]"
                    alias_preco = f"[Preço Venda {loja_alias_safe}]"

                    pivot_columns_select += f"""
                        ,MAX(CASE WHEN T.D2_LOJA = ? THEN T.[NomeReduzidoClienteLoja] END) AS {alias_nome_red}
                        ,MAX(CASE WHEN T.D2_LOJA = ? THEN T.DataPrimeiraNF END) AS {alias_data_primeira}
                        ,MAX(CASE WHEN T.D2_LOJA = ? THEN T.DataUltimaNF END) AS {alias_data_ultima}
                        ,MAX(CASE WHEN T.D2_LOJA = ? THEN T.DataPrevisao END) AS {alias_previsao}
                        ,ISNULL(MAX(CASE WHEN T.D2_LOJA = ? THEN T.QuantidadePrevisaoFutura END), 0) AS {alias_qtd_previsao}
                        ,MAX(CASE WHEN T.D2_LOJA = ? THEN T.DiasDesdeUltimaNF END) AS {alias_dias}
                        ,MAX(CASE WHEN T.D2_LOJA = ? THEN T.PrecoVenda END) AS {alias_preco}
                    """
                    # Adiciona os parâmetros 'loja' para cada '?' (7 vezes por loja)
                    pivot_parameters.extend([loja] * 7)

                # --- Query Base com CTEs ---
                query_base_cte = f"""
                    WITH DatasNF AS (
                        -- 1. Busca NFs
                        SELECT
                            TRIM(D2_COD) AS D2_COD, TRIM(D2_CLIENTE) AS D2_CLIENTE, TRIM(D2_LOJA) AS D2_LOJA,
                            MAX(D2_EMISSAO) AS DataUltimaNF, MIN(D2_EMISSAO) AS DataPrimeiraNF
                        FROM [dbo].[SD2010]
                        WHERE D_E_L_E_T_ <> '*' AND D2_CLIENTE = ? -- Param 1
                        GROUP BY TRIM(D2_COD), TRIM(D2_CLIENTE), TRIM(D2_LOJA)
                    ),
                    PrevisaoVendas AS (
                        -- 2. Busca Previsões
                        SELECT
                            TRIM(C4_PRODUTO) AS C4_PRODUTO, TRIM(C4_CLIENTE) AS C4_CLIENTE, TRIM(C4_LOJA) AS C4_LOJA,
                            SUM(CASE WHEN TRY_CAST(C4_DATA AS DATE) >= CAST(GETDATE() AS DATE) THEN C4_QUANT ELSE 0 END) AS QuantidadePrevisaoFutura,
                            CAST(MAX(C4_DATA) AS DATE) AS DataPrevisao
                        FROM [dbo].[SC4010]
                        WHERE D_E_L_E_T_ <> '*' AND C4_CLIENTE = ? AND C4_DATA <> '' -- Param 2
                        GROUP BY TRIM(C4_PRODUTO), TRIM(C4_CLIENTE), TRIM(C4_LOJA)
                    ),
                    ProdutosFiltrados AS (
                        -- 3. FILTRA os produtos com base na LOJA PRINCIPAL e filtros da UI
                        SELECT DISTINCT
                            A1.A1_COD AS Planta,
                            TRIM(A1.A1_NOME) AS Cliente,
                            TRIM(A1.A1_NREDUZ) AS [Nome Reduzido Cliente Mestre],
                            REPLACE(TRIM(A7.A7_CODCLI), ' ', '') AS [PN Cliente],
                            A7.A7_PRODUTO AS [PN Voss]
                        FROM [dbo].[SA1010] AS A1
                        INNER JOIN [dbo].[SA7010] AS A7
                            ON A7.A7_CLIENTE = A1.A1_COD
                            AND TRIM(A7.A7_LOJA) = TRIM(A1.A1_LOJA)
                            AND A7.D_E_L_E_T_ <> '*'
                        WHERE A1.A1_COD = ? -- Param 3
                          AND TRIM(A1.A1_LOJA) = ? -- Param 4
                          AND A1.D_E_L_E_T_ <> '*'
                          {where_clause_cte} -- Filtros dinâmicos (Params 5...N)
                    ),
                    LojaNomes AS (
                        -- 4. Busca o Nome Reduzido de TODAS as lojas
                        SELECT DISTINCT
                            TRIM(A1_LOJA) AS Loja, TRIM(A1_NREDUZ) AS NomeReduzidoClienteLoja
                        FROM [dbo].[SA1010]
                        WHERE A1_COD = ? -- Param N+1
                          AND D_E_L_E_T_ <> '*'
                    ),
                    PrecosVenda AS (
                        -- 5. Busca Preços de Venda
                        SELECT
                            A7_CLIENTE,
                            TRIM(A7_LOJA) AS A7_LOJA,
                            A7_PRODUTO,
                            A7_XPRCLIQ
                        FROM [dbo].[SA7010]
                        WHERE A7_CLIENTE = ? -- Param N+2
                          AND D_E_L_E_T_ <> '*'
                    ),
                    TabelaBase AS (
                        -- 6. Monta a ESTRUTURA (PRODUTO x LOJA) e anexa os dados
                        SELECT
                            PF.Cliente,
                            PF.[Nome Reduzido Cliente Mestre] AS [Nome Reduzido Mestre],
                            PF.[PN Cliente],
                            PF.[PN Voss],
                            LN.Loja AS D2_LOJA,
                            LN.NomeReduzidoClienteLoja,
                            PF.Planta,
                            CAST(UNF.DataUltimaNF AS DATE) AS DataUltimaNF,
                            CAST(UNF.DataPrimeiraNF AS DATE) AS DataPrimeiraNF,
                            PV.DataPrevisao,
                            ISNULL(PV.QuantidadePrevisaoFutura, 0) AS QuantidadePrevisaoFutura,
                            DATEDIFF(DAY, UNF.DataUltimaNF, GETDATE()) AS DiasDesdeUltimaNF,
                            CAST(PVN.A7_XPRCLIQ AS DECIMAL(18,2)) AS PrecoVenda

                        FROM ProdutosFiltrados AS PF
                        CROSS JOIN LojaNomes AS LN
                        LEFT JOIN DatasNF AS UNF
                            ON UNF.D2_COD = PF.[PN Voss]
                            AND UNF.D2_CLIENTE = PF.Planta
                            AND UNF.D2_LOJA = LN.Loja
                        LEFT JOIN PrevisaoVendas AS PV
                            ON PV.C4_PRODUTO = PF.[PN Voss]
                            AND PV.C4_CLIENTE = PF.Planta
                            AND PV.C4_LOJA = LN.Loja
                        LEFT JOIN PrecosVenda AS PVN
                            ON PVN.A7_PRODUTO = PF.[PN Voss]
                            AND PVN.A7_CLIENTE = PF.Planta
                            AND PVN.A7_LOJA = LN.Loja
                    )
                """

                # Parâmetros iniciais fixos (Params 1-4)
                cte_base_parameters = [
                    planta_filtrada,
                    planta_filtrada,
                    planta_filtrada,
                    loja_principal,
                ]

                # Montagem final da lista de parâmetros na ordem exata dos '?'
                final_parameters = (
                    cte_base_parameters
                    + parameters_cte
                    + [planta_filtrada]  # Para LojaNomes
                    + [planta_filtrada]  # Para PrecosVenda
                    + pivot_parameters   # Para o PIVOT dinâmico
                )

                final_query = f"""
                    {query_base_cte}
                    SELECT TOP 5000
                        T.Cliente,
                        T.[PN Voss],
                        T.[PN Cliente],
                        T.Planta,
                        T.[Nome Reduzido Mestre] AS [Nome Reduzido]
                        {pivot_columns_select}
                    FROM TabelaBase AS T
                    GROUP BY T.Cliente, T.[PN Voss], T.[PN Cliente], T.Planta, T.[Nome Reduzido Mestre]
                    ORDER BY T.Cliente, T.[PN Voss];
                """

                logging.info(
                    f"Executando query dinâmica com {len(final_parameters)} parâmetros."
                )

                cursor = connection.cursor()
                cursor.execute(final_query, final_parameters)
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except pyodbc.Error as ex:
            sqlstate = ex.args[0] if ex.args else "UNKNOWN"
            logging.error(
                f"ERRO DE BANCO DE DADOS SQLSTATE-{sqlstate}: {ex}"
            )
            raise
        except Exception as e:
            logging.error(f"ERRO INESPERADO: {e}")
            logging.error(traceback.format_exc())
            raise