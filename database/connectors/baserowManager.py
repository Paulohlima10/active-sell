import requests

# ===== Configurações Globais =====
API_TOKEN = '2imXAjnYOWn8FOiai5sF4Hal0fOZkiuz'
BASE_URL = 'https://api.baserow.io/api/database'
HEADERS = {
    'Authorization': f'Token {API_TOKEN}',
    'Content-Type': 'application/json'
}

# ===== Funções de Integração com Baserow =====

def list_rows(database_id, table_id):
    """Lista todas as linhas da tabela."""
    url = f"{BASE_URL}/rows/table/{table_id}/?user_field_names=true"
    response = requests.get(url, headers=HEADERS)
    if response.ok:
        return response.json()['results']
    else:
        print("Erro ao listar linhas:", response.text)
        return []

def create_row(database_id, table_id, data):
    """Cria uma nova linha na tabela."""
    url = f"{BASE_URL}/rows/table/{table_id}/?user_field_names=true"
    response = requests.post(url, headers=HEADERS, json=data)
    if response.ok:
        return response.json()
    else:
        print("Erro ao criar linha:", response.text)
        return None

def read_row(database_id, table_id, row_id):
    """Lê uma linha específica pelo ID."""
    url = f"{BASE_URL}/rows/table/{table_id}/{row_id}/?user_field_names=true"
    response = requests.get(url, headers=HEADERS)
    if response.ok:
        return response.json()
    else:
        print("Erro ao ler linha:", response.text)
        return None

def update_row(database_id, table_id, row_id, data):
    """Atualiza uma linha específica."""
    url = f"{BASE_URL}/rows/table/{table_id}/{row_id}/?user_field_names=true"
    response = requests.patch(url, headers=HEADERS, json=data)
    if response.ok:
        return response.json()
    else:
        print("Erro ao atualizar linha:", response.text)
        return None

def delete_row(database_id, table_id, row_id):
    """Deleta uma linha específica."""
    url = f"{BASE_URL}/rows/table/{table_id}/{row_id}/"
    response = requests.delete(url, headers=HEADERS)
    if response.ok:
        print(f"Linha {row_id} deletada com sucesso.")
    else:
        print("Erro ao deletar linha:", response.text)

# ===== Exemplo de uso =====

def main():
    database_id = 206301
    table_id = 497427

    # Criar uma linha
    # novo_parceiro = {
    # "Name": "Drogaria Central",
    # "Notes": "Nova drogaria parceira no centro",
    # "Active": True,
    # "type_database": "csv",
    # "config_json": None,
    # "table_map": None,
    # "history_csv": [],
    # "catalog_csv": [],
    # "process_history": "12345",
    # "process_catalog": "67890"
    # }   
    # created = create_row(database_id, table_id, novo_parceiro)
    # print("Criado:", created)


    # Listar todas as linhas
    linhas = list_rows(database_id, table_id)
    print("Todas as linhas:", linhas)

    # if linhas:
    #     row_id = linhas[0]['id']

    #     # Ler uma linha
    #     linha = read_row(database_id, table_id, row_id)
    #     print("Linha lida:", linha)

    #     # Atualizar a linha
    #     atualizacao = {"Notes": "11888888888"}
    #     updated = update_row(database_id, table_id, row_id, atualizacao)
    #     print("Linha atualizada:", updated)

    #     # Deletar a linha
    #     # delete_row(database_id, table_id, row_id)

if __name__ == '__main__':
    main()
