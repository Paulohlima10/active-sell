import psycopg2
from datetime import datetime
import requests
# from logs.logging_config import log_message
import os
import uuid
import base64
import asyncio
import re



# === CONFIGURAÇÕES ===
DB_CONFIG = {
    "host": "aws-0-us-east-1.pooler.supabase.com",
    "port": 6543,
    "dbname": "postgres",
    "user": "postgres.gzzvydiznhwaxrahzkjt",
    "password": "Activesell@01"
}

# === CONEXÃO COM O BANCO ===
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def normalize_phone(phone):
    """
    Normaliza o telefone para o formato 553491704671.
    Remove um '9' extra após o DDD se houver.
    Retorna None se o telefone não estiver no formato esperado.
    """
    # Remove caracteres não numéricos
    phone = re.sub(r'\D', '', phone)
    # Verifica se começa com 55 e tem 13 dígitos (com o 9 extra)
    if re.fullmatch(r'55\d{2}9\d{8}', phone):
        # Remove o 9 após o DDD
        return phone[:4] + phone[5:]
    # Verifica se já está no formato correto (12 dígitos após 55)
    elif re.fullmatch(r'55\d{10}', phone):
        return phone
    else:
        return None

# === ENVIO DE MENSAGEM WHATSAPP ===
async def send_message_via_http(
    phone_number,
    msg=None,
    image_url=None,
    pdf_url=None,
    msg_id=None,
    context_info=None,
    variables=None,
    token="9C84DC7EBCC6-4B17-8625-A4A60018AC03",
    text_url=f"{os.getenv('WUZAPI_BASE_URL')}/chat/send/text",
    image_url_api=f"{os.getenv('WUZAPI_BASE_URL')}/chat/send/image",
    pdf_url_api=f"{os.getenv('WUZAPI_BASE_URL')}/chat/send/document"
):
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }

    # Substitui variáveis no texto da mensagem
    if msg and variables:
        try:
            msg = msg.format(**variables)
        except KeyError as e:
            raise Exception(f"Variável não encontrada na mensagem: {e}")

    results = {}

    # Função auxiliar para envio de PDF
    def send_pdf(pdf_url_to_send):
        if not pdf_url_to_send or not isinstance(pdf_url_to_send, str):
            raise Exception("pdf_url inválido ou não fornecido")
        response = requests.get(pdf_url_to_send)
        if response.status_code != 200:
            raise Exception(f"Erro ao baixar PDF: {response.status_code}")
        pdf_base64 = base64.b64encode(response.content).decode("utf-8")
        pdf_data = f"data:application/octet-stream;base64,{pdf_base64}"
        file_name = os.path.basename(pdf_url_to_send)
        payload_pdf = {
            "Phone": phone_number,
            "Document": pdf_data,
            "FileName": file_name
        }
        resp_pdf = requests.post(pdf_url_api, headers=headers, json=payload_pdf)
        print(f"Resposta ao enviar PDF: {resp_pdf.status_code} - {resp_pdf.text}")
        results["pdf"] = resp_pdf.json()

    # Se mensagem, imagem e PDF
    if msg and image_url and pdf_url:
        # Envia imagem
        response = requests.get(image_url)
        if response.status_code != 200:
            raise Exception(f"Erro ao baixar imagem: {response.status_code}")
        content_type = response.headers.get("Content-Type", "image/jpeg")
        img_base64 = base64.b64encode(response.content).decode("utf-8")
        if content_type == "image/png":
            img_data = f"data:image/png;base64,{img_base64}"
        else:
            img_data = f"data:image/jpeg;base64,{img_base64}"

        payload_img = {
            "Phone": phone_number,
            "Image": img_data
        }
        resp_img = requests.post(image_url_api, headers=headers, json=payload_img)
        print(f"Resposta ao enviar imagem: {resp_img.status_code} - {resp_img.text}")
        results["image"] = resp_img.json()

        # Envia PDF
        send_pdf(pdf_url)

        # Envia mensagem de texto
        if msg_id is None:
            msg_id = uuid.uuid4().hex.upper()
        payload_text = {
            "Phone": phone_number,
            "Body": msg,
            "Id": msg_id
        }
        if context_info:
            payload_text["ContextInfo"] = context_info
        resp_text = requests.post(text_url, headers=headers, json=payload_text)
        print(f"Resposta ao enviar mensagem de texto: {resp_text.status_code} - {resp_text.text}")
        results["text"] = resp_text.json()
        return results

    # Se mensagem e imagem
    elif msg and image_url:
        response = requests.get(image_url)
        if response.status_code != 200:
            raise Exception(f"Erro ao baixar imagem: {response.status_code}")
        content_type = response.headers.get("Content-Type", "image/jpeg")
        img_base64 = base64.b64encode(response.content).decode("utf-8")
        if content_type == "image/png":
            img_data = f"data:image/png;base64,{img_base64}"
        else:
            img_data = f"data:image/jpeg;base64,{img_base64}"

        payload_img = {
            "Phone": phone_number,
            "Image": img_data
        }
        resp_img = requests.post(image_url_api, headers=headers, json=payload_img)
        print(f"Resposta ao enviar imagem: {resp_img.status_code} - {resp_img.text}")
        results["image"] = resp_img.json()

        # Envia mensagem de texto
        if msg_id is None:
            msg_id = uuid.uuid4().hex.upper()
        payload_text = {
            "Phone": phone_number,
            "Body": msg,
            "Id": msg_id
        }
        if context_info:
            payload_text["ContextInfo"] = context_info
        resp_text = requests.post(text_url, headers=headers, json=payload_text)
        print(f"Resposta ao enviar mensagem de texto: {resp_text.status_code} - {resp_text.text}")
        results["text"] = resp_text.json()
        return results

    # Se mensagem e PDF
    elif msg and pdf_url:
        # Envia PDF
        send_pdf(pdf_url)

        # Envia mensagem de texto
        if msg_id is None:
            msg_id = uuid.uuid4().hex.upper()
        payload_text = {
            "Phone": phone_number,
            "Body": msg,
            "Id": msg_id
        }
        if context_info:
            payload_text["ContextInfo"] = context_info
        resp_text = requests.post(text_url, headers=headers, json=payload_text)
        print(f"Resposta ao enviar mensagem de texto: {resp_text.status_code} - {resp_text.text}")
        results["text"] = resp_text.json()
        return results

    # Se apenas imagem
    elif image_url:
        response = requests.get(image_url)
        if response.status_code != 200:
            raise Exception(f"Erro ao baixar imagem: {response.status_code}")
        content_type = response.headers.get("Content-Type", "image/jpeg")
        img_base64 = base64.b64encode(response.content).decode("utf-8")
        if content_type == "image/png":
            img_data = f"data:image/png;base64,{img_base64}"
        else:
            img_data = f"data:image/jpeg;base64,{img_base64}"

        payload = {
            "Phone": phone_number,
            "Image": img_data
        }
        resp = requests.post(image_url_api, headers=headers, json=payload)
        print(f"Resposta ao enviar imagem: {resp.status_code} - {resp.text}")
        return resp.json()

    # Se apenas PDF
    elif pdf_url:
        send_pdf(pdf_url)
        return results["pdf"]

    # Se apenas texto
    else:
        if msg_id is None:
            msg_id = uuid.uuid4().hex.upper()
        payload = {
            "Phone": phone_number,
            "Body": msg,
            "Id": msg_id
        }
        if context_info:
            payload["ContextInfo"] = context_info
        response = requests.post(text_url, headers=headers, json=payload)
        print(f"Resposta ao enviar mensagem de texto: {response.status_code} - {response.text}")
        return response.json()


# === PROCESSAMENTO DE CAMPANHAS ===
async def process_campaigns():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Seleciona campanhas ativas
        cursor.execute("""
            SELECT id, message FROM campaigns
            WHERE status = 'active' AND start_date <= NOW() AND end_date >= NOW()
        """)
        campaigns = cursor.fetchall()

        for campaign_id, message in campaigns:
            print(f"📢 Processando campanha {campaign_id}")

            # Buscar percentual_desconto e validade_desconto da tabela campaigns
            cursor.execute("""
                SELECT discount_percentage, discount_days FROM campaigns WHERE id = %s
            """, (campaign_id,))
            campaign_data = cursor.fetchone()
            percentual_desconto = campaign_data[0] if campaign_data else None
            validade_desconto = campaign_data[1] if campaign_data else None

            # 2. Busca clientes da campanha ainda não enviados, incluindo nome_cliente e produto_recomendado
            cursor.execute("""
                SELECT cc.client_id, cl."TELEFONE", cl.nome_cliente, cl.produto_recomendado
                FROM campaign_clients cc
                JOIN clientes_classificados cl ON cl.id = cc.client_id
                WHERE cc.campaign_id = %s AND cc.status IS DISTINCT FROM 'sent'
            """, (campaign_id,))
            clients = cursor.fetchall()

            # 3. Verifica se há imagem vinculada
            cursor.execute("""
                SELECT file_url FROM campaign_files
                WHERE campaign_id = %s AND file_type = 'image'
                ORDER BY created_at DESC LIMIT 1
            """, (campaign_id,))
            image = cursor.fetchone()
            image_url = image[0] if image else None

            # 4. Envia mensagens
            for client_id, phone, nome_cliente, produto_recomendado in clients:
                normalized_phone = normalize_phone(phone)
                if not normalized_phone:
                    continue  # pula para o próximo cliente

                primeiro_nome = nome_cliente.split()[0] if nome_cliente else ""
                variables = {
                    "nome_cliente": primeiro_nome,
                    "produto_recomendado": produto_recomendado or "",
                    "link_personalizado": f"https://seusite.com/compra/{client_id}",
                    "percentual_desconto": percentual_desconto or "",
                    "validade_desconto": validade_desconto or ""
                }

                response = await send_message_via_http(normalized_phone, message, image_url, variables=variables)
                print(f"→ Enviado para {normalized_phone}: {response}")

                # Atualiza status da campanha
                cursor.execute("""
                    UPDATE campaign_clients
                    SET status = 'sent', sent_at = %s, updated_at = %s
                    WHERE client_id = %s AND campaign_id = %s
                """, (datetime.now(), datetime.now(), client_id, campaign_id))

        conn.commit()
        print("✅ Todas as campanhas foram processadas.")
    except Exception as e:
        print(f"⚠️ ERRO ao processar campanhas: {e}")
    finally:
        cursor.close()
        conn.close()

# === EXECUÇÃO ===
if __name__ == "__main__":
    asyncio.run(process_campaigns())
    