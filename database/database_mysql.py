import mysql.connector
from mysql.connector import Error
from typing import Tuple, Dict, Any, List, Optional
import json

def validate_connection_mysql(data: dict) -> Tuple[bool, Optional[str]]:
    record = data["record"]
    try:
        conn = mysql.connector.connect(
            host=record["db_host"],
            database=record["db_name"],
            port=int(record["db_port"]),
            user=record["db_username"],
            password=record["db_password"],
            connection_timeout=5
        )
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def validate_tables_exist_mysql(data: dict) -> Tuple[bool, Optional[str], List[str]]:
    record = data["record"]
    tables = [
        record["clients_table"],
        record["products_table"],
        record["purchases_table"]
    ]
    not_found = []
    try:
        conn = mysql.connector.connect(
            host=record["db_host"],
            database=record["db_name"],
            port=int(record["db_port"]),
            user=record["db_username"],
            password=record["db_password"]
        )
        cur = conn.cursor()
        for table in tables:
            cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
            """, (record["db_name"], table))
            exists = cur.fetchone()[0]
            if not exists:
                not_found.append(table)
        cur.close()
        conn.close()
        if not_found:
            return False, f"Tabelas não encontradas: {', '.join(not_found)}", not_found
        return True, None, []
    except Exception as e:
        return False, str(e), tables

def get_table_columns_mysql(data: dict, table: str) -> Dict[str, Any]:
    record = data["record"]
    columns = []
    try:
        conn = mysql.connector.connect(
            host=record["db_host"],
            database=record["db_name"],
            port=int(record["db_port"]),
            user=record["db_username"],
            password=record["db_password"]
        )
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (record["db_name"], table))
        for row in cur.fetchall():
            columns.append({
                "column_name": row["column_name"],
                "data_type": row["data_type"],
                "is_nullable": row["is_nullable"],
                "column_default": row["column_default"]
            })
        cur.close()
        conn.close()
        return {"table": table, "columns": columns}
    except Exception as e:
        return {"table": table, "error": str(e)}

if __name__ == "__main__":
    # Exemplo de JSON de entrada
    input_json = '''
    {
       "type":"INSERT",
       "table":"import_configurations",
       "record":{
          "id":"75483052-3e97-4263-8800-67e60949ec94",
          "status":"Em processamento",
          "db_host":"localhost",
          "db_name":"seu_banco",
          "db_port":"3306",
          "db_type":"mysql",
          "base_url":"None",
          "progress":0,
          "created_at":"2025-06-03T15:04:36.550373+00:00",
          "error_step":"None",
          "updated_at":"2025-06-03T15:04:36.550373+00:00",
          "db_password":"sua_senha",
          "db_username":"seu_usuario",
          "import_type":"database",
          "auth_headers":"None",
          "clients_table":"clientes_classificados",
          "error_message":"None",
          "requires_auth":"None",
          "products_table":"produtos_classificados",
          "purchases_table":"produtos_classificados_",
          "clients_endpoint":"None",
          "clients_file_path":"None",
          "products_endpoint":"None",
          "products_file_path":"None",
          "purchases_endpoint":"None",
          "purchases_file_path":"None",
          "processing_completed":false,
          "validation_completed":false,
          "clients_data_processed":false,
          "products_data_processed":false,
          "purchases_data_processed":false
       },
       "schema":"public",
       "old_record":"None"
    }
    '''
    data = json.loads(input_json)

    # Teste da conexão
    valid, reason = validate_connection_mysql(data)
    print("Conexão válida?", valid)
    if not valid:
        print("Motivo:", reason)
        exit(1)

    # Teste da existência das tabelas
    valid_tables, reason, not_found = validate_tables_exist_mysql(data)
    print("Tabelas existem?", valid_tables)
    if not valid_tables:
        print("Motivo:", reason)
        print("Tabelas não encontradas:", not_found)
        exit(1)

    # Consulta das colunas de cada tabela
    record = data["record"]
    for table in [record["clients_table"], record["products_table"], record["purchases_table"]]:
        columns_json = get_table_columns_mysql(data, table)
        print(f"Estrutura da tabela {table}:")
        print(columns_json)