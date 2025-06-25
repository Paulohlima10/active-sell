import re
import uuid
import asyncpg
from fastapi import APIRouter, Request
from datetime import datetime, timezone
from evolutionapi.client import EvolutionClient
from evolutionapi.models.message import TextMessage, MediaMessage, MediaType
from logs.logging_config import log_message
import requests
import base64
import os


router = APIRouter()

DB_CONFIG = {
    "host": "aws-0-us-east-1.pooler.supabase.com",
    "port": 6543,
    "database": "postgres",
    "user": "postgres.gzzvydiznhwaxrahzkjt",
    "password": "Activesell@01"
}

WHATSAPP_API_KEY = "132830D31E74-4F40-B8B3-AF27DC0D5B91"
INSTANCE_ID = "ActiveSell"
WHATSAPP_URL = "http://100.24.46.53:8080"
EVOLUTION_API_TOKEN = "429683C4C977415CAAFCCE10F7D57E11"

evo_client = EvolutionClient(
    base_url=WHATSAPP_URL,
    api_token=EVOLUTION_API_TOKEN
)

async def get_db_conn():
    await log_message("info", "Abrindo conexão com o banco de dados")
    return await asyncpg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )

async def get_or_create_conversation(conn, client_id, client_name):
    await log_message("info", f"Buscando ou criando conversa para client_id: {client_id}, client_name: {client_name}")
    row = await conn.fetchrow(
        "SELECT id FROM conversations WHERE client_id = $1", client_id
    )
    if row:
        await log_message("info", f"Conversa encontrada: {row['id']}")
        return row["id"]
    conv_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await conn.execute(
        """
        INSERT INTO conversations (id, client_id, client_name, status, last_seen, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        conv_id, client_id, client_name, "online", now, now, now
    )
    await log_message("info", f"Conversa criada: {conv_id}")
    return conv_id

async def send_whatsapp_message(phone_number, msg, image_url=None):
    await log_message("info", f"Preparando para enviar mensagem para {phone_number} (imagem: {bool(image_url)})")
    if image_url:
        message = MediaMessage(
            number=phone_number,
            mediatype=MediaType.IMAGE.value,
            mimetype="image/jpeg",
            caption=msg,
            media=image_url,
            fileName="imagem.jpg"
        )
        response = evo_client.messages.send_media(
            instance_id=INSTANCE_ID,
            message=message,
            instance_token=WHATSAPP_API_KEY
        )
    else:
        message = TextMessage(number=phone_number, text=msg, delay=1000)
        response = evo_client.messages.send_text(
            instance_id=INSTANCE_ID,
            message=message,
            instance_token=WHATSAPP_API_KEY
        )
    await log_message("info", f"Mensagem enviada para {phone_number}: {msg} response: {response}")
    return response

async def send_text_via_http(
    phone_number,
    msg,
    msg_id=None,
    context_info=None,
    token="9C84DC7EBCC6-4B17-8625-A4A60018AC03",
    url=f"{os.getenv('WUZAPI_BASE_URL')}/chat/send/text"
):
    await log_message("info", f"Enviando mensagem HTTP para {phone_number}: {msg}")
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    if msg_id is None:
        msg_id = uuid.uuid4().hex.upper()
    payload = {
        "Phone": phone_number,
        "Body": msg,
        "Id": msg_id
    }
    if context_info:
        payload["ContextInfo"] = context_info
    response = requests.post(url, headers=headers, json=payload)
    await log_message("info", f"Resposta HTTP: {response.status_code} - {response.text}")
    return response.json()

async def send_image_via_http(
    phone_number,
    image_url,
    token="9C84DC7EBCC6-4B17-8625-A4A60018AC03",
    url=f"{os.getenv('WUZAPI_BASE_URL')}/chat/send/image"
):
    await log_message("info", f"Baixando imagem para envio: {image_url}")
    response = requests.get(image_url)
    if response.status_code != 200:
        await log_message("error", f"Erro ao baixar imagem: {response.status_code}")
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
    headers = {
        "Token": token,
        "Content-Type": "application/json"
    }
    await log_message("info", f"Enviando imagem para {phone_number}")
    resp = requests.post(url, headers=headers, json=payload)
    await log_message("info", f"Resposta HTTP imagem: {resp.status_code} - {resp.text}")
    return resp.json()

async def handle_messages_upsert(msg_data):
    await log_message("info", f"Iniciando processamento de messages.upsert: {msg_data}")
    remote_jid = msg_data.get("key", {}).get("remoteJid", "")
    phone_number = re.sub(r"@s\.whatsapp\.net$", "", remote_jid)
    client_name = msg_data.get("pushName", "Desconhecido")
    raw_type = msg_data.get("messageType", "conversation")

    # Mapeamento para os tipos aceitos pelo banco
    if raw_type == "conversation":
        message_type = "text"
    elif raw_type == "imageMessage":
        message_type = "image"
    else:
        message_type = "text"  # padrão para evitar erro

    message_timestamp = msg_data.get("messageTimestamp")
    if message_timestamp:
        msg_dt = datetime.fromtimestamp(message_timestamp, tz=timezone.utc)
    else:
        msg_dt = datetime.now(timezone.utc)

    msg = msg_data.get("message", {})
    if "conversation" in msg:
        content = msg.get("conversation", "")
        file_url = None
        file_name = None
    elif "imageMessage" in msg:
        img = msg["imageMessage"]
        content = img.get("caption", "")
        file_url = img.get("url")
        file_name = "imagem.jpg"
    else:
        content = ""
        file_url = None
        file_name = None

    conn = await get_db_conn()
    try:
        conversation_id = await get_or_create_conversation(conn, phone_number, client_name)
        msg_id = str(uuid.uuid4())
        from_me = msg_data.get("key", {}).get("fromMe", False)
        sender = "agent" if from_me else "client"
        await log_message("info", f"Inserindo mensagem no banco: {msg_id} para {phone_number}")
        await conn.execute(
            """
            INSERT INTO messages (
                id, conversation_id, content, sender, read, type, file_url, file_name, message_timestamp, source
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            msg_id, conversation_id, content, sender, True, message_type, file_url, file_name, msg_dt, "whatsapp"
        )
        await log_message("info", f"Mensagem processada: {msg_id} para {phone_number} - {content}")
    except Exception as e:
        await log_message("error", f"Erro ao inserir mensagem: {e}")
        raise
    finally:
        await conn.close()

async def handle_insert_message(record):
    await log_message("info", f"Iniciando handle_insert_message para record: {record}")
    # Só envia se a mensagem NÃO veio do WhatsApp
    if record.get("source") == "whatsapp":
        await log_message("info", "Mensagem ignorada pois veio do WhatsApp")
        return

    conversation_id = record.get("conversation_id")
    content = record.get("content", "")
    image_url = record.get("file_url")

    phone_number = None
    conn = await get_db_conn()
    await log_message("info", f"Buscando conversa com ID: {conversation_id}")
    try:
        row = await conn.fetchrow(
            """
            SELECT client_id
            FROM conversations
            WHERE id = $1
            """,
            conversation_id
        )
        if row:
            phone_number = row["client_id"]
    except Exception as e:
        await log_message("error", f"Erro ao buscar conversa: {e}")
        raise
    finally:
        await conn.close()

    if phone_number:
        if image_url:
            await log_message("info", f"Enviando imagem via HTTP para {phone_number}")
            await send_image_via_http(phone_number, image_url) 
        else:
            await log_message("info", f"Enviando texto via HTTP para {phone_number}")
            await send_text_via_http(phone_number, content)

async def handle_new_event_message(event_data):
    await log_message("info", f"Iniciando handle_new_event_message: {event_data}")
    info = event_data.get("Info", {})
    message = event_data.get("Message", {})
    chat_jid = info.get("Chat", "")
    phone_number = re.sub(r"@s\.whatsapp\.net$", "", chat_jid)
    client_name = info.get("PushName", "Desconhecido")
    message_type = info.get("Type", "text")
    message_timestamp = info.get("Timestamp")
    if message_timestamp:
        try:
            msg_dt = datetime.fromisoformat(message_timestamp.replace("Z", "+00:00"))
        except Exception:
            await log_message("error", f"Erro ao converter timestamp: {message_timestamp}")
            msg_dt = datetime.now(timezone.utc)
    else:
        msg_dt = datetime.now(timezone.utc)

    # Conteúdo da mensagem
    content = message.get("conversation", "")
    file_url = None
    file_name = None

    conn = await get_db_conn()
    try:
        conversation_id = await get_or_create_conversation(conn, phone_number, client_name)
        msg_id = str(uuid.uuid4())
        sender = "client" if not info.get("IsFromMe", False) else "agent"
        await log_message("info", f"Inserindo mensagem (novo formato) no banco: {msg_id} para {phone_number}")
        await conn.execute(
            """
            INSERT INTO messages (
                id, conversation_id, content, sender, read, type, file_url, file_name, message_timestamp, source
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            msg_id, conversation_id, content, sender, True, message_type, file_url, file_name, msg_dt, "whatsapp"
        )
        await log_message("info", f"Mensagem (novo formato) processada: {msg_id} para {phone_number} - {content}")
    except Exception as e:
        await log_message("error", f"Erro ao inserir mensagem (novo formato): {e}")
        raise
    finally:
        await conn.close()

@router.post("/webhook_chat")
async def webhook_chat(request: Request):
    await log_message("info", "Recebendo requisição no webhook_chat")
    data = await request.json()
    await log_message("info", f"Payload recebido: {data}")
    # Evento padrão do WhatsApp
    if data.get("event") == "messages.upsert":
        msg_data = data.get("data", {})
        await handle_messages_upsert(msg_data)

    # Novo formato de mensagem
    elif data.get("type") == "Message" and isinstance(data.get("event"), dict):
        await handle_new_event_message(data["event"])

    # Evento do agente (INSERT na tabela messages)
    elif data.get("type") == "INSERT" and data.get("table") == "messages":
        record = data.get("record", {})
        if record.get("sender") == "agent":
            await handle_insert_message(record)

    return {"message": "Dados recebidos com sucesso"}