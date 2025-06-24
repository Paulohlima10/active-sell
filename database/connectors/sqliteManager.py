import sqlite3
from sqlite3 import Error

# ===== Conexão com o banco de dados =====

def create_connection(db_file):
    """Cria uma conexão com o banco de dados SQLite."""
    try:
        conn = sqlite3.connect(db_file)
        print(f"Conectado ao banco de dados: {db_file}")
        return conn
    except Error as e:
        print(f"Erro ao conectar: {e}")
        return None

# ===== Criação de tabela =====

def create_table(conn):
    """Cria a tabela CLIENTES se não existir."""
    try:
        sql = '''
        CREATE TABLE IF NOT EXISTS CLIENTES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE,
            telefone TEXT
        );
        '''
        conn.execute(sql)
        conn.commit()
        print("Tabela CLIENTES criada ou já existe.")
    except Error as e:
        print(f"Erro ao criar tabela: {e}")

# ===== Inserção de dados =====

def insert_cliente(conn, nome, email, telefone):
    """Insere um novo cliente na tabela CLIENTES."""
    try:
        sql = '''
        INSERT INTO CLIENTES (nome, email, telefone)
        VALUES (?, ?, ?);
        '''
        conn.execute(sql, (nome, email, telefone))
        conn.commit()
        print("Cliente inserido com sucesso.")
    except Error as e:
        print(f"Erro ao inserir cliente: {e}")

# ===== Consulta de dados =====

def select_all_clientes(conn):
    """Seleciona e imprime todos os clientes."""
    try:
        sql = "SELECT * FROM CLIENTES;"
        cursor = conn.execute(sql)
        clientes = cursor.fetchall()
        for cliente in clientes:
            print(cliente)
    except Error as e:
        print(f"Erro ao consultar clientes: {e}")

# ===== Atualização de dados =====

def update_cliente_email(conn, cliente_id, novo_email):
    """Atualiza o e-mail de um cliente com base no ID."""
    try:
        sql = '''
        UPDATE CLIENTES
        SET email = ?
        WHERE id = ?;
        '''
        conn.execute(sql, (novo_email, cliente_id))
        conn.commit()
        print("Cliente atualizado com sucesso.")
    except Error as e:
        print(f"Erro ao atualizar cliente: {e}")

# ===== Exclusão de dados =====

def delete_cliente(conn, cliente_id):
    """Remove um cliente com base no ID."""
    try:
        sql = '''
        DELETE FROM CLIENTES
        WHERE id = ?;
        '''
        conn.execute(sql, (cliente_id,))
        conn.commit()
        print("Cliente deletado com sucesso.")
    except Error as e:
        print(f"Erro ao deletar cliente: {e}")

# ===== Exemplo de uso =====

def main():
    db_file = "clientes.db"
    conn = create_connection(db_file)

    if conn:
        create_table(conn)
        insert_cliente(conn, "João da Silva", "joao@email.com", "11999999999")
        insert_cliente(conn, "Maria Souza", "maria@email.com", "11888888888")
        select_all_clientes(conn)
        update_cliente_email(conn, 1, "joaosilva@email.com")
        delete_cliente(conn, 2)
        select_all_clientes(conn)
        conn.close()

if __name__ == "__main__":
    main()
