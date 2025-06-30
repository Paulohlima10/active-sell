import requests
import secrets
import string
import os

# Função para gerar um token aleatório
def gerar_token(tamanho=8):
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(tamanho))

# Função para criar usuário
def criar_usuario(nome_usuario, admin_token):
    url = "http://18.205.29.7:8080/admin/users"
    token = gerar_token()
    headers = {
        "Authorization": admin_token,
        "Content-Type": "application/json"
    }
    payload = {
        "name": nome_usuario,
        "token": token,
        "webhook": "http://ec2-52-23-198-211.compute-1.amazonaws.com:8000/webhook_chat",
        "events": "All",
        "proxyConfig": {
            "enabled": False,
            "proxyURL": ""
        },
        "s3Config": {
            "enabled": True,
            "endpoint": "https://activesellbucket.s3.us-east-1.amazonaws.com/",
            "region": "us-east-1",
            "bucket": "acticesellbucket",
            "accessKey": os.getenv("S3_ACCESS_KEY"),
            "secretKey": os.getenv("S3_SECRET_KEY"),
            "pathStyle": False,
            "publicURL": "https://s3.amazonaws.com",
            "mediaDelivery": "both",
            "retentionDays": 30
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code, response.text, token

def conectar_usuario(token):
    url = "http://18.205.29.7:8080/session/connect"
    headers = {
        "token": token,
        "Content-Type": "application/json"
    }
    payload = {
        "Subscribe": ["Message", "ChatPresence"],
        "Immediate": True
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code, response.text

if __name__ == "__main__":
    nome_usuario = "teste"
    admin_token = "H4Zbhw72PBKdTIgS"
    status, resposta, token = criar_usuario(nome_usuario, admin_token)
    print("Resposta criar_usuario:", status, resposta)
    if status == 200:
        status_conn, resposta_conn = conectar_usuario(token)
        print("Resposta conectar_usuario:", status_conn, resposta_conn)
    else:
        print("Falha ao criar usuário, não foi possível conectar.")
