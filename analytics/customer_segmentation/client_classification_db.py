import sqlite3
import pandas as pd
from datetime import datetime
import numpy as np
import re

# Função para criar a conexão com o banco de dados
def get_connection(db_config):
    db_type = db_config.get('db_type')
    if db_type == 'mysql':
        import mysql.connector
        conn = mysql.connector.connect(
            host=db_config['host'],
            port=db_config.get('port', 3306),
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
    elif db_type == 'postgres':
        import psycopg2
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config.get('port', 5432),
            user=db_config['user'],
            password=db_config['password'],
            dbname=db_config['database']
        )
    else:
        raise ValueError("db_type deve ser 'mysql' ou 'postgres'")
    return conn

# Função para construir uma query dinâmica com base no JSON de configuração
def build_query(config, campos):
    """
    Constrói uma query SQL para os campos especificados.
    :param config: Configuração do banco de dados.
    :param campos: Lista de campos a serem incluídos na query.
    :return: Query SQL.
    """
    tabelas = {}
    for campo in campos:
        info = config["campos"][campo]
        tabela = info["tabela"]
        coluna = info["coluna"]
        if tabela not in tabelas:
            tabelas[tabela] = []
        tabelas[tabela].append(coluna)
    
    # Monta a query para cada tabela
    queries = []
    for tabela, colunas in tabelas.items():
        queries.append(f"SELECT {', '.join(colunas)} FROM {tabela}")
    
    # Combina as queries (assume que as tabelas podem ser unidas posteriormente)
    return queries

# Função para carregar os dados essenciais
def load_clientes(config, conn):
    query = f"""
    SELECT 
        {config['campos']['id_cliente']['coluna']} AS CODCLI, 
        {config['campos']['nome_cliente']['coluna']} AS NOME,
        {config['campos']['telefone_cliente']['coluna']} AS TELEFONE,
        {config['campos']['telefone2_cliente']['coluna']} AS TELEFONE2,
        {config['campos']['email_cliente']['coluna']} AS EMAIL,
        {config['campos']['cidade_cliente']['coluna']} AS CIDADE,
        {config['campos']['estado_cliente']['coluna']} AS ESTADO
    FROM {config['campos']['id_cliente']['tabela']}
    """
    return pd.read_sql_query(query, conn)

# Função para calcular a última compra e os dias desde a última compra
def load_ultima_compra(config, conn):
    query = f"""
    SELECT 
        {config['campos']['id_pedido']['coluna']} AS CODCLI, 
        MAX({config['campos']['data_pedido']['coluna']}) AS ultima_compra
    FROM {config['campos']['id_pedido']['tabela']}
    WHERE {config['campos']['data_pedido']['coluna']} > '2024-01-01'
    GROUP BY {config['campos']['id_pedido']['coluna']}
    """
    df = pd.read_sql_query(query, conn)
    df['ultima_compra'] = pd.to_datetime(df['ultima_compra'])
    df['dias_desde_ultima'] = (datetime.today() - df['ultima_compra']).dt.days
    return df

# Função para calcular o ticket médio
def load_ticket_medio(config, conn):
    query = f"""
    SELECT 
        {config['campos']['id_pedido']['coluna']} AS CODCLI, 
        AVG({config['campos']['valor_pedido']['coluna']}) AS ticket_medio
    FROM {config['campos']['id_pedido']['tabela']}
    WHERE {config['campos']['data_pedido']['coluna']} > '2024-01-01'
    GROUP BY {config['campos']['id_pedido']['coluna']}
    """
    return pd.read_sql_query(query, conn)

# Função para calcular a frequência média entre compras
def load_frequencia_media(config, conn):
    query = f"""
    WITH intervalo AS (
      SELECT 
        {config['campos']['id_pedido']['coluna']} AS CODCLI, 
        {config['campos']['data_pedido']['coluna']} AS EMISSAO,
        LAG({config['campos']['data_pedido']['coluna']}) OVER (PARTITION BY {config['campos']['id_pedido']['coluna']} ORDER BY {config['campos']['data_pedido']['coluna']}) AS anterior
      FROM {config['campos']['id_pedido']['tabela']}
      WHERE {config['campos']['data_pedido']['coluna']} > '2024-01-01'
    )
    SELECT 
      CODCLI,
      AVG(JULIANDAY(EMISSAO) - JULIANDAY(anterior)) AS frequencia_media
    FROM intervalo
    WHERE anterior IS NOT NULL
    GROUP BY CODCLI
    """
    return pd.read_sql_query(query, conn)

# Função para calcular a tendência de compra
def load_tendencia(config, conn):
    query = f"""
    WITH compras_periodos AS (
      SELECT 
        {config['campos']['id_pedido']['coluna']} AS CODCLI,
        CASE 
          WHEN {config['campos']['data_pedido']['coluna']} >= DATE('now', '-90 days') THEN 'recente'
          WHEN {config['campos']['data_pedido']['coluna']} BETWEEN DATE('now', '-180 days') AND DATE('now', '-91 days') THEN 'anterior'
        END AS periodo
      FROM {config['campos']['id_pedido']['tabela']}
      WHERE {config['campos']['data_pedido']['coluna']} > '2024-01-01'
    )
    SELECT 
      CODCLI,
      SUM(CASE WHEN periodo = 'recente' THEN 1 ELSE 0 END) AS compras_recentes,
      SUM(CASE WHEN periodo = 'anterior' THEN 1 ELSE 0 END) AS compras_anteriores,
      CASE 
        WHEN SUM(CASE WHEN periodo = 'recente' THEN 1 ELSE 0 END) > SUM(CASE WHEN periodo = 'anterior' THEN 1 ELSE 0 END) THEN 'AUMENTANDO'
        WHEN SUM(CASE WHEN periodo = 'recente' THEN 1 ELSE 0 END) < SUM(CASE WHEN periodo = 'anterior' THEN 1 ELSE 0 END) THEN 'REDUZINDO'
        ELSE 'ESTÁVEL'
      END AS tendencia
    FROM compras_periodos
    GROUP BY CODCLI
    """
    return pd.read_sql_query(query, conn)

# Função para calcular o produto mais comprado
def load_produto_mais_comprado(config, conn):
    # Função para verificar se uma coluna existe em uma tabela
    def column_exists(table, column):
        query = f"PRAGMA table_info({table})"
        columns = pd.read_sql_query(query, conn)['name'].tolist()
        return column in columns

    # Verifica se as colunas configuradas existem
    id_produto_col = config['campos']['id_produto']['coluna']
    nome_produto_col = config['campos']['nome_produto']['coluna']
    classe_produto_col = config['campos']['classe_produto']['coluna']
    if not column_exists(config['campos']['id_produto']['tabela'], id_produto_col):
        raise ValueError(f"A coluna '{id_produto_col}' não existe na tabela '{config['campos']['id_produto']['tabela']}'")
    if not column_exists(config['campos']['nome_produto']['tabela'], nome_produto_col):
        raise ValueError(f"A coluna '{nome_produto_col}' não existe na tabela '{config['campos']['nome_produto']['tabela']}'")
    if not column_exists(config['campos']['classe_produto']['tabela'], classe_produto_col):
        raise ValueError(f"A coluna '{classe_produto_col}' não existe na tabela '{config['campos']['classe_produto']['tabela']}'")

    # Query para obter os produtos comprados
    query = f"""
    SELECT 
        PD.{config['campos']['id_pedido']['coluna']} AS CODCLI, 
        PP.CODPR AS CODPR, 
        COUNT(*) AS total
    FROM {config['campos']['id_pedido']['tabela']} PD
    JOIN PRODPED PP ON PD.REGISTRO = PP.REGISTR
    WHERE PD.{config['campos']['data_pedido']['coluna']} > '2024-01-01'
    GROUP BY CODCLI, CODPR
    """
    produto_df = pd.read_sql_query(query, conn)

    # Calcula o ranking dos produtos por cliente
    produto_df['rank'] = produto_df.groupby('CODCLI')['total'].rank(method='first', ascending=False)
    produtos_top = produto_df[produto_df['rank'].isin([1, 2, 3])]

    # Pivot para obter uma única linha por cliente com os três produtos
    produtos_pivot = produtos_top.pivot(index='CODCLI', columns='rank', values='CODPR').reset_index()
    produtos_pivot.columns = ['CODCLI', 'produto_rank1', 'produto_rank2', 'produto_rank3']

    # Query para obter informações adicionais dos produtos
    prod_info_query = f"""
    SELECT {id_produto_col} AS CODPR, {nome_produto_col} AS NOME, {classe_produto_col} AS CLASSE
    FROM {config['campos']['id_produto']['tabela']}
    """
    prod_info = pd.read_sql_query(prod_info_query, conn)

    # Mescla para o 1º produto
    produto_final = produtos_pivot.merge(prod_info, how='left', left_on='produto_rank1', right_on='CODPR')
    produto_final = produto_final.rename(columns={'NOME': 'NOME1', 'CLASSE': 'CLASSE1'})
    produto_final.drop('CODPR', axis=1, inplace=True)

    # Mescla para o 2º produto
    produto_final = produto_final.merge(
        prod_info.add_suffix('2'),
        how='left',
        left_on='produto_rank2',
        right_on='CODPR2'
    )
    produto_final = produto_final.rename(columns={'NOME2': 'NOME2', 'CLASSE2': 'CLASSE2'})
    produto_final.drop('CODPR2', axis=1, inplace=True)

    # Mescla para o 3º produto
    produto_final = produto_final.merge(
        prod_info.add_suffix('3'),
        how='left',
        left_on='produto_rank3',
        right_on='CODPR3'
    )
    produto_final = produto_final.rename(columns={'NOME3': 'NOME3', 'CLASSE3': 'CLASSE3'})
    produto_final.drop('CODPR3', axis=1, inplace=True)
    # Exporta os dados de produto_final para um CSV
    produto_final.to_csv('analise_produtos.csv', index=False)

    # Gerar classificação geral dos produtos mais comprados
    classificacao_produtos = produto_df.groupby('CODPR')['total'].sum().reset_index()
    classificacao_produtos = classificacao_produtos.merge(prod_info, on='CODPR', how='left')
    classificacao_produtos = classificacao_produtos.sort_values(by='total', ascending=False).reset_index(drop=True)
    classificacao_produtos['rank'] = classificacao_produtos.index + 1

    # Selecionar colunas relevantes e exportar para CSV
    classificacao_produtos[['rank', 'NOME', 'CLASSE', 'total']].to_csv('classificacao_produtos.csv', index=False)

    return produto_final

def load_qtde_pedidos(config, conn):
    query = f"""
    SELECT {config['campos']['id_pedido']['coluna']} AS CODCLI,
           COUNT(*) AS quantidade_pedidos
    FROM {config['campos']['id_pedido']['tabela']}
    WHERE {config['campos']['data_pedido']['coluna']} > '2024-01-01'
    GROUP BY {config['campos']['id_pedido']['coluna']}
    """
    return pd.read_sql_query(query, conn)

# Função principal para gerar o relatório
def gerar_relatorio(config):
    conn = get_connection(config)
    clientes_df = load_clientes(config, conn)
    ultima_df = load_ultima_compra(config, conn)
    ticket_df = load_ticket_medio(config, conn)
    frequencia_df = load_frequencia_media(config, conn)
    tendencia_df = load_tendencia(config, conn)
    produto_final = load_produto_mais_comprado(config, conn)
    pedidos_df = load_qtde_pedidos(config, conn)

    # Junta todas as tabelas em um único DataFrame
    df = clientes_df.rename(columns={config['campos']['id_cliente']['coluna']: 'CODCLI'})
    df = df.merge(ultima_df[['CODCLI', 'dias_desde_ultima']], on='CODCLI', how='left')
    df = df.merge(ticket_df, on='CODCLI', how='left')
    df = df.merge(frequencia_df, on='CODCLI', how='left')
    df = df.merge(tendencia_df[['CODCLI', 'tendencia']], on='CODCLI', how='left')
    df = df.merge(produto_final[['CODCLI', 'NOME1', 'NOME2', 'NOME3', 'CLASSE1', 'CLASSE2', 'CLASSE3']], on='CODCLI', how='left')
    df = df.merge(pedidos_df[['CODCLI', 'quantidade_pedidos']], on='CODCLI', how='left') 

    # Formata colunas finais
    df['Ticket Médio'] = df['ticket_medio'].apply(lambda x: f"R$ {x:.2f}" if pd.notnull(x) else '')
    df['Frequência'] = df['frequencia_media'].apply(lambda x: f"A cada {int(round(x))} dias" if pd.notnull(x) else '')
    df['Última Compra'] = df['dias_desde_ultima'].apply(lambda x: f"{int(x)} dias atrás" if pd.notnull(x) else '')
    df['Frequência_n'] = df['Frequência'].apply(lambda x: int(re.search(r'\d+', x).group()) if isinstance(x, str) and re.search(r'\d+', x) else None)
    df['Ultima_compra_n'] = df['Última Compra'].apply(lambda x: int(re.search(r'\d+', x).group()) if isinstance(x, str) and re.search(r'\d+', x) else None)

    df['Produto Recomendado'] = df['NOME1']
    df['Categoria'] = df['CLASSE1']
    df['Segundo Produto'] = df['NOME2']
    df['Categoria Segundo Produto'] = df['CLASSE2']
    df['Terceiro Produto'] = df['NOME3']
    df['Categoria Terceiro Produto'] = df['CLASSE3']

    df['Pedidos'] = df['quantidade_pedidos'].fillna(0).astype(int)

    # Potencial de Compra baseado em dias desde última compra x frequência
    df['Potencial de Compra'] = df.apply(
        lambda row: 'Alto' if pd.notnull(row['frequencia_media']) and row['dias_desde_ultima'] >= 0.8 * row['frequencia_media'] else 'Baixo',
        axis=1
    )

    # Adicionar coluna de Fidelização
    def definir_nivel_fidelizacao(row):
        if pd.notnull(row['frequencia_media']) and pd.notnull(row['dias_desde_ultima']):
            if row['frequencia_media'] <= 30 and row['dias_desde_ultima'] <= 0.5 * row['frequencia_media'] and row['tendencia'] == 'AUMENTANDO':
                return 'Muito Fidelizado'
            elif row['frequencia_media'] <= 60 and row['dias_desde_ultima'] <= row['frequencia_media'] and row['tendencia'] in ['ESTÁVEL', 'AUMENTANDO']:
                return 'Fidelizado'
            elif row['frequencia_media'] > 60 and row['dias_desde_ultima'] > row['frequencia_media'] and row['tendencia'] == 'REDUZINDO':
                return 'Pouco Fidelizado'
            elif row['dias_desde_ultima'] > 2 * row['frequencia_media'] and row['tendencia'] in ['REDUZINDO', None]:
                return 'Inativo'
        return 'Indefinido'

    df['Fidelização'] = df.apply(definir_nivel_fidelizacao, axis=1)

    # Remove as linhas em que 'Última Compra' é string vazia
    df = df[df['Última Compra'] != '']

    # Seleciona colunas finais
    resultado = df[['NOME', 'TELEFONE', 'TELEFONE2', 'EMAIL', 'CIDADE', 'ESTADO', 'Produto Recomendado', 'Categoria', 
                    'Segundo Produto', 'Categoria Segundo Produto', 'Terceiro Produto', 'Categoria Terceiro Produto', 
                    'Potencial de Compra', 'Última Compra', 'Ultima_compra_n', 'Ticket Médio', 'Frequência', 'Frequência_n', 'Pedidos', 'tendencia', 
                    'Fidelização']].copy()
    resultado.rename(columns={
        'NOME': 'nome_cliente',
        'Produto Recomendado': 'produto_recomendado',
        'Categoria': 'categoria',
        'Segundo Produto': 'segundo_produto',
        'Categoria Segundo Produto': 'categoria_segundo_produto',
        'Terceiro Produto': 'terceiro_produto',
        'Categoria Terceiro Produto': 'categoria_terceiro_produto',
        'Potencial de Compra': 'potencial_compra',
        'Última Compra': 'ultima_compra',
        'Ticket Médio': 'ticket_medio',
        'Frequência': 'frequencia',
        'Pedidos': 'pedidos',
        'tendencia': 'tendencia',
        'Fidelização': 'fidelizacao',
        'Frequência_n': 'frequencia_n',
        'Ultima_compra_n': 'ultima_compra_n'
    }, inplace=True)
    # Exporta para CSV
    resultado.to_csv('resultado_final5.csv', index=False)

def analisar_resultado(resultado):
    # Quantidade total de registros gerados
    total_registros = len(resultado)

    # Quantidade de clientes com potencial alto
    clientes_potencial_alto = len(resultado[resultado['potencial_compra'] == 'Alto'])

    # Representação em % de clientes com potencial alto
    percentual_potencial_alto = (clientes_potencial_alto / total_registros) * 100 if total_registros > 0 else 0

    # Quantidade total de produtos únicos recomendados
    produtos_unicos = resultado['produto_recomendado'].nunique()

    # Quantidade de clientes com tendência "AUMENTANDO"
    clientes_tendencia_aumentando = len(resultado[resultado['tendencia'] == 'AUMENTANDO'])

    # Quantidade de clientes que atendem à regra (Frequência - Última Compra) <= 7 e > 0
    # def extrair_numero(texto):
    #     import re
    #     if isinstance(texto, str):  # Verifica se o valor é uma string
    #         match = re.search(r'\d+', texto)
    #         return int(match.group()) if match else None
    #     return None

    # resultado['Frequência (dias)'] = resultado['Frequência'].apply(lambda x: extrair_numero(x))
    # resultado['Última Compra (dias)'] = resultado['Última Compra'].apply(lambda x: extrair_numero(x))
    clientes_regra = len(resultado[
        (resultado['frequencia_n'] - resultado['ultima_compra_n'] <= 7) &
        (resultado['frequencia_n'] - resultado['ultima_compra_n'] > 0)
    ])

    # Converter o ticket médio para valor numérico
    def extrair_valor_ticket(texto):
        if isinstance(texto, str) and texto.startswith("R$"):
            return float(texto.replace("R$", "").replace(",", "").strip())
        return 0

    resultado['Ticket Médio (valor)'] = resultado['ticket_medio'].apply(lambda x: extrair_valor_ticket(x))

    # Calcular o ticket médio geral (excluindo clientes com ticket médio igual a 0)
    ticket_medio_geral = resultado[resultado['Ticket Médio (valor)'] > 0]['Ticket Médio (valor)'].mean()

    # Quantidade de clientes por nível de fidelização
    muito_fidelizados = len(resultado[resultado['fidelizacao'] == 'Muito Fidelizado'])
    fidelizados = len(resultado[resultado['fidelizacao'] == 'Fidelizado'])
    nao_fidelizados = total_registros - (muito_fidelizados + fidelizados)

    # Calcular a quantidade média de pedidos por cliente
    pedidos_medios = resultado['pedidos'].mean()

    # Gravar métricas em CSV
    metrics = {
        'total_registros': total_registros,
        'clientes_potencial_alto': clientes_potencial_alto,
        'percentual_potencial_alto': f"{percentual_potencial_alto:.2f}%",
        'produtos_unicos': produtos_unicos,
        'clientes_tendencia_aumentando': clientes_tendencia_aumentando,
        'clientes_regra': clientes_regra,
        'ticket_medio_geral': round(ticket_medio_geral, 2) if ticket_medio_geral is not None else 0,
        'muito_fidelizados': muito_fidelizados,
        'fidelizados': fidelizados,
        'nao_fidelizados': nao_fidelizados,
        'pedidos_medios': round(pedidos_medios, 2)
    }
    # cria um DataFrame com uma linha e salva
    pd.DataFrame([metrics]).to_csv('metricas.csv', index=False)

def gerar_correlacao_produtos(config, conn):
    # Query para obter os produtos comprados por cliente
    query = f"""
    SELECT 
        PD.{config['campos']['id_pedido']['coluna']} AS CODCLI, 
        PP.CODPR AS CODPR
    FROM {config['campos']['id_pedido']['tabela']} PD
    JOIN PRODPED PP ON PD.REGISTRO = PP.REGISTR
    """
    compras_df = pd.read_sql_query(query, conn)

    # Criar uma tabela binária (1 se o cliente comprou o produto, 0 caso contrário)
    compras_binaria = compras_df.pivot_table(index='CODCLI', columns='CODPR', aggfunc='size', fill_value=0)

    # Criar a matriz de coocorrência (produto x produto)
    coocorrencia = compras_binaria.T.dot(compras_binaria)

    # Remover a diagonal principal (um produto não deve ser correlacionado consigo mesmo)
    np.fill_diagonal(coocorrencia.values, 0)

    # Normalizar para obter a correlação (opcional)
    correlacao = coocorrencia / coocorrencia.max().max()

    # Obter os nomes dos produtos
    prod_info_query = f"""
    SELECT {config['campos']['id_produto']['coluna']} AS CODPR, {config['campos']['nome_produto']['coluna']} AS NOME
    FROM {config['campos']['id_produto']['tabela']}
    """
    prod_info = pd.read_sql_query(prod_info_query, conn)

    # Criar uma lista para armazenar os resultados
    correlacao_lista = []

    # Iterar sobre os produtos para encontrar os dois mais correlacionados
    for produto in correlacao.index:
        top_correlacionados = correlacao.loc[produto].nlargest(2).index.tolist()
        top_nomes = prod_info[prod_info['CODPR'].isin(top_correlacionados)]['NOME'].tolist()
        
        # Verificar se o produto existe em prod_info
        produto_nome_row = prod_info[prod_info['CODPR'] == produto]
        if not produto_nome_row.empty:
            produto_nome = produto_nome_row['NOME'].values[0]
        else:
            produto_nome = None  # Caso o produto não seja encontrado

        correlacao_lista.append({
            'Produto': produto_nome,
            'Mais Correlacionado 1': top_nomes[0] if len(top_nomes) > 0 else None,
            'Mais Correlacionado 2': top_nomes[1] if len(top_nomes) > 1 else None
        })

    # Converter a lista em um DataFrame
    correlacao_df = pd.DataFrame(correlacao_lista)

    # Exportar para CSV
    correlacao_df.to_csv('correlacao_produtos_resumida.csv', index=False)

    print("Tabela de correlação de produtos gerada com sucesso!")
    
# Exemplo de uso:
if __name__ == "__main__":
    db_config = {
        "db_type": "mysql",
        "host": "localhost",
        "port": 3306,
        "user": "seu_usuario",
        "password": "sua_senha",
        "database": "nome_do_banco",
        "campos": {
            "id_cliente": {"tabela": "CLIENTES", "coluna": "CODIGO"},
            "nome_cliente": {"tabela": "CLIENTES", "coluna": "NOME"},
            "id_pedido": {"tabela": "PEDIDOS", "coluna": "CODCLI"},
            "data_pedido": {"tabela": "PEDIDOS", "coluna": "EMISSAO"},
            "valor_pedido": {"tabela": "PEDIDOS", "coluna": "VALOR"},
            "id_produto": {"tabela": "PRODUTOS", "coluna": "CÓDIGO"},
            "nome_produto": {"tabela": "PRODUTOS", "coluna": "NOME"},
            "classe_produto": {"tabela": "PRODUTOS", "coluna": "CLASSE"},
            "telefone_cliente": {"tabela": "CLIENTES", "coluna": "FONE"},
            "telefone2_cliente": {"tabela": "CLIENTES", "coluna": "CELULAR"},
            "email_cliente": {"tabela": "CLIENTES", "coluna": "EMAIL"},
            "cidade_cliente": {"tabela": "CLIENTES", "coluna": "MUNICIPIO"},
            "estado_cliente": {"tabela": "CLIENTES", "coluna": "ESTADO"}
        }
    }
    campos_desejados = ["id_cliente", "nome_cliente", "telefone_cliente"]
    query = build_query(db_config, campos_desejados)
    print(query)