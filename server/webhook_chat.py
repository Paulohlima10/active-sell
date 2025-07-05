import re
import uuid
import asyncpg
from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timezone
from logs.logging_config import log_message
import requests
import base64
import os
from supabase import create_client
from agents.agentManager import global_manager

# Desabilitar telemetria do ChromaDB para evitar erros
os.environ["CHROMA_TELEMETRY"] = "false"

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

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL e SUPABASE_KEY precisam estar definidos nas variáveis de ambiente.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_db_conn():
    await log_message("info", "webhook_chat - Abrindo conexão com o banco de dados")
    return await asyncpg.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        statement_cache_size=0,  # Desabilita prepared statements para evitar conflito com pgbouncer
        command_timeout=10,  # Timeout mais conservador para EC2
        server_settings={
            'application_name': 'active-sell-ec2'
        }
    )

async def get_or_create_conversation(conn, client_id, client_name):
    await log_message("info", f"webhook_chat - Buscando ou criando conversa para client_id: {client_id}, client_name: {client_name}")
    row = await conn.fetchrow(
        "SELECT id FROM conversations WHERE client_id = $1", client_id
    )
    if row:
        await log_message("info", f"webhook_chat - Conversa encontrada: {row['id']}")
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
    await log_message("info", f"webhook_chat - Conversa criada: {conv_id}")
    return conv_id

async def send_text_via_http(
    phone_number,
    msg,
    msg_id=None,
    context_info=None,
    token="9C84DC7EBCC6-4B17-8625-A4A60018AC03",
    url=f"{os.getenv('WUZAPI_BASE_URL')}/chat/send/text"
):
    await log_message("info", f"webhook_chat - Enviando mensagem HTTP para {phone_number}: {msg}")
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
    await log_message("info", f"webhook_chat - Resposta envio de mensagem via HTTP: {response.status_code} - {response.text}")
    return response.json()

async def send_image_via_http(
    phone_number,
    image_url,
    token="9C84DC7EBCC6-4B17-8625-A4A60018AC03",
    url=f"{os.getenv('WUZAPI_BASE_URL')}/chat/send/image"
):
    await log_message("info", f"webhook_chat - Baixando imagem para envio: {image_url}")
    response = requests.get(image_url)
    if response.status_code != 200:
        await log_message("error", f"webhook_chat - Erro ao baixar imagem: {response.status_code}")
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
    await log_message("info", f"webhook_chat - Enviando imagem para {phone_number}")
    resp = requests.post(url, headers=headers, json=payload)
    await log_message("info", f"webhook_chat - Resposta HTTP imagem: {resp.status_code} - {resp.text}")
    return resp.json()

async def upload_image_to_supabase(base64_str, file_name):
    img_bytes = base64.b64decode(base64_str)
    now = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    file_path = f"whatsapp_images/{now}_{file_name}"
    res = supabase.storage.from_('conversation-files').upload(file_path, img_bytes, file_options={"content-type": "image/jpeg"})
    if not res:
        raise Exception("Erro ao fazer upload da imagem no Supabase")
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{file_path}"
    return public_url

# =============================
# Função principal solicitada
# =============================
async def agent_responder(conversation_id: str, mensagem_cliente: str):
    await log_message("info", f"agent_responder - Iniciando para conversation_id: {conversation_id}")
    conn = await get_db_conn()
    try:
        # 1. Buscar client_id e empresa_id na tabela conversations
        row = await conn.fetchrow(
            "SELECT client_id, empresa_id FROM conversations WHERE id = $1",
            conversation_id
        )
        if not row:
            await log_message("error", f"agent_responder - Conversa não encontrada: {conversation_id}")
            return {"error": "Conversa não encontrada"}
        
        phone_number = row["client_id"]
        # Extrair apenas o número antes do @, se houver
        if isinstance(phone_number, str) and "@" in phone_number:
            phone_number = phone_number.split("@")[0]
        
        empresa_id = row["empresa_id"]
        
        # 2. Se empresa_id for null, buscar o empresa_id padrão da ai_assistant_config
        if empresa_id is None:
            config_row = await conn.fetchrow(
                "SELECT empresa_id FROM ai_assistant_config LIMIT 1"
            )
            if config_row:
                empresa_id = config_row["empresa_id"]
                await log_message("info", f"agent_responder - Usando empresa_id padrão: {empresa_id}")
            else:
                await log_message("error", f"agent_responder - Nenhuma configuração encontrada na ai_assistant_config")
                return {"error": "Nenhuma configuração de assistente encontrada."}

        # Converter empresa_id para string se for UUID
        if empresa_id is not None:
            empresa_id = str(empresa_id)

        # 3. Verificar se o assistente está habilitado na ai_assistant_config
        config = await conn.fetchrow(
            "SELECT enabled FROM ai_assistant_config WHERE empresa_id = $1",
            empresa_id
        )
        if not config:
            await log_message("info", f"agent_responder - Configuração não encontrada para empresa_id: {empresa_id}")
            return {"error": "Configuração do assistente não encontrada para esta empresa."}
        
        if not config["enabled"]:
            await log_message("info", f"agent_responder - Assistente desabilitado para empresa_id: {empresa_id}")
            return {"error": "Assistente desabilitado para esta empresa."}

        # 4. Perguntar ao agente
        try:
            assistent = global_manager.get_assistant(empresa_id)
            if assistent is None:
                global_manager.add_assistant(empresa_id)
                assistent = global_manager.get_assistant(empresa_id)
                await log_message("info", f"Assistente não encontrado para o parceiro '{empresa_id}' Criar agente.")
            
            if assistent is None:
                await log_message("error", f"Falha ao criar assistente para o parceiro '{empresa_id}'")
                return {"error": f"Falha ao criar assistente para o parceiro '{empresa_id}'"}
            
            # Usar versão assíncrona com timeout otimizado para EC2
            import asyncio
            try:
                response = await asyncio.wait_for(
                    assistent.ask_question_async(mensagem_cliente, conversation_id),
                    timeout=15.0  # 15 segundos de timeout para EC2
                )
                await log_message("info", f"Pergunta feita ao assistente '{empresa_id}': {mensagem_cliente}")
            except asyncio.TimeoutError:
                await log_message("error", f"Timeout ao perguntar ao assistente '{empresa_id}'")
                return {"error": "Timeout ao processar pergunta. Tente novamente."}
        except Exception as e:
            await log_message("error", f"Erro ao perguntar ao assistente '{empresa_id}': {str(e)}")
            return {"error": f"Erro ao perguntar ao assistente: {str(e)}"}

        # 5. Enviar resposta do agente via WhatsApp
        if phone_number:
            await log_message("info", f"agent_responder - Enviando resposta do agente via WhatsApp para {phone_number}")
            await send_text_via_http(phone_number, response)
        return {"response": response}
    except Exception as e:
        await log_message("error", f"agent_responder - Erro geral: {str(e)}")
        return {"error": str(e)}
    finally:
        await conn.close()

async def handle_messages_upsert(msg_data):
    await log_message("info", f"webhook_chat - Iniciando processamento de messages.upsert: {msg_data}")
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
        await log_message("info", f"webhook_chat - Inserindo mensagem no banco: {msg_id} para {phone_number}")
        await conn.execute(
            """
            INSERT INTO messages (
                id, conversation_id, content, sender, read, type, file_url, file_name, message_timestamp, source
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            msg_id, conversation_id, content, sender, True, message_type, file_url, file_name, msg_dt, "whatsapp"
        )
        await log_message("info", f"webhook_chat - Mensagem processada: {msg_id} para {phone_number} - Conteudo: {content}")

    except Exception as e:
        await log_message("error", f"webhook_chat - Erro ao inserir mensagem: {e}")
        raise
    finally:
        await conn.close()
    
    # 4. Enviar resposta do agente via WhatsApp
    print(f"******** sender: {sender}")
    if sender == "client":
        await agent_responder(conversation_id, content)

async def handle_insert_message(record):
    await log_message("info", f"webhook_chat - Iniciando handle_insert_message para record: {record}")
    # Só envia se a mensagem NÃO veio do WhatsApp
    if record.get("source") == "whatsapp":
        await log_message("info", "webhook_chat - Mensagem ignorada pois veio do WhatsApp")
        return

    conversation_id = record.get("conversation_id")
    content = record.get("content", "")
    image_url = record.get("file_url")

    phone_number = None
    conn = await get_db_conn()
    await log_message("info", f"webhook_chat - Buscando conversa com ID: {conversation_id}")
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
        await log_message("error", f"webhook_chat - Erro ao buscar conversa: {e}")
        raise
    finally:
        await conn.close()

    if phone_number:
        if image_url:
            await log_message("info", f"webhook_chat - Enviando imagem via HTTP para {phone_number}")
            await send_image_via_http(phone_number, image_url) 
        else:
            await log_message("info", f"webhook_chat - Enviando texto via HTTP para {phone_number}")
            await send_text_via_http(phone_number, content)
    

async def handle_new_event_message(event_data):
    await log_message("info", f"webhook_chat - Iniciando handle_new_event_message: {event_data}")
    info = event_data.get("Info", {})
    message = event_data.get("Message", {})
    chat_jid = info.get("Chat", "")
    phone_number = re.sub(r"@s\\.whatsapp\\.net$", "", chat_jid)
    client_name = info.get("PushName", "Desconhecido")
    message_type = info.get("Type", "text")
    message_timestamp = info.get("Timestamp")
    if message_timestamp:
        try:
            msg_dt = datetime.fromisoformat(message_timestamp.replace("Z", "+00:00"))
        except Exception:
            await log_message("error", f"webhook_chat - Erro ao converter timestamp: {message_timestamp}")
            msg_dt = datetime.now(timezone.utc)
    else:
        msg_dt = datetime.now(timezone.utc)

    def extract_message_content(message):
        if "extendedTextMessage" in message:
            return message["extendedTextMessage"].get("text", "")
        elif "conversation" in message:
            return message.get("conversation", "")
        elif "imageMessage" in message:
            return message["imageMessage"].get("caption", "")
        return ""

    # --- NOVA LÓGICA PARA BASE64 DE IMAGEM ---
    base64_img = event_data.get("base64")
    file_url = None
    file_name = None

    if base64_img:
        await log_message("info", f"webhook_chat - Recebeu o base64 da imagem")
        file_name = event_data.get("fileName", f"{uuid.uuid4()}.jpeg")
        file_url = await upload_image_to_supabase(base64_img, file_name)
        await log_message("info", f"webhook_chat - retorno do upload da imagem: {file_url}")
        message_type = "image"
        content = ""
    else:
        content = extract_message_content(message)
        file_url = None
        file_name = None

    conn = await get_db_conn()
    try:
        conversation_id = await get_or_create_conversation(conn, phone_number, client_name)
        msg_id = str(uuid.uuid4())
        sender = "client" if not info.get("IsFromMe", False) else "agent"
        await log_message("info", f"webhook_chat - Inserindo mensagem (novo formato) no banco: {msg_id} para {phone_number}")
        await conn.execute(
            """
            INSERT INTO messages (
                id, conversation_id, content, sender, read, type, file_url, file_name, message_timestamp, source
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            msg_id, conversation_id, content, sender, True, message_type, file_url, file_name, msg_dt, "whatsapp"
        )
        await log_message("info", f"webhook_chat - Mensagem (novo formato) processada: {msg_id} para {phone_number} - Conteudo: {content}")
    except Exception as e:
        await log_message("error", f"webhook_chat - Erro ao inserir mensagem (novo formato): {e}")
        raise
    finally:
        await conn.close()
    
    # 4. Enviar resposta do agente via WhatsApp
    print(f"******** sender: {sender}")
    if sender == "client":
        await agent_responder(conversation_id, content)

@router.post("/webhook_chat")
async def webhook_chat(request: Request):
    await log_message("info", "webhook_chat - Recebendo requisição no webhook_chat")
    data = await request.json()
    await log_message("info", f"webhook_chat - Payload recebido: {data}")
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

