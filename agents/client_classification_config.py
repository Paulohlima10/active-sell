from openai import OpenAI
import os
import json

# Exemplo completo do JSON solicitado:
json_exemplo = {
    "campos": {
        "id_cliente": {"tabela": "CLIENTES", "coluna": "???"},
        "nome_cliente": {"tabela": "CLIENTES", "coluna": "???"},
        "id_pedido": {"tabela": "PEDIDOS", "coluna": "???"},
        "data_pedido": {"tabela": "PEDIDOS", "coluna": "???"},
        "valor_pedido": {"tabela": "PEDIDOS", "coluna": "???"},
        "id_produto": {"tabela": "PRODUTOS", "coluna": "???"},
        "nome_produto": {"tabela": "PRODUTOS", "coluna": "???"},
        "classe_produto": {"tabela": "PRODUTOS", "coluna": "???"},
        "telefone_cliente": {"tabela": "CLIENTES", "coluna": "???"},
        "telefone2_cliente": {"tabela": "CLIENTES", "coluna": "???"},
        "email_cliente": {"tabela": "CLIENTES", "coluna": "???"},
        "cidade_cliente": {"tabela": "CLIENTES", "coluna": "???"},
        "estado_cliente": {"tabela": "CLIENTES", "coluna": "???"},
        "data_nascimento": {"tabela": "CLIENTES", "coluna": "???"},
        "sexo": {"tabela": "CLIENTES", "coluna": "???"}
    }
}

def analisar_campos_tabelas(tabelas):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    """
    Usa IA (OpenAI GPT) para analisar os metadados das tabelas e retornar o JSON de mapeamento de campos.
    """
    client = OpenAI(api_key=openai_api_key)
    prompt = f"""
Você receberá a estrutura de colunas de três tabelas: clientes, produtos e pedidos. 
Seu objetivo é analisar os nomes das colunas e preencher o seguinte JSON, indicando para cada campo o nome da tabela e o nome da coluna correspondente. 
Se algum campo não existir, coloque o valor None para a coluna.

Exemplo de JSON de saída:
{json_exemplo}

Aqui estão as tabelas:
{tabelas}

Responda apenas com o JSON.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um assistente de análise de dados."},
            {"role": "user", "content": prompt}
        ]
    )
    # Converte a resposta string para JSON
    resposta_str = response.choices[0].message.content.strip()
    try:
        resposta_json = json.loads(resposta_str)
    except json.JSONDecodeError:
        # Tenta extrair o JSON de dentro da string, caso venha com texto extra
        import re
        match = re.search(r'(\{.*\})', resposta_str, re.DOTALL)
        if match:
            resposta_json = json.loads(match.group(1))
        else:
            raise
    return resposta_json


if __name__ == "__main__":
    # Exemplo de uso:
    tabelas = """Estrutura da tabela clientes:
    {'table': 'clientes_classificados', 'columns': [{'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO', 'column_default': "nextval('clientes_classificados_id_seq'::regclass)"}, {'column_name': 'nome_cliente', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'TELEFONE', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'TELEFONE2', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'EMAIL', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'CIDADE', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'ESTADO', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'produto_recomendado', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'categoria', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'segundo_produto', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'categoria_segundo_produto', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'terceiro_produto', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'categoria_terceiro_produto', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'potencial_compra', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'ultima_compra', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'ultima_compra_n', 'data_type': 'double precision', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'ticket_medio', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'frequencia', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'frequencia_n', 'data_type': 'double precision', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'pedidos', 'data_type': 'integer', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'tendencia', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'fidelizacao', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}]}

    Estrutura da tabela produtos:
    {'table': 'produtos_classificados', 'columns': [{'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO', 'column_default': "nextval('produtos_classificados_id_seq'::regclass)"}, {'column_name': 'rank', 'data_type': 'integer', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'NOME', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'CLASSE', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'total', 'data_type': 'integer', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'CATEGORIA', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'FREQUENCIA_USO', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'USO_RECORRENTE', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'PERIODO_ANO_TENDENCIA', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'DOSAGEM', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'FORMA_USO', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'EFEITO_CLIMA', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'RELACAO_EVENTOS_CALENDARIO', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'TENDENCIA_CONSUMO_IDADE', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'TENDENCIA_CONSUMO_SEXO', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'TENDENCIA_CONSUMO_LOCALIZACAO', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}]}  
    
    Estrutura da tabela pedidos:
    {'table': 'produtos_classificados_', 'columns': [{'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO', 'column_default': "nextval('produtos_classificados__id_seq'::regclass)"}, {'column_name': 'rank', 'data_type': 'integer', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'NOME', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'CLASSE', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'total', 'data_type': 'integer', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'CATEGORIA', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'FREQUENCIA_USO', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'USO_RECORRENTE', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'PERIODO_ANO_TENDENCIA', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'DOSAGEM', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'FORMA_USO', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'EFEITO_CLIMA', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'RELACAO_EVENTOS_CALENDARIO', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'TENDENCIA_CONSUMO_IDADE', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'TENDENCIA_CONSUMO_SEXO', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'TENDENCIA_CONSUMO_LOCALIZACAO', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}, {'column_name': 'NOME_USUAL', 'data_type': 'text', 'is_nullable': 'YES', 'column_default': None}]}"""

    resultado = analisar_campos_tabelas(tabelas)
    print(resultado)